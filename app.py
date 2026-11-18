import requests

rfid_input = input("Tap ur card: ")

def show_information(user_data):
    print(f'nama : {user['nama']} | saldo : {user['balance']}')

if rfid_input:
    url = f'url{rfid_input}'
    response = requests.get(rfid_input)

    if response.status_code == 200:
        user = response.json()
        show_informmation(user)
    else:
        print('Unknown user')

    nominal_transaction = int(input(' '))

    if saldo < nominal_transaction:
        reject_transaction
        print('Please top up ur wallet')
    else:
        update_saldo = requests.post('saldo')