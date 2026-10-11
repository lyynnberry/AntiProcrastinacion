"""Acceso a datos de TAREA.

Reglas de seguridad e integridad aplicadas AQUÍ para que no dependan de cada servicio:
- Toda consulta filtra por `id_usuario` (aislamiento de datos).
- Toda consulta excluye tareas eliminadas (`fecha_eliminacion IS NULL`, RF-06).
"""
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.modules.tareas.enums import PRIORIDAD_A_NUMERO, EstadoTarea, Prioridad
from app.modules.tareas.models import Tarea


@dataclass
class FiltrosTarea:
    estado: EstadoTarea | None = None
    prioridad: Prioridad | None = None
    id_materia: uuid.UUID | None = None
    limite_desde: datetime | None = None  # fecha_limite >= limite_desde
    limite_hasta: datetime | None = None  # fecha_limite <  limite_hasta


def _condicion_estado(estado: EstadoTarea, ahora: datetime):
    """Traduce el estado EFECTIVO a SQL (misma regla que tareas/reglas.py::estado_efectivo)."""
    abiertas = Tarea.estado.in_([EstadoTarea.PENDIENTE.value, EstadoTarea.EN_PROGRESO.value])
    if estado == EstadoTarea.VENCIDA:
        return or_(Tarea.estado == EstadoTarea.VENCIDA.value, and_(abiertas, Tarea.fecha_limite < ahora))
    if estado == EstadoTarea.COMPLETADA:
        return Tarea.estado == EstadoTarea.COMPLETADA.value
    # PENDIENTE / EN_PROGRESO: solo mientras no hayan vencido.
    return and_(Tarea.estado == estado.value, Tarea.fecha_limite >= ahora)


class TareaRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear(self, **campos) -> Tarea:
        tarea = Tarea(**campos)
        self.db.add(tarea)
        self.db.flush()
        return tarea

    def obtener(self, id_tarea: uuid.UUID, id_usuario: uuid.UUID) -> Tarea | None:
        return self.db.scalar(
            select(Tarea).where(
                Tarea.id_tarea == id_tarea,
                Tarea.id_usuario == id_usuario,
                Tarea.fecha_eliminacion.is_(None),
            )
        )

    def listar(
        self,
        id_usuario: uuid.UUID,
        filtros: FiltrosTarea,
        ahora: datetime,
        limite: int,
        desplazamiento: int,
    ) -> list[Tarea]:
        consulta = select(Tarea).where(Tarea.id_usuario == id_usuario, Tarea.fecha_eliminacion.is_(None))

        if filtros.estado is not None:
            consulta = consulta.where(_condicion_estado(filtros.estado, ahora))
        if filtros.prioridad is not None:
            consulta = consulta.where(Tarea.prioridad == PRIORIDAD_A_NUMERO[filtros.prioridad])
        if filtros.id_materia is not None:
            consulta = consulta.where(Tarea.id_materia == filtros.id_materia)
        if filtros.limite_desde is not None:
            consulta = consulta.where(Tarea.fecha_limite >= filtros.limite_desde)
        if filtros.limite_hasta is not None:
            consulta = consulta.where(Tarea.fecha_limite < filtros.limite_hasta)

        # Orden por defecto (RF-07 regla 6): la que vence primero, primero. El id desempata.
        consulta = (
            consulta.order_by(Tarea.fecha_limite.asc(), Tarea.id_tarea.asc())
            .limit(limite)
            .offset(desplazamiento)
        )
        return list(self.db.scalars(consulta))
