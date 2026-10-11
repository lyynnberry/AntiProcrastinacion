"""Reglas de validación de credenciales (RF-01).

Las "reglas de seguridad definidas por el sistema" no estaban especificadas en el documento;
se adoptó una política sencilla (ver DECISIONES.md).
"""
from app.core.errors import ErrorValidacion

PASSWORD_MIN = 8


def normalizar_email(email: str) -> str:
    """Minúsculas y sin espacios en los extremos: así 'Ana@X.com ' y 'ana@x.com' son la misma cuenta."""
    return email.strip().lower()


def validar_password(password: str) -> None:
    problemas = []
    if len(password) < PASSWORD_MIN:
        problemas.append(f"tener al menos {PASSWORD_MIN} caracteres")
    if not any(c.isalpha() for c in password):
        problemas.append("incluir al menos una letra")
    if not any(c.isdigit() for c in password):
        problemas.append("incluir al menos un número")
    if problemas:
        raise ErrorValidacion(
            "La contraseña debe " + ", ".join(problemas) + ".", "PASSWORD_DEBIL"
        )
