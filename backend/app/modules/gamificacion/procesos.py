"""Proceso diario de gamificación (RF-21): evalúa los días cerrados de todos los usuarios.

    cd backend && python -m app.modules.gamificacion.procesos

Conviene programarlo con cron poco después de la medianoche (por ejemplo cada hora, porque cada usuario
tiene su zona horaria). Es idempotente: un día ya evaluado no se vuelve a evaluar. Además, cualquier consulta
de gamificación pone al día al usuario que la hace, así que el proceso no es imprescindible.
"""
from app.core.tiempo import ahora_utc
from app.db import registro_modelos  # noqa: F401
from app.db.session import SessionLocal
from app.modules.gamificacion.service import procesar_todos


def main() -> None:
    with SessionLocal() as db:
        total = procesar_todos(db, ahora_utc())
    print(f"Gamificación puesta al día para {total} usuario(s).")


if __name__ == "__main__":
    main()
