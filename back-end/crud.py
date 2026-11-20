from sqlalchemy import select
from sqlalchemy.orm import Session, contains_eager
from models import Cards, Users, Wallets

def get_user_by_card(db: Session, rfid_input: str):

    stmt = (
        select(Cards, Users, Wallets)
        .join(Cards.Users)
        .join(Users.Wallets)
        .options(
            contains_eager(Cards.Users)
            .contains_eager(Users.Wallets)
        )
        .where(
            Cards.rfid_uid == rfid_input,
            Cards.is_active == True
        )
    )

    card = db.scalars(stmt).first()

    if not card:
        return None