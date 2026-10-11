"""Reglas de negocio puras de las tareas (sin acceso a BD, fáciles de probar).

RF-08 regla 5: una tarea es VENCIDA cuando su fecha límite ya pasó y no está completada.
En esta etapa ese estado se CALCULA al consultar (no se guarda), así siempre es correcto sin
necesitar un proceso programado. Si en RF-17 se decide persistirlo, solo cambia este archivo
y el filtro del repositorio.
"""
from datetime import datetime

from app.core.errors import ErrorValidacion
from app.modules.tareas.enums import EstadoTarea

_ESTADOS_ABIERTOS = (EstadoTarea.PENDIENTE.value, EstadoTarea.EN_PROGRESO.value)


def estado_efectivo(tarea, ahora: datetime) -> EstadoTarea:
    """Estado que se muestra al usuario."""
    if tarea.estado == EstadoTarea.VENCIDA.value:
        return EstadoTarea.VENCIDA
    if tarea.estado in _ESTADOS_ABIERTOS and tarea.fecha_limite < ahora:
        return EstadoTarea.VENCIDA
    return EstadoTarea(tarea.estado)


def validar_fecha_limite_futura(fecha_limite: datetime, ahora: datetime) -> None:
    """RF-04 regla 7 / RF-08: la fecha límite debe ser posterior al momento actual.

    Se usa al crear una tarea y SOLO cuando se modifica la fecha límite de una existente.
    """
    if fecha_limite <= ahora:
        raise ErrorValidacion(
            "La fecha límite debe ser posterior a la fecha y hora actual.", "FECHA_LIMITE_INVALIDA"
        )
