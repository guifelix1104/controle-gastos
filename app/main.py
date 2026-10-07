from fastapi import FastAPI

app= FastAPI(title="Controle de Gastos")

@app.get("/")
def raiz():
    return {"mensagem": "Controle de gastos funcionando!"}