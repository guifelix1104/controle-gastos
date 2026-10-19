from app import models


def cadastrar(client, email="ana@exemplo.com", senha="senha-forte-123"):
    return client.post("/auth/cadastro", json={"email": email, "senha": senha})


def test_cadastro_cria_usuario_e_ja_deixa_logado(client):
    resposta = cadastrar(client)

    assert resposta.status_code == 201
    assert resposta.json()["email"] == "ana@exemplo.com"
    assert "senha" not in resposta.json()
    assert "senha_hash" not in resposta.json()
    assert client.get("/auth/me").status_code == 200


def test_email_e_guardado_em_minusculas(client):
    resposta = cadastrar(client, email="  ANA@Exemplo.com ")

    assert resposta.json()["email"] == "ana@exemplo.com"


def test_senha_e_guardada_como_hash(client, db):
    cadastrar(client, senha="senha-forte-123")

    usuario = db.query(models.Usuario).one()

    assert usuario.senha_hash != "senha-forte-123"
    assert usuario.senha_hash.startswith("$argon2")


def test_email_repetido_e_recusado(client):
    cadastrar(client)

    assert cadastrar(client).status_code == 409


def test_email_repetido_ignora_maiusculas(client):
    cadastrar(client, email="ana@exemplo.com")

    assert cadastrar(client, email="ANA@exemplo.com").status_code == 409


def test_senha_curta_e_recusada(client):
    assert cadastrar(client, senha="1234567").status_code == 422


def test_email_invalido_e_recusado(client):
    assert cadastrar(client, email="isso-nao-e-email").status_code == 422


def test_me_sem_login_da_401(client):
    assert client.get("/auth/me").status_code == 401


def test_login_com_senha_correta(client):
    cadastrar(client)
    client.post("/auth/logout")

    resposta = client.post(
        "/auth/login", json={"email": "ana@exemplo.com", "senha": "senha-forte-123"}
    )

    assert resposta.status_code == 200
    assert client.get("/auth/me").status_code == 200


def test_login_com_senha_errada(client):
    cadastrar(client)
    client.post("/auth/logout")

    resposta = client.post(
        "/auth/login", json={"email": "ana@exemplo.com", "senha": "senha-errada"}
    )

    assert resposta.status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_login_com_email_inexistente_da_o_mesmo_erro(client):
    cadastrar(client)

    senha_errada = client.post(
        "/auth/login", json={"email": "ana@exemplo.com", "senha": "senha-errada"}
    )
    sem_conta = client.post(
        "/auth/login", json={"email": "ninguem@exemplo.com", "senha": "qualquer-coisa"}
    )

    assert sem_conta.status_code == 401
    assert sem_conta.json() == senha_errada.json()


def test_logout_encerra_a_sessao(client):
    cadastrar(client)

    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_cookie_de_sessao_e_protegido(client):
    resposta = cadastrar(client)

    cookie = resposta.headers["set-cookie"].lower()

    assert "httponly" in cookie
    assert "samesite=lax" in cookie