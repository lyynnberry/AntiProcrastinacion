"""Un único lugar para obtener la hora actual (siempre en UTC y con zona horaria)."""
from datetime import datetime, timezone


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def zona_horaria(nombre: str | None):
    """ZoneInfo del usuario; si el nombre no es válido se usa la zona por defecto de la configuración."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    from app.core.config import settings

    try:
        return ZoneInfo(nombre or settings.zona_horaria_defecto)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(settings.zona_horaria_defecto)
