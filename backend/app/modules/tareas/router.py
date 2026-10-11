import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.tiempo import ahora_utc
from app.modules.auth.dependencies import get_usuario_actual
from app.modules.tareas.enums import EstadoTarea, Prioridad
from app.modules.tareas.schemas import TareaActualizar, TareaCrear, TareaSalida
from app.modules.tareas.service import TareaService
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/tareas", tags=["Tareas"])

UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]
BaseDatos = Annotated[Session, Depends(get_db)]


@router.post("", response_model=TareaSalida, status_code=status.HTTP_201_CREATED)
def crear_tarea(datos: TareaCrear, usuario: UsuarioActual, db: BaseDatos):
    """RF-04, RF-08, RF-09, RF-11."""
    tarea = TareaService(db).crear(usuario, datos)
    return TareaSalida.desde_tarea(tarea, ahora_utc())


@router.get("", response_model=list[TareaSalida])
def listar_tareas(
    usuario: UsuarioActual,
    db: BaseDatos,
    estado: Annotated[EstadoTarea | None, Query()] = None,
    prioridad: Annotated[Prioridad | None, Query()] = None,
    id_materia: Annotated[uuid.UUID | None, Query()] = None,
    fecha_desde: Annotated[date | None, Query(description="Día inicial (inclusive) de la fecha límite")] = None,
    fecha_hasta: Annotated[date | None, Query(description="Día final (inclusive) de la fecha límite")] = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
):
    """RF-07. Filtros combinables; sin filtros devuelve todas las tareas del usuario."""
    tareas = TareaService(db).listar(
        usuario, estado, prioridad, id_materia, fecha_desde, fecha_hasta, limite, desplazamiento
    )
    ahora = ahora_utc()
    return [TareaSalida.desde_tarea(t, ahora) for t in tareas]


@router.get("/{id_tarea}", response_model=TareaSalida)
def obtener_tarea(id_tarea: uuid.UUID, usuario: UsuarioActual, db: BaseDatos):
    """RF-07 (detalle)."""
    return TareaSalida.desde_tarea(TareaService(db).obtener(usuario, id_tarea), ahora_utc())


@router.patch("/{id_tarea}", response_model=TareaSalida)
def editar_tarea(id_tarea: uuid.UUID, datos: TareaActualizar, usuario: UsuarioActual, db: BaseDatos):
    """RF-05. Modifica solo los campos enviados."""
    tarea = TareaService(db).actualizar(usuario, id_tarea, datos)
    return TareaSalida.desde_tarea(tarea, ahora_utc())


@router.delete("/{id_tarea}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tarea(id_tarea: uuid.UUID, usuario: UsuarioActual, db: BaseDatos):
    """RF-06. El frontend debe pedir confirmación antes de llamar a este endpoint."""
    TareaService(db).eliminar(usuario, id_tarea)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
