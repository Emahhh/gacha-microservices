import os
import uuid
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import requests
from auth_utils import role_required, get_userID_from_jwt
from datetime import datetime
import json
import logging

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, instance_relative_config=True)

# URLS dei microservizi
GATCHA_URL = os.getenv('GATCHA_URL')
MARKET_URL = os.getenv('MARKET_URL')

# Connessione ai database dei microservizi (modificato per usare i container MongoDB tramite nome servizio)
client_user = MongoClient("db-user", 27017, maxPoolSize=50)
db_user= client_user["db_users"]

UNIT_TEST_MODE = os.getenv('UNIT_TEST_MODE', 'False') == 'True'

if UNIT_TEST_MODE:
    app.logger.info("Running in unit test mode!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    from mocks import start_mocking_http_requests, no_op_decorator, fake_get_userID_from_jwt # mocks.py in the same folder
    start_mocking_http_requests() # after calling this function, the requests are now mocked: they answer with the mocks defined inside app.py
    role_required = no_op_decorator # override the role_required decorator to do nothing
    get_userID_from_jwt = fake_get_userID_from_jwt # override the get_userID_from_jwt function to return a predefined user ID
    test_user = {
        "balance": 470,
        "collection": [
            "9b307cd40cb74f6790274111304d11e4",
            "274d711d776c41bf81a63285c07fd519",
            "4fa275d4ecd44f20a5f56543664e5b8f"
        ],
        "transactions": [
            {
                "amount": 500,
                "timestamp": "Fri, 06 Dec 2024 10:55:18 GMT",
                "type": "increase"
            },
            {
                "amount": 10,
                "timestamp": "Fri, 06 Dec 2024 10:55:18 GMT",
                "type": "decrease"
            },
            {
                "amount": 10,
                "timestamp": "Fri, 06 Dec 2024 10:55:18 GMT",
                "type": "decrease"
            },
            {
                "amount": 10,
                "timestamp": "Fri, 06 Dec 2024 10:55:18 GMT",
                "type": "decrease"
            }
        ],
        "userID": "12d558b3-0f50-42cf-b28b-7c692e684317"
    }

    # Insert the test user into the database
    try:
        if not db_user.collection.find_one({"userID": test_user["userID"]}):
            db_user.collection.insert_one(test_user)
            logging.info("Inserted test user into the database")
    except ServerSelectionTimeoutError:
        print("Could not connect to MongoDB server.")
else :
    app.logger.info("Running in normal mode!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    

def userExists(userID):
    return db_user.collection.find_one({"userID": userID}) is not None

# Endpoint per registrare un utente passando i dati nel body della richiesta
# questo endpoint dovrebbe essere chiamabile solo dal microservizio 'auth'
# nessun utente dovrebbe normalmente chiamare questo endpoint
@app.route('/init-user', methods=['POST'])
def init_user():
    try:
        payload = request.json  # Ottieni i dati JSON dal corpo della richiesta 
        if payload is None:
            logger.debug("No data provided in request")
            return make_response(jsonify({"error": "No data provided"}), 400)
        
        logger.debug("Received payload: " + str(payload))
        userID = payload.get("userID")
        if not userID:
            logger.debug("No userID provided in payload")
            return make_response(jsonify({"error": "No userID provided"}), 400)
        
        if userExists(userID):
            logger.debug(f"User with userID {userID} already exists")
            return make_response(jsonify({"error": "User already exists"}), 409)
        
        user = {
            "userID": userID,
            "balance": 0,
            "collection": [],
            "transactions": []
        }
        db_user.collection.insert_one(user)
        logger.debug(f"User with userID {userID} initialized successfully")
        return make_response(jsonify({"message": "User initialized successfully"}), 201)
    except Exception as e:
        logger.error(f"Error initializing user: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 502)
    
@app.route('/delete_user', methods=['POST'])
def delete_user():
    #receive user ID from POST request and delete the user from the database
    data = request.get_json()
    userID = data['userID']
    try:
        db_user.collection.delete_one({"userID": userID})
        return make_response(jsonify({"message": "User deleted successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
    

# Endpoint per ottenere un utente passando il nome utente nel body della richiesta
@app.route('/users/<userID>', methods=['GET'])
@role_required('adminUser')
def get_user_by_id(userID):
    try:
        user = db_user.collection.find_one({'userID': userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        user_data = {
            'userID': user["userID"],
            'balance': user["balance"],
            'collection': user["collection"],
            'transactions': user["transactions"]
        }
        return make_response(jsonify(user_data), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# endpoint to get the balance of a user
@app.route('/balance', methods=['GET'])
def get_balance():
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": "Error decoding token"}), 401)
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        return make_response(jsonify({"balance": user["balance"]}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# endpoint to increase the balance of a user
@app.route('/increase_balance', methods=['POST'])
def increase_balance():
    data = request.json
    userID = data.get("userID")
    amount = data.get("amount")
    try:
        logger.debug("Searching for user with userID: " + str(userID))
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        db_user.collection.update_one({"userID": userID}, {"$inc": {"balance": amount}})
        transaction = {
            "amount": amount,
            "type": "increase",
            "timestamp": datetime.now()
        }
        db_user.collection.update_one({"userID": userID}, {"$push": {"transactions": transaction}})
        return make_response(jsonify({"message": "Balance updated successfully"}), 200)
    except Exception as e:
        logger.warning("Error increasing balance: " + str(e))
        return make_response(jsonify({"error": str(e)}), 500)
    
# endpoint to decrease the balance of a user
# must be usable only by roll and after an auction win
@app.route('/decrease_balance', methods=['POST'])
def decrease_balance():  
    data = request.json
    userID = data.get("userID")
    amount = data.get("amount")
    try:
        logger.debug(f"Attempting to decrease balance for userID: {userID} by amount: {amount}")
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            logger.debug(f"User with userID {userID} not found")
            return make_response(jsonify({"error": "User not found"}), 404)
        if user["balance"] < amount:
            logger.debug(f"Insufficient funds for userID {userID}. Current balance: {user['balance']}, requested amount: {amount}")
            return make_response(jsonify({"error": "Insufficient funds"}), 400)
        db_user.collection.update_one({"userID": userID}, {"$inc": {"balance": -amount}})
        transaction = {
            "amount": amount,
            "type": "decrease",
            "timestamp": datetime.now()
        }
        db_user.collection.update_one({"userID": userID}, {"$push": {"transactions": transaction}})
        logger.debug(f"Balance decreased successfully for userID {userID}. New balance: {user['balance'] - amount}")
        return make_response(jsonify({"message": "Balance updated successfully"}), 200)
    except Exception as e:
        logger.error(f"Error decreasing balance for userID {userID}: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 500)
    
# endpoint to get the full list of transactions of a user
@app.route('/transactions', methods=['GET'])
def get_transactions():
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": "Error decoding token"}), 401)
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        return make_response(jsonify(user["transactions"]), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


# endpoint per fare i refund di una bid
@app.route('/refund', methods=['POST'])
def refund():
    data = request.json
    userID = data.get("userID")
    amount = data.get("amount")
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        db_user.collection.update_one({"userID": userID}, {"$inc": {"balance": amount}})
        transaction = {
            "amount": amount,
            "type": "refund",
            "timestamp": datetime.now()
        }
        db_user.collection.update_one({"userID": userID}, {"$push": {"transactions": transaction}})
        return make_response(jsonify({"message": "Refund successful"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Endpoint per aggiungere un gatcha alla collezione di un utente
@app.route('/add_gatcha', methods=['POST'])
def add_gatcha():
    data = request.json
    userID = data.get("userID")
    gatcha = data.get("gatcha_ID")
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        db_user.collection.update_one({"userID": userID}, {"$push": {"collection": gatcha}})
        return make_response(jsonify({"message": "Gatcha added successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
    
# Endpoint per eliminare un gatcha dalla collezione di un utente
@app.route('/remove_gatcha', methods=['POST'])
def remove_gatcha():
    data = request.json
    userID = data.get("userID")
    gatcha = data.get("gatcha_ID")
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        if gatcha not in user["collection"]:
            return make_response(jsonify({"error": "Gatcha not found in collection"}), 404)
        db_user.collection.update_one(
            {"userID": userID, "collection": gatcha},
            {"$set": {"collection.$": None}}
        )
        db_user.collection.update_one(
            {"userID": userID},
            {"$pull": {"collection": None}}
        )
        return make_response(jsonify({"message": "Gatcha removed successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Endpoint per restituire la collezione di un utente
@app.route('/collection', methods=['GET'])
def get_collection():
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": "Error decoding token"}), 401)
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        return make_response(jsonify(user["collection"]), 200)
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
                'userID': element["userID"],
                'balance': element["balance"],
                'collection': element["collection"],
                'transactions': element["transactions"]})
        return make_response(jsonify(res), 200)
    except Exception as e:
        print("DEBUG: Error fetching logs:", str(e))
        return make_response(str(e), 500)
