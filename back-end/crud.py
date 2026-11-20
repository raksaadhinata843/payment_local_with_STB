from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Cards, Users, Wallets

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