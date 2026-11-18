import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Customer, RFIDCard, Wallet, Transaction, BiometricTemplate, STBDevice
from app import schemas

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode('utf-8')).hexdigest()

def get_customer_by_rfid(db: Session, rfid_uid: str):
    card = db.query(RFIDCard).filter(
        RFIDCard.rfid_uid == rfid_uid, 
        RFIDCard.status == "ACTIVE"
    ).first()
    
    if not card:
        return None, "RFID card not found or inactive"

    customer = db.query(Customer).filter(
        Customer.id == card.customer_id, 
        Customer.status == "ACTIVE"
    ).first()

    if not customer:
        return None, "Customer account is inactive or blocked"

    wallet = db.query(Wallet).filter(Wallet.customer_id == customer.id).first()
    balance = wallet.balance if wallet else 0

    has_bio = db.query(BiometricTemplate).filter(BiometricTemplate.customer_id == customer.id).count() > 0
    has_pin = customer.pin_hash is not None and len(customer.pin_hash) > 0

    customer_info = schemas.CustomerInfo(
        customer_id=customer.id,
        name=customer.name,
        photo_url=customer.photo_url,
        status=customer.status,
        balance=balance,
        has_fingerprint=has_bio,
        has_pin=has_pin
    )

    return customer_info, None

def process_charge(db: Session, charge_in: schemas.ChargeRequest, is_offline_sync: bool = False):
    # 1. Idempotency Check: prevent double charge
    existing_tx = db.query(Transaction).filter(Transaction.idempotency_key == charge_in.idempotency_key).first()
    if existing_tx:
        customer = db.query(Customer).filter(Customer.id == existing_tx.customer_id).first()
        return schemas.ChargeResponseData(
            transaction_id=existing_tx.id,
            idempotency_key=existing_tx.idempotency_key,
            customer_id=existing_tx.customer_id,
            customer_name=customer.name if customer else "Unknown",
            amount=existing_tx.amount,
            balance_before=existing_tx.balance_before,
            balance_after=existing_tx.balance_after,
            auth_method=existing_tx.auth_method,
            is_offline_sync=existing_tx.is_offline_sync,
            status=existing_tx.status,
            transacted_at=existing_tx.transacted_at
        ), "Transaction already processed (Idempotent response)"

    # 2. Get card & customer
    card = db.query(RFIDCard).filter(RFIDCard.rfid_uid == charge_in.rfid_uid, RFIDCard.status == "ACTIVE").first()
    if not card:
        raise ValueError("Invalid or unassigned RFID Card")

    customer = db.query(Customer).filter(Customer.id == card.customer_id, Customer.status == "ACTIVE").first()
    if not customer:
        raise ValueError("Customer account is inactive or blocked")

    # 3. Handle PIN Fallback if requested
    if charge_in.auth_method == "PIN_FALLBACK":
        if not charge_in.pin:
            raise ValueError("PIN is required for PIN_FALLBACK authentication")
        if customer.pin_hash and hash_pin(charge_in.pin) != customer.pin_hash:
            raise ValueError("Invalid PIN")

    # 4. Atomic Wallet Balance Check & Update (with SQLite/Postgres transaction lock)
    wallet = db.query(Wallet).filter(Wallet.customer_id == customer.id).with_for_update().first()
    if not wallet:
        raise ValueError("Customer wallet not found")

    if wallet.balance < charge_in.amount:
        raise ValueError(f"Insufficient funds. Current balance: Rp {wallet.balance:,}")

    balance_before = wallet.balance
    balance_after = balance_before - charge_in.amount

    wallet.balance = balance_after
    wallet.updated_at = datetime.utcnow()

    # 5. Record Transaction
    tx_timestamp = charge_in.transacted_at if charge_in.transacted_at else datetime.utcnow()
    
    new_tx = Transaction(
        idempotency_key=charge_in.idempotency_key,
        customer_id=customer.id,
        rfid_uid=charge_in.rfid_uid,
        stb_device_id=charge_in.stb_device_id,
        type="DEBIT",
        amount=charge_in.amount,
        balance_before=balance_before,
        balance_after=balance_after,
        auth_method=charge_in.auth_method,
        is_offline_sync=is_offline_sync,
        status="SUCCESS",
        transacted_at=tx_timestamp
    )

    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)

    return schemas.ChargeResponseData(
        transaction_id=new_tx.id,
        idempotency_key=new_tx.idempotency_key,
        customer_id=customer.id,
        customer_name=customer.name,
        amount=new_tx.amount,
        balance_before=balance_before,
        balance_after=balance_after,
        auth_method=new_tx.auth_method,
        is_offline_sync=is_offline_sync,
        status=new_tx.status,
        transacted_at=new_tx.transacted_at
    ), "Payment processed successfully"

def process_offline_sync(db: Session, sync_in: schemas.SyncOfflineRequest):
    details = []
    processed_count = 0
    skipped_count = 0
    failed_count = 0

    for item in sync_in.transactions:
        # Check duplicate
        existing = db.query(Transaction).filter(Transaction.idempotency_key == item.idempotency_key).first()
        if existing:
            skipped_count += 1
            details.append(schemas.SyncResultItem(
                idempotency_key=item.idempotency_key,
                status="DUPLICATE_SKIPPED",
                message="Transaction already synced previously",
                transaction_id=existing.id
            ))
            continue

        try:
            charge_req = schemas.ChargeRequest(
                idempotency_key=item.idempotency_key,
                rfid_uid=item.rfid_uid,
                amount=item.amount,
                stb_device_id=sync_in.stb_device_id,
                auth_method=item.auth_method,
                transacted_at=item.transacted_at
            )
            data, msg = process_charge(db, charge_req, is_offline_sync=True)
            processed_count += 1
            details.append(schemas.SyncResultItem(
                idempotency_key=item.idempotency_key,
                status="PROCESSED",
                message="Synced & processed successfully",
                transaction_id=data.transaction_id
            ))
        except Exception as e:
            failed_count += 1
            details.append(schemas.SyncResultItem(
                idempotency_key=item.idempotency_key,
                status="FAILED",
                message=str(e)
            ))

    return schemas.SyncOfflineResponse(
        success=True,
        message="Batch offline sync completed",
        total_batch=len(sync_in.transactions),
        processed_count=processed_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        details=details
    )

def process_topup(db: Session, topup_in: schemas.TopupRequest):
    customer = None
    if topup_in.customer_id:
        customer = db.query(Customer).filter(Customer.id == topup_in.customer_id).first()
    elif topup_in.rfid_uid:
        card = db.query(RFIDCard).filter(RFIDCard.rfid_uid == topup_in.rfid_uid).first()
        if card:
            customer = db.query(Customer).filter(Customer.id == card.customer_id).first()

    if not customer:
        raise ValueError("Customer or Card not found")

    wallet = db.query(Wallet).filter(Wallet.customer_id == customer.id).with_for_update().first()
    if not wallet:
        wallet = Wallet(customer_id=customer.id, balance=0)
        db.add(wallet)

    balance_before = wallet.balance
    balance_after = balance_before + topup_in.amount
    wallet.balance = balance_after
    wallet.updated_at = datetime.utcnow()

    # Record Topup Tx
    idempotency_key = f"TOPUP-{customer.id}-{int(datetime.utcnow().timestamp())}"
    tx = Transaction(
        idempotency_key=idempotency_key,
        customer_id=customer.id,
        rfid_uid=topup_in.rfid_uid or "MANUAL_ADMIN",
        stb_device_id=topup_in.admin_device_id,
        type="TOPUP",
        amount=topup_in.amount,
        balance_before=balance_before,
        balance_after=balance_after,
        auth_method="ADMIN_TOPUP",
        is_offline_sync=False,
        status="SUCCESS",
        transacted_at=datetime.utcnow()
    )
    db.add(tx)
    db.commit()

    return schemas.TopupResponse(
        success=True,
        message="Top-up successful",
        customer_id=customer.id,
        amount_added=topup_in.amount,
        balance_before=balance_before,
        balance_after=balance_after
    )
