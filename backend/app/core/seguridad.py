"""Seguridad: hashing de contraseñas (Argon2) y tokens JWT access+refresh (§4)."""

from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _crear_token(sub: str, tipo: str, expira: timedelta, extra: dict | None = None) -> str:
    ahora = datetime.now(UTC)
    payload = {"sub": sub, "type": tipo, "iat": ahora, "exp": ahora + expira}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algoritmo)


def crear_access_token(usuario_id: str, extra: dict | None = None) -> str:
    return _crear_token(
        usuario_id, "access", timedelta(minutes=settings.jwt_access_token_minutos), extra
    )


def crear_refresh_token(usuario_id: str) -> str:
    return _crear_token(usuario_id, "refresh", timedelta(days=settings.jwt_refresh_token_dias))


def decodificar_token(token: str, tipo_esperado: str) -> dict | None:
    """Devuelve el payload si el token es válido y del tipo esperado; si no, None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algoritmo])
    except JWTError:
        return None
    if payload.get("type") != tipo_esperado:
        return None
    return payload
