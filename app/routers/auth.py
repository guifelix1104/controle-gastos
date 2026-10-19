from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.config import COOKIE_SECURE, DIAS_DE_SESSAO
from app.database import get_db
from app.dependencias import NOME_DO_COOKIE, usuario_atual
from app.seguranca import criar_token, gerar_hash, verificar_senha

router = APIRouter(prefix="/auth", tags=["Autenticação"])

PADRAO_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Usado quando o e-mail não existe, para o login levar o mesmo tempo
# e não revelar quais e-mails estão cadastrados.
HASH_FALSO = gerar_hash("senha-falsa-para-igualar-o-tempo")


class Login(BaseModel):
    email: str = Field(max_length=254, pattern=PADRAO_EMAIL)
    senha: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def limpar_email(cls, valor):
        return valor.strip().lower() if isinstance(valor, str) else valor


class Cadastro(Login):
    senha: str = Field(min_length=8, max_length=128)


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


def colocar_cookie(resposta: Response, usuario_id: int) -> None:
    resposta.set_cookie(
        key=NOME_DO_COOKIE,
        value=criar_token(usuario_id),
        max_age=DIAS_DE_SESSAO * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def buscar_por_email(db: Session, email: str) -> models.Usuario | None:
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()


@router.post("/cadastro", response_model=UsuarioSaida, status_code=201)
def cadastrar(dados: Cadastro, resposta: Response, db: Session = Depends(get_db)):
    if buscar_por_email(db, dados.email):
        raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado")

    usuario = models.Usuario(email=dados.email, senha_hash=gerar_hash(dados.senha))
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado")
    db.refresh(usuario)

    colocar_cookie(resposta, usuario.id)
    return usuario


@router.post("/login", response_model=UsuarioSaida)
def entrar(dados: Login, resposta: Response, db: Session = Depends(get_db)):
    usuario = buscar_por_email(db, dados.email)

    senha_hash = usuario.senha_hash if usuario else HASH_FALSO
    senha_confere = verificar_senha(dados.senha, senha_hash)

    if usuario is None or not senha_confere:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

    colocar_cookie(resposta, usuario.id)
    return usuario


@router.post("/logout", status_code=204)
def sair(resposta: Response):
    resposta.delete_cookie(NOME_DO_COOKIE, path="/")


@router.get("/me", response_model=UsuarioSaida)
def quem_sou_eu(usuario: models.Usuario = Depends(usuario_atual)):
    return usuario