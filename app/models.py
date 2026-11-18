import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    photo_url = Column(String(255), nullable=True)
    pin_hash = Column(String(255), nullable=True)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cards = relationship("RFIDCard", back_populates="customer", cascade="all, delete-orphan")
    wallet = relationship("Wallet", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    biometrics = relationship("BiometricTemplate", back_populates="customer", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="customer")

class RFIDCard(Base):
    __tablename__ = "rfid_cards"

    rfid_uid = Column(String(50), primary_key=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="ACTIVE")
    issued_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="cards")

class Wallet(Base):
    __tablename__ = "wallets"

    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True)
    balance = Column(BigInteger, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="wallet")

class BiometricTemplate(Base):
    __tablename__ = "biometric_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    finger_index = Column(Integer, default=1)
    template_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="biometrics")

class STBDevice(Base):
    __tablename__ = "stb_devices"

    device_id = Column(String(50), primary_key=True)
    device_name = Column(String(100), nullable=False)
    hmac_secret = Column(String(255), nullable=False)
    status = Column(String(20), default="ACTIVE")
    last_seen_at = Column(DateTime, nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    rfid_uid = Column(String(50), nullable=False)
    stb_device_id = Column(String(50), ForeignKey("stb_devices.device_id"), nullable=False)
    type = Column(String(20), nullable=False) # DEBIT / TOPUP
    amount = Column(BigInteger, nullable=False)
    balance_before = Column(BigInteger, nullable=False)
    balance_after = Column(BigInteger, nullable=False)
    auth_method = Column(String(30), nullable=False) # FINGERPRINT, PIN_FALLBACK, ADMIN_OVERRIDE
    is_offline_sync = Column(Boolean, default=False)
    status = Column(String(20), default="SUCCESS")
    transacted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="transactions")
    device = relationship("STBDevice")
