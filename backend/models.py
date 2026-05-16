"""
models.py
---------
Modelos de dados da aplicação Conecta Bairro.

Entidades:
- Usuario            → moradores e administradores cadastrados
- Evento             → eventos comunitários
- Inscricao          → relação N:N entre usuários e eventos
- PasswordResetToken → tokens temporários para redefinição de senha

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
    """Tabela real de usuários. NUNCA retornar este modelo direto pela API."""
    id: Optional[int] = Field(default=None, primary_key=True)
    senha_hash: str
    role: str = Field(default="morador")  # 'morador' ou 'admin'
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    ativo: bool = Field(default=True)

    inscricoes: list["Inscricao"] = Relationship(back_populates="usuario")
    tokens_reset: list["PasswordResetToken"] = Relationship(back_populates="usuario")


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
    bairro: Optional[str] = None          # bairro onde ocorre o evento
    data: str                             # string de exibição ("Sábado, 09:00")
    data_inicio: Optional[datetime] = None  # datetime para filtragem
    vagas: int = 30                       # 0 = ilimitado
    imagem_url: Optional[str] = None      # caminho da imagem do evento


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
    bairro: Optional[str] = None
    data: Optional[str] = None
    data_inicio: Optional[datetime] = None
    vagas: Optional[int] = None
    imagem_url: Optional[str] = None


class EventoPublic(EventoBase):
    id: int
    criado_em: datetime
    total_inscritos: int = 0
    inscrito: bool = False


class EventosPaginados(SQLModel):
    """Resposta paginada de eventos."""
    total: int
    limite: int
    offset: int
    tem_mais: bool
    eventos: list[EventoPublic]


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
# RECUPERAÇÃO DE SENHA
# ============================================================

class PasswordResetToken(SQLModel, table=True):
    """Token temporário para redefinição de senha (válido por 1 hora)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    expira_em: datetime
    usado: bool = Field(default=False)

    usuario: Optional[Usuario] = Relationship(back_populates="tokens_reset")


# ============================================================
# COMENTÁRIO
# ============================================================

class Comentario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    texto: str = Field(max_length=500)
    evento_id: int = Field(foreign_key="evento.id")
    usuario_id: int = Field(foreign_key="usuario.id")
    criado_em: datetime = Field(default_factory=datetime.utcnow)


class ComentarioCreate(SQLModel):
    texto: str


class ComentarioPublic(SQLModel):
    id: int
    texto: str
    criado_em: datetime
    usuario_id: int
    usuario_nome: str
    pode_deletar: bool = False


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


class EsqueciSenhaRequest(SQLModel):
    email: str


class RedefinirSenhaRequest(SQLModel):
    token: str
    nova_senha: str
