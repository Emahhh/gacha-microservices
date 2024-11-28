import os
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from auth_utils import decode_token, role_required

app = Flask(__name__)

# URLS dei microservizi
GATCHA_URL = os.getenv('GATCHA_URL')
MARKET_URL = os.getenv('MARKET_URL')



# Connessione ai database dei microservizi (modificato per usare i container MongoDB tramite nome servizio)
client_user = MongoClient("db-user", 27017, maxPoolSize=50)
db_user= client_user["db_users"]

def userExists(username):
    return db_user.collection.find_one({"username": username}) is not None

# Endpoint per registrare un utente passando i dati nel body della richiesta
@app.route('/init-user', methods=['POST'])
def init_user():
    try:
        payload = request.json  # Ottieni i dati JSON dal corpo della richiesta 
        if payload is None:
            return make_response(jsonify({"error": "No data provided"}), 400)
        
        if 'username' not in payload:
            return make_response(jsonify({"error": "Username is required"}), 400)
        
        if userExists(payload.get("username")):
            return make_response(jsonify({"error": "User already exists"}), 400)

        user = {
            "username": payload.get("username"),
            "balance": 0,
            "collection": [],
            "transactions": []
        }
        db_user.collection.insert_one(user)
        return make_response(jsonify({"message": "User initialized successfully"}), 201)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 502)

# Endpoint per ottenere un utente passando il nome utente nel body della richiesta
@app.route('/get_user_from_name', methods=['GET'])
def get_user_from_name():
    data = request.get_json()  # Ottieni i dati JSON dalla richiesta
    username = data['username']
    try:
        res = []
        all = list(db_user.collection.find({'username': username}))
        for element in all:
            res.append({
                'username': element["username"],
                'balance': element["balance"],
                'collection': element["collection"],
                'transactions': element["transactions"]
            })
        return make_response(jsonify(res), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# endpoint to increase the balance of a user
@app.route('/increase_balance', methods=['POST'])
@role_required('admin')
def increase_balance():
    token_payload, error = decode_token()
    if error:
        return make_response(jsonify({"error": error}), 401)
    
    data = request.json
    username = data.get("username")
    amount = data.get("amount")
    try:
        user = db_user.collection.find_one({"username": username})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        db_user.collection.update_one({"username": username}, {"$inc": {"balance": amount}})
        return make_response(jsonify({"message": "Balance updated successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
    

# Endpoint per verificare la connessione al database
@app.route('/checkconnection', methods=['GET'])
def check_connection():
    try:
        # Esegui un ping al database per verificare la connessione
        client_user.admin.command('ping')
        return make_response(jsonify({"message": "Connection to db-gatcha is successful!"}), 200)
    except ServerSelectionTimeoutError:
        return make_response(jsonify({"error": "Failed to connect to db-gatcha"}), 500)
    
# Endpoint per recuperare tutti i log (da un database gatcha)
@app.route('/getAll', methods=['GET'])
def get_all_logs():
    try:
        res = []
        all = list(db_user.collection.find({}))
        for element in all:
            res.append({
                'username': element["username"],
                'balance': element["balance"],
                'collection': element["collection"],
                'transactions': element["transactions"]})
        return make_response(jsonify(res), 200)
    except Exception as e:
        print("DEBUG: Error fetching logs:", str(e))
        return make_response(str(e), 500)
