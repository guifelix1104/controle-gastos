from fastapi import FastAPI

from app import models
from app.database import Base, SessionLocal, engine
from app.seed import criar_categorias_padrao

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    criar_categorias_padrao(db)

app = FastAPI(title="Controle de Gastos")


@app.get("/")
def raiz():
    return {"mensagem": "Controle de gastos funcionando!"}