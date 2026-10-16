from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/metas", tags=["Metas"])


def montar_saida(meta: models.Meta, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()

    faltante = round(max(meta.valor_alvo - meta.valor_guardado, 0), 2)
    progresso = min(meta.valor_guardado / meta.valor_alvo * 100, 100)

    if faltante == 0:
        status = "concluida"
        meses = 0
        por_mes = 0.0
    elif meta.prazo <= hoje:
        status = "vencida"
        meses = 0
        por_mes = None
    else:
        status = "em_andamento"
        meses = (meta.prazo.year - hoje.year) * 12 + (meta.prazo.month - hoje.month)
        meses = max(meses, 1)
        por_mes = faltante / meses

    return {
        "id": meta.id,
        "nome": meta.nome,
        "valor_alvo": meta.valor_alvo,
        "valor_guardado": meta.valor_guardado,
        "prazo": meta.prazo,
        "faltante": faltante,
        "progresso": round(progresso, 1),
        "meses_restantes": meses,
        "guardar_por_mes": round(por_mes, 2) if por_mes is not None else None,
        "status": status,
    }


def buscar_ou_404(db: Session, meta_id: int) -> models.Meta:
    meta = db.get(models.Meta, meta_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    return meta


@router.post("/", response_model=schemas.MetaSaida, status_code=201)
def criar(dados: schemas.MetaCriar, db: Session = Depends(get_db)):
    if dados.prazo <= date.today():
        raise HTTPException(status_code=400, detail="O prazo precisa ser uma data futura")

    meta = models.Meta(**dados.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return montar_saida(meta)


@router.get("/", response_model=list[schemas.MetaSaida])
def listar(db: Session = Depends(get_db)):
    metas = db.query(models.Meta).order_by(models.Meta.prazo).all()
    return [montar_saida(meta) for meta in metas]


@router.post("/{meta_id}/depositar", response_model=schemas.MetaSaida)
def depositar(meta_id: int, dados: schemas.Deposito, db: Session = Depends(get_db)):
    meta = buscar_ou_404(db, meta_id)

    meta.valor_guardado = round(meta.valor_guardado + dados.valor, 2)
    db.commit()
    db.refresh(meta)
    return montar_saida(meta)


@router.delete("/{meta_id}", status_code=204)
def apagar(meta_id: int, db: Session = Depends(get_db)):
    meta = buscar_ou_404(db, meta_id)

    db.delete(meta)
    db.commit()