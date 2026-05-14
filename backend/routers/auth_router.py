"""
routers/auth_router.py
----------------------
Rotas públicas de autenticação:
- POST /auth/registro → cria um novo morador
- POST /auth/login    → retorna token JWT
- GET  /auth/me       → dados do usuário autenticado
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import (
    Usuario,
    UsuarioCreate,
    UsuarioPublic,
    LoginRequest,
    TokenResponse,
)
from auth import (
    hash_senha,
    verificar_senha,
    criar_token,
    usuario_atual,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/registro", response_model=UsuarioPublic, status_code=201)
def registrar(dados: UsuarioCreate, session: Session = Depends(get_session)):
    """Cadastra um novo morador. Email precisa ser único."""
    # Verifica se o email já existe
    existente = session.exec(
        select(Usuario).where(Usuario.email == dados.email)
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado",
        )

    # Validação simples de senha
    if len(dados.senha) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha precisa ter no mínimo 6 caracteres",
        )

    novo = Usuario(
        nome=dados.nome.strip(),
        email=dados.email.strip().lower(),
        bairro=dados.bairro,
        telefone=dados.telefone,
        senha_hash=hash_senha(dados.senha),
        role="morador",
    )
    session.add(novo)
    session.commit()
    session.refresh(novo)
    return novo


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, session: Session = Depends(get_session)):
    """Autentica um usuário e retorna o token JWT + dados públicos."""
    email = dados.email.strip().lower()
    usuario = session.exec(
        select(Usuario).where(Usuario.email == email)
    ).first()

    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Procure o administrador.",
        )

    # 'sub' é o claim padrão JWT para identidade do usuário
    token = criar_token({"sub": str(usuario.id), "role": usuario.role})

    return TokenResponse(access_token=token, usuario=usuario)


@router.get("/me", response_model=UsuarioPublic)
def quem_sou_eu(usuario: Usuario = Depends(usuario_atual)):
    """Retorna os dados do usuário autenticado (útil pro frontend após reload)."""
    return usuario
