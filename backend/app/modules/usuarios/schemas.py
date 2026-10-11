import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UsuarioSalida(BaseModel):
    """Datos públicos del usuario. Nunca incluye la contraseña ni su hash."""

    model_config = ConfigDict(from_attributes=True)

    id_usuario: uuid.UUID
    email: str
    nombre: str | None
    zona_horaria: str
    fecha_registro: datetime
