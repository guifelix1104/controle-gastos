from fastapi import FastAPI # é tipo uma biblioteca do python

app= FastAPI(title="Controle de Gastos")

@app.get("/") # quando alguem ir no endereço principal do site, vai rodar a função de baixo
def raiz(): # a que vai rodar
    return {"mensagem": "Controle de gastos funcionando!"} # vai retornar a mensagem