"""
routers/eventos_router.py
-------------------------
Rotas de eventos e inscrições.

Públicas:
- GET    /eventos                    → lista (com flag 'inscrito' se logado)
- GET    /eventos/{id}               → detalhes

Restritas a morador autenticado:
- POST   /eventos/{id}/inscrever     → confirma presença
- DELETE /eventos/{id}/inscrever     → cancela presença
- GET    /eventos/meus               → eventos em que estou inscrito

Restritas a admin:
- POST   /eventos                    → cria
- PUT    /eventos/{id}               → edita
- DELETE /eventos/{id}               → remove
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from database import get_session
from models import (
    Usuario,
    Evento,
    EventoCreate,
    EventoUpdate,
    EventoPublic,
    Inscricao,
)
from auth import usuario_atual, apenas_admin, usuario_atual_opcional

router = APIRouter(prefix="/eventos", tags=["Eventos"])


# Helper: monta um EventoPublic com total_inscritos e flag 'inscrito'
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

    publico = EventoPublic(
        **evento.model_dump(),
        total_inscritos=total or 0,
        inscrito=inscrito,
    )
    return publico


# ---------------------- LISTAGEM ----------------------

@router.get("", response_model=list[EventoPublic])
def listar_eventos(
    modalidade: Optional[str] = None,
    session: Session = Depends(get_session),
    usuario: Optional[Usuario] = Depends(usuario_atual_opcional),
):
    """Lista todos os eventos. Filtra por modalidade se informada."""
    query = select(Evento).order_by(Evento.criado_em.desc())
    if modalidade and modalidade.lower() != "todos":
        query = query.where(Evento.modalidade == modalidade)
    eventos = session.exec(query).all()
    return [_para_publico(session, ev, usuario) for ev in eventos]


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


# ---------------------- INSCRIÇÃO ----------------------

@router.post("/{evento_id}/inscrever", status_code=201)
def inscrever_em_evento(
    evento_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    # Verifica duplicidade
    ja = session.exec(
        select(Inscricao).where(
            Inscricao.evento_id == evento_id,
            Inscricao.usuario_id == usuario.id,
        )
    ).first()
    if ja:
        raise HTTPException(status_code=409, detail="Você já está inscrito neste evento")

    # Verifica limite de vagas (0 = ilimitado)
    if evento.vagas and evento.vagas > 0:
        total = session.exec(
            select(func.count(Inscricao.id)).where(Inscricao.evento_id == evento_id)
        ).one()
        if total >= evento.vagas:
            raise HTTPException(status_code=409, detail="Vagas esgotadas para este evento")

    nova = Inscricao(usuario_id=usuario.id, evento_id=evento_id)
    session.add(nova)
    session.commit()
    return {"mensagem": "Inscrição confirmada!", "evento_id": evento_id}


@router.delete("/{evento_id}/inscrever")
def cancelar_inscricao(
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
    session.delete(inscricao)
    session.commit()
    return {"mensagem": "Inscrição cancelada"}


# ---------------------- ADMIN: CRUD ----------------------

@router.post("", response_model=EventoPublic, status_code=201)
def criar_evento(
    dados: EventoCreate,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    """Apenas admin pode criar."""
    novo = Evento(**dados.model_dump(), criado_por_id=admin.id)
    session.add(novo)
    session.commit()
    session.refresh(novo)
    return _para_publico(session, novo, admin)


@router.put("/{evento_id}", response_model=EventoPublic)
def atualizar_evento(
    evento_id: int,
    dados: EventoUpdate,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    # Aplica somente campos enviados (não-None)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(evento, campo, valor)

    session.add(evento)
    session.commit()
    session.refresh(evento)
    return _para_publico(session, evento, admin)


@router.delete("/{evento_id}")
def deletar_evento(
    evento_id: int,
    session: Session = Depends(get_session),
    admin: Usuario = Depends(apenas_admin),
):
    evento = session.get(Evento, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    session.delete(evento)
    session.commit()
    return {"mensagem": "Evento excluído com sucesso"}
