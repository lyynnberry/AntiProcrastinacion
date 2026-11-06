"""Entidad HISTORIAL_EVENTO (documento §4.2).

Soporta RF-05 (reglas 5-7), RF-06 (regla 4), RF-32 (historial de tareas) y RF-13 regla 5 (registro de
notificaciones enviadas). Los registros son de solo-agregar: ningún servicio los modifica ni los borra.

- `id_notificacion` (migración 0003): FK COMPUESTA (id_notificacion, id_usuario) -> notificacion, igual que
  la de tarea: un evento solo puede apuntar a datos del mismo usuario.
- `id_sesion` (sesión de enfoque) todavía no existe: llega con RF-14/RF-21.
"""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HistorialEvento(Base):
    __tablename__ = "historial_evento"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_tarea", "id_usuario"],
            ["tarea.id_tarea", "tarea.id_usuario"],
            name="fk_historial_tarea_del_mismo_usuario",
        ),
        ForeignKeyConstraint(
            ["id_notificacion", "id_usuario"],
            ["notificacion.id_notificacion", "notificacion.id_usuario"],
            name="fk_historial_notificacion_del_mismo_usuario",
        ),
        CheckConstraint("origen IN ('USUARIO', 'SISTEMA', 'NOTIFICACION')", name="origen_valido"),
        Index("ix_historial_evento_usuario_fecha", "id_usuario", "fecha_evento"),
    )

    id_evento: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    id_tarea: Mapped[uuid.UUID | None] = mapped_column(index=True)
    id_notificacion: Mapped[uuid.UUID | None] = mapped_column()
    tipo_evento: Mapped[str] = mapped_column(String(40))
    origen: Mapped[str] = mapped_column(String(15), server_default="USUARIO")
    # Valores anteriores y nuevos del cambio: {"antes": {...}, "despues": {...}}
    datos: Mapped[dict | None] = mapped_column(JSONB)
    fecha_evento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
