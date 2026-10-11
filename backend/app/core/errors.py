"""Errores de dominio y su conversión a respuestas HTTP con un formato único:

    {"error": {"codigo": "EMAIL_DUPLICADO", "mensaje": "...", "detalles": [...]}}

Los servicios lanzan estas excepciones; no conocen HTTP. Aquí se traducen.
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ErrorDominio(Exception):
    status_code = 400
    codigo_defecto = "ERROR"

    def __init__(self, mensaje: str, codigo: str | None = None, detalles: list | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo or self.codigo_defecto
        self.detalles = detalles


class ErrorValidacion(ErrorDominio):
    status_code = 422
    codigo_defecto = "VALIDACION"


class NoAutenticado(ErrorDominio):
    status_code = 401
    codigo_defecto = "NO_AUTENTICADO"


class NoEncontrado(ErrorDominio):
    status_code = 404
    codigo_defecto = "NO_ENCONTRADO"


class Conflicto(ErrorDominio):
    status_code = 409
    codigo_defecto = "CONFLICTO"


def _respuesta(status: int, codigo: str, mensaje: str, detalles=None, headers=None) -> JSONResponse:
    cuerpo = {"error": {"codigo": codigo, "mensaje": mensaje}}
    if detalles:
        cuerpo["error"]["detalles"] = detalles
    return JSONResponse(status_code=status, content=cuerpo, headers=headers)


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDominio)
    async def manejar_error_dominio(_: Request, exc: ErrorDominio):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return _respuesta(exc.status_code, exc.codigo, exc.mensaje, exc.detalles, headers)

    @app.exception_handler(RequestValidationError)
    async def manejar_validacion_entrada(_: Request, exc: RequestValidationError):
        # Solo se exponen el campo y el mensaje (el detalle crudo de pydantic puede no ser serializable).
        detalles = [
            {"campo": ".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]), "mensaje": e["msg"]}
            for e in exc.errors()
        ]
        return _respuesta(422, "VALIDACION", "Los datos enviados no son válidos.", detalles)
