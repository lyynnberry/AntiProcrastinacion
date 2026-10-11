"""Escritura en HISTORIAL_EVENTO. Los registros son de solo-agregar: nunca se modifican ni se borran."""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.historial.models import HistorialEvento


class HistorialRepository:
    def __init__(self, db: Session):
        self.db = db

    def registrar(
        self,
        id_usuario: uuid.UUID,
        id_tarea: uuid.UUID,
        tipo_evento: str,
        datos: dict,
        fecha_evento: datetime,
        origen: str = "USUARIO",
    ) -> HistorialEvento:
        evento = HistorialEvento(
            id_usuario=id_usuario,
            id_tarea=id_tarea,
            tipo_evento=tipo_evento,
            origen=origen,
            datos=datos,
            fecha_evento=fecha_evento,
        )
        self.db.add(evento)
        return evento
