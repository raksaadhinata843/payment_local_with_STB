from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, engine, Base
from app.models import STBDevice
from app.auth import verify_device_hmac
from app import schemas, crud

# Initialize DB Tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# CORS middleware for local web dashboards on STB
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME}

# --- Device API Endpoints ---

@app.get(
    f"{settings.API_V1_STR}/device/customer-by-card", 
    response_model=schemas.CustomerLookupResponse,
    tags=["Device API"]
)
def get_customer_by_card(
    rfid_uid: str = Query(..., description="UID RFID dari sensor kasir"),
    db: Session = Depends(get_db),
    device: STBDevice = Depends(verify_device_hmac)
):
    customer_info, error_msg = crud.get_customer_by_rfid(db, rfid_uid)
    if error_msg:
        return schemas.CustomerLookupResponse(
            success=False,
            message=error_msg,
            data=None
        )
    return schemas.CustomerLookupResponse(
        success=True,
        message="Customer data retrieved successfully",
        data=customer_info
    )

@app.post(
    f"{settings.API_V1_STR}/device/charge",
    response_model=schemas.ChargeResponse,
    tags=["Device API"]
)
def charge_payment(
    charge_in: schemas.ChargeRequest,
    db: Session = Depends(get_db),
    device: STBDevice = Depends(verify_device_hmac)
):
    try:
        data, msg = crud.process_charge(db, charge_in)
        return schemas.ChargeResponse(
            success=True,
            message=msg,
            data=data
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing transaction: {str(e)}"
        )

@app.post(
    f"{settings.API_V1_STR}/device/sync-offline",
    response_model=schemas.SyncOfflineResponse,
    tags=["Device API"]
)
def sync_offline_transactions(
    sync_in: schemas.SyncOfflineRequest,
    db: Session = Depends(get_db),
    device: STBDevice = Depends(verify_device_hmac)
):
    try:
        result = crud.process_offline_sync(db, sync_in)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing offline transactions: {str(e)}"
        )

# --- Admin API Endpoints ---

@app.post(
    f"{settings.API_V1_STR}/admin/topup",
    response_model=schemas.TopupResponse,
    tags=["Admin API"]
)
def topup_balance(
    topup_in: schemas.TopupRequest,
    db: Session = Depends(get_db)
):
    try:
        res = crud.process_topup(db, topup_in)
        return res
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
