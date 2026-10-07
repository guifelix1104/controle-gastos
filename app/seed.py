from sqlalchemy.orm import Session

from app.models import Categoria

CATEGORIAS_PADRAO = {
    "Moradia": "aluguel,condominio,luz,agua,internet,gas,iptu",
    "Alimentação": "mercado,supermercado,restaurante,ifood,padaria,lanche",
    "Transporte": "uber,gasolina,combustivel,onibus,metro,estacionamento",
    "Lazer": "netflix,spotify,cinema,bar,show,jogo,viagem",
    "Saúde": "farmacia,remedio,consulta,academia,plano de saude",
    "Educação": "curso,faculdade,escola,livro,mensalidade",
    "Outros": "",
}


def criar_categorias_padrao(db: Session):
    if db.query(Categoria).count() > 0:
        return  # já existem, não duplica

    for nome, palavras in CATEGORIAS_PADRAO.items():
        db.add(Categoria(nome=nome, palavras_chave=palavras))
    db.commit()