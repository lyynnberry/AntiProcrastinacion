"""Dependencias comunes de FastAPI."""
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Iterator[Session]:
    """Una sesión de base de datos por petición."""
    with SessionLocal() as db:
        yield db
