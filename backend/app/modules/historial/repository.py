"""Escritura en HISTORIAL_EVENTO. Los registros son de solo-agregar: nunca se modifican ni se borran."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.historial.models import HistorialEvento


class HistorialRepository:
    def __init__(self, db: Session):
        self.db = db

    def registrar(
        self,
        id_usuario: uuid.UUID,
        id_tarea: uuid.UUID | None,
        tipo_evento: str,
        datos: dict,
        fecha_evento: datetime,
        origen: str = "USUARIO",
        id_notificacion: uuid.UUID | None = None,
    ) -> HistorialEvento:
        evento = HistorialEvento(
            id_usuario=id_usuario,
            id_tarea=id_tarea,
            id_notificacion=id_notificacion,
            tipo_evento=tipo_evento,
            origen=origen,
            datos=datos,
            fecha_evento=fecha_evento,
        )
        self.db.add(evento)
        return evento

    def listar_de_tarea(self, id_usuario: uuid.UUID, id_tarea: uuid.UUID) -> list[HistorialEvento]:
        """RF-32. Eventos de una tarea, en orden cronológico. Siempre filtra por el usuario."""
        return list(
            self.db.scalars(
                select(HistorialEvento)
                .where(HistorialEvento.id_usuario == id_usuario, HistorialEvento.id_tarea == id_tarea)
                .order_by(HistorialEvento.fecha_evento.asc(), HistorialEvento.tipo_evento.asc())
            )
        )
