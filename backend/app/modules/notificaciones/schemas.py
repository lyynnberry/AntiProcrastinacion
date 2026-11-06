import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

EstadoNotificacion = Literal["PROGRAMADA", "ENVIADA", "RESPONDIDA", "IGNORADA", "CANCELADA"]


class NotificacionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_notificacion: uuid.UUID
    id_tarea: uuid.UUID | None
    tipo: str
    nivel_intensidad: int | None
    mensaje: str
    requiere_accion: bool
    es_aviso_final: bool
    estado: EstadoNotificacion
    fecha_generacion: datetime
    fecha_programada: datetime
    fecha_envio: datetime | None
    fecha_cancelacion: datetime | None
