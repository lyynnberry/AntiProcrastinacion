"""Primitivas de seguridad: hash de contraseñas, token de acceso (JWT) y refresh token.

- Contraseñas: Argon2id (RNF-03). Nunca se guarda ni se registra la contraseña en texto plano.
- Token de acceso: JWT firmado y de vida corta. Solo contiene el id del usuario y de la sesión.
- Refresh token: cadena aleatoria opaca. En la BD se guarda únicamente su hash SHA-256
  (es seguro usar SHA-256 porque el token ya tiene 384 bits de entropía).
"""
import hashlib
import secrets
import uuid
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings
from app.core.errors import NoAutenticado
from app.core.tiempo import ahora_utc

_ALGORITMO_JWT = "HS256"
_hasher = PasswordHasher()
# Hash de relleno: se verifica contra él cuando el correo no existe, para que el login
# tarde parecido exista o no la cuenta (evita revelar qué correos están registrados).
_HASH_RELLENO = _hasher.hash("relleno-para-igualar-tiempos")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def verificar_password_de_relleno(password: str) -> None:
    verificar_password(password, _HASH_RELLENO)


def crear_access_token(id_usuario: uuid.UUID, id_sesion: uuid.UUID) -> str:
    ahora = ahora_utc()
    claims = {
        "sub": str(id_usuario),
        "sid": str(id_sesion),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.access_token_minutos),
    }
    return jwt.encode(claims, settings.secret_key, algorithm=_ALGORITMO_JWT)


def decodificar_access_token(token: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Devuelve (id_usuario, id_sesion) o lanza NoAutenticado si el token no es válido o expiró."""
    try:
        claims = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[_ALGORITMO_JWT],
            options={"require": ["exp", "sub", "sid"]},
        )
        return uuid.UUID(claims["sub"]), uuid.UUID(claims["sid"])
    except (jwt.InvalidTokenError, ValueError):
        raise NoAutenticado("Token inválido o expirado.", "TOKEN_INVALIDO")


def generar_refresh_token() -> tuple[str, str]:
    """Devuelve (token_para_el_cliente, hash_para_guardar_en_bd)."""
    token = secrets.token_urlsafe(48)
    return token, hash_refresh_token(token)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
