from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import Settings
from app.models.common import UserRole


def create_access_token(
    user_id: str,
    email: str,
    role: UserRole,
    settings: Settings,
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
