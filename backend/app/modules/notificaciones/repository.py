"""Acceso a datos de NOTIFICACION. Toda consulta filtra por `id_usuario` (aislamiento de datos)."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notificaciones.models import Notificacion

PROGRAMADA = "PROGRAMADA"
ENVIADA = "ENVIADA"
CANCELADA = "CANCELADA"


class NotificacionRepository:
    def __init__(self, db: Session):
        self.db = db

    def programadas_futuras(self, id_usuario: uuid.UUID, ahora: datetime) -> list[Notificacion]:
        return list(
            self.db.scalars(
                select(Notificacion).where(
                    Notificacion.id_usuario == id_usuario,
                    Notificacion.estado == PROGRAMADA,
                    Notificacion.fecha_programada > ahora,
                )
            )
        )

    def programadas_vencidas(self, id_usuario: uuid.UUID, ahora: datetime) -> list[Notificacion]:
        """PROGRAMADA cuya hora ya llegó: hay que decidir si cuentan como enviadas o se cancelan."""
        return list(
            self.db.scalars(
                select(Notificacion).where(
                    Notificacion.id_usuario == id_usuario,
                    Notificacion.estado == PROGRAMADA,
                    Notificacion.fecha_programada <= ahora,
                )
            )
        )

    def no_canceladas_entre(self, id_usuario: uuid.UUID, desde: datetime, hasta: datetime) -> list[Notificacion]:
        return list(
            self.db.scalars(
                select(Notificacion).where(
                    Notificacion.id_usuario == id_usuario,
                    Notificacion.estado != CANCELADA,
                    Notificacion.fecha_programada >= desde,
                    Notificacion.fecha_programada <= hasta,
                )
            )
        )

    def agregar(self, notificacion: Notificacion) -> None:
        self.db.add(notificacion)

    def listar(
        self,
        id_usuario: uuid.UUID,
        estado: str | None = None,
        id_tarea: uuid.UUID | None = None,
        limite: int = 100,
    ) -> list[Notificacion]:
        consulta = select(Notificacion).where(Notificacion.id_usuario == id_usuario)
        if estado is not None:
            consulta = consulta.where(Notificacion.estado == estado)
        if id_tarea is not None:
            consulta = consulta.where(Notificacion.id_tarea == id_tarea)
        consulta = consulta.order_by(Notificacion.fecha_programada.asc(), Notificacion.id_notificacion.asc())
        return list(self.db.scalars(consulta.limit(limite)))
