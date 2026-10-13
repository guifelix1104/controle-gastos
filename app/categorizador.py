import re
import unicodedata

from sqlalchemy.orm import Session

from app.models import Categoria


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_acento.lower().strip()


def descobrir_categoria(db: Session, descricao: str) -> Categoria | None:
    texto = normalizar(descricao)

    melhor_categoria = None
    melhor_tamanho = 0

    for categoria in db.query(Categoria).all():
        for palavra in categoria.palavras_chave.split(","):
            palavra = normalizar(palavra)
            if not palavra:
                continue

            achou = re.search(rf"\b{re.escape(palavra)}\b", texto)
            if achou and len(palavra) > melhor_tamanho:
                melhor_categoria = categoria
                melhor_tamanho = len(palavra)

    if melhor_categoria is not None:
        return melhor_categoria

    return db.query(Categoria).filter(Categoria.nome == "Outros").first()