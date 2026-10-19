from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import models
from app.database import Base, SessionLocal, engine
from app.routers import auth, categorias, metas, resumo, transacoes
from app.seed import criar_categorias_padrao

PASTA_STATIC = Path(__file__).parent / "static"

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    criar_categorias_padrao(db)

app = FastAPI(title="Controle de Gastos")

app.include_router(transacoes.router)
app.include_router(categorias.router)
app.include_router(resumo.router)
app.include_router(metas.router)
app.include_router(auth.router)

app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")


@app.get("/", include_in_schema=False)
def pagina_inicial():
    return FileResponse(PASTA_STATIC / "index.html")