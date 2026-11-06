"""Entidad NOTIFICACION (documento V6 §4.2). Soporta RF-12 y RF-13.

Basada en el diseño revisado del parche `entregas/paso1_migracion_0003.patch` (solo la parte de
notificaciones; enfoque, gamificación y riesgo quedan fuera de este alcance).

Qué significa cada estado aquí (DECISIONES.md §4.1):
- PROGRAMADA: el backend la generó y guardó. NO quiere decir que llegó al teléfono.
- ENVIADA: su `fecha_programada` ya pasó y el dispositivo la había sincronizado
  (`fecha_sincronizacion` no nula). Es una aproximación: el backend no puede confirmar que Android
  la mostró físicamente. `fecha_envio` = `fecha_programada`.
- CANCELADA: dejó de ser necesaria (tarea completada, eliminada, fecha cambiada, preferencias) o su
  hora pasó sin que el dispositivo la sincronizara.
- RESPONDIDA / IGNORADA: reservadas para RF-14 (fuera de alcance), no se escriben todavía.

Diferencias con V6 (extensiones documentadas en DECISIONES.md):
- `fecha_generacion`: cuándo la creó el backend.
- `fecha_sincronizacion`: cuándo el dispositivo la recibió por última vez.
- `es_aviso_final`: marca el aviso especial T - 1 h (prioritario en el máximo diario).
- Índice único PARCIAL (id_tarea, fecha_programada) para estados no cancelados: impide duplicados.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class Notificacion(Base):
    __tablename__ = "notificacion"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_tarea", "id_usuario"],
            ["tarea.id_tarea", "tarea.id_usuario"],
            name="fk_notificacion_tarea_del_mismo_usuario",
        ),
        # Necesaria para la FK compuesta que usa HISTORIAL_EVENTO.
        UniqueConstraint("id_notificacion", "id_usuario", name="uq_notificacion_id_usuario"),
        CheckConstraint(
            "tipo IN ('RECORDATORIO', 'URGENTE', 'CRITICA', 'CORRECTIVA', 'ACUMULACION')",
            name="tipo_valido",
        ),
        CheckConstraint(
            "estado IN ('PROGRAMADA', 'ENVIADA', 'RESPONDIDA', 'IGNORADA', 'CANCELADA')",
            name="estado_valido",
        ),
        CheckConstraint(
            "accion_respuesta IN ('COMPLETAR', 'INICIAR_ENFOQUE', 'POSPONER', 'CONTINUAR_DESPUES')",
            name="accion_respuesta_valida",
        ),
        CheckConstraint("nivel_intensidad BETWEEN 1 AND 4", name="nivel_intensidad_valido"),
        # V6: id_tarea "es NULL solo en alertas de acumulación" (RF-15).
        CheckConstraint(
            "id_tarea IS NOT NULL OR tipo = 'ACUMULACION'", name="tarea_obligatoria_salvo_acumulacion"
        ),
        CheckConstraint("length(trim(mensaje)) > 0", name="mensaje_no_vacio"),
        # Una tarea no puede tener dos avisos vigentes en el mismo instante (prevención de duplicados).
        Index(
            "uq_notificacion_tarea_momento_vigente",
            "id_tarea",
            "fecha_programada",
            unique=True,
            postgresql_where=text("estado <> 'CANCELADA'"),
        ),
        Index("ix_notificacion_usuario_estado_programada", "id_usuario", "estado", "fecha_programada"),
        Index("ix_notificacion_tarea_estado", "id_tarea", "estado"),
    )

    id_notificacion: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_usuario: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id_usuario"))
    id_tarea: Mapped[uuid.UUID | None] = mapped_column()
    tipo: Mapped[str] = mapped_column(String(20))
    nivel_intensidad: Mapped[int | None] = mapped_column(SmallInteger)
    mensaje: Mapped[str] = mapped_column(Text)
    requiere_accion: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    es_aviso_final: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    estado: Mapped[str] = mapped_column(String(15), server_default="PROGRAMADA")
    fecha_generacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_programada: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_sincronizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_cancelacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accion_respuesta: Mapped[str | None] = mapped_column(String(20))
    fecha_respuesta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
