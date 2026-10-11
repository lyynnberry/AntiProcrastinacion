from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.auth.dependencies import get_usuario_actual
from app.modules.materias.schemas import MateriaCrear, MateriaSalida
from app.modules.materias.service import MateriaService
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/materias", tags=["Materias"])


@router.post("", response_model=MateriaSalida, status_code=status.HTTP_201_CREATED)
def crear_materia(
    datos: MateriaCrear,
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
    db: Annotated[Session, Depends(get_db)],
):
    """RF-10."""
    return MateriaService(db).crear(usuario, datos)


@router.get("", response_model=list[MateriaSalida])
def listar_materias(
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
    db: Annotated[Session, Depends(get_db)],
):
    """Materias activas del usuario (necesarias para asociarlas a tareas, RF-11)."""
    return MateriaService(db).listar(usuario)
