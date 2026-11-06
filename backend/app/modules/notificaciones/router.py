"""Endpoints de RF-12 / RF-13. Todos exigen sesión y solo devuelven datos del usuario autenticado."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.tiempo import ahora_utc
from app.modules.auth.dependencies import get_usuario_actual
from app.modules.notificaciones.schemas import EstadoNotificacion, NotificacionSalida
from app.modules.notificaciones.service import NotificacionService
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])

UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]
BaseDatos = Annotated[Session, Depends(get_db)]


@router.post("/sincronizar", response_model=list[NotificacionSalida])
def sincronizar(usuario: UsuarioActual, db: BaseDatos):
    """Actualiza el plan y devuelve los avisos PROGRAMADA futuros para que la app los programe en el
    teléfono. La app debe REEMPLAZAR todos sus avisos locales por esta lista (lo que no viene, se quita)."""
    return NotificacionService(db).sincronizar(usuario, ahora_utc())


@router.get("", response_model=list[NotificacionSalida])
def listar(
    usuario: UsuarioActual,
    db: BaseDatos,
    estado: Annotated[EstadoNotificacion | None, Query()] = None,
    id_tarea: Annotated[uuid.UUID | None, Query()] = None,
    limite: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """Consulta (solo lectura) de las notificaciones del usuario, ordenadas por hora programada."""
    return NotificacionService(db).listar(usuario, estado, id_tarea, limite)
