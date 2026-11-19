from datetime import datetime
import uuid
import enum
from sqlalchemy import TIMESTAMP, Enum, String, BigInteger, LargeBinary, func, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class StatusUsers(enum.Enum):
    BLOCKED="blocked"
    ACTIVE="active"
    DELETED="deleted"

class RoleAdmins(enum.Enum):
    SUPERADMIN="superadmins"
    OPERATOR="operator"

class TypeTransaction(enum.Enum):
    PAYMENT="payment"
    TOPUP="top_up"
    REFUND="refund"

class StatusTransaction(enum.Enum):
    PENDING="pending"
    SUCCESS="success"
    FAILED="failed"

class AuthTransaction(enum.Enum):
    FINGERPRINT="fingerprint"
    FALLBACKPIN="fallback_pin"

class Base(DeclarativeBase):
    pass

class Admins(Base):
    __tablename__ = "admins"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50))
    role: Mapped[RoleAdmins] = mapped_column(
        Enum(RoleAdmins),
        default=RoleAdmins.OPERATOR
    )
    password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

class Devices(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(
        String(17),
        primary_key=True
    )
    location_name: Mapped[str] = mapped_column(String(21))
    ip_address: Mapped[str] = mapped_column(String(17))
    last_seen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

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
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

class Cards(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        default=uuid.uuid4
    )
    rfid_uid: Mapped[str] = mapped_column(
        String(),
        unique=True,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
    
class Wallets(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        default=uuid.uuid4
    )
    balance: Mapped[int] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class Biometrics(Base):
    __tablename__ = "biometrics"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        default=uuid.uuid4
    )
    fingerprint_template: Mapped[bytes] = mapped_column(LargeBinary)
    fallback_pin: Mapped[str] = mapped_column(String())

class Transactions(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(),
        unique=True,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        default=uuid.uuid4
    )
    device_id: Mapped[str] = mapped_column(
        String(17),
        ForeignKey("device.id", ondelete="CASCADE")
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("admins.id", ondelete="CASCADE"),
        default=uuid.uuid4
    )
    amount: Mapped[int] = mapped_column(BigInteger)
    balance_before: Mapped[int] = mapped_column(BigInteger)
    balance_after: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[TypeTransaction] = mapped_column(
        Enum(TypeTransaction),
        default=TypeTransaction.PAYMENT
    )
    status: Mapped[StatusTransaction] = mapped_column(
        Enum(StatusTransaction),
        default=StatusTransaction.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
    auth_method: Mapped[AuthTransaction] = mapped_column(
        Enum(AuthTransaction),
        default=AuthTransaction.FINGERPRINT
    )