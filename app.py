import requests

rfid_input = input("Tap ur card: ")

def show_information(user_data):
    print(f'nama : {user['nama']} | saldo : {user['balance']}')

if rfid_input:
    url = f'url{rfid_input}'
    headers = {}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user = response.json()
        show_informmation(user)

        nominal_transaction = int(input(' '))
        
        if saldo < nominal_transaction:
            print('Please top up ur wallet')
        else:
            charge_url = url
            payload =  {}

            update_saldo = requests.post(charge_url, json=payload, headers=headers)

            if update_saldo.status_code == 200:
                data_sukses = res_charge.json()
                print(f"Pembayaran Berhasil! Sisa Saldo: Rp {data_sukses['balance_after']}") 
            else: print("Transaksi Gagal Diproses Server!")
    else:
        print('Unknown user')