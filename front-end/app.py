import requests

BASE_URL = "[url]"
HEADERS = {"X-Device-ID": "STB-Kasir-01", "X-Device-HMAC": "secret-key-kasir"}

rfid_input = input("Tap ur card: ")

def show_information(user):
    print(f'nama : {user['username']} | saldo : {user['balance']}')

if rfid_input:
    check_url = f"{BASE_URL}/customer-by-card?rfid_uid={rfid_input}"
    response = requests.get(check_url, headers=HEADERS)

    if response.status_code == 200:
        res_json = response.json()
        user = res_json['data']
        show_information(user)

        nominal_transaction = int(input(' '))
        saldo = user{wallets['balance']}
        
        if saldo < nominal_transaction:
            print('Please top up ur wallet')
        else:
            charge_url = url
            payload =  {}

            update_saldo = requests.post(charge_url, json=payload, headers=HEADERS)

            if update_saldo.status_code == 200:
                data_sukses = update_saldo.json()
                print(f"Pembayaran Berhasil! Sisa Saldo: Rp {data_sukses['wallets']}") 
            else: print("Transaksi Gagal Diproses Server!")
    else:
        print('Unknown user')