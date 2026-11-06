"""Esquemas de salida de gamificación. Ninguno recibe un id de usuario: siempre se usa el autenticado."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class LogroSalida(BaseModel):
    codigo: str
    nombre: str
    descripcion: str
    categoria: str
    tipo_condicion: str
    valor_condicion: int
    valor_actual: int
    progreso: int  # 0-100
    recompensa_puntos: int
    desbloqueado: bool
    fecha_desbloqueo: datetime | None


class ResumenHoy(BaseModel):
    fecha: date
    tareas_comprometidas: int
    tareas_cumplidas_a_tiempo: int


class RecuperacionActiva(BaseModel):
    id_recuperacion: uuid.UUID
    estado: str
    racha_perdida: int
    fecha_inicio: date
    fecha_fin_prevista: date
    tareas_atrasadas_total: int
    tareas_atrasadas_completadas: int
    dias_restantes: int


class ProteccionPosible(BaseModel):
    fecha: date
    racha_a_conservar: int


class ProgresoSalida(BaseModel):
    """RF-26: estado actual del usuario autenticado."""

    racha_actual: int
    racha_maxima: int
    puntos_totales: int
    nivel: int
    protecciones_disponibles: int
    ultima_fecha_evaluada: date | None
    hoy: ResumenHoy
    tareas_a_tiempo: int
    logros_desbloqueados: list[LogroSalida]
    logros_pendientes: list[LogroSalida]
    recuperacion_activa: RecuperacionActiva | None
    puede_proteger: ProteccionPosible | None
    puede_recuperar: bool


class TransaccionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_transaccion: uuid.UUID
    recurso: str
    cantidad: int
    motivo: str
    codigo_recompensa: str | None
    id_tarea: uuid.UUID | None
    id_logro: uuid.UUID | None
    id_dia_racha: uuid.UUID | None
    fecha: datetime


class DiaRachaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_dia_racha: uuid.UUID
    fecha: date
    resultado: str
    tareas_comprometidas: int
    tareas_cumplidas_a_tiempo: int
    racha_previa: int
    racha_resultante: int


class RecuperacionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_recuperacion: uuid.UUID
    id_dia_perdido: uuid.UUID
    racha_perdida: int
    tareas_atrasadas: list[uuid.UUID]
    fecha_inicio: date
    fecha_fin_prevista: date
    estado: str
    racha_restaurada: int | None
    motivo_resolucion: str | None
    fecha_creacion: datetime
    fecha_resolucion: datetime | None


class HistorialGamificacionSalida(BaseModel):
    transacciones: list[TransaccionSalida]
    dias: list[DiaRachaSalida]
    recuperaciones: list[RecuperacionSalida]
