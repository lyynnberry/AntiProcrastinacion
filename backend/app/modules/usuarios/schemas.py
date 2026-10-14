import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

Idioma = Literal["es", "en"]
PerfilRecordatorios = Literal["tranquilo", "equilibrado", "insistente"]


class UsuarioSalida(BaseModel):
    """Datos públicos del usuario. Nunca incluye la contraseña ni su hash."""

    model_config = ConfigDict(from_attributes=True)

    id_usuario: uuid.UUID
    email: str
    nombre: str | None
    zona_horaria: str
    fecha_registro: datetime
    idioma: Idioma
    personalizacion_completada_en: datetime | None
    tutorial_completado_en: datetime | None
    foto_actualizada_en: datetime | None

    @computed_field
    @property
    def personalizacion_completada(self) -> bool:
        return self.personalizacion_completada_en is not None

    @computed_field
    @property
    def tutorial_completado(self) -> bool:
        return self.tutorial_completado_en is not None

    @computed_field
    @property
    def tiene_foto(self) -> bool:
        return self.foto_actualizada_en is not None


class PerfilActualizar(BaseModel):
    """PATCH /usuarios/me. El correo no es editable (no existe aquí y `extra=forbid` lo rechaza)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, max_length=100)
    idioma: Idioma | None = None

    @field_validator("nombre")
    @classmethod
    def _nombre_valido(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        if any(not (c.isalpha() or c in " '-.") for c in v):
            raise ValueError("El nombre solo puede contener letras, espacios, apóstrofos, guiones y puntos.")
        return v


class PreferenciaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    perfil_recordatorios: PerfilRecordatorios
    notificaciones_activas: bool = True


class PreferenciaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    perfil_recordatorios: PerfilRecordatorios
    notificaciones_activas: bool
