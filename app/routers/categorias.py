from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("/", response_model=list[schemas.CategoriaSaida])
def listar(db: Session = Depends(get_db)):
    return db.query(models.Categoria).order_by(models.Categoria.nome).all()