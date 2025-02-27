from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
import json
import base64
import hashlib
import hmac
import time
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myuser:mypassword@localhost/mydatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), unique=True)
    card_number = db.Column(db.String(16))
    card_expiration = db.Column(db.String(5))
    card_cvv = db.Column(db.String(3))
    balance = db.Column(db.Float)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'))
    amount = db.Column(db.Float)
    timestamp = db.Column(db.Float)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'))
    card_number = db.Column(db.String(16))
    card_expiration = db.Column(db.String(5))
    card_cvv = db.Column(db.String(3))

db.create_all()

@app.route('/create_wallet', methods=['POST'])
def create_wallet():
    response = requests.post('https://api.mastercard.com/card/token', headers={'Authorization': 'Bearer YOUR_MASTERCARD_API_KEY'}, json={'cardholderName': 'John Doe', 'cardNumber': '4242424242424242', 'expirationDate': '2025', 'securityCode': '123'})
    if response.status_code == 200:
        wallet = Wallet(address=response.json()['cardNumber'], card_number=response.json()['cardNumber'], card_expiration=response.json()['expirationDate'], card_cvv=response.json()['securityCode'], balance=0)
        db.session.add(wallet)
        db.session.commit()
        return jsonify({'wallet_id': wallet.id})
    else:
        return jsonify({'error': 'Failed to create wallet'})

@app.route('/create_card', methods=['POST'])
def create_card():
    wallet_id = int(request.json['wallet_id'])
    wallet = Wallet.query.get(wallet_id)
    if wallet:
        response = requests.post('https://api.mastercard.com/card/token', headers={'Authorization': 'Bearer YOUR_MASTERCARD_API_KEY'}, json={'cardholderName': 'John Doe', 'cardNumber': wallet.card_number, 'expirationDate': wallet.card_expiration, 'securityCode': wallet.card_cvv})
        if response.status_code == 200:
            card = Card(wallet_id=wallet_id, card_number=response.json()['cardNumber'], card_expiration=response.json()['expirationDate'], card_cvv=response.json()['securityCode'])
            db.session.add(card)
            db.session.commit()
            return jsonify({'card_id': card.id})
        else:
            return jsonify({'error': 'Failed to create card'})
    else:
        return jsonify({'error': 'Invalid wallet id'})

@app.route('/create_coinbase_wallet', methods=['POST'])
def create_coinbase_wallet():
    response = requests.post('https://api.coinbase.com/v2/accounts', headers={'CB-ACCESS-KEY': 'YOUR_COINBASE_API_KEY', 'CB-ACCESS-SIGN': hmac.new('YOUR_COINBASE_API_SECRET', 'POST /v2/accounts HTTP/1.1', hashlib.sha256).hexdigest(), 'CB-ACCESS-TIMESTAMP': str(int(time.time()))})
    if response.status_code == 200:
        wallet = Wallet(address=response.json()['data']['id'])
        db.session.add(wallet)
        db.session.commit()
        return jsonify({'wallet_id': wallet.id})
    else:
        return jsonify({'error': 'Failed to create wallet'})

@app.route('/exchange', methods=['POST'])
def exchange():
    wallet_id = int(request.json['wallet_id'])
    wallet = Wallet.query.get(wallet_id)
    if wallet:
        response = requests.post('https://api.coinbase.com/v2/prices/BTC-USD/spot', headers={'CB-ACCESS-KEY': 'YOUR_COINBASE_API_KEY', 'CB-ACCESS-SIGN': hmac.new('YOUR_COINBASE_API_SECRET', 'POST /v2/prices/BTC-USD/spot HTTP/1.1', hashlib.sha256).hexdigest(), 'CB-ACCESS-TIMESTAMP': str(int(time.time()))})
        if response.status_code == 200:
            amount = float(request.json['amount'])
            wallet.balance += amount
            db.session.commit()
            return jsonify({'balance': wallet.balance})
        else:
            return jsonify({'error': 'Failed to exchange'})
    else:
        return jsonify({'error': 'Invalid wallet id'})

@app.route('/transfer', methods=['POST'])
def transfer():
    wallet_id = int(request.json['wallet_id'])
    wallet = Wallet.query.get(wallet_id)
    if wallet:
        response = requests.post('https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID/eth/tx/new', headers={'Content-Type': 'application/json'}, json={'from': '0x0000000000000000000000000000000000000000000', 'to': '0x' + request.json['to'], 'value': '0x' + format(int(request.json['amount'] * 10**18, '0x')}, 'gas': '0x5208', 'gasPrice': '0x9184e300'})
        if response.status_code == 200:
            transaction = Transaction(wallet_id=wallet_id, amount=request.json['amount'])
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'transaction_id': transaction.id})
        else:
            return jsonify({'error': 'Failed to transfer'})
    else:
        return jsonify({'error': 'Invalid wallet id'})

@app.route('/login', methods=['POST'])
def login():
    wallet_id = int(request.json['wallet_id'])
    wallet = Wallet.query.get(wallet_id)
    if wallet:
        return jsonify({'wallet_id': wallet_id, 'balance': wallet.balance})
    else:
        return jsonify({'error': 'Invalid wallet id'})

@app.route('/balance', methods=['GET'])
def view_balance():
    wallet_id = int(request.args.get('wallet_id'))
    wallet = Wallet.query.get(wallet_id)
    if wallet:
        return jsonify({'balance': wallet.balance})
    else:
        return jsonify({'error': 'Invalid wallet id'})

@app.route('/transactions', methods=['GET'])
def view_transactions():
    wallet_id = int(request.args.get('wallet_id'))
    wallet = Wallet.query.get(wallet_id)
    if wallet:
        transactions = Transaction.query.filter_by(wallet_id=wallet_id).all()
        return jsonify([{'id': t.id, 'amount': t.amount} for t in transactions])
    else:
        return jsonify({'error': 'Invalid wallet id'})

@app.route('/logout', methods=['POST'])
def logout():
    wallet_id = int(request.json['wallet_id'])
    wallet = Wallet.query.get(wallet_id)
    if wallet:
        db.session.delete(wallet)
        db.session.commit()
        return jsonify({'message': 'Logged out'})
    else:
        return jsonify({'error': 'Invalid wallet id'})

if __name__ == '__main__':
    app.run(debug=True)
