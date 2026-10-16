import pytest


def nova_transacao(client, **campos):
    corpo = {
        "descricao": "Netflix",
        "valor": 55.9,
        "tipo": "gasto",
        "data": "2026-10-06",
    }
    corpo.update(campos)
    return client.post("/transacoes/", json=corpo)


def test_resumo_soma_renda_gastos_e_saldo(client):
    nova_transacao(client, descricao="Salário", valor=3500, tipo="renda", data="2026-10-05")
    nova_transacao(client, descricao="Netflix", valor=55.9)
    nova_transacao(client, descricao="Uber", valor=23.5, data="2026-10-08")

    dados = client.get("/resumo/?mes=2026-10").json()

    assert dados["total_renda"] == pytest.approx(3500)
    assert dados["total_gastos"] == pytest.approx(79.4)
    assert dados["saldo"] == pytest.approx(3420.6)


def test_resumo_agrupa_gastos_por_categoria_em_ordem(client):
    nova_transacao(client, descricao="Netflix", valor=55.9)
    nova_transacao(client, descricao="Uber", valor=23.5)

    categorias = client.get("/resumo/?mes=2026-10").json()["gastos_por_categoria"]

    assert [c["categoria"] for c in categorias] == ["Lazer", "Transporte"]


def test_resumo_ignora_outros_meses(client):
    nova_transacao(client, valor=100, data="2026-11-02")

    dados = client.get("/resumo/?mes=2026-10").json()

    assert dados["total_gastos"] == 0
    assert dados["gastos_por_categoria"] == []


def test_resumo_de_mes_vazio(client):
    dados = client.get("/resumo/?mes=2026-09").json()

    assert dados["total_renda"] == 0
    assert dados["saldo"] == 0


def test_resumo_rejeita_formato_de_mes_invalido(client):
    assert client.get("/resumo/?mes=outubro").status_code == 422