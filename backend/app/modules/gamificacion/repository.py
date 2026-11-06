"""Acceso a datos de gamificación. Toda consulta recibe `id_usuario` y filtra por él."""
import uuid
from datetime import date, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.gamificacion.models import (
    DiaRacha,
    Logro,
    LogroUsuario,
    PerfilGamificacion,
    RecuperacionRacha,
    TransaccionGamificacion,
)
from app.modules.historial import tipos as tipos_evento
from app.modules.historial.models import HistorialEvento
from app.modules.tareas.models import Tarea


class GamificacionRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---- perfil (con bloqueo de fila: serializa todas las operaciones de un mismo usuario) ----
    def perfil_bloqueado(self, id_usuario: uuid.UUID, primer_dia: date) -> PerfilGamificacion:
        self.db.execute(
            insert(PerfilGamificacion)
            .values(id_usuario=id_usuario, primer_dia_evaluable=primer_dia)
            .on_conflict_do_nothing(index_elements=["id_usuario"])
        )
        perfil = self.db.scalar(
            select(PerfilGamificacion)
            .where(PerfilGamificacion.id_usuario == id_usuario)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return perfil

    def perfil(self, id_usuario: uuid.UUID) -> PerfilGamificacion | None:
        return self.db.get(PerfilGamificacion, id_usuario)

    # ---- días de racha ----
    def agregar(self, objeto) -> None:
        self.db.add(objeto)

    def dia(self, id_usuario: uuid.UUID, fecha: date) -> DiaRacha | None:
        return self.db.scalar(select(DiaRacha).where(DiaRacha.id_usuario == id_usuario, DiaRacha.fecha == fecha))

    def dias_entre(self, id_usuario: uuid.UUID, desde: date, hasta: date) -> list[DiaRacha]:
        return list(
            self.db.scalars(
                select(DiaRacha)
                .where(DiaRacha.id_usuario == id_usuario, DiaRacha.fecha >= desde, DiaRacha.fecha <= hasta)
                .order_by(DiaRacha.fecha)
            )
        )

    def ultimo_incumplido_con_racha(self, id_usuario: uuid.UUID) -> DiaRacha | None:
        return self.db.scalar(
            select(DiaRacha)
            .where(DiaRacha.id_usuario == id_usuario, DiaRacha.resultado == "INCUMPLIDO", DiaRacha.racha_previa > 0)
            .order_by(DiaRacha.fecha.desc())
            .limit(1)
        )

    def ultimos_dias(self, id_usuario: uuid.UUID, limite: int) -> list[DiaRacha]:
        return list(
            self.db.scalars(
                select(DiaRacha).where(DiaRacha.id_usuario == id_usuario).order_by(DiaRacha.fecha.desc()).limit(limite)
            )
        )

    # ---- compromisos (RF-21) ----
    def tareas_del_dia(self, id_usuario: uuid.UUID, dia: date, inicio: datetime, fin: datetime) -> list[Tarea]:
        """Tareas programadas para `dia`, o sin programar y con fecha límite en ese día local."""
        return list(
            self.db.scalars(
                select(Tarea).where(
                    Tarea.id_usuario == id_usuario,
                    # Antitrampa: una tarea eliminada DURANTE (o después de) el día sigue contando, salvo que
                    # se haya creado ese mismo día (p. ej. un duplicado creado por error).
                    or_(
                        Tarea.fecha_eliminacion.is_(None),
                        and_(Tarea.fecha_eliminacion >= inicio, Tarea.fecha_creacion < inicio),
                    ),
                    or_(
                        Tarea.fecha_programada == dia,
                        and_(Tarea.fecha_programada.is_(None), Tarea.fecha_limite >= inicio, Tarea.fecha_limite < fin),
                    ),
                )
            )
        )

    def cambios_de_fecha_en(self, id_usuario: uuid.UUID, inicio: datetime, fin: datetime) -> list[HistorialEvento]:
        """Posposiciones/reprogramaciones hechas durante el día (antitrampa de RF-21)."""
        return list(
            self.db.scalars(
                select(HistorialEvento).where(
                    HistorialEvento.id_usuario == id_usuario,
                    HistorialEvento.tipo_evento.in_([tipos_evento.TAREA_POSPUESTA, tipos_evento.TAREA_REPROGRAMADA]),
                    HistorialEvento.fecha_evento >= inicio,
                    HistorialEvento.fecha_evento < fin,
                )
            )
        )

    def tareas_por_id(self, id_usuario: uuid.UUID, ids: list[uuid.UUID]) -> list[Tarea]:
        if not ids:
            return []
        return list(self.db.scalars(select(Tarea).where(Tarea.id_usuario == id_usuario, Tarea.id_tarea.in_(ids))))

    # ---- transacciones (libro de puntos y protecciones) ----
    def existe_clave(self, id_usuario: uuid.UUID, clave: str) -> bool:
        return (
            self.db.scalar(
                select(TransaccionGamificacion.id_transaccion).where(
                    TransaccionGamificacion.id_usuario == id_usuario,
                    TransaccionGamificacion.clave_idempotencia == clave,
                )
            )
            is not None
        )

    def insertar_unico(self, objeto) -> bool:
        """Inserta dentro de un SAVEPOINT; si choca con una restricción única devuelve False sin romper la
        transacción principal (segunda barrera contra duplicados, además del bloqueo del perfil)."""
        try:
            with self.db.begin_nested():
                self.db.add(objeto)
                self.db.flush()
            return True
        except IntegrityError:
            return False

    def contar_tareas_a_tiempo(self, id_usuario: uuid.UUID) -> int:
        return self.db.scalar(
            select(func.count()).where(
                TransaccionGamificacion.id_usuario == id_usuario,
                TransaccionGamificacion.motivo == "TAREA_A_TIEMPO",
            )
        )

    def contar_tareas_anticipadas(self, id_usuario: uuid.UUID) -> int:
        return self.db.scalar(
            select(func.count(func.distinct(HistorialEvento.id_tarea))).where(
                HistorialEvento.id_usuario == id_usuario,
                HistorialEvento.tipo_evento == tipos_evento.TAREA_COMPLETADA,
                HistorialEvento.datos["anticipada"].as_boolean().is_(True),
            )
        )

    def transacciones(self, id_usuario: uuid.UUID, limite: int) -> list[TransaccionGamificacion]:
        return list(
            self.db.scalars(
                select(TransaccionGamificacion)
                .where(TransaccionGamificacion.id_usuario == id_usuario)
                .order_by(TransaccionGamificacion.fecha.desc(), TransaccionGamificacion.clave_idempotencia)
                .limit(limite)
            )
        )

    # ---- logros ----
    def logros_activos(self) -> list[Logro]:
        return list(
            self.db.scalars(
                select(Logro).where(Logro.activo.is_(True)).order_by(Logro.categoria, Logro.valor_condicion)
            )
        )

    def logros_del_usuario(self, id_usuario: uuid.UUID) -> dict[uuid.UUID, LogroUsuario]:
        return {
            lu.id_logro: lu
            for lu in self.db.scalars(select(LogroUsuario).where(LogroUsuario.id_usuario == id_usuario))
        }

    # ---- recuperación ----
    def recuperacion_activa(self, id_usuario: uuid.UUID) -> RecuperacionRacha | None:
        return self.db.scalar(
            select(RecuperacionRacha).where(
                RecuperacionRacha.id_usuario == id_usuario, RecuperacionRacha.estado == "ACTIVA"
            )
        )

    def recuperacion_de_dia(self, id_usuario: uuid.UUID, id_dia: uuid.UUID) -> RecuperacionRacha | None:
        return self.db.scalar(
            select(RecuperacionRacha).where(
                RecuperacionRacha.id_usuario == id_usuario, RecuperacionRacha.id_dia_perdido == id_dia
            )
        )

    def recuperacion(self, id_usuario: uuid.UUID, id_recuperacion: uuid.UUID) -> RecuperacionRacha | None:
        return self.db.scalar(
            select(RecuperacionRacha).where(
                RecuperacionRacha.id_usuario == id_usuario, RecuperacionRacha.id_recuperacion == id_recuperacion
            )
        )

    def recuperaciones(self, id_usuario: uuid.UUID, limite: int) -> list[RecuperacionRacha]:
        return list(
            self.db.scalars(
                select(RecuperacionRacha)
                .where(RecuperacionRacha.id_usuario == id_usuario)
                .order_by(RecuperacionRacha.fecha_creacion.desc())
                .limit(limite)
            )
        )
