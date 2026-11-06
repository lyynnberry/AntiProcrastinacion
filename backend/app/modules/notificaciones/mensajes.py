"""Texto de cada notificación (V6 RF-12 regla 3: indicar como mínimo el título de la tarea).

Se genera en el idioma del usuario (`usuario.idioma`) con la fecha límite en su zona horaria.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

_PLANTILLAS = {
    "es": {
        "RECORDATORIO": "Recordatorio: «{titulo}» vence el {fecha}.",
        "URGENTE": "Urgente: «{titulo}» vence el {fecha}. Quedan menos de 3 días.",
        "CRITICA": "Último día: «{titulo}» vence el {fecha}.",
        "FINAL": "Falta 1 hora: «{titulo}» vence a las {hora}.",
        "CORRECTIVA": "«{titulo}» venció el {fecha}. Todavía puedes completarla.",
    },
    "en": {
        "RECORDATORIO": "Reminder: \"{titulo}\" is due on {fecha}.",
        "URGENTE": "Urgent: \"{titulo}\" is due on {fecha}. Less than 3 days left.",
        "CRITICA": "Last day: \"{titulo}\" is due on {fecha}.",
        "FINAL": "1 hour left: \"{titulo}\" is due at {hora}.",
        "CORRECTIVA": "\"{titulo}\" was due on {fecha}. You can still complete it.",
    },
}


def construir_mensaje(
    tipo: str, es_aviso_final: bool, titulo: str, fecha_limite: datetime, zona: ZoneInfo, idioma: str
) -> str:
    plantillas = _PLANTILLAS.get(idioma, _PLANTILLAS["es"])
    local = fecha_limite.astimezone(zona)
    clave = "FINAL" if es_aviso_final else tipo
    return plantillas[clave].format(
        titulo=titulo, fecha=local.strftime("%d/%m/%Y %H:%M"), hora=local.strftime("%H:%M")
    )
