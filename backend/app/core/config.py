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

    # ---- RF-12 / RF-13: notificaciones (DECISIONES.md §4). V6 deja estos valores "definidos por el
    # sistema"; por eso viven aquí y se pueden sobrescribir por variable de entorno (JSON en los dict).
    # Horas entre avisos por perfil de recordatorios y nivel (§4.3).
    notif_intervalos_horas: dict[str, dict[str, int]] = {
        "tranquilo": {"RECORDATORIO": 48, "URGENTE": 24, "CRITICA": 8},
        "equilibrado": {"RECORDATORIO": 24, "URGENTE": 12, "CRITICA": 4},
        "insistente": {"RECORDATORIO": 12, "URGENTE": 6, "CRITICA": 2},
    }
    # Límites de cada nivel según el tiempo restante T (§4.2): CRITICA 0<T<=24 h, URGENTE 24<T<=72 h,
    # RECORDATORIO 72 h<T<=7 días. Con T mayor no hay avisos.
    notif_umbral_critica_horas: int = 24
    notif_umbral_urgente_horas: int = 72
    notif_umbral_recordatorio_horas: int = 168
    notif_aviso_final_minutos: int = 60  # aviso especial T - 1 h (§4.3)
    notif_separacion_minima_minutos: int = 15  # dos avisos de la misma tarea no pueden estar más cerca
    notif_maximo_diario: dict[str, int] = {"tranquilo": 4, "equilibrado": 8, "insistente": 12}  # §4.4
    notif_silencio_inicio: str = "22:00"  # §4.5, hora local del usuario
    notif_silencio_fin: str = "07:00"
    notif_silencio_alternativa: str = "21:30"  # [PROPUESTA §12] si mover a las 07:00 deja el aviso tarde
    # [PROPUESTA §12] CORRECTIVA: 1 h después de vencer y luego a las 19:00 locales, como máximo N días.
    notif_correctiva_primera_horas: int = 1
    notif_correctiva_hora_diaria: str = "19:00"
    notif_correctiva_dias: dict[str, int] = {"tranquilo": 0, "equilibrado": 3, "insistente": 3}
    # Solo se planifican avisos dentro de este horizonte; al sincronizar se extiende el plan.
    notif_horizonte_horas: int = 168

    # ---- RF-21 a RF-27: gamificación. V6 no fija estos valores (DECISIONES.md, sección gamificación).
    gam_puntos_tarea_a_tiempo: int = 10  # RF-22 regla 2
    gam_puntos_tarea_con_retraso: int = 0  # RF-22 regla 3: no recibe la misma recompensa
    gam_horas_anticipacion: int = 24  # logros VELOCIDAD: completada al menos N h antes del límite
    gam_puntos_por_nivel: int = 200  # nivel = 1 + puntos // N (dato derivado, V6)
    gam_max_protecciones: int = 3  # inventario máximo de protecciones (RF-24)
    gam_recompensa_racha_cada_dias: int = 7  # RF-27: +1 protección cada vez que la racha llega a un múltiplo
    gam_recompensa_puntos_umbral: int = 500  # RF-27: +1 protección única al alcanzar estos puntos
    gam_recuperacion_dias: int = 3  # RF-25: duración del periodo de recuperación (días locales)
    gam_recuperacion_ventana_dias: int = 3  # RF-25: días después de perder la racha para poder iniciarla

    @model_validator(mode="after")
    def exigir_clave_segura_en_produccion(self) -> "Settings":
        if self.entorno == "produccion" and (
            self.secret_key == SECRET_KEY_DESARROLLO or len(self.secret_key) < 32
        ):
            raise ValueError("En producción SECRET_KEY debe definirse (mínimo 32 caracteres).")
        return self


settings = Settings()
