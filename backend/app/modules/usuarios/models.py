"""Entidad USUARIO (documento §4.2). Soporta RF-01 y RF-02.

Diferencias con el documento (ver DECISIONES.md):
- No se crea `auth_uid` (proveedor externo): Google Sign-In no está en el alcance de RF-01/02.
- `nombre` es opcional.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Se guarda normalizado (minúsculas, sin espacios en los extremos) -> la unicidad es insensible a mayúsculas.
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # Argon2id; nunca texto plano
    nombre: Mapped[str | None] = mapped_column(String(100))
    zona_horaria: Mapped[str] = mapped_column(
        String(64), server_default="America/Mexico_City"
    )
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
