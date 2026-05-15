"""
test_auth.py
------------
Testes das rotas de autenticação:
- Registro, login, /me
- Esqueci senha / redefinir senha
"""

from tests.conftest import registrar_usuario, login_usuario, login_admin


class TestRegistro:
    def test_registro_sucesso(self, client):
        r = client.post(
            "/auth/registro",
            json={"nome": "João Silva", "email": "joao@test.com", "senha": "senha123"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "joao@test.com"
        assert data["role"] == "morador"
        assert "senha_hash" not in data

    def test_registro_email_duplicado(self, client):
        registrar_usuario(client)
        r = client.post(
            "/auth/registro",
            json={"nome": "Outro", "email": "morador@test.com", "senha": "senha123"},
        )
        assert r.status_code == 409

    def test_registro_senha_curta(self, client):
        r = client.post(
            "/auth/registro",
            json={"nome": "Ana", "email": "ana@test.com", "senha": "123"},
        )
        assert r.status_code == 400


class TestLogin:
    def test_login_sucesso(self, client):
        registrar_usuario(client)
        r = client.post(
            "/auth/login",
            json={"email": "morador@test.com", "senha": "senha123"},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert r.json()["token_type"] == "bearer"

    def test_login_senha_errada(self, client):
        registrar_usuario(client)
        r = client.post(
            "/auth/login",
            json={"email": "morador@test.com", "senha": "errada"},
        )
        assert r.status_code == 401

    def test_login_email_inexistente(self, client):
        r = client.post(
            "/auth/login",
            json={"email": "naoexiste@test.com", "senha": "senha123"},
        )
        assert r.status_code == 401

    def test_login_admin(self, client):
        token = login_admin(client)
        assert token


class TestMe:
    def test_me_autenticado(self, client):
        registrar_usuario(client)
        token = login_usuario(client)
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "morador@test.com"

    def test_me_sem_token(self, client):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_token_invalido(self, client):
        r = client.get("/auth/me", headers={"Authorization": "Bearer token_invalido"})
        assert r.status_code == 401


class TestAtualizarPerfil:
    def test_atualizar_nome(self, client):
        registrar_usuario(client)
        token = login_usuario(client)
        r = client.put("/auth/me", json={"nome": "Novo Nome"}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["nome"] == "Novo Nome"

    def test_atualizar_bairro_e_telefone(self, client):
        registrar_usuario(client)
        token = login_usuario(client)
        r = client.put(
            "/auth/me",
            json={"bairro": "Centro", "telefone": "61999999999"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["bairro"] == "Centro"
        assert r.json()["telefone"] == "61999999999"

    def test_atualizar_senha(self, client):
        registrar_usuario(client)
        token = login_usuario(client)
        client.put("/auth/me", json={"senha": "novasenha999"}, headers={"Authorization": f"Bearer {token}"})
        r = client.post("/auth/login", json={"email": "morador@test.com", "senha": "novasenha999"})
        assert r.status_code == 200

    def test_atualizar_nome_vazio(self, client):
        registrar_usuario(client)
        token = login_usuario(client)
        r = client.put("/auth/me", json={"nome": "  "}, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 400

    def test_sem_autenticacao(self, client):
        r = client.put("/auth/me", json={"nome": "Teste"})
        assert r.status_code == 401


class TestEsqueciSenha:
    def test_esqueci_senha_email_existente(self, client):
        registrar_usuario(client)
        r = client.post("/auth/esqueci-senha", json={"email": "morador@test.com"})
        assert r.status_code == 202
        assert "mensagem" in r.json()

    def test_esqueci_senha_email_inexistente(self, client):
        # Deve retornar 202 mesmo se o e-mail não existir (segurança)
        r = client.post("/auth/esqueci-senha", json={"email": "naoexiste@test.com"})
        assert r.status_code == 202

    def test_redefinir_senha_token_invalido(self, client):
        r = client.post(
            "/auth/redefinir-senha",
            json={"token": "token_falso", "nova_senha": "novasenha123"},
        )
        assert r.status_code == 400

    def test_redefinir_senha_fluxo_completo(self, client):
        """Cria token manualmente e redefinir senha."""
        from datetime import datetime, timedelta
        from sqlmodel import Session, select
        from models import PasswordResetToken, Usuario
        import database

        registrar_usuario(client)

        with Session(database.engine) as s:
            usuario = s.exec(
                select(Usuario).where(Usuario.email == "morador@test.com")
            ).first()
            token = PasswordResetToken(
                token="token-valido-123",
                usuario_id=usuario.id,
                expira_em=datetime.utcnow() + timedelta(hours=1),
            )
            s.add(token)
            s.commit()

        r = client.post(
            "/auth/redefinir-senha",
            json={"token": "token-valido-123", "nova_senha": "novasenha456"},
        )
        assert r.status_code == 200

        # Deve conseguir logar com a nova senha
        r2 = client.post(
            "/auth/login",
            json={"email": "morador@test.com", "senha": "novasenha456"},
        )
        assert r2.status_code == 200
