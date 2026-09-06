import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.core.database import Base


def get_utc_now() -> datetime:
    """Return current UTC datetime timezone-aware."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a clean UUID4 hex string."""
    return str(uuid.uuid4())


class TimestampMixin:
    """Mixin for models requiring created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """Abstract base model providing UUID primary key and timestamps."""
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
