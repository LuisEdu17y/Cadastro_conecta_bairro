"""
test_eventos.py
---------------
Testes das rotas de eventos e inscrições.
"""

from tests.conftest import (
    registrar_usuario,
    login_usuario,
    login_admin,
    criar_evento,
)


# Helper: extrai lista de eventos da resposta paginada
def eventos(r):
    return r.json()["eventos"]


class TestListagem:
    def test_listar_sem_autenticacao(self, client):
        r = client.get("/eventos")
        assert r.status_code == 200
        data = r.json()
        assert "eventos" in data
        assert "total" in data
        assert "tem_mais" in data

    def test_paginacao_basica(self, client):
        token = login_admin(client)
        for i in range(5):
            criar_evento(client, token, titulo=f"Evento {i}")

        r = client.get("/eventos?limite=2&offset=0")
        assert r.status_code == 200
        data = r.json()
        assert len(data["eventos"]) == 2
        assert data["tem_mais"] is True

        r2 = client.get(f"/eventos?limite=2&offset=2")
        assert len(r2.json()["eventos"]) == 2

    def test_filtro_modalidade(self, client):
        token = login_admin(client)
        criar_evento(client, token, titulo="Futebol A", modalidade="Futebol")
        criar_evento(client, token, titulo="Zumba B", modalidade="Zumba")

        r = client.get("/eventos?modalidade=Futebol")
        assert all(e["modalidade"] == "Futebol" for e in eventos(r))

    def test_filtro_bairro(self, client):
        token = login_admin(client)
        criar_evento(client, token, titulo="Evento Norte", bairro="Asa Norte")
        criar_evento(client, token, titulo="Evento Sul", bairro="Asa Sul")

        r = client.get("/eventos?bairro=Asa Norte")
        evs = eventos(r)
        assert len(evs) == 1
        assert evs[0]["bairro"] == "Asa Norte"

    def test_filtro_local(self, client):
        token = login_admin(client)
        criar_evento(client, token, local="ArenaExclusiva99")
        criar_evento(client, token, local="PraçaOutra")

        r = client.get("/eventos?local=ArenaExclusiva99")
        evs = eventos(r)
        assert len(evs) == 1
        assert "ArenaExclusiva99" in evs[0]["local"]

    def test_detalhar_evento(self, client):
        token = login_admin(client)
        evento = criar_evento(client, token)
        r = client.get(f"/eventos/{evento['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == evento["id"]

    def test_detalhar_evento_inexistente(self, client):
        r = client.get("/eventos/9999")
        assert r.status_code == 404


class TestCrudAdmin:
    def test_criar_evento(self, client):
        token = login_admin(client)
        evento = criar_evento(client, token)
        assert evento["titulo"] == "Evento Teste"
        assert evento["total_inscritos"] == 0

    def test_criar_evento_sem_admin(self, client):
        registrar_usuario(client)
        token = login_usuario(client)
        r = client.post(
            "/eventos",
            json={"titulo": "Teste", "modalidade": "Futebol", "local": "X", "data": "Hoje", "vagas": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403

    def test_atualizar_evento(self, client):
        token = login_admin(client)
        evento = criar_evento(client, token)
        r = client.put(
            f"/eventos/{evento['id']}",
            json={"titulo": "Evento Atualizado"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["titulo"] == "Evento Atualizado"

    def test_deletar_evento(self, client):
        token = login_admin(client)
        evento = criar_evento(client, token)
        r = client.delete(
            f"/eventos/{evento['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert client.get(f"/eventos/{evento['id']}").status_code == 404


class TestInscricoes:
    def test_inscrever_e_cancelar(self, client):
        registrar_usuario(client)
        token_user = login_usuario(client)
        token_admin = login_admin(client)
        evento = criar_evento(client, token_admin)

        r = client.post(
            f"/eventos/{evento['id']}/inscrever",
            headers={"Authorization": f"Bearer {token_user}"},
        )
        assert r.status_code == 201

        r2 = client.get(
            f"/eventos/{evento['id']}",
            headers={"Authorization": f"Bearer {token_user}"},
        )
        assert r2.json()["inscrito"] is True
        assert r2.json()["total_inscritos"] == 1

        r3 = client.delete(
            f"/eventos/{evento['id']}/inscrever",
            headers={"Authorization": f"Bearer {token_user}"},
        )
        assert r3.status_code == 200
        assert client.get(f"/eventos/{evento['id']}").json()["total_inscritos"] == 0

    def test_inscricao_duplicada(self, client):
        registrar_usuario(client)
        token_user = login_usuario(client)
        token_admin = login_admin(client)
        evento = criar_evento(client, token_admin)

        client.post(f"/eventos/{evento['id']}/inscrever", headers={"Authorization": f"Bearer {token_user}"})
        r = client.post(f"/eventos/{evento['id']}/inscrever", headers={"Authorization": f"Bearer {token_user}"})
        assert r.status_code == 409

    def test_vagas_esgotadas(self, client):
        registrar_usuario(client, email="user1@test.com")
        registrar_usuario(client, nome="User2", email="user2@test.com")
        token1 = login_usuario(client, email="user1@test.com")
        token2 = login_usuario(client, email="user2@test.com")
        token_admin = login_admin(client)

        evento = criar_evento(client, token_admin, vagas=1)

        client.post(f"/eventos/{evento['id']}/inscrever", headers={"Authorization": f"Bearer {token1}"})
        r = client.post(f"/eventos/{evento['id']}/inscrever", headers={"Authorization": f"Bearer {token2}"})
        assert r.status_code == 409
        assert "esgotadas" in r.json()["detail"].lower()

    def test_meus_eventos(self, client):
        registrar_usuario(client)
        token_user = login_usuario(client)
        token_admin = login_admin(client)
        evento = criar_evento(client, token_admin)

        client.post(f"/eventos/{evento['id']}/inscrever", headers={"Authorization": f"Bearer {token_user}"})
        r = client.get("/eventos/meus", headers={"Authorization": f"Bearer {token_user}"})
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["id"] == evento["id"]
