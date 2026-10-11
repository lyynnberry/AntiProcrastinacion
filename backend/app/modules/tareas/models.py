"""Entidad TAREA (documento §4.2). Soporta RF-04 a RF-09 y RF-11.

Columnas del documento que aún NO se crean (pertenecen a requerimientos posteriores o están
"pendientes de confirmar" en el documento): `progreso`, `veces_pospuesta`, `fecha_programada`.
Se agregan con una migración cuando se implementen.

Notas de diseño:
- `prioridad`: 1 = Baja, 2 = Media, 3 = Alta (RF-09). La API usa los nombres.
- `estado`: el CHECK admite los cuatro estados del documento. Hoy la aplicación solo escribe
  PENDIENTE, EN_PROGRESO y COMPLETADA; VENCIDA se calcula al consultar (ver tareas/reglas.py).
- `id_materia` es opcional. La FK COMPUESTA (id_materia, id_usuario) -> materia garantiza en la
  base de datos que la materia pertenece al mismo usuario (RF-11). Con id_materia NULL no se aplica.
- Eliminación lógica (`fecha_eliminacion`): así el historial conserva su referencia a la tarea (RF-06 regla 5).
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tarea(Base):
    __tablename__ = "tarea"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_materia", "id_usuario"],
            ["materia.id_materia", "materia.id_usuario"],
            name="fk_tarea_materia_del_mismo_usuario",
        ),
        # Necesaria para la FK compuesta que usa HISTORIAL_EVENTO.
        UniqueConstraint("id_tarea", "id_usuario", name="uq_tarea_id_usuario"),
        CheckConstraint("prioridad IN (1, 2, 3)", name="prioridad_valida"),
        CheckConstraint(
            "estado IN ('PENDIENTE', 'EN_PROGRESO', 'COMPLETADA', 'VENCIDA')", name="estado_valido"
        ),
        CheckConstraint("fecha_limite > fecha_creacion", name="limite_posterior_a_creacion"),  # RF-08
        CheckConstraint("length(trim(titulo)) > 0", name="titulo_no_vacio"),
        Index("ix_tarea_usuario_fecha_limite", "id_usuario", "fecha_limite"),
    )

    id_tarea: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    id_materia: Mapped[uuid.UUID | None] = mapped_column()
    titulo: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text)
    prioridad: Mapped[int] = mapped_column(SmallInteger)
    estado: Mapped[str] = mapped_column(String(20), server_default="PENDIENTE")
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_limite: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Se asigna al crear y no se modifica jamás (RF-29 la usará para reprogramaciones).
    fecha_limite_original: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_completada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Si tiene valor, la tarea está eliminada (RF-06).
    fecha_eliminacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
