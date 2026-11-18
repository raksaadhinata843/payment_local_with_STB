import hmac
import hashlib
from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import STBDevice

def verify_device_hmac(
    x_device_id: Optional[str] = Header(None, alias="X-Device-ID"),
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    db: Session = Depends(get_db)
) -> STBDevice:
    if not x_device_id:
        raise HTTPException(status_code=401, detail="Header X-Device-ID missing")
    
    device = db.query(STBDevice).filter(STBDevice.device_id == x_device_id, STBDevice.status == "ACTIVE").first()
    if not device:
        raise HTTPException(status_code=403, detail="Unregistered or inactive STB device")
    
    # If signature headers are provided, verify signature
    if x_signature and x_timestamp:
        message = f"{x_device_id}:{x_timestamp}".encode('utf-8')
        expected_sig = hmac.new(
            device.hmac_secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(x_signature, expected_sig):
            raise HTTPException(status_code=401, detail="Invalid HMAC Signature")

    return device
