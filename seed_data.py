import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal, Base, engine
from app.models import Customer, RFIDCard, Wallet, STBDevice, BiometricTemplate
from app.crud import hash_pin

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Clear existing data if re-running
        db.query(RFIDCard).delete()
        db.query(Wallet).delete()
        db.query(BiometricTemplate).delete()
        db.query(Customer).delete()
        db.query(STBDevice).delete()
        db.commit()

        # 1. Register STB Device
        device = STBDevice(
            device_id="STB-KASIR-01",
            device_name="Kasir Utama Kantin",
            hmac_secret="stb_secret_key_2026_super_secure",
            status="ACTIVE"
        )
        db.add(device)

        # 2. Add Customer Budi
        cust1 = Customer(
            id="CUST-001",
            name="Budi Santoso",
            photo_url="/static/photos/budi_santoso.jpg",
            pin_hash=hash_pin("123456"),
            status="ACTIVE"
        )
        db.add(cust1)

        # 3. Add RFID Card for Budi
        card1 = RFIDCard(
            rfid_uid="4B2A8F90",
            customer_id="CUST-001",
            status="ACTIVE"
        )
        db.add(card1)

        # 4. Add Wallet for Budi (Rp 100.000)
        wallet1 = Wallet(
            customer_id="CUST-001",
            balance=100000
        )
        db.add(wallet1)

        # 5. Add Biometric Template sample
        bio1 = BiometricTemplate(
            customer_id="CUST-001",
            finger_index=1,
            template_data="SAMPLE_FINGERPRINT_HASH_TEMPLATE_DATA_XYZ"
        )
        db.add(bio1)

        db.commit()
        print("✅ Database successfully seeded!")
        print(" - Device: STB-KASIR-01 (secret: stb_secret_key_2026_super_secure)")
        print(" - Customer: Budi Santoso (ID: CUST-001, Balance: Rp 100,000)")
        print(" - RFID UID: 4B2A8F90")
        print(" - PIN: 123456")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
