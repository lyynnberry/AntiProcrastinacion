"""Pruebas de RF-01 (registro), RF-02 (inicio de sesión) y RF-03 (sesión)."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.modules.auth.models import SesionAutenticacion
from app.modules.usuarios.models import Usuario
from tests.conftest import PASSWORD_VALIDA


# ---------------------------------------------------------------- RF-01: registro
def test_registro_con_correo_valido(client, db):
    r = client.post("/auth/registro", json={"email": "ana@correo.com", "password": PASSWORD_VALIDA})
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["email"] == "ana@correo.com"
    assert cuerpo["id_usuario"]
    # La respuesta nunca expone la contraseña ni su hash.
    assert "password" not in cuerpo and "password_hash" not in cuerpo

    usuario = db.scalar(select(Usuario).where(Usuario.email == "ana@correo.com"))
    assert usuario.password_hash != PASSWORD_VALIDA  # no está en texto plano
    assert usuario.password_hash.startswith("$argon2id$")


def test_registro_normaliza_el_correo_a_minusculas(client):
    r = client.post("/auth/registro", json={"email": "Ana@Correo.COM", "password": PASSWORD_VALIDA})
    assert r.status_code == 201
    assert r.json()["email"] == "ana@correo.com"


@pytest.mark.parametrize("email", ["no-es-un-correo", "sin-dominio@", "@sin-usuario.com", ""])
def test_registro_con_correo_invalido(client, email):
    r = client.post("/auth/registro", json={"email": email, "password": PASSWORD_VALIDA})
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "VALIDACION"


def test_registro_con_correo_duplicado(client):
    datos = {"email": "ana@correo.com", "password": PASSWORD_VALIDA}
    assert client.post("/auth/registro", json=datos).status_code == 201
    r = client.post("/auth/registro", json=datos)
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "EMAIL_DUPLICADO"


def test_registro_duplicado_ignora_mayusculas(client):
    client.post("/auth/registro", json={"email": "ana@correo.com", "password": PASSWORD_VALIDA})
    r = client.post("/auth/registro", json={"email": "ANA@correo.com", "password": PASSWORD_VALIDA})
    assert r.status_code == 409


@pytest.mark.parametrize("password", ["corta1", "sinnumeroslargos", "1234567890"])
def test_registro_con_password_debil(client, password):
    r = client.post("/auth/registro", json={"email": "ana@correo.com", "password": password})
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "PASSWORD_DEBIL"


def test_registro_rechaza_campos_desconocidos(client):
    r = client.post(
        "/auth/registro",
        json={"email": "ana@correo.com", "password": PASSWORD_VALIDA, "activo": False},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------- RF-02: inicio de sesión
def test_login_correcto(client, db):
    client.post("/auth/registro", json={"email": "ana@correo.com", "password": PASSWORD_VALIDA})
    r = client.post("/auth/login", json={"email": "ana@correo.com", "password": PASSWORD_VALIDA})
    assert r.status_code == 200
    tokens = r.json()
    assert tokens["access_token"] and tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    sesion = db.scalar(select(SesionAutenticacion))
    assert sesion is not None
    assert sesion.refresh_token_hash != tokens["refresh_token"]  # solo se guarda el hash


def test_login_acepta_correo_con_otras_mayusculas(client):
    client.post("/auth/registro", json={"email": "ana@correo.com", "password": PASSWORD_VALIDA})
    r = client.post("/auth/login", json={"email": " ANA@correo.com ", "password": PASSWORD_VALIDA})
    assert r.status_code == 200


def test_login_incorrecto_no_revela_si_falla_el_correo_o_la_password(client):
    client.post("/auth/registro", json={"email": "ana@correo.com", "password": PASSWORD_VALIDA})

    password_mala = client.post("/auth/login", json={"email": "ana@correo.com", "password": "Otra12345"})
    correo_inexistente = client.post("/auth/login", json={"email": "nadie@correo.com", "password": PASSWORD_VALIDA})

    assert password_mala.status_code == 401
    assert correo_inexistente.status_code == 401
    # RF-02 regla 6: ambas respuestas son idénticas.
    assert password_mala.json() == correo_inexistente.json()
    assert password_mala.json()["error"]["codigo"] == "CREDENCIALES_INVALIDAS"


# ---------------------------------------------------------------- RF-03: sesión
def test_sesion_valida_permite_acceder_a_recursos_protegidos(client, usuario_a):
    r = client.get("/usuarios/me", headers=usuario_a.headers)
    assert r.status_code == 200
    assert r.json()["email"] == "ana@correo.com"


def test_endpoint_protegido_sin_token(client):
    r = client.get("/usuarios/me")
    assert r.status_code == 401
    assert r.json()["error"]["codigo"] == "NO_AUTENTICADO"


def test_endpoint_protegido_con_token_basura(client):
    r = client.get("/usuarios/me", headers={"Authorization": "Bearer esto-no-es-un-jwt"})
    assert r.status_code == 401
    assert r.json()["error"]["codigo"] == "TOKEN_INVALIDO"


def test_token_firmado_con_otra_clave_es_rechazado(client, usuario_a, db):
    sesion = db.scalar(select(SesionAutenticacion))
    falso = jwt.encode(
        {
            "sub": str(usuario_a.id),
            "sid": str(sesion.id_sesion_auth),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "otra-clave-distinta-de-la-del-servidor-0123456789",
        algorithm="HS256",
    )
    r = client.get("/usuarios/me", headers={"Authorization": f"Bearer {falso}"})
    assert r.status_code == 401


def test_access_token_expirado_es_rechazado(client, usuario_a, db):
    sesion = db.scalar(select(SesionAutenticacion))
    vencido = jwt.encode(
        {
            "sub": str(usuario_a.id),
            "sid": str(sesion.id_sesion_auth),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    r = client.get("/usuarios/me", headers={"Authorization": f"Bearer {vencido}"})
    assert r.status_code == 401
    assert r.json()["error"]["codigo"] == "TOKEN_INVALIDO"


def test_sesion_expirada_pide_autenticarse_de_nuevo(client, usuario_a, db):
    # Se envejece la sesión en la BD: emitida hace 2 días y vencida hace 1.
    sesion = db.scalar(select(SesionAutenticacion))
    ahora = datetime.now(timezone.utc)
    sesion.fecha_emision = ahora - timedelta(days=2)
    sesion.fecha_expiracion = ahora - timedelta(days=1)
    db.commit()

    r = client.get("/usuarios/me", headers=usuario_a.headers)  # el JWT aún no vence, la sesión sí
    assert r.status_code == 401
    assert r.json()["error"]["codigo"] == "SESION_INVALIDA"

    r = client.post("/auth/refresh", json={"refresh_token": usuario_a.tokens["refresh_token"]})
    assert r.status_code == 401


def test_refresh_renueva_el_acceso_y_el_refresh_anterior_deja_de_servir(client, usuario_a):
    r = client.post("/auth/refresh", json={"refresh_token": usuario_a.tokens["refresh_token"]})
    assert r.status_code == 200
    nuevos = r.json()
    assert nuevos["refresh_token"] != usuario_a.tokens["refresh_token"]

    r = client.get("/usuarios/me", headers={"Authorization": f"Bearer {nuevos['access_token']}"})
    assert r.status_code == 200

    reutilizado = client.post("/auth/refresh", json={"refresh_token": usuario_a.tokens["refresh_token"]})
    assert reutilizado.status_code == 401


def test_refresh_con_token_desconocido(client):
    r = client.post("/auth/refresh", json={"refresh_token": "token-que-no-existe"})
    assert r.status_code == 401


def test_logout_invalida_la_sesion_de_inmediato(client, usuario_a):
    assert client.post("/auth/logout", headers=usuario_a.headers).status_code == 204

    r = client.get("/usuarios/me", headers=usuario_a.headers)
    assert r.status_code == 401
    r = client.post("/auth/refresh", json={"refresh_token": usuario_a.tokens["refresh_token"]})
    assert r.status_code == 401


def test_logout_solo_cierra_la_sesion_propia(client, usuario_a, usuario_b):
    client.post("/auth/logout", headers=usuario_a.headers)
    assert client.get("/usuarios/me", headers=usuario_b.headers).status_code == 200
