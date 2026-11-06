"""RF-32: consulta del historial de una tarea (solo lectura; el historial nunca se edita por la API)."""
import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import NoEncontrado
from app.modules.auth.dependencies import get_usuario_actual
from app.modules.historial.repository import HistorialRepository
from app.modules.tareas.repository import TareaRepository
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/tareas", tags=["Historial"])


class EventoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_evento: uuid.UUID
    id_tarea: uuid.UUID | None
    id_notificacion: uuid.UUID | None
    tipo_evento: str
    origen: str
    datos: dict[str, Any] | None
    fecha_evento: datetime


@router.get("/{id_tarea}/historial", response_model=list[EventoSalida])
def historial_de_tarea(
    id_tarea: uuid.UUID,
    usuario: Annotated[Usuario, Depends(get_usuario_actual)],
    db: Annotated[Session, Depends(get_db)],
):
    """Eventos de una tarea propia, en orden cronológico. Tarea ajena, inexistente o eliminada -> 404."""
    if TareaRepository(db).obtener(id_tarea, usuario.id_usuario) is None:
        raise NoEncontrado("Tarea no encontrada.", "TAREA_NO_ENCONTRADA")
    return HistorialRepository(db).listar_de_tarea(usuario.id_usuario, id_tarea)
