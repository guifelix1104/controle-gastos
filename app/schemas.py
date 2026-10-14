from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransacaoCriar(BaseModel):
    descricao: str = Field(min_length=1, max_length=100)
    valor: float = Field(gt=0)
    tipo: Literal["renda", "gasto"]
    data: date
    fixa: bool = False
    categoria_id: int | None = None


class TransacaoSaida(TransacaoCriar):
    id: int
    categoria_nome: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CategoriaSaida(BaseModel):
    id: int
    nome: str
    palavras_chave: str

    model_config = ConfigDict(from_attributes=True)


class MetaCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    valor_alvo: float = Field(gt=0)
    valor_guardado: float = Field(default=0, ge=0)
    prazo: date


class MetaSaida(MetaCriar):
    id: int
    faltante: float
    progresso: float
    meses_restantes: int
    guardar_por_mes: float | None
    status: Literal["em_andamento", "concluida", "vencida"]


class Deposito(BaseModel):
    valor: float = Field(gt=0)