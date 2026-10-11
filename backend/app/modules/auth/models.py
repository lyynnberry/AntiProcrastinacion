"""Entidad SESION_AUTENTICACION (documento §4.2). Soporta RF-03.

Una fila = una sesión iniciada en un dispositivo. Vence en `fecha_expiracion` (vigencia absoluta)
o cuando se cierra sesión (`fecha_revocacion`).
"""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SesionAutenticacion(Base):
    __tablename__ = "sesion_autenticacion"
    __table_args__ = (
        CheckConstraint("fecha_expiracion > fecha_emision", name="expiracion_posterior_a_emision"),
    )

    id_sesion_auth: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    # Solo el hash del refresh token; el token en sí nunca se guarda.
    refresh_token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    dispositivo: Mapped[str | None] = mapped_column(String(100))
    fecha_emision: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_expiracion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_revocacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
