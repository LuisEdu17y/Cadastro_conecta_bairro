"""
database.py
-----------
Configuração centralizada do banco de dados via SQLModel.

Suporta SQLite (padrão, para desenvolvimento) e PostgreSQL (produção).
Configure a variável de ambiente DATABASE_URL para usar PostgreSQL:
    DATABASE_URL=postgresql://user:pass@host:5432/dbname

Se DATABASE_URL não estiver definida, usa SQLite local.
"""

import os
from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL (ou outro banco externo)
    # Render/Railway usam "postgres://" — SQLAlchemy 2.x exige "postgresql://"
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # SQLite local (desenvolvimento)
    DB_FILE = BASE_DIR / "conecta_bairro.db"
    engine = create_engine(
        f"sqlite:///{DB_FILE}",
        echo=False,
        connect_args={"check_same_thread": False},
    )


def criar_banco() -> None:
    """Cria todas as tabelas e roda migrações de colunas novas."""
    SQLModel.metadata.create_all(engine)
    _migrar_colunas()
    if DATABASE_URL:
        _stamp_alembic_if_needed()


def _stamp_alembic_if_needed() -> None:
    """
    Em PostgreSQL, as tabelas são criadas pelo create_all (não pelo Alembic).
    Se alembic_version não existir, faz stamp head para que migrações futuras
    funcionem corretamente.
    """
    from sqlalchemy import inspect as sa_inspect
    from alembic.config import Config
    from alembic import command

    insp = sa_inspect(engine)
    if "alembic_version" not in insp.get_table_names():
        cfg = Config(str(BASE_DIR / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", str(engine.url))
        command.stamp(cfg, "head")


def _migrar_colunas() -> None:
    """
    Adiciona colunas novas a tabelas existentes (migração lightweight).
    Necessário quando o banco já existe e adicionamos campos ao modelo.
    Só funciona com SQLite; PostgreSQL usa Alembic em produção.
    """
    if DATABASE_URL:
        return  # PostgreSQL: use Alembic

    novas_colunas = {
        "evento": [
            ("bairro", "TEXT"),
            ("data_inicio", "DATETIME"),
            ("imagem_url", "TEXT"),
            ("latitude", "REAL"),
            ("longitude", "REAL"),
        ],
        "usuario": [
            ("foto_url", "TEXT"),
            ("precisa_cesta_basica", "INTEGER NOT NULL DEFAULT 0"),
        ],
        "passwordresettoken": [],  # tabela nova, create_all cuida disso
    }

    with engine.connect() as conn:
        for tabela, colunas in novas_colunas.items():
            # Descobre colunas existentes
            resultado = conn.execute(text(f"PRAGMA table_info({tabela})"))
            existentes = {row[1] for row in resultado}

            for col_nome, col_tipo in colunas:
                if col_nome not in existentes:
                    conn.execute(
                        text(f"ALTER TABLE {tabela} ADD COLUMN {col_nome} {col_tipo}")
                    )
            conn.commit()


def get_session():
    """Dependência FastAPI: abre uma sessão por request e fecha automaticamente."""
    with Session(engine) as session:
        yield session
