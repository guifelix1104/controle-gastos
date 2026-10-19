from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import ALGORITMO, DIAS_DE_SESSAO, SECRET_KEY

hasher = PasswordHash.recommended()  # Argon2


def gerar_hash(senha: str) -> str:
    return hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return hasher.verify(senha, senha_hash)


def criar_token(usuario_id: int) -> str:
    expira = datetime.now(timezone.utc) + timedelta(days=DIAS_DE_SESSAO)
    dados = {"sub": str(usuario_id), "exp": expira}
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITMO)


def ler_token(token: str) -> int | None:
    """Devolve o id do usuário, ou None se o token for inválido ou estiver vencido."""
    try:
        dados = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
        return int(dados["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None