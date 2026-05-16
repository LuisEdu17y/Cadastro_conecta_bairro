"""
routers/comentarios_router.py
------------------------------
- GET    /eventos/{id}/comentarios   → lista comentários do evento (público)
- POST   /eventos/{id}/comentarios   → adiciona comentário (autenticado)
- DELETE /comentarios/{id}           → remove comentário (próprio ou admin)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import Comentario, ComentarioCreate, ComentarioPublic, Evento, Usuario
from auth import usuario_atual, usuario_atual_opcional

router = APIRouter(tags=["Comentários"])


def _para_publico(c: Comentario, usuario_nome: str, usuario_atual_id: Optional[int], is_admin: bool) -> ComentarioPublic:
    return ComentarioPublic(
        id=c.id,
        texto=c.texto,
        criado_em=c.criado_em,
        usuario_id=c.usuario_id,
        usuario_nome=usuario_nome,
        pode_deletar=(usuario_atual_id == c.usuario_id or is_admin),
    )


from typing import Optional


@router.get("/eventos/{evento_id}/comentarios", response_model=list[ComentarioPublic])
def listar_comentarios(
    evento_id: int,
    session: Session = Depends(get_session),
    usuario: Optional[Usuario] = Depends(usuario_atual_opcional),
):
    if not session.get(Evento, evento_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    comentarios = session.exec(
        select(Comentario).where(Comentario.evento_id == evento_id)
        .order_by(Comentario.criado_em.asc())
    ).all()

    uid = usuario.id if usuario else None
    is_admin = usuario.role == "admin" if usuario else False

    resultado = []
    for c in comentarios:
        autor = session.get(Usuario, c.usuario_id)
        nome = autor.nome if autor else "Usuário removido"
        resultado.append(_para_publico(c, nome, uid, is_admin))
    return resultado


@router.post("/eventos/{evento_id}/comentarios", response_model=ComentarioPublic, status_code=201)
def criar_comentario(
    evento_id: int,
    dados: ComentarioCreate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    if not session.get(Evento, evento_id):
        raise HTTPException(status_code=404, detail="Evento não encontrado")

    texto = dados.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Comentário não pode ser vazio")
    if len(texto) > 500:
        raise HTTPException(status_code=400, detail="Máximo de 500 caracteres")

    c = Comentario(texto=texto, evento_id=evento_id, usuario_id=usuario.id)
    session.add(c)
    session.commit()
    session.refresh(c)
    return _para_publico(c, usuario.nome, usuario.id, usuario.role == "admin")


@router.delete("/comentarios/{comentario_id}", status_code=204)
def deletar_comentario(
    comentario_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    c = session.get(Comentario, comentario_id)
    if not c:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    if c.usuario_id != usuario.id and usuario.role != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão para remover este comentário")
    session.delete(c)
    session.commit()
