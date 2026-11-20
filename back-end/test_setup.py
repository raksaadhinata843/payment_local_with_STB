from models import Base, Users, StatusUsers, Wallets, Cards
from database import engine, SessionLocal
from crud import get_user_by_card
from schemas import UserResponse

def run_test():
    print("=== TESTING SETUP DATABASE & CRUD CASPRA ===")

    print("\n1. Membuat struktur tabel di SQLite (caspra.db)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("   [OK] Tabel berhasil dibuat!")

    print("\n2. Memasukkan data dummy...")
    db = SessionLocal()
    try:
        new_user = Users(
            username="Budi Santoso",
            photo_url="/static/photos/budi.jpg",
            status=StatusUsers.ACTIVE
        )
        db.add(new_user)
        db.flush()

        new_wallet = Wallets(user_id=new_user.id, balance=75000)
        new_card = Cards(user_id=new_user.id, rfid_uid="CARD12345", is_active=True)

        db.add_all([new_wallet, new_card])
        db.commit()
        print("   [OK] Data User, Wallet, dan Card berhasil disimpan!")
    except Exception as e:
        db.rollback()
        print(f"   [ERROR] Gagal memasukkan data dummy: {e}")
        db.close()
        return

    print("\n3. Menguji fungsi get_user_by_card('CARD12345')...")
    user_dict = get_user_by_card(db, rfid_input="CARD12345")

    if user_dict:
        print("   [OK] Hasil Kueri CRUD:")
        print("       ", user_dict)

        print("\n4. Menguji Validasi Schema Pydantic (UserResponse)...")
        response_schema = UserResponse(
            status="success",
            data=user_dict
        )
        print("   [OK] Schema Valid! Format JSON Response:")
        print(response_schema.model_dump_json(indent=2))
    else:
        print("   [ERROR] Kartu tidak ditemukan!")

    db.close()
    print("\n=== PENGUJIAN SELESAI DENGAN SUKSES ===")

if __name__ == "__main__":
    run_test()
