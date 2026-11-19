from datetime import datetime
import uuid
import enum
from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class StatusUsers(enum.Enum):
    BLOCKED="blocked"
    ACTIVE="active"
    DELETED="deleted"

class Base (DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50))
    photo_url: Mapped[str] = mapped_column(String(255))
    status: Mapped[StatusUsers] = mapped_column(
        Enum(StatusUsers),
        default=StatusUsers.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )