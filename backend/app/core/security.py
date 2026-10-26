"""Hash de contrasenas (scrypt) y tokens de acceso (JWT HS256)."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from .config import settings

# N=2^14, r=8, p=1: minimo recomendado por OWASP para scrypt, manteniendo el
# login rapido en una demo (N=2^17 seria mas fuerte pero usa ~128 MB/hash).
_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1
_ALGORITHM = "HS256"


def _scrypt(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    return f"scrypt${salt.hex()}${_scrypt(password, salt).hex()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        scheme, salt_hex, digest_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    return hmac.compare_digest(_scrypt(password, salt).hex(), digest_hex)


def create_access_token(staff_id: int, expires_minutes: int | None = None) -> str:
    minutes = (
        expires_minutes if expires_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(staff_id), "exp": datetime.now(UTC) + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Devuelve el id del personal, o None si el token es invalido o expiro."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
