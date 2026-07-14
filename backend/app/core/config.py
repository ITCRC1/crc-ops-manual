from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la app, leída de variables de entorno (.env en desarrollo)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CRC Operations Manual Hub API"
    entorno: str = "desarrollo"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/crc_ops_manual"

    @field_validator("database_url", mode="before")
    @classmethod
    def _forzar_driver_asyncpg(cls, v: str) -> str:
        """Normaliza la URL de base al driver async (asyncpg).

        Railway/Heroku entregan la conexión como `postgres://` o `postgresql://`,
        que SQLAlchemy resuelve al driver sync (psycopg2, no instalado). Todo el
        stack es async, así que forzamos `postgresql+asyncpg://`. Además quitamos
        parámetros de query que asyncpg no entiende (`sslmode`, `channel_binding`,
        propios de libpq), para que la conexión no falle.
        """
        if not isinstance(v, str) or not v:
            return v
        esquema, _, resto = v.partition("://")
        if esquema in ("postgres", "postgresql"):
            v = f"postgresql+asyncpg://{resto}"
        partes = urlsplit(v)
        if partes.query:
            filtrados = [
                (k, val)
                for k, val in parse_qsl(partes.query, keep_blank_values=True)
                if k not in ("sslmode", "channel_binding")
            ]
            v = urlunsplit(partes._replace(query=urlencode(filtrados)))
        return v

    jwt_secret_key: str = "cambiar-en-produccion"
    jwt_algoritmo: str = "HS256"
    jwt_access_token_minutos: int = 20
    jwt_refresh_token_dias: int = 7

    cors_allow_origins: list[str] = ["http://localhost:3000"]

    # URL pública del frontend. Se usa en el PDF exportable (sello "entrá a validar a la
    # plataforma"). Override por env FRONTEND_URL si cambia el dominio.
    frontend_url: str = "https://crc-ops-manual-web.vercel.app"

    nivel_minimo_firmante: int = 3

    # Almacenamiento de los PDF firmados (documentos controlados). En producción
    # debería ser un volumen persistente / object storage.
    storage_dir: str = "documentos_controlados"


@lru_cache
def get_settings() -> Settings:
    return Settings()
