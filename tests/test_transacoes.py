def nova_transacao(client, **campos):
    corpo = {
        "descricao": "Netflix",
        "valor": 55.9,
        "tipo": "gasto",
        "data": "2026-10-06",
    }
    corpo.update(campos)
    return client.post("/transacoes/", json=corpo)


def id_da_categoria(client, nome):
    categorias = client.get("/categorias/").json()
    return next(c["id"] for c in categorias if c["nome"] == nome)


def test_criar_gasto_categoriza_automaticamente(client):
    resposta = nova_transacao(client, descricao="Uber para o trabalho")

    assert resposta.status_code == 201
    assert resposta.json()["categoria_nome"] == "Transporte"


def test_categoria_manual_tem_prioridade(client):
    lazer = id_da_categoria(client, "Lazer")

    resposta = nova_transacao(client, descricao="Uber", categoria_id=lazer)

    assert resposta.json()["categoria_nome"] == "Lazer"


def test_renda_nao_recebe_categoria(client):
    resposta = nova_transacao(client, descricao="Salário", tipo="renda")

    assert resposta.status_code == 201
    assert resposta.json()["categoria_nome"] is None


def test_rejeita_valor_negativo(client):
    assert nova_transacao(client, valor=-10).status_code == 422


def test_rejeita_tipo_invalido(client):
    assert nova_transacao(client, tipo="presente").status_code == 422


def test_rejeita_categoria_inexistente(client):
    assert nova_transacao(client, categoria_id=999).status_code == 400


def test_listar_filtra_por_mes(client):
    nova_transacao(client, descricao="Netflix", data="2026-10-06")
    nova_transacao(client, descricao="Spotify", data="2026-11-02")

    resposta = client.get("/transacoes/?mes=2026-10")

    descricoes = [t["descricao"] for t in resposta.json()]
    assert descricoes == ["Netflix"]


def test_editar_transacao_recalcula_categoria(client):
    criada = nova_transacao(client, descricao="Netflix").json()

    corpo = {
        "descricao": "Mercado",
        "valor": 150,
        "tipo": "gasto",
        "data": "2026-10-06",
    }
    resposta = client.put(f"/transacoes/{criada['id']}", json=corpo)

    assert resposta.status_code == 200
    assert resposta.json()["valor"] == 150
    assert resposta.json()["categoria_nome"] == "Alimentação"


def test_editar_transacao_inexistente(client):
    corpo = {"descricao": "X", "valor": 1, "tipo": "gasto", "data": "2026-10-06"}

    assert client.put("/transacoes/999", json=corpo).status_code == 404


def test_apagar_transacao(client):
    criada = nova_transacao(client).json()

    resposta = client.delete(f"/transacoes/{criada['id']}")

    assert resposta.status_code == 204
    assert client.get(f"/transacoes/{criada['id']}").status_code == 404


def test_gerar_fixas_copia_para_o_mes_seguinte(client):
    nova_transacao(client, descricao="Netflix", data="2026-10-06", fixa=True)

    resposta = client.post("/transacoes/gerar-fixas?mes=2026-11")

    assert resposta.json()["criadas"] == 1
    novembro = client.get("/transacoes/?mes=2026-11").json()
    assert len(novembro) == 1
    assert novembro[0]["data"] == "2026-11-06"
    assert novembro[0]["fixa"] is True


def test_gerar_fixas_nao_duplica(client):
    nova_transacao(client, fixa=True)

    client.post("/transacoes/gerar-fixas?mes=2026-11")
    resposta = client.post("/transacoes/gerar-fixas?mes=2026-11")

    assert resposta.json()["criadas"] == 0


def test_transacao_nao_fixa_nao_e_copiada(client):
    nova_transacao(client, fixa=False)

    resposta = client.post("/transacoes/gerar-fixas?mes=2026-11")

    assert resposta.json()["criadas"] == 0


def test_parar_de_repetir_interrompe_a_geracao(client):
    criada = nova_transacao(client, fixa=True).json()
    client.patch(f"/transacoes/{criada['id']}/fixa", json={"fixa": False})

    resposta = client.post("/transacoes/gerar-fixas?mes=2026-11")

    assert resposta.json()["criadas"] == 0


def test_gerar_fixas_ajusta_dia_em_mes_curto(client):
    nova_transacao(client, descricao="Aluguel", data="2026-01-31", fixa=True)

    client.post("/transacoes/gerar-fixas?mes=2026-02")

    fevereiro = client.get("/transacoes/?mes=2026-02").json()
    assert fevereiro[0]["data"] == "2026-02-28"