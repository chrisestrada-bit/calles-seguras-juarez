"""Configuración de la aplicación, leída únicamente de variables de entorno (.env)."""

from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
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
    weather_cache_ttl_minutes: int = 60  # HU-08.1: caché de 1 h
    # Tras un fallo del proveedor no se reintenta durante este lapso (se sirve la caché, aunque esté vencida).
    weather_backoff_minutes: int = 5
    weather_timeout_seconds: float = 5
    # Open-Meteo limita o rechaza clientes anónimos desde nubes compartidas (Render): se identifica la app (D-10).
    weather_user_agent: str = "CallesSegurasJuarez/1.0 (+https://calles-seguras-juarez.onrender.com)"

    # Sólo backend: la llave nunca se envía al frontend ni se registra en logs.
    geocoding_api_url: str = "https://us1.locationiq.com/v1"
    geocoding_api_key: SecretStr = SecretStr("")
    geocoding_timeout_seconds: float = 5

    # HU-04.6: servicio de rutas (OSRM). Vacío = siempre línea recta entre origen y destino.
    routing_api_url: str = "https://router.project-osrm.org"
    routing_timeout_seconds: float = 6

    # IP real del cliente detrás de proxies (auditoría final, A4). Por omisión se usa la IP de la conexión TCP,
    # correcta en docker compose. Sólo se confía en una cabecera si el despliegue la fija explícitamente:
    #   CLIENT_IP_HEADER=CF-Connecting-IP  -> la cabecera que escribe el proxy de confianza (Cloudflare, etc.).
    #   TRUSTED_PROXY_HOPS=1               -> toma la entrada de X-Forwarded-For agregada por el proxy más cercano.
    client_ip_header: str = ""
    trusted_proxy_hops: int = Field(default=0, ge=0, le=5)

    # Límites anti-abuso por IP (en memoria, por proceso). Las pruebas los elevan por variable de entorno.
    limite_registros_por_hora_ip: int = Field(default=10, ge=1)
    limite_login_fallidos_por_ip: int = Field(default=30, ge=1)  # por ventana de 15 min
    limite_login_fallidos_por_cuenta_ip: int = Field(default=5, ge=1)  # por ventana de 15 min

    # HU-08.3: tope de conexiones WebSocket (en memoria, por proceso) contra el agotamiento de recursos (M6).
    ws_max_conexiones: int = Field(default=1000, ge=1)
    ws_max_conexiones_por_ip: int = Field(default=20, ge=1)

    # Tamaño máximo del cuerpo de una petición con archivos (3 fotos de 5 MB + margen multipart), M7.
    max_cuerpo_bytes: int = Field(default=16 * 1024 * 1024, ge=1024 * 1024)

    # HU-02.4: directorio persistente de fotos (en Docker, un volumen montado). Nunca se sirve como estático.
    uploads_dir: str = "uploads"

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
