"""Entidades de gamificación (documento V6 §4.2). Soportan RF-21 a RF-27.

Tablas V6: PERFIL_GAMIFICACION, DIA_RACHA, TRANSACCION_GAMIFICACION, LOGRO, LOGRO_USUARIO y
RECUPERACION_RACHA. Extensiones documentadas en DECISIONES.md (sección gamificación):
- perfil_gamificacion.primer_dia_evaluable: no hay racha retroactiva (se evalúa desde que existe el perfil).
- dia_racha.racha_previa: valor de la racha ANTES de evaluar el día (RF-24 la restaura al proteger).
- transaccion_gamificacion.clave_idempotencia (+ UNIQUE por usuario): una misma acción nunca genera dos
  movimientos (RF-22 regla 6, RF-27 regla 4), aunque dos procesos corran a la vez.
- transaccion_gamificacion.codigo_recompensa: qué recompensa (RF-27) originó el movimiento.
- logro.nombre_en / descripcion_en: textos en inglés (la app es bilingüe).
- logro.tipo_condicion TAREAS_ANTICIPADAS: para la categoría VELOCIDAD (V6 no trae una condición para ella).
- recuperacion_racha.id_dia_perdido, tareas_atrasadas, racha_restaurada: qué incumplimiento se recupera,
  qué tareas había que atender y con qué valor quedó la racha.

Todas las FK hacia tarea / dia_racha son COMPUESTAS con id_usuario: nada puede apuntar a datos de otra cuenta.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PerfilGamificacion(Base):
    __tablename__ = "perfil_gamificacion"
    __table_args__ = (
        CheckConstraint("puntos_totales >= 0", name="puntos_no_negativos"),  # RF-22 regla 7
        CheckConstraint("nivel >= 1", name="nivel_valido"),
        CheckConstraint("racha_actual >= 0", name="racha_no_negativa"),
        CheckConstraint("racha_maxima >= racha_actual", name="racha_maxima_valida"),  # V6
        CheckConstraint("protecciones_disponibles >= 0", name="protecciones_no_negativas"),  # V6
    )

    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), primary_key=True)
    puntos_totales: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    nivel: Mapped[int] = mapped_column(SmallInteger, server_default=text("1"))
    racha_actual: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    racha_maxima: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    protecciones_disponibles: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    ultima_fecha_evaluada: Mapped[date | None] = mapped_column(Date)
    primer_dia_evaluable: Mapped[date] = mapped_column(Date)
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DiaRacha(Base):
    __tablename__ = "dia_racha"
    __table_args__ = (
        UniqueConstraint("id_usuario", "fecha", name="uq_dia_racha_usuario_fecha"),  # un día se evalúa una vez
        UniqueConstraint("id_dia_racha", "id_usuario", name="uq_dia_racha_id_usuario"),
        CheckConstraint(
            "resultado IN ('CUMPLIDO', 'INCUMPLIDO', 'PROTEGIDO', 'SIN_COMPROMISOS')", name="resultado_valido"
        ),
        CheckConstraint("tareas_comprometidas >= 0", name="comprometidas_no_negativas"),
        CheckConstraint(
            "tareas_cumplidas_a_tiempo BETWEEN 0 AND tareas_comprometidas", name="cumplidas_validas"
        ),
        CheckConstraint("racha_resultante >= 0 AND racha_previa >= 0", name="rachas_no_negativas"),
    )

    id_dia_racha: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    fecha: Mapped[date] = mapped_column(Date)  # día local del usuario
    resultado: Mapped[str] = mapped_column(String(20))
    tareas_comprometidas: Mapped[int] = mapped_column(SmallInteger)
    tareas_cumplidas_a_tiempo: Mapped[int] = mapped_column(SmallInteger)
    racha_previa: Mapped[int] = mapped_column(Integer)
    racha_resultante: Mapped[int] = mapped_column(Integer)
    fecha_evaluacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Logro(Base):
    __tablename__ = "logro"
    __table_args__ = (
        CheckConstraint(
            "categoria IN ('RACHA', 'VELOCIDAD', 'PRODUCTIVIDAD', 'CONSTANCIA')", name="categoria_valida"
        ),
        CheckConstraint(
            "tipo_condicion IN ('DIAS_RACHA', 'PUNTOS_TOTALES', 'TAREAS_A_TIEMPO', 'TAREAS_ANTICIPADAS')",
            name="tipo_condicion_valido",
        ),
        CheckConstraint("valor_condicion > 0", name="valor_condicion_positivo"),
        CheckConstraint("recompensa_puntos >= 0", name="recompensa_no_negativa"),
    )

    id_logro: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str] = mapped_column(Text)
    nombre_en: Mapped[str] = mapped_column(String(100))
    descripcion_en: Mapped[str] = mapped_column(Text)
    categoria: Mapped[str] = mapped_column(String(20))
    tipo_condicion: Mapped[str] = mapped_column(String(30))
    valor_condicion: Mapped[int] = mapped_column(Integer)
    recompensa_puntos: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class LogroUsuario(Base):
    __tablename__ = "logro_usuario"
    __table_args__ = (UniqueConstraint("id_usuario", "id_logro", name="uq_logro_usuario"),)  # RF-23 regla 2

    id_logro_usuario: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    id_logro: Mapped[uuid.UUID] = mapped_column(ForeignKey("logro.id_logro"))
    fecha_desbloqueo: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # RF-23 regla 4


class TransaccionGamificacion(Base):
    """Libro de movimientos de puntos y protecciones (historial de gamificación)."""

    __tablename__ = "transaccion_gamificacion"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_tarea", "id_usuario"], ["tarea.id_tarea", "tarea.id_usuario"],
            name="fk_transaccion_tarea_del_mismo_usuario",
        ),
        ForeignKeyConstraint(
            ["id_dia_racha", "id_usuario"], ["dia_racha.id_dia_racha", "dia_racha.id_usuario"],
            name="fk_transaccion_dia_del_mismo_usuario",
        ),
        UniqueConstraint("id_usuario", "clave_idempotencia", name="uq_transaccion_usuario_clave"),
        CheckConstraint("recurso IN ('PUNTOS', 'PROTECCION_RACHA')", name="recurso_valido"),
        CheckConstraint("cantidad <> 0", name="cantidad_no_cero"),
        CheckConstraint(
            "motivo IN ('TAREA_A_TIEMPO', 'LOGRO_DESBLOQUEADO', 'RECOMPENSA', 'PROTECCION_USADA')",
            name="motivo_valido",
        ),
        Index("ix_transaccion_usuario_fecha", "id_usuario", "fecha"),
    )

    id_transaccion: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"))
    recurso: Mapped[str] = mapped_column(String(20))
    cantidad: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(String(40))
    codigo_recompensa: Mapped[str | None] = mapped_column(String(40))
    id_tarea: Mapped[uuid.UUID | None] = mapped_column()
    id_logro: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("logro.id_logro"))
    id_dia_racha: Mapped[uuid.UUID | None] = mapped_column()
    clave_idempotencia: Mapped[str] = mapped_column(String(120))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecuperacionRacha(Base):
    __tablename__ = "recuperacion_racha"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_dia_perdido", "id_usuario"], ["dia_racha.id_dia_racha", "dia_racha.id_usuario"],
            name="fk_recuperacion_dia_del_mismo_usuario",
        ),
        UniqueConstraint("id_dia_perdido", name="uq_recuperacion_dia_perdido"),  # una por racha perdida
        CheckConstraint("racha_perdida > 0", name="racha_perdida_positiva"),  # V6
        CheckConstraint("fecha_fin_prevista >= fecha_inicio", name="fin_posterior_a_inicio"),  # V6
        CheckConstraint("estado IN ('ACTIVA', 'EXITOSA', 'FALLIDA', 'CANCELADA')", name="estado_valido"),
        # Como máximo una recuperación ACTIVA por usuario (también ante solicitudes simultáneas).
        Index(
            "uq_recuperacion_usuario_activa", "id_usuario", unique=True, postgresql_where=text("estado = 'ACTIVA'")
        ),
    )

    id_recuperacion: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"), index=True)
    id_dia_perdido: Mapped[uuid.UUID] = mapped_column()
    racha_perdida: Mapped[int] = mapped_column(Integer)
    tareas_atrasadas: Mapped[list] = mapped_column(JSONB)  # ids de las tareas que causaron el incumplimiento
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin_prevista: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(15), server_default="ACTIVA")
    racha_restaurada: Mapped[int | None] = mapped_column(Integer)
    motivo_resolucion: Mapped[str | None] = mapped_column(String(40))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_resolucion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
