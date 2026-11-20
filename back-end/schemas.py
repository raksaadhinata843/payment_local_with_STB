from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UserData(BaseModel):
    user_id: int
    username: str
    photo_url: str
    balance: int
    status: str

class UserResponse(BaseModel):
    status: str
    data: UserData
    
    model_config = ConfigDict(from_attributes=True)

class ChargeRequest(BaseModel):
    idempotency_key: str
    rfid_uid: str
    amount: int
    auth_method: str
    timestamp: datetime

class ChargeResponse(BaseModel):
    status: str
    transaction_id: str
    idempotency_key: str
    balance_before: int
    balance_after: int
    message: str

    model_config = ConfigDict(from_attributes=True)