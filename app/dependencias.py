from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.seguranca import ler_token

NOME_DO_COOKIE = "sessao"


def usuario_atual(
    sessao: str | None = Cookie(default=None, alias=NOME_DO_COOKIE),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """Descobre quem está logado pelo cookie. Sem login válido, responde 401."""
    usuario_id = ler_token(sessao) if sessao else None
    usuario = db.get(models.Usuario, usuario_id) if usuario_id else None

    if usuario is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return usuario