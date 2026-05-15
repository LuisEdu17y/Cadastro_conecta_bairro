"""
test_admin.py
-------------
Testes do painel administrativo.
"""

from tests.conftest import (
    registrar_usuario,
    login_usuario,
    login_admin,
    criar_evento,
)


class TestEstatisticas:
    def test_estatisticas_admin(self, client):
        token = login_admin(client)
        r = client.get("/admin/estatisticas", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert "total_usuarios" in data
        assert "total_eventos" in data
        assert "total_inscricoes" in data

    def test_estatisticas_nao_admin(self, client):
        registrar_usuario(client)
        token = login_usuario(client)
        r = client.get("/admin/estatisticas", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_estatisticas_sem_token(self, client):
        r = client.get("/admin/estatisticas")
        assert r.status_code == 401


class TestGestaoUsuarios:
    def test_listar_usuarios(self, client):
        registrar_usuario(client)
        token = login_admin(client)
        r = client.get("/admin/usuarios", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert len(r.json()) >= 2  # admin + morador

    def test_promover_usuario(self, client):
        registrar_usuario(client)
        token = login_admin(client)

        usuarios = client.get(
            "/admin/usuarios", headers={"Authorization": f"Bearer {token}"}
        ).json()
        morador = next(u for u in usuarios if u["role"] == "morador")

        r = client.put(
            f"/admin/usuarios/{morador['id']}",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    def test_desativar_usuario(self, client):
        registrar_usuario(client)
        token = login_admin(client)

        usuarios = client.get(
            "/admin/usuarios", headers={"Authorization": f"Bearer {token}"}
        ).json()
        morador = next(u for u in usuarios if u["role"] == "morador")

        r = client.put(
            f"/admin/usuarios/{morador['id']}",
            json={"ativo": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["ativo"] is False

    def test_deletar_usuario(self, client):
        registrar_usuario(client)
        token = login_admin(client)

        usuarios = client.get(
            "/admin/usuarios", headers={"Authorization": f"Bearer {token}"}
        ).json()
        morador = next(u for u in usuarios if u["role"] == "morador")

        r = client.delete(
            f"/admin/usuarios/{morador['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    def test_admin_nao_pode_deletar_si_mesmo(self, client):
        token = login_admin(client)
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        r = client.delete(
            f"/admin/usuarios/{me['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400


class TestInscritos:
    def test_listar_inscritos(self, client):
        registrar_usuario(client)
        token_user = login_usuario(client)
        token_admin = login_admin(client)
        evento = criar_evento(client, token_admin)

        client.post(
            f"/eventos/{evento['id']}/inscrever",
            headers={"Authorization": f"Bearer {token_user}"},
        )

        r = client.get(
            f"/admin/eventos/{evento['id']}/inscritos",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_listar_inscritos_evento_inexistente(self, client):
        token = login_admin(client)
        r = client.get(
            "/admin/eventos/9999/inscritos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404
