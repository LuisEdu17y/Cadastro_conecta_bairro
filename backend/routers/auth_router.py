"""
routers/auth_router.py
----------------------
Rotas de autenticação:
- POST /auth/registro          → cria um novo morador
- POST /auth/login             → retorna token JWT
- GET  /auth/me                → dados do usuário autenticado
- POST /auth/esqueci-senha     → envia e-mail com link de reset
- POST /auth/redefinir-senha   → valida token e define nova senha
"""

import secrets
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlmodel import Session, select

from database import get_session
from models import (
    Usuario,
    UsuarioCreate,
    UsuarioPublic,
    UsuarioUpdate,
    LoginRequest,
    TokenResponse,
    PasswordResetToken,
    EsqueciSenhaRequest,
    RedefinirSenhaRequest,
)
from auth import (
    hash_senha,
    verificar_senha,
    criar_token,
    usuario_atual,
)
from email_service import email_redefinir_senha

router = APIRouter(prefix="/auth", tags=["Autenticação"])

RESET_TOKEN_HORAS = 1


@router.post("/registro", response_model=UsuarioPublic, status_code=201)
def registrar(dados: UsuarioCreate, session: Session = Depends(get_session)):
    """Cadastra um novo morador. Email precisa ser único."""
    existente = session.exec(
        select(Usuario).where(Usuario.email == dados.email)
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado",
        )

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
        precisa_cesta_basica=dados.precisa_cesta_basica or False,
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

    token = criar_token({"sub": str(usuario.id), "role": usuario.role})
    return TokenResponse(access_token=token, usuario=usuario)


@router.get("/me", response_model=UsuarioPublic)
def quem_sou_eu(usuario: Usuario = Depends(usuario_atual)):
    """Retorna os dados do usuário autenticado."""
    return usuario


@router.put("/me", response_model=UsuarioPublic)
def atualizar_perfil(
    dados: UsuarioUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    """Atualiza nome, bairro, telefone ou senha do próprio usuário."""
    if dados.nome is not None:
        nome = dados.nome.strip()
        if not nome:
            raise HTTPException(status_code=400, detail="Nome não pode ser vazio")
        usuario.nome = nome

    if dados.bairro is not None:
        usuario.bairro = dados.bairro.strip() or None

    if dados.telefone is not None:
        usuario.telefone = dados.telefone.strip() or None

    if dados.senha is not None:
        if len(dados.senha) < 6:
            raise HTTPException(status_code=400, detail="A senha precisa ter no mínimo 6 caracteres")
        usuario.senha_hash = hash_senha(dados.senha)

    if dados.precisa_cesta_basica is not None:
        usuario.precisa_cesta_basica = dados.precisa_cesta_basica

    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "perfil"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
EXTENSOES_FOTO = {".jpg", ".jpeg", ".png", ".webp"}
TAMANHO_MAX_MB = 3


@router.post("/me/foto", response_model=UsuarioPublic)
async def upload_foto_perfil(
    arquivo: UploadFile = File(...),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(usuario_atual),
):
    """Faz upload da foto de perfil do usuário autenticado."""
    sufixo = Path(arquivo.filename or "").suffix.lower()
    if sufixo not in EXTENSOES_FOTO:
        raise HTTPException(status_code=400, detail=f"Formato não permitido. Use: {', '.join(EXTENSOES_FOTO)}")

    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAX_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Arquivo muito grande. Máximo: {TAMANHO_MAX_MB} MB")

    import cloudinary_service as cdn
    if cdn.disponivel():
        public_id = f"perfil/usuario_{usuario.id}"
        try:
            usuario.foto_url = cdn.fazer_upload(conteudo, public_id)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Erro ao enviar foto: {exc}")
    else:
        nome_arquivo = f"perfil_{usuario.id}_{uuid.uuid4().hex}{sufixo}"
        caminho = UPLOADS_DIR / nome_arquivo
        if usuario.foto_url and usuario.foto_url.startswith("/uploads/perfil/"):
            antigo = UPLOADS_DIR / Path(usuario.foto_url).name
            if antigo.exists():
                antigo.unlink()
        caminho.write_bytes(conteudo)
        usuario.foto_url = f"/uploads/perfil/{nome_arquivo}"

    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.post("/esqueci-senha", status_code=202)
async def esqueci_senha(
    dados: EsqueciSenhaRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Gera um token de reset e envia e-mail com o link.
    Sempre retorna 202 (não revela se o e-mail existe ou não).
    """
    usuario = session.exec(
        select(Usuario).where(Usuario.email == dados.email.strip().lower())
    ).first()

    if usuario and usuario.ativo:
        # Invalida tokens anteriores deste usuário
        tokens_antigos = session.exec(
            select(PasswordResetToken).where(
                PasswordResetToken.usuario_id == usuario.id,
                PasswordResetToken.usado == False,
            )
        ).all()
        for t in tokens_antigos:
            t.usado = True
            session.add(t)

        token_str = secrets.token_urlsafe(32)
        token = PasswordResetToken(
            token=token_str,
            usuario_id=usuario.id,
            expira_em=datetime.utcnow() + timedelta(hours=RESET_TOKEN_HORAS),
        )
        session.add(token)
        session.commit()

        # Monta o link de reset (usa a origin da requisição ou fallback)
        base_url = str(request.base_url).rstrip("/")
        link = f"{base_url}/redefinir-senha?token={token_str}"

        await email_redefinir_senha(usuario.email, usuario.nome, link)

    return {"mensagem": "Se este e-mail estiver cadastrado, você receberá as instruções em breve."}


@router.post("/redefinir-senha")
def redefinir_senha(
    dados: RedefinirSenhaRequest,
    session: Session = Depends(get_session),
):
    """Valida o token de reset e define a nova senha."""
    token = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token == dados.token)
    ).first()

    if not token or token.usado or token.expira_em < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado",
        )

    if len(dados.nova_senha) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha precisa ter no mínimo 6 caracteres",
        )

    usuario = session.get(Usuario, token.usuario_id)
    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não encontrado ou desativado",
        )

    usuario.senha_hash = hash_senha(dados.nova_senha)
    token.usado = True

    session.add(usuario)
    session.add(token)
    session.commit()

    return {"mensagem": "Senha redefinida com sucesso. Faça login com a nova senha."}
