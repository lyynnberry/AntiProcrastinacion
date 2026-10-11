"""Entidad MATERIA (documento §4.2). Soporta RF-10 y RF-11.

Cambios respecto al documento (ver DECISIONES.md):
- `nombre_normalizado`: RF-10 regla 5 exige guardar el nombre normalizado para evitar duplicados
  por mayúsculas/minúsculas, y la tabla del documento no tenía esa columna.
- `uq_materia_id_usuario`: restricción única (id_materia, id_usuario) necesaria para la FK
  compuesta que usa TAREA (RF-11: una tarea solo puede asociarse a una materia del mismo usuario).
- Índice único PARCIAL: un usuario no puede tener dos materias ACTIVAS con el mismo nombre (RF-10 regla 3).
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Materia(Base):
    __tablename__ = "materia"
    __table_args__ = (
        UniqueConstraint("id_materia", "id_usuario", name="uq_materia_id_usuario"),
        Index(
            "uq_materia_usuario_nombre_activa",
            "id_usuario",
            "nombre_normalizado",
            unique=True,
            postgresql_where=text("activa"),
        ),
        CheckConstraint("length(trim(nombre)) > 0", name="nombre_no_vacio"),
    )

    id_materia: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    nombre_normalizado: Mapped[str] = mapped_column(String(100))
    activa: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
