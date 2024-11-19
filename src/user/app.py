import os
from flask import Flask, request, make_response, jsonify
import requests
import time

app = Flask(__name__)

# DB Manager URL
DBM_URL = os.getenv('DBM_URL', 'http://db-manager:5000')
# Funzione per inviare i dati al db-manager
def save_to_db(username, password):
    payload = {'username': username, 'password': password}
    try:
        response = requests.post(f'{DBM_URL}/register', json=payload)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to DB manager: {e}")
        return False


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # Ottieni i dati JSON dalla richiesta

    # Verifica se i dati di input sono validi
    if not data or 'username' not in data or 'password' not in data:
        return make_response('Invalid input\n', 400)  # HTTP 400 BAD REQUEST
    
    # TODO: controllare se l'utente esiste già: attualmente nel databse posso creare due utenti con lo stesso username

    # Salva l'utente nel database

    response = requests.post(DBM_URL + "/register", json=data) ## WEI++AWDAWDAWDKJAWNFKAWNFl
    if response.status_code == 200:
        return jsonify({"message": "User registered successfully"}), 200


    else:
        return jsonify({"message": "User NOT registered successfully"}), 500

   
    
@app.route('/get_user_from_name', methods=['POST'])
def get_user_from_name():
    data = request.get_json()  # Ottieni i dati JSON dalla richiesta

    # Verifica se i dati di input sono validi
    if not data or 'username' not in data:
        return make_response('Invalid input\n', 400)  # HTTP 400 BAD REQUEST

    username = data['username']
    try:
        x = requests.post(DBM_URL + '/get_user_from_name', json=data)
        x.raise_for_status()
        return x.json()
    except ConnectionError:
        return make_response('DB Manager service is down\n', 500)
    except requests.HTTPError:
        return make_response(x.content, x.status_code)

if __name__ == '__main__':
    app.run(debug=True)
