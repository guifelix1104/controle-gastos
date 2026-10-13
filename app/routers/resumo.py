from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/resumo", tags=["Resumo"])


def intervalo_do_mes(mes: str) -> tuple[date, date]:
    ano, numero = map(int, mes.split("-"))
    inicio = date(ano, numero, 1)
    if numero == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, numero + 1, 1)
    return inicio, fim


@router.get("/")
def resumo_do_mes(
    mes: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: Session = Depends(get_db),
):
    if mes is None:
        hoje = date.today()
        mes = f"{hoje.year}-{hoje.month:02d}"

    inicio, fim = intervalo_do_mes(mes)

    def somar(tipo: str) -> float:
        total = (
            db.query(func.coalesce(func.sum(models.Transacao.valor), 0.0))
            .filter(
                models.Transacao.tipo == tipo,
                models.Transacao.data >= inicio,
                models.Transacao.data < fim,
            )
            .scalar()
        )
        return round(total, 2)

    total_renda = somar("renda")
    total_gastos = somar("gasto")

    linhas = (
        db.query(models.Categoria.nome, func.sum(models.Transacao.valor))
        .select_from(models.Transacao)
        .outerjoin(
            models.Categoria, models.Transacao.categoria_id == models.Categoria.id
        )
        .filter(
            models.Transacao.tipo == "gasto",
            models.Transacao.data >= inicio,
            models.Transacao.data < fim,
        )
        .group_by(models.Categoria.nome)
        .all()
    )

    por_categoria = [
        {"categoria": nome or "Sem categoria", "total": round(total, 2)}
        for nome, total in linhas
    ]
    por_categoria.sort(key=lambda item: item["total"], reverse=True)

    return {
        "mes": mes,
        "total_renda": total_renda,
        "total_gastos": total_gastos,
        "saldo": round(total_renda - total_gastos, 2),
        "gastos_por_categoria": por_categoria,
    }