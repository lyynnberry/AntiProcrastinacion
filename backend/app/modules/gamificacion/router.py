"""Endpoints de RF-21 a RF-27. Todos exigen sesión y operan SOLO sobre el usuario autenticado: ningún
endpoint acepta un id de usuario enviado por el cliente."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.tiempo import ahora_utc
from app.modules.auth.dependencies import get_usuario_actual
from app.modules.gamificacion.schemas import (
    HistorialGamificacionSalida,
    LogroSalida,
    ProgresoSalida,
    RecuperacionSalida,
)
from app.modules.gamificacion.service import GamificacionService
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/gamificacion", tags=["Gamificación"])

UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]
BaseDatos = Annotated[Session, Depends(get_db)]


@router.get("/progreso", response_model=ProgresoSalida)
def progreso(usuario: UsuarioActual, db: BaseDatos):
    """RF-26: racha actual y máxima, puntos, nivel, protecciones, logros, recuperación y el día de hoy.
    Antes de responder evalúa los días cerrados pendientes (RF-21)."""
    return GamificacionService(db).progreso(usuario, ahora_utc())


@router.get("/logros", response_model=list[LogroSalida])
def logros(usuario: UsuarioActual, db: BaseDatos):
    """RF-23: catálogo de logros con el estado y el progreso del usuario (desbloqueados primero)."""
    return GamificacionService(db).logros(usuario, ahora_utc())


@router.get("/historial", response_model=HistorialGamificacionSalida)
def historial(
    usuario: UsuarioActual, db: BaseDatos, limite: Annotated[int, Query(ge=1, le=200)] = 50
):
    """Movimientos de puntos y protecciones, días evaluados y recuperaciones (más recientes primero)."""
    return GamificacionService(db).historial(usuario, ahora_utc(), limite)


@router.post("/protecciones/usar", response_model=ProgresoSalida)
def usar_proteccion(usuario: UsuarioActual, db: BaseDatos):
    """RF-24: usa una protección sobre el último día incumplido; la racha conserva su valor."""
    servicio = GamificacionService(db)
    ahora = ahora_utc()
    servicio.usar_proteccion(usuario, ahora)
    return servicio.progreso(usuario, ahora)


@router.post("/recuperaciones", response_model=RecuperacionSalida, status_code=status.HTTP_201_CREATED)
def iniciar_recuperacion(usuario: UsuarioActual, db: BaseDatos):
    """RF-25: inicia la recuperación de la racha perdida más reciente."""
    return GamificacionService(db).iniciar_recuperacion(usuario, ahora_utc())


@router.post("/recuperaciones/{id_recuperacion}/cancelar", response_model=RecuperacionSalida)
def cancelar_recuperacion(id_recuperacion: uuid.UUID, usuario: UsuarioActual, db: BaseDatos):
    """RF-25: cancela una recuperación ACTIVA propia (404 si no existe o es de otro usuario)."""
    return GamificacionService(db).cancelar_recuperacion(usuario, id_recuperacion, ahora_utc())
