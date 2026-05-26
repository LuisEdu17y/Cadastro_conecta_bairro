"""
routers/avaliacoes_router.py
-----------------------------
- GET    /eventos/{id}/avaliacoes   → lista avaliações do evento (público)
- POST   /eventos/{id}/avaliacoes   → cria ou atualiza avaliação (autenticado)
- DELETE /avaliacoes/{id}           → remove avaliação (própria ou admin)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import Avaliacao, AvaliacaoCreate, AvaliacaoPublic, Evento, Inscricao, Usuario
from auth import usuario_atual, usuario_atual_opcional

router = APIRouter(tags=["Avaliações"])


def _para_publico(a: Avaliacao, usuario_nome: str, usuario_atual_id: Optional[int], is_admin: bool) -> AvaliacaoPublic:
    return AvaliacaoPublic(
        id=a.id,
        nota=a.nota,
        comentario=a.comentario,
        criado_em=a.criado_em,
        usuario_nome=usuario_nome,
        pode_deletar=(usuario_atual_id == a.usuario_id or is_admin),
    )


@router.get("/eventos/{evento_id}/avaliacoes", response_model=list[AvaliacaoPublic])
def listar_avaliacoes(
    evento_id: int,
    session: Session = Depends(get_session),
    usuario: Optional[Usuario] = Depends(usuario_atual_opcional),
):
    if not session.get(Evento, evento_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    avaliacoes = session.exec(
        select(Avaliacao).where(Avaliacao.evento_id == evento_id)
        .order_by(Avaliacao.criado_em.desc())
    ).all()

    uid = usuario.id if usuario else None
    is_admin = usuario.role == "admin" if usuario else False

    resultado = []
    for a in avaliacoes:
        autor = session.get(Usuario, a.usuario_id)
        nome = autor.nome if autor else "Usuário removido"
        resultado.append(_para_publico(a, nome, uid, is_admin))
    return resultado


@router.post("/eventos/{evento_id}/avaliacoes", response_model=AvaliacaoPublic, status_code=201)
def criar_ou_atualizar_avaliacao(
    evento_id: int,
    dados: AvaliacaoCreate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    if not session.get(Evento, evento_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    inscrito = session.exec(
        select(Inscricao).where(
            Inscricao.evento_id == evento_id,
            Inscricao.usuario_id == usuario.id,
        )
    ).first()
    if not inscrito:
        raise HTTPException(status_code=403, detail="Você precisa estar inscrito para avaliar este evento")

    if not 1 <= dados.nota <= 5:
        raise HTTPException(status_code=400, detail="Nota deve ser entre 1 e 5")

    existente = session.exec(
        select(Avaliacao).where(
            Avaliacao.evento_id == evento_id,
            Avaliacao.usuario_id == usuario.id,
        )
    ).first()

    if existente:
        existente.nota = dados.nota
        existente.comentario = dados.comentario
        session.add(existente)
        session.commit()
        session.refresh(existente)
        return _para_publico(existente, usuario.nome, usuario.id, usuario.role == "admin")

    nova = Avaliacao(
        nota=dados.nota,
        comentario=dados.comentario,
        evento_id=evento_id,
        usuario_id=usuario.id,
    )
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return _para_publico(nova, usuario.nome, usuario.id, usuario.role == "admin")


@router.delete("/avaliacoes/{avaliacao_id}", status_code=204)
def deletar_avaliacao(
    avaliacao_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    a = session.get(Avaliacao, avaliacao_id)
    if not a:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    if a.usuario_id != usuario.id and usuario.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão para remover esta avaliação")
    session.delete(a)
    session.commit()
