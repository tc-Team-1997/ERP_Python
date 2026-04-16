from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user, require_admin
from backend.app.core.security import create_access_token, get_password_hash, verify_password
from backend.app.db.session import get_db
from backend.app.models.tenant import Tenant
from backend.app.models.user import User
from backend.app.schemas.auth import RegistrationResponse, TenantRegisterRequest, Token, UserCreateRequest, UserRead
from backend.app.services.audit_service import log_event
from fastapi import Request

router = APIRouter()


@router.post("/register-tenant", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_tenant(payload: TenantRegisterRequest, db: Session = Depends(get_db)):
    existing_tenant = db.query(Tenant).filter((Tenant.slug == payload.business_slug) | (Tenant.name == payload.business_name)).first()
    if existing_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business name or slug already exists")

    existing_user = db.query(User).filter(User.email == payload.admin_email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin email already exists")

    tenant = Tenant(name=payload.business_name, slug=payload.business_slug)
    db.add(tenant)
    db.flush()

    admin_user = User(
        tenant_id=tenant.id,
        email=payload.admin_email,
        full_name=payload.admin_name,
        hashed_password=get_password_hash(payload.admin_password),
        role="admin",
    )
    db.add(admin_user)
    db.commit()
    db.refresh(tenant)
    db.refresh(admin_user)

    return RegistrationResponse(
        tenant=tenant,
        admin_user=admin_user,
        message="Tenant and admin user created successfully",
    )


@router.post("/login", response_model=Token)
def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = create_access_token(subject=user.email, tenant_id=user.tenant_id, role=user.role)
    log_event(db, user, "LOGIN", "user", user.id,
              f"{user.email} logged in",
              ip_address=request.client.host if request.client else None)
    return Token(access_token=access_token)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin-only: create a new user (manager / user / auditor) within the tenant."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    user = User(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(db, current_user, "CREATE", "user", user.id,
              f"Created {payload.role} user {payload.email}",
              ip_address=request.client.host if request.client else None)
    return user


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Admin-only: list all users within the tenant."""
    return db.query(User).filter(User.tenant_id == current_user.tenant_id).order_by(User.id).all()


@router.get("/me", response_model=UserRead)
def read_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = (
        db.query(User)
        .options(joinedload(User.tenant))
        .filter(User.id == current_user.id)
        .first()
    )
    return user
