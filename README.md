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
2. STB Kasir membaca UID kartu secara otomatis (tanpa input manual ID oleh kasir).
3. STB Kasir mengirim permintaan kueri `GET /api/v1/device/customer-by-card?uid={UID}` ke STB Admin.
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
1. Setelah autentikasi berhasil (Sidik Jari VALID / PIN Approval VALID), STB Kasir membentuk *payload* transaksi yang berisi: `card_uid`, `amount`, `device_id`, `idempotency_key`, dan `timestamp`.
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

### Tabel `customers`
* `id` (UUID, Primary Key)
* `full_name` (VARCHAR)
* `photo_url` (VARCHAR) - Jalur file foto profil untuk tampilan monitor.
* `status` (ENUM: ACTIVE, SUSPENDED)
* `created_at` (TIMESTAMP)

### Tabel `cards`
* `id` (UUID, Primary Key)
* `customer_id` (UUID, Foreign Key -> `customers.id`)
* `rfid_uid` (VARCHAR, Unique, Indexed) - UID unik dari kartu/wristband.
* `is_active` (BOOLEAN)

### Tabel `biometrics`
* `id` (UUID, Primary Key)
* `customer_id` (UUID, Foreign Key -> `customers.id`)
* `fingerprint_template` (BLOB/TEXT) - Template hash sidik jari.
* `fallback_pin_hash` (VARCHAR) - Hash PIN cadangan.

### Tabel `wallets`
* `id` (UUID, Primary Key)
* `customer_id` (UUID, Foreign Key -> `customers.id`, Unique)
* `balance` (BIGINT) - Saldo disimpan dalam satuan terkecil (integer / tanpa desimal).
* `updated_at` (TIMESTAMP)

### Tabel `transactions`
* `id` (UUID, Primary Key)
* `idempotency_key` (VARCHAR, Unique, Indexed) - UUID unik transaksi dari kasir.
* `device_id` (VARCHAR) - Identitas STB Kasir pengirim.
* `customer_id` (UUID, Foreign Key -> `customers.id`)
* `amount` (BIGINT) - Nominal transaksi.
* `type` (ENUM: DEBIT, TOPUP, REFUND)
* `status` (ENUM: SUCCESS, PENDING_SYNC, REJECTED)
* `created_at` (TIMESTAMP)

---

## 6. Spesifikasi API Utama (Device REST API)

### 1. Kueri Pelanggan via RFID
* **Endpoint**: `GET /api/v1/device/customer-by-card`
* **Headers**: `X-Device-ID`, `X-Device-HMAC`
* **Query Params**: `uid=4B2A8F90`
* **Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "customer_id": "c7b8a910-1234-5678-9abc-def012345678",
    "full_name": "Budi Santoso",
    "photo_url": "/static/photos/c7b8a910.jpg",
    "balance": 75000,
    "card_status": "ACTIVE"
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
  "previous_balance": 75000,
  "current_balance": 55000,
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

## 8. Langkah Pengembangan Selanjutnya (Roadmap)

1. [ ] **Setup Infrastructure**: Install Armbian di STB Admin & STB Kasir, kustomisasi jaringan lokal dengan IP Statis / mDNS (`stb-admin.local`).
2. [ ] **Development Backend**: Implementasi FastAPI REST Engine & Database Migration Script di STB Admin.
3. [ ] **Development Terminal POS App**: Membuat skrip GUI/Web Kiosk di STB Kasir untuk membaca USB RFID & USB Fingerprint secara simultan.
4. [ ] **Testing Mode Kedua**: Pengujian pemutusan koneksi LAN untuk memastikan fungsi pencatatan SQLite lokal & auto-sync berjalan tanpa duplikasi data.
