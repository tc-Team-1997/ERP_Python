from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        token_data = TokenData(**payload)
    except JWTError as exc:
        raise credentials_exception from exc

    if token_data.sub is None or token_data.tenant_id is None:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.email == token_data.sub, User.tenant_id == token_data.tenant_id)
        .first()
    )
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_roles(*roles: str):
    """Dependency factory: allow users whose role is in the list. Auditor is always read-only."""
    allowed = {r.lower() for r in roles}

    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(sorted(allowed))}",
            )
        return current_user

    return _check


def require_admin_or_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.lower() not in {"admin", "manager"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Manager role required")
    return current_user


def require_write(current_user: User = Depends(get_current_user)) -> User:
    """Any role EXCEPT auditor can write."""
    if current_user.role.lower() == "auditor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Auditors have read-only access")
    return current_user
