"""Ejecución manual / programada del proceso de notificaciones (DECISIONES.md §10).

    cd backend && python -m app.modules.notificaciones.procesos

Registra como ENVIADA lo que ya se sincronizó y pasó su hora, cancela lo que nunca llegó al teléfono y
extiende el plan de cada usuario dentro del horizonte. Es idempotente: se puede ejecutar varias veces.
Para producción se puede programar con cron (no se agregó APScheduler, ver DECISIONES.md).
"""
from app.core.tiempo import ahora_utc
from app.db import registro_modelos  # noqa: F401
from app.db.session import SessionLocal
from app.modules.notificaciones.service import procesar_todos


def main() -> None:
    with SessionLocal() as db:
        total = procesar_todos(db, ahora_utc())
    print(f"Notificaciones procesadas para {total} usuario(s).")


if __name__ == "__main__":
    main()
