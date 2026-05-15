"""
conftest.py
-----------
Fixtures compartilhadas para todos os testes.

Usa um banco SQLite em memória, isolado por sessão de teste.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_session_test():
    with Session(TEST_ENGINE) as session:
        yield session


@pytest.fixture(autouse=True)
def banco_limpo():
    """Recria as tabelas antes de cada teste e descarta depois."""
    SQLModel.metadata.create_all(TEST_ENGINE)
    yield
    SQLModel.metadata.drop_all(TEST_ENGINE)


@pytest.fixture()
def client(banco_limpo):
    """TestClient com banco em memória e admin padrão criado."""
    # Substitui o engine nos dois módulos que o referenciam
    import database
    import main as main_module

    database.engine = TEST_ENGINE
    main_module.engine = TEST_ENGINE  # usado em `with Session(engine)` no lifespan

    from main import app
    from database import get_session
    app.dependency_overrides[get_session] = get_session_test

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────
# Helpers reutilizáveis
# ──────────────────────────────────────────────

def registrar_usuario(client, nome="Morador Teste", email="morador@test.com", senha="senha123"):
    r = client.post("/auth/registro", json={"nome": nome, "email": email, "senha": senha})
    assert r.status_code == 201
    return r.json()


def login_usuario(client, email="morador@test.com", senha="senha123"):
    r = client.post("/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200
    return r.json()["access_token"]


def login_admin(client):
    r = client.post(
        "/auth/login",
        json={"email": "admin@conectabairro.com", "senha": "admin123"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def criar_evento(client, token, **kwargs):
    payload = {
        "titulo": "Evento Teste",
        "modalidade": "Futebol",
        "cor": "green",
        "local": "Campo do Bairro",
        "data": "Sábado, 10:00",
        "vagas": 20,
        **kwargs,
    }
    r = client.post("/eventos", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201
    return r.json()
