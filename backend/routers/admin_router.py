"""
routers/admin_router.py
-----------------------
Rotas exclusivas do painel administrativo.

Todas exigem role='admin'.
- GET    /admin/estatisticas              → KPIs do dashboard
- GET    /admin/usuarios                  → lista todos
- PUT    /admin/usuarios/{id}             → ativa/desativa, muda role
- DELETE /admin/usuarios/{id}             → remove (não permite remover a si mesmo)
- GET    /admin/eventos/{id}/inscritos    → lista inscritos num evento
- GET    /admin/eventos/{id}/inscritos/csv → exporta inscritos em CSV
"""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func

from database import get_session
from models import Usuario, UsuarioPublic, Evento, Inscricao
from auth import apenas_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------- DASHBOARD ----------------------

@router.get("/estatisticas")
def estatisticas(
    session: Session = Depends(get_session),
    _: Usuario = Depends(apenas_admin),
):
    """KPIs para o dashboard do admin."""
    total_usuarios = session.exec(select(func.count(Usuario.id))).one()
    total_eventos = session.exec(select(func.count(Evento.id))).one()
    total_inscricoes = session.exec(select(func.count(Inscricao.id))).one()
    total_admins = session.exec(
        select(func.count(Usuario.id)).where(Usuario.role == "admin")
    ).one()

    # Eventos por modalidade (para gráfico)
    por_modalidade = session.exec(
        select(Evento.modalidade, func.count(Evento.id))
        .group_by(Evento.modalidade)
    ).all()

    # Top 5 eventos com mais inscritos
    top = session.exec(
        select(
            Evento.id,
            Evento.titulo,
            Evento.modalidade,
            func.count(Inscricao.id).label("total"),
        )
        .join(Inscricao, Inscricao.evento_id == Evento.id, isouter=True)
        .group_by(Evento.id)
        .order_by(func.count(Inscricao.id).desc())
        .limit(5)
    ).all()

    return {
        "total_usuarios": total_usuarios or 0,
        "total_eventos": total_eventos or 0,
        "total_inscricoes": total_inscricoes or 0,
        "total_admins": total_admins or 0,
        "eventos_por_modalidade": [
            {"modalidade": m, "quantidade": q} for m, q in por_modalidade
        ],
        "top_eventos": [
            {"id": i, "titulo": t, "modalidade": m, "total_inscritos": q}
            for i, t, m, q in top
        ],
    }


# ---------------------- USUÁRIOS ----------------------

@router.get("/usuarios", response_model=list[UsuarioPublic])
def listar_usuarios(
    session: Session = Depends(get_session),
    _: Usuario = Depends(apenas_admin),
):
    return session.exec(select(Usuario).order_by(Usuario.criado_em.desc())).all()


@router.put("/usuarios/{usuario_id}", response_model=UsuarioPublic)
def atualizar_usuario(
    usuario_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    """
    Aceita atualizar:
      - role  ('admin' ou 'morador')
      - ativo (true/false)
    Esses são os únicos campos que o admin pode mudar em outros usuários.
    """
    alvo = session.get(Usuario, usuario_id)
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Bloqueios de segurança
    if alvo.id == admin.id and payload.get("role") not in (None, "admin"):
        raise HTTPException(
            status_code=400,
            detail="Você não pode rebaixar a si mesmo de admin",
        )
    if alvo.id == admin.id and payload.get("ativo") is False:
        raise HTTPException(
            status_code=400,
            detail="Você não pode desativar a si mesmo",
        )

    if "role" in payload and payload["role"] in ("admin", "morador"):
        alvo.role = payload["role"]
    if "ativo" in payload and isinstance(payload["ativo"], bool):
        alvo.ativo = payload["ativo"]

    session.add(alvo)
    session.commit()
    session.refresh(alvo)
    return alvo


@router.delete("/usuarios/{usuario_id}")
def deletar_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    alvo = session.get(Usuario, usuario_id)
    if not alvo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if alvo.id == admin.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir a si mesmo")

    # Remove inscrições do usuário antes (FK)
    inscricoes = session.exec(
        select(Inscricao).where(Inscricao.usuario_id == usuario_id)
    ).all()
    for ins in inscricoes:
        session.delete(ins)

    session.delete(alvo)
    session.commit()
    return {"mensagem": "Usuário removido com sucesso"}


# ---------------------- INSCRITOS DE UM EVENTO ----------------------

@router.get("/eventos/{evento_id}/inscritos", response_model=list[UsuarioPublic])
def listar_inscritos(
    evento_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(apenas_admin),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    query = (
        select(Usuario)
        .join(Inscricao, Inscricao.usuario_id == Usuario.id)
        .where(Inscricao.evento_id == evento_id)
        .order_by(Inscricao.criado_em.desc())
    )
    return session.exec(query).all()


@router.get("/eventos/{evento_id}/inscritos/csv")
def exportar_inscritos_csv(
    evento_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(apenas_admin),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    inscritos = session.exec(
        select(Usuario, Inscricao.criado_em)
        .join(Inscricao, Inscricao.usuario_id == Usuario.id)
        .where(Inscricao.evento_id == evento_id)
        .order_by(Inscricao.criado_em.asc())
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nome", "E-mail", "Bairro", "Telefone", "Inscrito em"])
    for usuario, inscrito_em in inscritos:
        writer.writerow([
            usuario.nome,
            usuario.email,
            usuario.bairro or "",
            usuario.telefone or "",
            inscrito_em.strftime("%d/%m/%Y %H:%M"),
        ])

    nome_arquivo = evento.titulo.replace(" ", "_").lower()[:40]
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="inscritos_{nome_arquivo}.csv"'},
    )
