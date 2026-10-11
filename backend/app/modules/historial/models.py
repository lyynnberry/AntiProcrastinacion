"""Entidad HISTORIAL_EVENTO (documento §4.2), versión MÍNIMA.

Por qué existe ya: RF-05 (reglas 5-7) y RF-06 (regla 4) exigen registrar ediciones y eliminaciones.
Completa RF-32/RF-33 queda para más adelante.

Aún no se crean `id_notificacion` ni `id_sesion` (FK a tablas que todavía no existen);
se agregarán por migración junto con esos módulos.
"""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, String, func
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
        CheckConstraint("origen IN ('USUARIO', 'SISTEMA', 'NOTIFICACION')", name="origen_valido"),
    )

    id_evento: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    id_tarea: Mapped[uuid.UUID | None] = mapped_column(index=True)
    tipo_evento: Mapped[str] = mapped_column(String(40))
    origen: Mapped[str] = mapped_column(String(15), server_default="USUARIO")
    # Valores anteriores y nuevos del cambio: {"antes": {...}, "despues": {...}}
    datos: Mapped[dict | None] = mapped_column(JSONB)
    fecha_evento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
