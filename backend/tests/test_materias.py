"""Pruebas de RF-10 (crear materia)."""
import pytest
from sqlalchemy import select

from app.modules.materias.models import Materia


def test_crear_materia(client, usuario_a, db):
    r = client.post("/materias", json={"nombre": "Cálculo I"}, headers=usuario_a.headers)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["nombre"] == "Cálculo I"
    assert cuerpo["activa"] is True

    materia = db.scalar(select(Materia))
    assert materia.id_usuario == usuario_a.id  # pertenece a quien la creó (RF-10 regla 4)
    assert materia.nombre_normalizado == "cálculo i"


def test_crear_materia_requiere_autenticacion(client):
    r = client.post("/materias", json={"nombre": "Cálculo I"})
    assert r.status_code == 401


@pytest.mark.parametrize("nombre", ["", "   ", "x" * 101])
def test_crear_materia_con_nombre_invalido(client, usuario_a, nombre):
    r = client.post("/materias", json={"nombre": nombre}, headers=usuario_a.headers)
    assert r.status_code == 422


def test_crear_materia_sin_nombre(client, usuario_a):
    r = client.post("/materias", json={}, headers=usuario_a.headers)
    assert r.status_code == 422


def test_materia_duplicada(client, usuario_a):
    assert client.post("/materias", json={"nombre": "Cálculo I"}, headers=usuario_a.headers).status_code == 201
    r = client.post("/materias", json={"nombre": "Cálculo I"}, headers=usuario_a.headers)
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "MATERIA_DUPLICADA"


def test_materia_duplicada_ignora_mayusculas_y_espacios(client, usuario_a):
    client.post("/materias", json={"nombre": "Cálculo I"}, headers=usuario_a.headers)
    r = client.post("/materias", json={"nombre": "  CÁLCULO    i "}, headers=usuario_a.headers)
    assert r.status_code == 409


def test_materia_con_acento_distinto_se_considera_otra(client, usuario_a):
    """Decisión documentada: los acentos sí cuentan al comparar nombres."""
    client.post("/materias", json={"nombre": "Calculo"}, headers=usuario_a.headers)
    r = client.post("/materias", json={"nombre": "Cálculo"}, headers=usuario_a.headers)
    assert r.status_code == 201


def test_distintos_usuarios_pueden_tener_materias_con_el_mismo_nombre(client, usuario_a, usuario_b):
    assert client.post("/materias", json={"nombre": "Física"}, headers=usuario_a.headers).status_code == 201
    assert client.post("/materias", json={"nombre": "Física"}, headers=usuario_b.headers).status_code == 201


def test_listar_solo_devuelve_las_materias_propias(client, usuario_a, usuario_b):
    client.post("/materias", json={"nombre": "Física"}, headers=usuario_a.headers)
    client.post("/materias", json={"nombre": "Álgebra"}, headers=usuario_a.headers)
    client.post("/materias", json={"nombre": "Historia"}, headers=usuario_b.headers)

    r = client.get("/materias", headers=usuario_a.headers)
    assert r.status_code == 200
    assert [m["nombre"] for m in r.json()] == ["Álgebra", "Física"]

    r = client.get("/materias", headers=usuario_b.headers)
    assert [m["nombre"] for m in r.json()] == ["Historia"]
