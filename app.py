import requests

rfid_input = input("Tap ur card: ")

def show_information(user):
    print(f'nama : {users['username']} | saldo : {wallets['balance']}')

if rfid_input:
    url = f'url{rfid_input}'
    headers = {}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user = response.json()
        show_information(user)

        nominal_transaction = int(input(' '))
        saldo = user{wallets['balance']}
        
        if saldo < nominal_transaction:
            print('Please top up ur wallet')
        else:
            charge_url = url
            payload =  {}

            update_saldo = requests.post(charge_url, json=payload, headers=headers)

            if update_saldo.status_code == 200:
                data_sukses = update_saldo.json()
                print(f"Pembayaran Berhasil! Sisa Saldo: Rp {data_sukses['wallets']}") 
            else: print("Transaksi Gagal Diproses Server!")
    else:
        print('Unknown user')