[README.md](https://github.com/user-attachments/files/34941102/README.md)
# Sistem Pembayaran Kasir Non-Tunai RFID + Biometrik (Multi-STB Edge Architecture)

Dokumentasi arsitektur dan spesifikasi teknis untuk sistem pembayaran lokal non-tunai (*cashless payment*) berbasis **1 STB Admin (Server Pusat)** dan **Banyak STB Kasir (Terminal POS Edge)**. System ini menggabungkan identifikasi cepat via **RFID/NFC**, autentikasi **Sidik Jari (Fingerprint)**, verifikasi visual 2-faktor, serta mode ketahanan jaringan terdistribusi (*Offline Mode / Mode Kedua*).

---

## 1. Ikhtisar Sistem & Filosofi Desain

Sistem ini dirancang untuk ekosistem lokal terisolasi seperti kantin, minimarket komunitas, atau pusat hiburan lokal. Dengan memanfaatkan perangkat *Set-Top Box* (STB bekas/murah berbasis Armbian Linux seperti HG680P/B860H), sistem ini menghadirkan infrastruktur *point-of-sale* terpusat yang hemat biaya namun berstandar industri.

### Prinsip Utama Desain
* **Keamanan Berlapis (Defense-in-Depth)**: Kombinasi ID Fisik (RFID), Verifikasi Visual Kasir (Foto di Monitor), dan Otorisasi Biometrik (Sidik Jari / PIN Temporer).
* **Ketahanan Operasional (Offline-First Resilience)**: Kasir tetap dapat bertransaksi meskipun jaringan lokal terputus atau server STB Admin mengalami gangguan sementara.
* **Integritas Keuangan**: Pencatatan transaksi berbasis *atomic ledger* dengan kunci idempotensi (*Idempotency Key*) untuk mencegah pemotongan saldo ganda.

---

## 2. Arsitektur Jaringan & Topologi Perangkat

Sistem terbagi menjadi dua peran utama perangkat berbasis STB:

```
                          [ Jaringan Lokal LAN / Wi-Fi ]
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
    ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
    │  STB Kasir 1    │        │  STB Kasir 2    │        │  STB Kasir N    │
    │  (Terminal POS) │        │  (Terminal POS) │        │  (Terminal POS) │
    │ ├─ USB RFID     │        │ ├─ USB RFID     │        │ ├─ USB RFID     │
    │ └─ USB Finger   │        │ └─ USB Finger   │        │ └─ USB Finger   │
    └────────┬────────┘        └────────┬────────┘        └────────┬────────┘
             │                          │                          │
             └──────────────────────────┼──────────────────────────┘
                                        │ (HTTP REST API / HMAC)
                                        ▼
                           ┌─────────────────────────┐
                           │   STB Admin (Server)    │
                           │ ├─ Database Terpusat    │
                           │ ├─ Engine Transactions  │
                           │ ├─ Dashboard Web Admin  │
                           │ └─ Redundancy Backup    │
                           └─────────────────────────┘
```

### A. STB Admin (Server Pusat & Engine Ledger)
* Menjalankan basis data terpusat (PostgreSQL / SQLite) pada media penyimpanan eksternal (USB SSD/Flashdisk) untuk mencegah kerusakan media *flash* internal (eMMC/MicroSD).
* Menyediakan REST API terpusat untuk otorisasi dan pemrosesan saldo.
* Menyediakan *Web Dashboard* untuk pendaftaran kartu/pelanggan baru, registrasi sidik jari, pengisian saldo (*top-up*), serta laporan audit transaksi.
* Dilengkapi node cadangan (*Redundancy Backup STB*) yang dapat menggantikan fungsi server utama jika terjadi kegagalan hardware.

### B. STB Kasir (Terminal POS Edge)
* Bertindak sebagai terminal transaksi independen di setiap titik meja kasir.
* Di-colokkan perangkat USB RFID Reader (HID/UART) dan USB Fingerprint Scanner (R307/FPM10A/ZKTeco).
* Memiliki layar monitor lokal untuk menampilkan informasi pembeli, status transaksi, dan foto profil pelanggan.
* Memiliki penyimpanan SQLite lokal untuk mencatat transaksi saat berada dalam **Mode Kedua (Offline Mode)**.

---

## 3. Alur Kerja Transaksi (5-Stage Payment Flow)

```
[ Pelanggan Tap RFID ] ──► [ Kueri Data & Tampil Foto di Monitor ]
                                         │
                                         ▼
                            [ Kasir Input Nominal Belanja ]
                                         │
                                         ▼
                            [ Validasi Saldo Mampu? ]
                                   │           │
                          (Tidak) ─┘           └─► (Ya)
                             │                        │
                             ▼                        ▼
                   [ Transaksi Ditolak ]     [ Autentikasi Biometrik ]
                                                 │           │
                                        (Gagal) ─┘           └─► (Berhasil)
                                           │                          │
                                           ▼                          ▼
                                 [ Fallback: PIN Temp ]     [ Eksekusi Debit Ledger ]
```

### Tahap 1: Pembacaan RFID & Kueri Data Pelanggan
1. Pelanggan menempelkan kartu RFID/wristband pada reader di STB Kasir.
2. STB Kasir membaca UID kartu secara otomatis.
3. STB Kasir mengirim permintaan kueri `GET /api/v1/device/user-by-card?uid={UID}` ke STB Admin.
4. Layar monitor kasir menampilkan **Nama Pelanggan**, **Sisa Saldo**, dan **Foto Profil Pelanggan**. Kasir melakukan pencocokan visual antara fisik pembeli dan foto profil di layar.

### Tahap 2: Input Nominal & Validasi Saldo Awal
1. Kasir memasukkan jumlah nominal pembayaran belanjaan.
2. STB Kasir memeriksa kecukupan saldo (`Sisa Saldo >= Nominal Belanja`).
3. Jika saldo tidak mencukupi, sistem menampilkan pemberitahuan *"Saldo Tidak Cukup"* dan transaksi langsung dibatalkan.

### Tahap 3: Autentikasi Biometrik & Fallback PIN
1. Pelanggan menempelkan jari pada sensor sidik jari di STB Kasir.
2. Sensor melakukan pencocokan template biometrik.
3. **Mekanisme Fallback (Jari Kotor/Rusak)**: Jika autentikasi sidik jari gagal berulang kali, kasir dapat memilih opsi *"Gunakan PIN Temporer"*. Kasir meminta kode persetujuan/PIN temporer dari Admin untuk memvalidasi transaksi secara manual.

### Tahap 4: Eksekusi Transaksi Debit
1. Setelah autentikasi berhasil (Sidik Jari VALID / PIN Approval VALID), STB Kasir membentuk *payload* transaksi yang berisi: `rfid_uid`, `amount`, `device_id`, `idempotency_key`, dan `timestamp`.
2. Jika jaringan **Online**, *payload* dikirim ke STB Admin (`POST /api/v1/device/charge`). STB Admin memproses pemotongan saldo secara *atomic* pada database ledger terpusat.
3. Jika jaringan **Offline (Mode Kedua)**, transaksi dicatat secara lokal di database SQLite STB Kasir dan ditandai sebagai *Pending Synchronization*.

### Tahap 5: Status & Penyelesaian
1. Layar monitor kasir menampilkan status **"PEMBAYARAN BERHASIL"** beserta sisa saldo terbaru.
2. Indikator visual di layar menjadi acuan resmi bahwa transaksi telah selesai.

---

## 4. Kebijakan Keamanan & Antisipasi Skenario Terburuk

| Skenario Terburuk | Risiko | Mitigasi Teknis & Kebijakan Operasional |
| :--- | :--- | :--- |
| **Koneksi LAN Putus / STB Admin Down** | Kasir tidak bisa memotong saldo secara realtime. | **Mode Kedua (Offline Mode)**: STB Kasir menyimpan transaksi ke SQLite lokal. Saat koneksi pulih, STB Kasir otomatis menyinkronkan log ke STB Admin. |
| **Request Terduplikasi (Lagging Network)** | Pemotongan saldo terjadi dua kali (*Double Charge*). | **Idempotency Key**: Setiap transaksi diberi UUID unik dari STB Kasir. STB Admin akan mengabaikan request dengan UUID yang sudah pernah diproses. |
| **Kasir Minta Scan Ulang karena Ragu** | Pelanggan dirugikan akibat pemotongan saldo berulang. | **Aturan Mutlak Interaksi**: Jika layar sudah menampilkan status "BERHASIL", kasir DILARANG meminta scan ulang. Pelanggan berhak melaporkan pelanggaran ke Admin. |
| **Sensor Fingerprint Gagal Membaca Jari** | Antrean kasir macet total. | **PIN Temporer via Admin**: Kasir meminta otorisasi PIN sementara dari Admin setelah verifikasi identitas manual. |
| **Kloning Kartu RFID (Mifare Classic)** | Penggunaan saldo oleh pihak tidak berhak. | **Visual 2FA**: Sablon foto profil pada kartu fisik wajib dicocokkan oleh kasir dengan foto profil yang muncul di monitor kasir saat kartu di-tap. |
| **Kerusakan eMMC STB akibat Log Transaksi** | STB Admin rusak (*Wear-Out Storage*). | **External Storage Mounting**: Seluruh file database dan log transaksi wajib ditulis pada SSD/Flashdisk external yang terhubung via USB. |

---

## 5. Skema Basis Data Terpusat (Data Models)

### Tabel 'admins'
* `id` (UUID, Primary Key)
* `username` (VARCHAR)
* `role` (ENUM: SUPERADMIN, OPERATOR)
* `password` (VARCHAR)
* `is_active` (BOOLEAN)

### Tabel 'devices'
* `id` (VARCHAR, Primary Key)
* `location_name` (VARCHAR)
* `ip_address` (VARCHAR)
* `last_seen_at` (TIMESTAMP)

### Tabel `users`
* `id` (UUID, Primary Key)
* `username` (VARCHAR)
* `photo_url` (VARCHAR) - Jalur file foto profil untuk tampilan monitor.
* `status` (ENUM: ACTIVE, BLOCKED, DELETED)
* `created_at` (TIMESTAMP)

### Tabel `cards`
* `id` (UUID, Primary Key)
* `user_id` (UUID, Foreign Key -> `users.id`)
* `rfid_uid` (VARCHAR, Unique, Indexed) - UID unik dari kartu/wristband.
* `is_active` (BOOLEAN)

### Tabel `wallets`
* `id` (UUID, Primary Key)
* `user_id` (UUID, Foreign Key -> `users.id`, Unique)
* `balance` (BIGINT) - Saldo disimpan dalam satuan terkecil (integer / tanpa desimal).
* `updated_at` (TIMESTAMP)

### Tabel `biometrics`
* `id` (UUID, Primary Key)
* `user_id` (UUID, Foreign Key -> `users.id`)
* `fingerprint_template` (BLOB/TEXT) - Template hash sidik jari.
* `fallback_pin` (VARCHAR) - Hash PIN cadangan.

### Tabel `transactions`
* `id` (UUID, Primary Key)
* `idempotency_key` (VARCHAR, Unique, Indexed) - UUID unik transaksi dari kasir.
* `device_id` (VARCHAR, Foreign Key -> `devices.id`) - Identitas STB Kasir pengirim.
* `user_id` (UUID, Foreign Key -> `users.id`)
* `admin_id` (UUID, Foreign Key -> `admins.id`)
* `amount` (BIGINT) - Nominal transaksi.
* `balance_before` (BIGINT)
* `balance_after` (BIGINT)
* `type` (ENUM: REFUND, TOP UP, PAYMENT)
* `status` (ENUM: PENDING, SUCCESS, FAILED)
* `created_at` (TIMESTAMP)

---

## 6. Spesifikasi API Utama (Device REST API)

### 1. Kueri Pelanggan via RFID
* **Endpoint**: `GET /api/v1/device/user-by-card`
* **Headers**: `X-Device-ID`, `X-Device-HMAC`
* **Query Params**: `uid=4B2A8F90`
* **Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "user_id": "c7b8a910-1234-5678-9abc-def012345678",
    "username": "Budi Santoso",
    "photo_url": "/static/photos/c7b8a910.jpg",
    "balance": 75000,
    "status": "ACTIVE"
  }
}
```

### 2. Eksekusi Pembayaran (Charge Debit)
* **Endpoint**: `POST /api/v1/device/charge`
* **Headers**: `X-Device-ID`, `X-Device-HMAC`
* **Request Body**:
```json
{
  "idempotency_key": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "rfid_uid": "4B2A8F90",
  "amount": 20000,
  "auth_method": "FINGERPRINT", 
  "timestamp": "2026-11-16T14:00:00Z"
}
```
* **Response (200 OK)**:
```json
{
  "status": "SUCCESS",
  "transaction_id": "tx-88391029",
  "idempotency_key": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "balance_before": 75000,
  "balance_after": 55000,
  "message": "Pembayaran berhasil diproses."
}
```

---

## 7. Persyaratan Perangkat Keras & Lingkungan

### STB Admin (Server Utama)
* **Hardware**: Set-Top Box ARM64 (HG680P / B860H / Amlogic S905X), RAM min. 2GB.
* **OS**: Armbian Linux (Debian/Ubuntu Server LTS).
* **Storage**: SSD External / USB Flash Drive High-Speed (Mounted at `/mnt/data`).
* **Software**: Python 3.11+ (FastAPI) / Node.js, PostgreSQL / SQLite3, Nginx Web Server.

### STB Kasir (Terminal POS)
* **Hardware**: Set-Top Box ARM64 / ARMv7, RAM min. 1GB.
* **OS**: Armbian Linux dengan GUI Ringan (XFCE) atau Kiosk Mode Browser.
* **Perangkat I/O**:
  * Reader RFID USB (Mifare 13.56MHz / PN532 / USB HID Reader).
  * Pemindai Sidik Jari USB (Modul R307/FPM10A via USB-to-TTL Converter atau ZKTeco USB).
  * Monitor Layar (HDMI / VGA Converter).

---
