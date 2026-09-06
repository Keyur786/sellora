from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.core.security import ALGORITHM
from app.models.organization import Organization, User, OrganizationMember

security = HTTPBearer(auto_error=False)

DEFAULT_DEV_ORG_SLUG = "demo-seller-india"
DEFAULT_DEV_USER_EMAIL = "seller@sellora.in"


def get_or_create_dev_tenant(db: Session) -> tuple[User, Organization]:
    """Helper to retrieve or initialize the default development organization and user."""
    org = db.query(Organization).filter(Organization.slug == DEFAULT_DEV_ORG_SLUG).first()
    if not org:
        org = Organization(
            name="Apex Retail India",
            slug=DEFAULT_DEV_ORG_SLUG,
            currency="INR",
            timezone="Asia/Kolkata",
        )
        db.add(org)
        db.commit()
        db.refresh(org)

    user = db.query(User).filter(User.email == DEFAULT_DEV_USER_EMAIL).first()
    if not user:
        user = User(
            email=DEFAULT_DEV_USER_EMAIL,
            full_name="Rajesh Sharma",
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role="owner",
        )
        db.add(member)
        db.commit()

    return user, org


def get_current_user(
    db: Session = Depends(get_db),
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
) -> User:
    """Validate bearer token or handle development mock user."""
    # 1. Development Mode fallback
    if settings.ENVIRONMENT == "development" and not auth_header:
        dev_user, _ = get_or_create_dev_tenant(db)
        return dev_user

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.credentials
    try:
        # Check provider type (e.g. Supabase, Clerk, or internal JWT)
        if settings.AUTH_PROVIDER == "supabase" and settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
            email = payload.get("email")
            auth_uid = payload.get("sub")
        else:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            auth_uid = payload.get("sub")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials: email missing in token payload",
            )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Auto-provision user on verified token
        user = User(email=email, auth_provider_id=auth_uid, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user


def get_current_organization(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-Id"),
) -> Organization:
    """Enforce tenant isolation by retrieving and validating organization access."""
    # 1. Development fallback
    if settings.ENVIRONMENT == "development" and not x_tenant_id:
        _, org = get_or_create_dev_tenant(db)
        return org

    if x_tenant_id:
        # Verify the user is a member of the requested tenant
        membership = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.organization_id == x_tenant_id,
            )
            .first()
        )
        if not membership and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Not a member of the requested organization",
            )
        org = db.query(Organization).filter(Organization.id == x_tenant_id).first()
        if not org or not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found or inactive",
            )
        return org

    # Default to user's first organization
    first_membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .first()
    )
    if not first_membership:
        # Create default organization for new user
        org_name = f"{current_user.email.split('@')[0]}'s Store"
        org = Organization(
            name=org_name,
            slug=f"org-{current_user.id[:8]}",
            currency="INR",
            timezone="Asia/Kolkata",
        )
        db.add(org)
        db.commit()
        db.refresh(org)

        member = OrganizationMember(organization_id=org.id, user_id=current_user.id, role="owner")
        db.add(member)
        db.commit()
        return org

    org = db.query(Organization).filter(Organization.id == first_membership.organization_id).first()
    return org
