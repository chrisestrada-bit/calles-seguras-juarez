"""Configuración de la aplicación, leída únicamente de variables de entorno (.env)."""

from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_VALOR_EJEMPLO_JWT = "valor-ficticio"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    app_timezone: str = "America/Ciudad_Juarez"

    database_url: str
    db_echo: bool = False

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    frontend_url: str = "http://localhost:5173"

    weather_api_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_cache_ttl_minutes: int = 30
    weather_timeout_seconds: float = 5

    # Sólo backend: la llave nunca se envía al frontend ni se registra en logs.
    geocoding_api_url: str = "https://us1.locationiq.com/v1"
    geocoding_api_key: SecretStr = SecretStr("")
    geocoding_timeout_seconds: float = 5

    @property
    def es_produccion(self) -> bool:
        return self.app_env.lower() == "production"

    @model_validator(mode="after")
    def _validar_secretos_en_produccion(self) -> "Settings":
        clave = self.jwt_secret_key.get_secret_value()
        if self.es_produccion and (clave.startswith(_VALOR_EJEMPLO_JWT) or len(clave) < 32):
            raise ValueError(
                "JWT_SECRET_KEY debe ser una clave aleatoria de al menos 32 caracteres en producción."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
