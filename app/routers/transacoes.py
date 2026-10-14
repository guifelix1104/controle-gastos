import calendar
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.categorizador import descobrir_categoria, normalizar
from app.database import get_db
from app.routers.resumo import intervalo_do_mes

router = APIRouter(prefix="/transacoes", tags=["Transações"])

PADRAO_MES = r"^\d{4}-(0[1-9]|1[0-2])$"


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


@router.post("/gerar-fixas")
def gerar_fixas(
    mes: str = Query(pattern=PADRAO_MES),
    db: Session = Depends(get_db),
):
    inicio, fim = intervalo_do_mes(mes)
    ultimo_dia = calendar.monthrange(inicio.year, inicio.month)[1]

    anteriores = (
        db.query(models.Transacao)
        .filter(models.Transacao.data < inicio)
        .order_by(models.Transacao.data.desc(), models.Transacao.id.desc())
        .all()
    )

    mais_recentes = {}
    for transacao in anteriores:
        chave = (normalizar(transacao.descricao), transacao.tipo)
        if chave not in mais_recentes:
            mais_recentes[chave] = transacao

    do_mes = (
        db.query(models.Transacao)
        .filter(models.Transacao.data >= inicio, models.Transacao.data < fim)
        .all()
    )
    ja_existem = {(normalizar(t.descricao), t.tipo) for t in do_mes}

    criadas = 0
    for chave, origem in mais_recentes.items():
        if not origem.fixa or chave in ja_existem:
            continue

        nova = models.Transacao(
            descricao=origem.descricao,
            valor=origem.valor,
            tipo=origem.tipo,
            data=date(inicio.year, inicio.month, min(origem.data.day, ultimo_dia)),
            fixa=True,
            categoria_id=origem.categoria_id,
        )
        db.add(nova)
        criadas += 1

    db.commit()
    return {"mes": mes, "criadas": criadas}


@router.get("/", response_model=list[schemas.TransacaoSaida])
def listar(
    mes: str | None = Query(default=None, pattern=PADRAO_MES),
    db: Session = Depends(get_db),
):
    consulta = db.query(models.Transacao)

    if mes is not None:
        inicio, fim = intervalo_do_mes(mes)
        consulta = consulta.filter(
            models.Transacao.data >= inicio,
            models.Transacao.data < fim,
        )

    return consulta.order_by(
        models.Transacao.data.desc(), models.Transacao.id.desc()
    ).all()


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


@router.patch("/{transacao_id}/fixa", response_model=schemas.TransacaoSaida)
def alterar_fixa(
    transacao_id: int,
    dados: schemas.FixaAtualizar,
    db: Session = Depends(get_db),
):
    transacao = db.get(models.Transacao, transacao_id)
    if transacao is None:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    transacao.fixa = dados.fixa
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