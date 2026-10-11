"""Configuración de la aplicación (se lee de variables de entorno o del archivo .env)."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRET_KEY_DESARROLLO = "clave-solo-para-desarrollo-no-usar-en-produccion"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    entorno: str = "desarrollo"  # "desarrollo" o "produccion"
    database_url: str = (
        "postgresql+psycopg://antiproc:antiproc_dev@localhost:5432/antiprocrastinacion"
    )
    secret_key: str = SECRET_KEY_DESARROLLO

    # RF-03: periodos de validez. El token de acceso es corto; la sesión (refresh token) dura más.
    access_token_minutos: int = 15
    sesion_dias: int = 30

    zona_horaria_defecto: str = "America/Mexico_City"

    @model_validator(mode="after")
    def exigir_clave_segura_en_produccion(self) -> "Settings":
        if self.entorno == "produccion" and (
            self.secret_key == SECRET_KEY_DESARROLLO or len(self.secret_key) < 32
        ):
            raise ValueError("En producción SECRET_KEY debe definirse (mínimo 32 caracteres).")
        return self


settings = Settings()
