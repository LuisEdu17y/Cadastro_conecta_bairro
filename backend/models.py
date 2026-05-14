"""
models.py
---------
Modelos de dados da aplicação Conecta Bairro.

Três entidades principais:
- Usuario     → moradores e administradores cadastrados
- Evento      → eventos comunitários
- Inscricao   → relação N:N entre usuários e eventos (presença confirmada)

Cada modelo tem variações:
- *Base    → campos compartilhados
- (sem sufixo, com table=True) → entidade real no banco
- *Public  → o que sai pela API (não expõe senha hash)
- *Create  → o que entra pela API ao criar
- *Update  → o que entra ao editar (todos opcionais)
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


# ============================================================
# USUÁRIO
# ============================================================

class UsuarioBase(SQLModel):
    nome: str
    email: str = Field(index=True, unique=True)
    bairro: Optional[str] = None
    telefone: Optional[str] = None


class Usuario(UsuarioBase, table=True):
    """Tabela real de usuários. NUNCA retornar este modelo direto pela API
    (expõe o hash da senha). Use UsuarioPublic."""
    id: Optional[int] = Field(default=None, primary_key=True)
    senha_hash: str
    role: str = Field(default="morador")  # 'morador' ou 'admin'
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    ativo: bool = Field(default=True)

    # Relação reversa: eventos em que o usuário está inscrito
    inscricoes: list["Inscricao"] = Relationship(back_populates="usuario")


class UsuarioCreate(UsuarioBase):
    """Payload de cadastro público (POST /auth/registro)."""
    senha: str


class UsuarioPublic(UsuarioBase):
    """Resposta pública — sem senha."""
    id: int
    role: str
    criado_em: datetime
    ativo: bool


class UsuarioUpdate(SQLModel):
    nome: Optional[str] = None
    bairro: Optional[str] = None
    telefone: Optional[str] = None
    senha: Optional[str] = None


# ============================================================
# EVENTO
# ============================================================

class EventoBase(SQLModel):
    titulo: str
    descricao: Optional[str] = None
    modalidade: str          # Futebol, Zumba, Capoeira, Outros...
    cor: str = "blue"        # blue, orange, pink, green, purple
    local: str = "Quadra Poliesportiva"
    data: str                # "Sábado, 09:00" ou "2026-05-20 09:00"
    vagas: int = 30          # limite de inscrições; 0 = ilimitado


class Evento(EventoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    criado_por_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    inscricoes: list["Inscricao"] = Relationship(
        back_populates="evento",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class EventoCreate(EventoBase):
    pass


class EventoUpdate(SQLModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    modalidade: Optional[str] = None
    cor: Optional[str] = None
    local: Optional[str] = None
    data: Optional[str] = None
    vagas: Optional[int] = None


class EventoPublic(EventoBase):
    id: int
    criado_em: datetime
    total_inscritos: int = 0   # campo computado e preenchido nos endpoints
    inscrito: bool = False     # se o usuário atual está inscrito


# ============================================================
# INSCRIÇÃO
# ============================================================

class Inscricao(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    evento_id: int = Field(foreign_key="evento.id")
    criado_em: datetime = Field(default_factory=datetime.utcnow)

    usuario: Optional[Usuario] = Relationship(back_populates="inscricoes")
    evento: Optional[Evento] = Relationship(back_populates="inscricoes")


# ============================================================
# AUTENTICAÇÃO (payloads, não vão pro banco)
# ============================================================

class LoginRequest(SQLModel):
    email: str
    senha: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublic
