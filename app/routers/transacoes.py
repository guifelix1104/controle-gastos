from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.categorizador import descobrir_categoria
from app.database import get_db

router = APIRouter(prefix="/transacoes", tags=["Transações"])


def validar_categoria(db: Session, categoria_id: int | None):
    if categoria_id is not None and db.get(models.Categoria, categoria_id) is None:
        raise HTTPException(status_code=400, detail="Categoria não existe")


def resolver_categoria(db: Session, dados: schemas.TransacaoCriar) -> int | None:
    if dados.categoria_id is not None:
        return dados.categoria_id

    if dados.tipo == "gasto":
        categoria = descobrir_categoria(db, dados.descricao)
        return categoria.id if categoria else None

    return None


@router.post("/", response_model=schemas.TransacaoSaida, status_code=201)
def criar(dados: schemas.TransacaoCriar, db: Session = Depends(get_db)):
    validar_categoria(db, dados.categoria_id)

    valores = dados.model_dump()
    valores["categoria_id"] = resolver_categoria(db, dados)

    transacao = models.Transacao(**valores)
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    return transacao


@router.get("/", response_model=list[schemas.TransacaoSaida])
def listar(db: Session = Depends(get_db)):
    return db.query(models.Transacao).order_by(models.Transacao.data.desc()).all()


@router.get("/{transacao_id}", response_model=schemas.TransacaoSaida)
def buscar(transacao_id: int, db: Session = Depends(get_db)):
    transacao = db.get(models.Transacao, transacao_id)
    if transacao is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    return transacao


@router.put("/{transacao_id}", response_model=schemas.TransacaoSaida)
def atualizar(
    transacao_id: int,
    dados: schemas.TransacaoCriar,
    db: Session = Depends(get_db),
):
    transacao = db.get(models.Transacao, transacao_id)
    if transacao is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    validar_categoria(db, dados.categoria_id)

    valores = dados.model_dump()
    valores["categoria_id"] = resolver_categoria(db, dados)

    for campo, valor in valores.items():
        setattr(transacao, campo, valor)

    db.commit()
    db.refresh(transacao)
    return transacao


@router.delete("/{transacao_id}", status_code=204)
def apagar(transacao_id: int, db: Session = Depends(get_db)):
    transacao = db.get(models.Transacao, transacao_id)
    if transacao is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    db.delete(transacao)
    db.commit()