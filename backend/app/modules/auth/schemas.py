from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegistroEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr  # RF-01 regla 2: formato válido
    password: str = Field(max_length=128)  # Las reglas de seguridad se validan en validators.py
    nombre: str | None = Field(default=None, max_length=100)


class LoginEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Se acepta cualquier texto: un correo mal formado simplemente no coincidirá con ninguna cuenta,
    # y la respuesta es la misma que con credenciales incorrectas (RF-02 regla 6).
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class RefreshEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(max_length=255)


class TokensSalida(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos de vida del access_token
