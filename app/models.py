from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True)
    palavras_chave: Mapped[str] = mapped_column(String, default="")

    transacoes: Mapped[list["Transacao"]] = relationship(back_populates="categoria")


class Transacao(Base):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(100))
    valor: Mapped[float]
    tipo: Mapped[str] = mapped_column(String(10))  # "renda" ou "gasto"
    data: Mapped[date]
    fixa: Mapped[bool] = mapped_column(default=False)

    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"))
    categoria: Mapped["Categoria | None"] = relationship(back_populates="transacoes")

    @property
    def categoria_nome(self) -> str | None:
        return self.categoria.nome if self.categoria else None


class Meta(Base):
    __tablename__ = "metas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    valor_alvo: Mapped[float]
    valor_guardado: Mapped[float] = mapped_column(default=0.0)
    prazo: Mapped[date]


    # --- Usuários (Etapa 9) ---
from datetime import datetime, timezone  # noqa: E402

from sqlalchemy import DateTime, String  # noqa: E402
from sqlalchemy.orm import Mapped, mapped_column  # noqa: E402


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )