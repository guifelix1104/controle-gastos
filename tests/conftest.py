import os

# Precisa vir antes de importar o app (o app exige uma SECRET_KEY)
os.environ.setdefault("SECRET_KEY", "chave-usada-apenas-nos-testes-do-controle-de-gastos")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import models  # noqa: E402,F401
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import criar_categorias_padrao  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Sessao = sessionmaker(bind=engine, autoflush=False)

    with Sessao() as sessao:
        criar_categorias_padrao(sessao)
        yield sessao

    engine.dispose()


@pytest.fixture()
def client(db):
    def usar_banco_de_teste():
        yield db

    app.dependency_overrides[get_db] = usar_banco_de_teste

    with TestClient(app) as cliente:
        yield cliente

    app.dependency_overrides.clear()