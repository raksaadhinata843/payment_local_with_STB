from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Cards, Users, wallets

def get_user_by_card(db: Session, rfid_input: str):

    users_fk = [col for col in users.__table__.columns if col.foreign_keys]
    wallets_fk = [col for col in wallets.__table__.columns if col.foreign_keys]
    stmt = (
        select(cards, *users_fk, *wallets_fk)
        .join(cards.users)
        .join(users.wallets)
        .options(
            contains_eager(cards.users)
            .contains_eager(users.wallets)
        )
        .where(
            cards.rfid_uid == rfid_input,
            cards.is_active == True
        )
    )

    card = db.scalars(stmt).first()

    if not card:
        return None