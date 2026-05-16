"""
routers/eventos_router.py
-------------------------
Rotas de eventos e inscrições.

Públicas:
- GET    /eventos                    → lista (filtros: modalidade, bairro, data_inicio, data_fim, local)
- GET    /eventos/{id}               → detalhes

Restritas a morador autenticado:
- POST   /eventos/{id}/inscrever     → confirma presença
- DELETE /eventos/{id}/inscrever     → cancela presença
- GET    /eventos/meus               → eventos em que estou inscrito

Restritas a admin:
- POST   /eventos                    → cria
- PUT    /eventos/{id}               → edita (notifica inscritos por e-mail)
- DELETE /eventos/{id}               → remove (notifica inscritos por e-mail)
- POST   /eventos/{id}/imagem        → upload de imagem
"""

import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlmodel import Session, select, func

from database import get_session
from models import (
    Usuario,
    Evento,
    EventoCreate,
    EventoUpdate,
    EventoPublic,
    EventosPaginados,
    Inscricao,
)
from auth import usuario_atual, apenas_admin, usuario_atual_opcional
from email_service import (
    email_inscricao_confirmada,
    email_inscricao_cancelada,
    email_evento_atualizado,
    email_evento_cancelado,
)

router = APIRouter(prefix="/eventos", tags=["Eventos"])

# Pasta onde as imagens dos eventos são salvas
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TAMANHO_MAX_MB = 5


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def _para_publico(
    session: Session, evento: Evento, usuario: Optional[Usuario]
) -> EventoPublic:
    total = session.exec(
        select(func.count(Inscricao.id)).where(Inscricao.evento_id == evento.id)
    ).one()

    inscrito = False
    if usuario:
        ja_inscrito = session.exec(
            select(Inscricao).where(
                Inscricao.evento_id == evento.id,
                Inscricao.usuario_id == usuario.id,
            )
        ).first()
        inscrito = ja_inscrito is not None

    return EventoPublic(
        **evento.model_dump(),
        total_inscritos=total or 0,
        inscrito=inscrito,
    )


def _listar_inscritos_com_usuarios(session: Session, evento_id: int) -> list[Usuario]:
    return session.exec(
        select(Usuario)
        .join(Inscricao, Inscricao.usuario_id == Usuario.id)
        .where(Inscricao.evento_id == evento_id)
    ).all()


# ──────────────────────────────────────────────
# LISTAGEM / DETALHE
# ──────────────────────────────────────────────

LIMITE_PADRAO = 12
LIMITE_MAXIMO = 100


ORDENS_VALIDAS = {"recentes", "antigos", "inscritos", "vagas"}


@router.get("", response_model=EventosPaginados)
def listar_eventos(
    modalidade: Optional[str] = None,
    bairro: Optional[str] = None,
    local: Optional[str] = None,
    q: Optional[str] = Query(default=None, description="Busca por título, descrição ou local"),
    ordem: Optional[str] = Query(default="recentes", description="recentes | antigos | inscritos | vagas"),
    data_inicio: Optional[datetime] = Query(default=None, description="Filtrar a partir desta data (ISO 8601)"),
    data_fim: Optional[datetime] = Query(default=None, description="Filtrar até esta data (ISO 8601)"),
    limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO, description="Eventos por página"),
    offset: int = Query(default=0, ge=0, description="Quantos eventos pular"),
    session: Session = Depends(get_session),
    usuario: Optional[Usuario] = Depends(usuario_atual_opcional),
):
    """Lista eventos paginados com filtros, busca e ordenação."""
    query_base = select(Evento)

    if modalidade and modalidade.lower() != "todos":
        query_base = query_base.where(Evento.modalidade == modalidade)
    if bairro:
        query_base = query_base.where(Evento.bairro == bairro)
    if local:
        query_base = query_base.where(Evento.local.ilike(f"%{local}%"))
    if q:
        termo = f"%{q.strip()}%"
        query_base = query_base.where(
            Evento.titulo.ilike(termo)
            | Evento.descricao.ilike(termo)
            | Evento.local.ilike(termo)
        )
    if data_inicio:
        query_base = query_base.where(Evento.data_inicio >= data_inicio)
    if data_fim:
        query_base = query_base.where(Evento.data_inicio <= data_fim)

    # Total para paginação
    total = session.exec(
        select(func.count()).select_from(query_base.subquery())
    ).one()

    # Ordenação
    if ordem == "antigos":
        query_base = query_base.order_by(Evento.criado_em.asc())
    elif ordem == "inscritos":
        sub = (
            select(Inscricao.evento_id, func.count(Inscricao.id).label("cnt"))
            .group_by(Inscricao.evento_id)
            .subquery()
        )
        query_base = (
            query_base.outerjoin(sub, Evento.id == sub.c.evento_id)
            .order_by(func.coalesce(sub.c.cnt, 0).desc(), Evento.criado_em.desc())
        )
    elif ordem == "vagas":
        query_base = query_base.order_by(Evento.vagas.desc(), Evento.criado_em.desc())
    else:  # recentes (padrão)
        query_base = query_base.order_by(Evento.criado_em.desc())

    eventos = session.exec(
        query_base.offset(offset).limit(limite)
    ).all()

    return EventosPaginados(
        total=total,
        limite=limite,
        offset=offset,
        tem_mais=(offset + limite) < total,
        eventos=[_para_publico(session, ev, usuario) for ev in eventos],
    )


@router.get("/meus", response_model=list[EventoPublic])
def meus_eventos(
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    """Eventos em que o usuário logado está inscrito."""
    query = (
        select(Evento)
        .join(Inscricao, Inscricao.evento_id == Evento.id)
        .where(Inscricao.usuario_id == usuario.id)
        .order_by(Inscricao.criado_em.desc())
    )
    eventos = session.exec(query).all()
    return [_para_publico(session, ev, usuario) for ev in eventos]


@router.get("/{evento_id}", response_model=EventoPublic)
def detalhar_evento(
    evento_id: int,
    session: Session = Depends(get_session),
    usuario: Optional[Usuario] = Depends(usuario_atual_opcional),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return _para_publico(session, evento, usuario)


# ──────────────────────────────────────────────
# INSCRIÇÃO
# ──────────────────────────────────────────────

@router.post("/{evento_id}/inscrever", status_code=201)
async def inscrever_em_evento(
    evento_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    ja = session.exec(
        select(Inscricao).where(
            Inscricao.evento_id == evento_id,
            Inscricao.usuario_id == usuario.id,
        )
    ).first()
    if ja:
        raise HTTPException(status_code=409, detail="Você já está inscrito neste evento")

    if evento.vagas and evento.vagas > 0:
        total = session.exec(
            select(func.count(Inscricao.id)).where(Inscricao.evento_id == evento_id)
        ).one()
        if total >= evento.vagas:
            raise HTTPException(status_code=409, detail="Vagas esgotadas para este evento")

    nova = Inscricao(usuario_id=usuario.id, evento_id=evento_id)
    session.add(nova)
    session.commit()

    await email_inscricao_confirmada(
        usuario.email, usuario.nome, evento.titulo, evento.local, evento.data
    )

    return {"mensagem": "Inscrição confirmada!", "evento_id": evento_id}


@router.delete("/{evento_id}/inscrever")
async def cancelar_inscricao(
    evento_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    inscricao = session.exec(
        select(Inscricao).where(
            Inscricao.evento_id == evento_id,
            Inscricao.usuario_id == usuario.id,
        )
    ).first()
    if not inscricao:
        raise HTTPException(status_code=404, detail="Você não está inscrito neste evento")

    evento = session.get(Evento, evento_id)
    session.delete(inscricao)
    session.commit()

    if evento:
        await email_inscricao_cancelada(usuario.email, usuario.nome, evento.titulo)

    return {"mensagem": "Inscrição cancelada"}


# ──────────────────────────────────────────────
# ADMIN: CRUD
# ──────────────────────────────────────────────

@router.post("", response_model=EventoPublic, status_code=201)
def criar_evento(
    dados: EventoCreate,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    novo = Evento(**dados.model_dump(), criado_por_id=admin.id)
    session.add(novo)
    session.commit()
    session.refresh(novo)
    return _para_publico(session, novo, admin)


@router.put("/{evento_id}", response_model=EventoPublic)
async def atualizar_evento(
    evento_id: int,
    dados: EventoUpdate,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(evento, campo, valor)

    session.add(evento)
    session.commit()
    session.refresh(evento)

    # Notifica todos os inscritos sobre a atualização
    inscritos = _listar_inscritos_com_usuarios(session, evento_id)
    for u in inscritos:
        await email_evento_atualizado(u.email, u.nome, evento.titulo, evento.local, evento.data)

    return _para_publico(session, evento, admin)


@router.delete("/{evento_id}")
async def deletar_evento(
    evento_id: int,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    # Coleta inscritos antes de deletar
    inscritos = _listar_inscritos_com_usuarios(session, evento_id)
    titulo = evento.titulo

    session.delete(evento)
    session.commit()

    # Notifica inscritos após deletar
    for u in inscritos:
        await email_evento_cancelado(u.email, u.nome, titulo)

    return {"mensagem": "Evento excluído com sucesso"}


# ──────────────────────────────────────────────
# ADMIN: UPLOAD DE IMAGEM
# ──────────────────────────────────────────────

@router.post("/{evento_id}/imagem", response_model=EventoPublic)
async def upload_imagem(
    evento_id: int,
    arquivo: UploadFile = File(..., description="Imagem do evento (jpg, png, webp, gif — máx 5 MB)"),
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    # Valida extensão
    sufixo = Path(arquivo.filename or "").suffix.lower()
    if sufixo not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não permitido. Use: {', '.join(EXTENSOES_PERMITIDAS)}",
        )

    # Valida tamanho
    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAX_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Máximo: {TAMANHO_MAX_MB} MB",
        )

    import cloudinary_service as cdn

    if cdn.disponivel():
        # Produção: Cloudinary (persistente entre deploys)
        public_id = cdn.public_id_do_evento(evento_id)
        evento.imagem_url = cdn.fazer_upload(conteudo, public_id)
    else:
        # Desenvolvimento: filesystem local
        nome_arquivo = f"evento_{evento_id}_{uuid.uuid4().hex}{sufixo}"
        caminho = UPLOADS_DIR / nome_arquivo
        if evento.imagem_url and evento.imagem_url.startswith("/uploads/"):
            antigo = UPLOADS_DIR / Path(evento.imagem_url).name
            if antigo.exists():
                antigo.unlink()
        caminho.write_bytes(conteudo)
        evento.imagem_url = f"/uploads/{nome_arquivo}"
    session.add(evento)
    session.commit()
    session.refresh(evento)

    return _para_publico(session, evento, admin)
