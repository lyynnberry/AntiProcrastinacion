"""Entidad USUARIO (documento §4.2). Soporta RF-01 y RF-02.

Diferencias con el documento (ver DECISIONES.md):
- No se crea `auth_uid` (proveedor externo): Google Sign-In no está en el alcance de RF-01/02.
- `nombre` es opcional.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, LargeBinary, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (CheckConstraint("idioma IN ('es', 'en')", name="idioma_valido"),)

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
    # --- Configuración inicial y preferencias de cuenta (extensión del documento V6, ver DECISIONES.md) ---
    idioma: Mapped[str] = mapped_column(String(5), server_default="es")  # 'es' | 'en'
    # NULL = aún no ha pasado por esa etapa. Las dos fechas gobiernan el flujo de primer uso y se
    # guardan en el servidor para que sobrevivan a cerrar la app o cambiar de dispositivo.
    personalizacion_completada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tutorial_completado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # NULL = sin foto. Se actualiza al subir/borrar y sirve para saber si hay foto sin leer los bytes
    # y para que el cliente refresque su caché.
    foto_actualizada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PreferenciaNotificacion(Base):
    """Preferencia de recordatorios elegida por el usuario (pantalla "Personaliza tu experiencia").

    NO es `notificacion.nivel_intensidad` (V6 §4.7), que es el nivel de ESCALADA de cada recordatorio
    (RF-13). Aquí solo se guarda qué tan insistente quiere el usuario que sea el sistema; RF-12/RF-13
    la leerán como parámetro y la escalada por nivel se mantiene intacta.
    """

    __tablename__ = "preferencia_notificacion"
    __table_args__ = (
        CheckConstraint(
            "perfil_recordatorios IN ('tranquilo', 'equilibrado', 'insistente')",
            name="perfil_valido",
        ),
    )

    id_usuario: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"), primary_key=True
    )
    perfil_recordatorios: Mapped[str] = mapped_column(String(12), server_default="equilibrado")
    notificaciones_activas: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FotoPerfil(Base):
    """Foto de perfil ya validada y re-codificada (JPEG cuadrado). Una por usuario.

    Vive en una tabla aparte para que las consultas de usuario nunca carguen los bytes.
    """

    __tablename__ = "foto_perfil"

    id_usuario: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"), primary_key=True
    )
    contenido: Mapped[bytes] = mapped_column(LargeBinary)
    tipo_mime: Mapped[str] = mapped_column(String(32))
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
