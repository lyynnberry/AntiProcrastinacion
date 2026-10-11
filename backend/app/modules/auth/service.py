"""Lógica de negocio de autenticación: RF-01 (registro), RF-02 (login), RF-03 (sesión).

Diseño de la sesión (ver DECISIONES.md):
- El login crea una fila en SESION_AUTENTICACION con vigencia absoluta (`sesion_dias`).
- Se entrega un access token (JWT, vida corta) y un refresh token (opaco; en BD solo su hash).
- En cada petición protegida se comprueba en BD que la sesión siga vigente. Así, cerrar sesión
  invalida el acceso de inmediato aunque el JWT aún no haya vencido.
"""
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.errors import Conflicto, NoAutenticado
from app.core.tiempo import ahora_utc
from app.modules.auth.models import SesionAutenticacion
from app.modules.auth.repository import SesionRepository
from app.modules.auth.schemas import LoginEntrada, RegistroEntrada, TokensSalida
from app.modules.auth.validators import normalizar_email, validar_password
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.repository import UsuarioRepository


@dataclass
class ContextoAutenticacion:
    usuario: Usuario
    sesion: SesionAutenticacion


def _credenciales_invalidas() -> NoAutenticado:
    # Mismo mensaje para correo inexistente y contraseña incorrecta (RF-02 regla 6).
    return NoAutenticado("Correo o contraseña incorrectos.", "CREDENCIALES_INVALIDAS")


def _sesion_invalida() -> NoAutenticado:
    return NoAutenticado("La sesión no es válida o ya expiró. Inicia sesión de nuevo.", "SESION_INVALIDA")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.usuarios = UsuarioRepository(db)
        self.sesiones = SesionRepository(db)

    # ---- RF-01 -------------------------------------------------------------------------
    def registrar(self, datos: RegistroEntrada) -> Usuario:
        email = normalizar_email(datos.email)
        validar_password(datos.password)
        nombre = datos.nombre.strip() if datos.nombre else None

        if self.usuarios.obtener_por_email(email):
            raise Conflicto("Ya existe una cuenta con ese correo.", "EMAIL_DUPLICADO")

        try:
            usuario = self.usuarios.crear(email, security.hash_password(datos.password), nombre or None)
            self.db.commit()
        except IntegrityError:
            # Dos registros simultáneos con el mismo correo: la restricción UNIQUE de la BD decide.
            self.db.rollback()
            raise Conflicto("Ya existe una cuenta con ese correo.", "EMAIL_DUPLICADO")
        return usuario

    # ---- RF-02 -------------------------------------------------------------------------
    def iniciar_sesion(self, datos: LoginEntrada, dispositivo: str | None) -> TokensSalida:
        usuario = self.usuarios.obtener_por_email(normalizar_email(datos.email))
        if usuario is None or not usuario.activo:
            security.verificar_password_de_relleno(datos.password)  # igualar tiempos de respuesta
            raise _credenciales_invalidas()
        if not security.verificar_password(datos.password, usuario.password_hash):
            raise _credenciales_invalidas()

        ahora = ahora_utc()
        refresh_token, refresh_hash = security.generar_refresh_token()
        sesion = self.sesiones.crear(
            id_usuario=usuario.id_usuario,
            refresh_token_hash=refresh_hash,
            dispositivo=dispositivo[:100] if dispositivo else None,
            fecha_emision=ahora,
            fecha_expiracion=ahora + timedelta(days=settings.sesion_dias),
        )
        self.db.commit()
        return self._tokens(usuario, sesion, refresh_token)

    # ---- RF-03 -------------------------------------------------------------------------
    def renovar_sesion(self, refresh_token: str) -> TokensSalida:
        """Cambia un refresh token por un nuevo access token. El refresh token rota (un solo uso)."""
        sesion = self.sesiones.obtener_por_refresh_hash(security.hash_refresh_token(refresh_token))
        if sesion is None or not self._sesion_vigente(sesion):
            raise _sesion_invalida()
        usuario = self.usuarios.obtener_por_id(sesion.id_usuario)
        if usuario is None or not usuario.activo:
            raise _sesion_invalida()

        nuevo_refresh, nuevo_hash = security.generar_refresh_token()
        sesion.refresh_token_hash = nuevo_hash  # el refresh anterior deja de funcionar
        self.db.commit()
        return self._tokens(usuario, sesion, nuevo_refresh)

    def cerrar_sesion(self, sesion: SesionAutenticacion) -> None:
        sesion.fecha_revocacion = ahora_utc()
        self.db.commit()

    def autenticar(self, access_token: str) -> ContextoAutenticacion:
        """Valida el access token y que su sesión siga vigente. Se usa en cada petición protegida."""
        id_usuario, id_sesion = security.decodificar_access_token(access_token)
        sesion = self.sesiones.obtener_por_id(id_sesion)
        if sesion is None or sesion.id_usuario != id_usuario or not self._sesion_vigente(sesion):
            raise _sesion_invalida()
        usuario = self.usuarios.obtener_por_id(id_usuario)
        if usuario is None or not usuario.activo:
            raise _sesion_invalida()
        return ContextoAutenticacion(usuario=usuario, sesion=sesion)

    # ---- auxiliares --------------------------------------------------------------------
    @staticmethod
    def _sesion_vigente(sesion: SesionAutenticacion) -> bool:
        return sesion.fecha_revocacion is None and sesion.fecha_expiracion > ahora_utc()

    @staticmethod
    def _tokens(usuario: Usuario, sesion: SesionAutenticacion, refresh_token: str) -> TokensSalida:
        return TokensSalida(
            access_token=security.crear_access_token(usuario.id_usuario, sesion.id_sesion_auth),
            refresh_token=refresh_token,
            expires_in=settings.access_token_minutos * 60,
        )
