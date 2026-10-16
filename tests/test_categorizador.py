import pytest

from app.categorizador import descobrir_categoria, normalizar


def test_normalizar_remove_acentos_e_maiusculas():
    assert normalizar("  Saúde  ") == "saude"


@pytest.mark.parametrize(
    "descricao, esperado",
    [
        ("Uber para o trabalho", "Transporte"),
        ("Mercado do mês", "Alimentação"),
        ("Conta de luz", "Moradia"),
        ("Netflix", "Lazer"),
        ("Consulta médica", "Saúde"),
        ("Presente da Ana", "Outros"),
    ],
)
def test_descobre_categoria_pela_descricao(db, descricao, esperado):
    assert descobrir_categoria(db, descricao).nome == esperado


def test_palavra_mais_longa_vence(db):
    # "uber" (Transporte) e "cinema" (Lazer) aparecem juntas: vence a mais longa
    assert descobrir_categoria(db, "Uber para o cinema").nome == "Lazer"


def test_palavra_precisa_ser_inteira(db):
    # "bar" é palavra-chave de Lazer, mas não deve casar com "barbearia"
    assert descobrir_categoria(db, "Barbearia").nome == "Outros"


def test_gasolina_e_transporte(db):
    # "gas" (Moradia) não deve casar com "gasolina"
    assert descobrir_categoria(db, "Gasolina").nome == "Transporte"