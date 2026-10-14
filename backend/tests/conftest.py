"""Infraestructura de pruebas.

- Usa una base PostgreSQL SEPARADA (nombre terminado en _test). Nunca toca la de desarrollo.
- El esquema se crea con las migraciones de Alembic: así las pruebas también validan las migraciones.
- Entre pruebas se vacían las tablas.
"""
import itertools
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.dependencies import get_db
from app.main import app
from app.modules.tareas.models import Tarea

RAIZ = Path(__file__).resolve().parent.parent
URL_PRUEBAS = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://antiproc:antiproc_dev@localhost:5432/antiprocrastinacion_test",
)
# Salvaguarda: estas pruebas borran datos. Solo se ejecutan contra una base "_test".
assert URL_PRUEBAS.rsplit("/", 1)[-1].endswith("_test"), "TEST_DATABASE_URL debe apuntar a una BD *_test"

PASSWORD_VALIDA = "ClaveSegura123"


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(URL_PRUEBAS, connect_args={"options": "-c timezone=UTC"})
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    cfg.set_main_option("sqlalchemy.url", URL_PRUEBAS)
    command.upgrade(cfg, "head")
    yield eng
    eng.dispose()


@pytest.fixture(autouse=True)
def limpiar_tablas(engine):
    yield
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE historial_evento, tarea, materia, sesion_autenticacion, foto_perfil, preferencia_notificacion, usuario CASCADE")
        )


@pytest.fixture
def db(engine):
    """Sesión directa a la BD para preparar o verificar datos fuera de la API."""
    with sessionmaker(bind=engine, expire_on_commit=False)() as sesion:
        yield sesion


@pytest.fixture
def client(engine):
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)

    def _get_db():
        with fabrica() as sesion:
            yield sesion

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@dataclass
class UsuarioPrueba:
    id: uuid.UUID
    email: str
    tokens: dict

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.tokens['access_token']}"}


@pytest.fixture
def crear_usuario(client):
    contador = itertools.count(1)

    def _crear(email: str | None = None) -> UsuarioPrueba:
        email = email or f"usuario{next(contador)}@correo.com"
        r = client.post("/auth/registro", json={"email": email, "password": PASSWORD_VALIDA})
        assert r.status_code == 201, r.text
        id_usuario = uuid.UUID(r.json()["id_usuario"])
        r = client.post("/auth/login", json={"email": email, "password": PASSWORD_VALIDA})
        assert r.status_code == 200, r.text
        return UsuarioPrueba(id=id_usuario, email=email, tokens=r.json())

    return _crear


@pytest.fixture
def usuario_a(crear_usuario) -> UsuarioPrueba:
    return crear_usuario("ana@correo.com")


@pytest.fixture
def usuario_b(crear_usuario) -> UsuarioPrueba:
    return crear_usuario("beto@correo.com")


@pytest.fixture
def insertar_tarea(db):
    """Inserta una tarea directamente en la BD (permite crear tareas ya vencidas, que la API no permite)."""

    def _insertar(
        id_usuario: uuid.UUID,
        titulo: str = "Tarea de prueba",
        fecha_limite: datetime | None = None,
        fecha_creacion: datetime | None = None,
        prioridad: int = 2,
        estado: str = "PENDIENTE",
        id_materia: uuid.UUID | None = None,
    ) -> Tarea:
        ahora = datetime.now(timezone.utc)
        fecha_limite = fecha_limite or ahora + timedelta(days=1)
        tarea = Tarea(
            id_usuario=id_usuario,
            id_materia=id_materia,
            titulo=titulo,
            prioridad=prioridad,
            estado=estado,
            fecha_creacion=fecha_creacion or ahora - timedelta(days=2),
            fecha_limite=fecha_limite,
            fecha_limite_original=fecha_limite,
        )
        db.add(tarea)
        db.commit()
        return tarea

    return _insertar
