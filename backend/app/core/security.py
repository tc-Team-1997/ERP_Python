from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from backend.app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(subject: str, tenant_id: int, role: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode = {"sub": subject, "tenant_id": tenant_id, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
