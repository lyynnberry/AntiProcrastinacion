"""Un único lugar para obtener la hora actual (siempre en UTC y con zona horaria)."""
from datetime import datetime, timezone


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)
