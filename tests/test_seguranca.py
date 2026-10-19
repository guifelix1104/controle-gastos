from datetime import datetime, timedelta, timezone

import jwt

from app.config import ALGORITMO, SECRET_KEY
from app.seguranca import criar_token, gerar_hash, ler_token, verificar_senha


def test_hash_nao_guarda_a_senha_em_texto():
    senha_hash = gerar_hash("minha-senha-123")

    assert senha_hash != "minha-senha-123"
    assert verificar_senha("minha-senha-123", senha_hash)


def test_senha_errada_nao_confere():
    senha_hash = gerar_hash("minha-senha-123")

    assert not verificar_senha("outra-senha", senha_hash)


def test_mesma_senha_gera_hashes_diferentes():
    # cada hash tem um "sal" aleatório
    assert gerar_hash("minha-senha-123") != gerar_hash("minha-senha-123")


def test_token_devolve_o_id_do_usuario():
    assert ler_token(criar_token(42)) == 42


def test_token_adulterado_e_rejeitado():
    cabecalho, _, assinatura = criar_token(1).split(".")
    _, corpo_de_outro_usuario, _ = criar_token(2).split(".")

    falso = f"{cabecalho}.{corpo_de_outro_usuario}.{assinatura}"

    assert ler_token(falso) is None


def test_token_vencido_e_rejeitado():
    vencido = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        SECRET_KEY,
        algorithm=ALGORITMO,
    )

    assert ler_token(vencido) is None


def test_token_lixo_e_rejeitado():
    assert ler_token("isso-nao-e-um-token") is None