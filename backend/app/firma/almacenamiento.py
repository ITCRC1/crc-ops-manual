"""Almacenamiento de los PDF de documentos controlados.

Implementación local (filesystem). En producción se reemplaza por object storage
(volumen persistente de Railway / S3) sin cambiar la interfaz.
"""

from pathlib import Path

from app.core.config import get_settings

settings = get_settings()
_BASE = Path(settings.storage_dir)


def guardar_pdf(clave: str, contenido: bytes) -> str:
    _BASE.mkdir(parents=True, exist_ok=True)
    ruta = _BASE / clave
    ruta.write_bytes(contenido)
    return clave


def leer_pdf(clave: str) -> bytes | None:
    ruta = _BASE / clave
    return ruta.read_bytes() if ruta.exists() else None
