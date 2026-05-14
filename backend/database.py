"""
database.py
-----------
Configuração centralizada do banco de dados SQLite via SQLModel.

- Cria a engine única usada por toda a aplicação
- Expõe `get_session` para injeção de dependência nas rotas FastAPI
- Função `criar_banco` é chamada na inicialização do servidor
"""

from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine

# Caminho absoluto do arquivo .db (fica ao lado deste arquivo, na pasta backend/)
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "conecta_bairro.db"

# URL de conexão SQLite
SQLITE_URL = f"sqlite:///{DB_FILE}"

# `check_same_thread=False` permite que a engine seja usada por múltiplas threads
# (necessário pra FastAPI/Uvicorn). `echo=False` em produção; troque para True
# se quiser ver as queries SQL no terminal durante desenvolvimento.
engine = create_engine(
    SQLITE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def criar_banco() -> None:
    """Cria todas as tabelas declaradas nos modelos SQLModel."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependência FastAPI: abre uma sessão por request e fecha automaticamente."""
    with Session(engine) as session:
        yield session
