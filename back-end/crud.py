from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Cards, Users, Wallets, Transactions

def get_user_by_card(db: Session, rfid_input: str):

    stmt = (
        select(Cards, Users, Wallets)
        .join(Users, Cards.user_id == Users.id)
        .join(Wallets, Users.id == Wallets.user_id)
        .where(
            Cards.rfid_uid == rfid_input,
            Cards.is_active == True
        )
    )

    card = db.execute(stmt).first()

    if not card:
        return None
    
    return card

def process_payment_transaction(db: Session, idempotency_key: str):

    stmt = (
        select(Transactions)
        .where(Transactions.idempotency_key == idempotency_key)
    )

    has_own_key = db.execute(stmt).first()

    if not has_own_key:

        new_transaction = Transactions(
            idempotency_key=idempotency_key,
            balance_before=balance_before,
            balance_after=balance_after
        )
        
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        return {
            "status": "SUCCESS",
            "transaction_id": str(new_transaction.id),
            "idempotency_key": idempotency_key,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "message": "Terimakasih telah belanja di sini!!!..."
        }
    
    return {
        "status": "SUCCESS",
        "transaction_id": str(has_own_key.id),
        "idempotency_key": has_own_key.idempotency_key,
        "balance_before": has_own_key.balance_before,
        "balance_after": has_own_key.balance_after,
        "message": "Terimakasih telah belanja di sini!!!..."
    }