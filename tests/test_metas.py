from datetime import date

from app import models
from app.routers.metas import montar_saida

HOJE = date(2026, 10, 13)


def nova_meta(**campos):
    base = dict(
        id=1,
        nome="Viagem pro Chile",
        valor_alvo=8000.0,
        valor_guardado=0.0,
        prazo=date(2027, 12, 1),
    )
    base.update(campos)
    return models.Meta(**base)


def test_calcula_quanto_guardar_por_mes():
    saida = montar_saida(nova_meta(), hoje=HOJE)

    assert saida["meses_restantes"] == 14
    assert saida["guardar_por_mes"] == 571.43
    assert saida["status"] == "em_andamento"


def test_valor_guardado_reduz_o_que_falta():
    saida = montar_saida(nova_meta(valor_guardado=2000.0), hoje=HOJE)

    assert saida["faltante"] == 6000.0
    assert saida["progresso"] == 25.0
    assert saida["guardar_por_mes"] == 428.57


def test_meta_concluida():
    saida = montar_saida(nova_meta(valor_guardado=8000.0), hoje=HOJE)

    assert saida["status"] == "concluida"
    assert saida["faltante"] == 0
    assert saida["guardar_por_mes"] == 0


def test_progresso_nunca_passa_de_100():
    saida = montar_saida(nova_meta(valor_guardado=9000.0), hoje=HOJE)

    assert saida["progresso"] == 100
    assert saida["status"] == "concluida"


def test_meta_vencida():
    saida = montar_saida(nova_meta(prazo=date(2026, 9, 1)), hoje=HOJE)

    assert saida["status"] == "vencida"
    assert saida["guardar_por_mes"] is None


def test_prazo_no_mesmo_mes_conta_como_um_mes():
    saida = montar_saida(nova_meta(prazo=date(2026, 10, 30)), hoje=HOJE)

    assert saida["meses_restantes"] == 1
    assert saida["guardar_por_mes"] == 8000.0


def test_criar_meta_com_prazo_no_passado(client):
    corpo = {"nome": "Moto", "valor_alvo": 20000, "prazo": "2020-01-01"}

    assert client.post("/metas/", json=corpo).status_code == 400


def test_depositar_soma_ao_valor_guardado(client):
    corpo = {"nome": "Viagem", "valor_alvo": 8000, "prazo": "2099-01-01"}
    meta = client.post("/metas/", json=corpo).json()

    client.post(f"/metas/{meta['id']}/depositar", json={"valor": 500})
    resposta = client.post(f"/metas/{meta['id']}/depositar", json={"valor": 250})

    assert resposta.status_code == 200
    assert resposta.json()["valor_guardado"] == 750


def test_depositar_em_meta_inexistente(client):
    resposta = client.post("/metas/999/depositar", json={"valor": 100})

    assert resposta.status_code == 404