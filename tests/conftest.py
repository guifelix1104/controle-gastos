import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (garante que as tabelas sejam conhecidas)
from app.database import Base, get_db
from app.main import app
from app.seed import criar_categorias_padrao


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