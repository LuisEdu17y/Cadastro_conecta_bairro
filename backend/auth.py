"""
auth.py
-------
Autenticação e autorização da aplicação.

- Hash de senhas com bcrypt (uso direto, sem passlib)
- Geração e verificação de JWT (via python-jose)
- Dependências FastAPI:
    * usuario_atual    → exige token válido
    * apenas_admin     → exige token + role admin

A chave secreta vem da variável de ambiente JWT_SECRET. Se não estiver
definida, um valor padrão é usado (OK para desenvolvimento, NÃO para produção).
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from database import get_session
from models import Usuario


# --------- Configuração ---------
JWT_SECRET = os.getenv("JWT_SECRET", "troque-este-segredo-em-producao-por-favor-12345")
JWT_ALGORITHM = "HS256"
JWT_EXPIRA_MINUTOS = 60 * 24 * 7   # 7 dias

# Lê o token do header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


# --------- Hash de senha ---------
# Usamos bcrypt diretamente (passlib está sem manutenção e quebra com bcrypt >= 4.1).

def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha_plana.encode("utf-8"), senha_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------- JWT ---------

def criar_token(dados: dict, expira_em: Optional[timedelta] = None) -> str:
    payload = dados.copy()
    expira = datetime.utcnow() + (expira_em or timedelta(minutes=JWT_EXPIRA_MINUTOS))
    payload.update({"exp": expira})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


# --------- Dependências FastAPI ---------

def usuario_atual(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    """Retorna o usuário autenticado. 401 se o token estiver ausente/inválido."""
    erro_401 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou ausentes",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise erro_401

    payload = decodificar_token(token)
    if not payload:
        raise erro_401

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise erro_401

    usuario = session.get(Usuario, int(usuario_id))
    if not usuario or not usuario.ativo:
        raise erro_401

    return usuario


def apenas_admin(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
    """Mesma coisa que usuario_atual, mas exige role='admin'."""
    if usuario.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return usuario


def usuario_atual_opcional(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Optional[Usuario]:
    """Como usuario_atual, mas NÃO lança erro se não estiver autenticado.
    Útil em rotas públicas que enriquecem a resposta quando há login."""
    if not token:
        return None
    payload = decodificar_token(token)
    if not payload:
        return None
    usuario_id = payload.get("sub")
    if usuario_id is None:
        return None
    usuario = session.get(Usuario, int(usuario_id))
    if not usuario or not usuario.ativo:
        return None
    return usuario


# --------- Bootstrap: cria admin padrão se não existir ---------

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@conectabairro.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def garantir_admin_padrao(session: Session) -> None:
    """
    Garante que existe um admin no banco e popula alguns eventos de exemplo
    na primeira execução.

    Credenciais configuráveis via variáveis de ambiente:
        ADMIN_EMAIL     (padrão: admin@conectabairro.com)
        ADMIN_PASSWORD  (padrão: admin123 — troque em produção!)

    Se o admin já existir e ADMIN_PASSWORD estiver definida no ambiente,
    atualiza a senha para o valor configurado.
    """
    from models import Evento  # import local para evitar ciclo

    existe = session.exec(
        select(Usuario).where(Usuario.email == ADMIN_EMAIL)
    ).first()

    if existe:
        # Atualiza senha se ADMIN_PASSWORD foi explicitamente configurada
        if os.getenv("ADMIN_PASSWORD"):
            existe.senha_hash = hash_senha(ADMIN_PASSWORD)
            session.add(existe)
            session.commit()
        return

    admin = Usuario(
        nome="Administrador",
        email=ADMIN_EMAIL,
        senha_hash=hash_senha(ADMIN_PASSWORD),
        role="admin",
        bairro="Sol Nascente",
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)

    # Eventos de exemplo (apenas na primeira execução, junto com o admin)
    eventos_exemplo = [
        Evento(
            titulo="Aula de Capoeira",
            descricao="Aulas abertas para todas as idades, com mestres da comunidade. Traga roupa confortável!",
            modalidade="Capoeira",
            cor="orange",
            local="Praça Central",
            data="Sexta, 19:00",
            vagas=25,
            criado_por_id=admin.id,
        ),
        Evento(
            titulo="Zumba na Praça",
            descricao="Encontro semanal de zumba ao ar livre. Energia, ritmo e muita diversão para começar bem o sábado.",
            modalidade="Zumba",
            cor="pink",
            local="Praça da Juventude",
            data="Sábado, 08:00",
            vagas=40,
            criado_por_id=admin.id,
        ),
        Evento(
            titulo="Pelada do Bairro",
            descricao="Time misto, formado na hora. Chegue cedo para garantir vaga e leve sua garrafinha de água.",
            modalidade="Futebol",
            cor="green",
            local="Campo do Sol Nascente",
            data="Domingo, 16:00",
            vagas=22,
            criado_por_id=admin.id,
        ),
        Evento(
            titulo="Roda de Conversa: Vizinhança Ativa",
            descricao="Bate-papo sobre projetos da comunidade, ideias para o bairro e propostas de novos eventos.",
            modalidade="Outros",
            cor="blue",
            local="Centro Comunitário",
            data="Quarta, 20:00",
            vagas=0,
            criado_por_id=admin.id,
        ),
        Evento(
            titulo="Treino Funcional",
            descricao="Circuito ao ar livre com foco em condicionamento. Para iniciantes e veteranos.",
            modalidade="Outros",
            cor="purple",
            local="Quadra Poliesportiva",
            data="Terça e Quinta, 06:30",
            vagas=20,
            criado_por_id=admin.id,
        ),
    ]
    session.add_all(eventos_exemplo)
    session.commit()
