from flask import Flask, request, jsonify, send_from_directory
import joblib
import numpy as np
import os
import json
import uuid
import datetime
import hashlib
import requests
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn

load_dotenv()

# Initialize Firebase
try:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'YOUR_DATABASE_URL'
    })
    firebase_enabled = True
except Exception as e:
    print("Firebase not configured:", e)
    firebase_enabled = False

app = Flask(__name__)

# Algorand configuration
ALGOD_ADDRESS = os.getenv('ALGOD_ADDRESS', 'https://testnet-algorand.api.purestake.io/ps2')
ALGOD_TOKEN = os.getenv('ALGOD_TOKEN', '')
ALGOD_HEADERS = {'X-API-Key': ALGOD_TOKEN} if ALGOD_TOKEN else {}
CREATOR_MNEMONIC = os.getenv('CREATOR_MNEMONIC', '')

PINATA_API_KEY = os.getenv('PINATA_API_KEY', '')
PINATA_API_SECRET = os.getenv('PINATA_API_SECRET', '')

# Load model
model_path = os.path.join(os.path.dirname(__file__), '../breath_model.pkl')
model = joblib.load(model_path)


def upload_to_pinata(record_json):
    if not PINATA_API_KEY or not PINATA_API_SECRET:
        raise ValueError('Pinata credentials are required in environment variables')
    url = 'https://api.pinata.cloud/pinning/pinJSONToIPFS'
    headers = {
        'Content-Type': 'application/json',
        'pinata_api_key': PINATA_API_KEY,
        'pinata_secret_api_key': PINATA_API_SECRET
    }
    payload = {
        'pinataOptions': {'cidVersion': 1},
        'pinataContent': record_json
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get('IpfsHash')


def unpin_from_pinata(ipfs_hash):
    if not PINATA_API_KEY or not PINATA_API_SECRET:
        raise ValueError('Pinata credentials are required in environment variables')
    url = f'https://api.pinata.cloud/pinning/unpin/{ipfs_hash}'
    headers = {
        'pinata_api_key': PINATA_API_KEY,
        'pinata_secret_api_key': PINATA_API_SECRET
    }
    response = requests.delete(url, headers=headers, timeout=30)
    response.raise_for_status()
    return True


def get_algod_client():
    if not ALGOD_TOKEN or not ALGOD_ADDRESS:
        raise ValueError('Algod address/token missing in environment variables')
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS, headers=ALGOD_HEADERS)


def get_account_keys_from_mnemonic():
    if not CREATOR_MNEMONIC:
        raise ValueError('Creator mnemonic is required')
    private_key = mnemonic.to_private_key(CREATOR_MNEMONIC)
    public_addr = account.address_from_private_key(private_key)
    return public_addr, private_key


def create_algorand_asa(name, unit_name, metadata_cid, metadata_url=None, total=2):
    client = get_algod_client()
    creator_addr, creator_pk = get_account_keys_from_mnemonic()
    suggested_params = client.suggested_params()

    if isinstance(metadata_cid, str):
        metadata_b = hashlib.sha256(metadata_cid.encode('utf-8')).digest()
    else:
        metadata_b = hashlib.sha256(str(metadata_cid).encode('utf-8')).digest()

    asset_metadata_url = metadata_url or f'https://ipfs.io/ipfs/{metadata_cid}'

    txn = AssetConfigTxn(
        sender=creator_addr,
        sp=suggested_params,
        total=total,
        default_frozen=False,
        unit_name=unit_name,
        asset_name=name,
        manager=creator_addr,
        reserve=creator_addr,
        freeze=creator_addr,
        clawback=creator_addr,
        url=asset_metadata_url,
        metadata_hash=metadata_b[:32]
    )

    signed_txn = txn.sign(creator_pk)
    txid = client.send_transaction(signed_txn)
    confirmed_txn = transaction.wait_for_confirmation(client, txid, 4)
    asset_id = confirmed_txn['asset-index']
    return asset_id, txid


def algo_opt_in(account_address, asset_id):
    client = get_algod_client()
    _, creator_pk = get_account_keys_from_mnemonic()
    params = client.suggested_params()

    opt_txn = AssetTransferTxn(
        sender=account_address,
        sp=params,
        receiver=account_address,
        amt=0,
        index=asset_id
    )
    # client can't sign for external address; this path assumes contract account control not implemented
    raise NotImplementedError('Opt-in for non-creator wallet must be done client-side with wallet key')


def transfer_asset(from_addr, from_pk, to_addr, asset_id, amount=1):
    client = get_algod_client()
    params = client.suggested_params()
    txn = AssetTransferTxn(sender=from_addr, sp=params, receiver=to_addr, amt=amount, index=asset_id)
    signed = txn.sign(from_pk)
    txid = client.send_transaction(signed)
    algod.wait_for_confirmation(client, txid, 4)
    return txid


@app.route('/')
def home():
    return send_from_directory('../frontend', 'index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    
    features = [
        data['mq3'],
        data['mq135'],
        data['mq138'],
        data['temp'],
        data['humidity'],
        data['pressure'],
        data['spo2'],
        data['hr']
    ]
    
    prediction = model.predict([features])[0]
    
    # Save to Firebase if enabled
    if firebase_enabled:
        ref = db.reference('predictions')
        ref.push({
            'features': features,
            'prediction': prediction,
            'timestamp': {'.sv': 'timestamp'}
        })
    
    return jsonify({'prediction': prediction})


@app.route('/pinata-unpin', methods=['POST'])
def pinata_unpin():
    data = request.json or {}
    ipfs_hash = data.get('ipfs_hash')
    if not ipfs_hash:
        return jsonify({'error': 'ipfs_hash is required'}), 400
    try:
        unpin_from_pinata(ipfs_hash)
        return jsonify({'status': 'unpinned', 'ipfs_hash': ipfs_hash})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/algod-params', methods=['GET'])
def algod_params():
    try:
        client = get_algod_client()
        params = client.suggested_params()
        return jsonify({
            'fee': params['fee'],
            'firstRound': params['first-round'],
            'lastRound': params['last-round'],
            'genesisID': params['genesis-id'],
            'genesisHash': params['genesis-hash'],
            'consensusVersion': params['consensus-version']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/share-access', methods=['POST'])
def share_access():
    data = request.json or {}
    asset_id = data.get('asset_id')
    target_wallet = data.get('doctor_wallet')
    amount = int(data.get('amount', 1))

    if not asset_id or not target_wallet:
        return jsonify({'error': 'asset_id and doctor_wallet are required'}), 400

    try:
        creator_addr, creator_pk = get_account_keys_from_mnemonic()
        txid = transfer_asset(creator_addr, creator_pk, target_wallet, int(asset_id), amount)
        return jsonify({'status': 'shared', 'txid': txid, 'asset_id': asset_id, 'doctor_wallet': target_wallet})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process-v1', methods=['POST'])
def process_v1():
    data = request.json or {}
    required = ['mq3','mq135','mq138','temp','humidity','pressure','spo2','hr','patient_wallet','doctor_wallet','patient_id','doctor_id']
    missing = [k for k in required if k not in data or data[k] in [None, '']]
    if missing:
        return jsonify({'error': 'missing_fields', 'fields': missing}), 400

    features = [
        float(data['mq3']),
        float(data['mq135']),
        float(data['mq138']),
        float(data['temp']),
        float(data['humidity']),
        float(data['pressure']),
        float(data['spo2']),
        int(data['hr'])
    ]

    prediction = model.predict([features])[0]

    record_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat() + 'Z'

    medical_record = {
        'record_id': record_id,
        'patient_id': data['patient_id'],
        'doctor_id': data['doctor_id'],
        'patient_wallet': data['patient_wallet'],
        'doctor_wallet': data['doctor_wallet'],
        'features': {
            'mq3': features[0],
            'mq135': features[1],
            'mq138': features[2],
            'temp': features[3],
            'humidity': features[4],
            'pressure': features[5],
            'spo2': features[6],
            'hr': features[7]
        },
        'prediction': str(prediction),
        'timestamp': timestamp
    }

    ipfs_cid = None
    asset_id = None
    asset_txid = None
    pinata_error = None
    asa_error = None

    try:
        ipfs_cid = upload_to_pinata(medical_record)
    except Exception as e:
        pinata_error = str(e)

    if ipfs_cid:
        try:
            asset_name = f'BreathMedicalRecord-{record_id[:8]}'
            unit_name = 'BMR'
            asset_id, asset_txid = create_algorand_asa(asset_name, unit_name, ipfs_cid, total=2)

            creator_addr, creator_pk = get_account_keys_from_mnemonic()
            transfer_asset(creator_addr, creator_pk, data['patient_wallet'], asset_id, 1)
            transfer_asset(creator_addr, creator_pk, data['doctor_wallet'], asset_id, 1)

        except Exception as e:
            asa_error = str(e)
            # rollback IPFS pin if ASA creation/transfer fails
            try:
                unpin_from_pinata(ipfs_cid)
            except Exception as rollback_error:
                asa_error += f'; rollback pinata failed: {rollback_error}'
            asset_id = None
            asset_txid = None

    if firebase_enabled:
        rec_ref = db.reference('medical_records').child(record_id)
        rec_ref.set({
            'medical_record': medical_record,
            'prediction': prediction,
            'ipfs_cid': ipfs_cid,
            'asset_id': asset_id,
            'asset_txid': asset_txid,
            'doctor_access_shared': True,
            'timestamp': {'.sv': 'timestamp'}
        })

        # store access record
        access_ref = db.reference('access_control').child(record_id)
        access_ref.set({
            'patient_wallet': data['patient_wallet'],
            'doctor_wallet': data['doctor_wallet'],
            'asset_id': asset_id,
            'status': 'stored'
        })

    result = {
        'record_id': record_id,
        'prediction': prediction,
        'ipfs_cid': ipfs_cid,
        'asset_id': asset_id,
        'asset_txid': asset_txid,
        'pinata_error': pinata_error,
        'asa_error': asa_error,
        'note': 'Patient must opt-in with their wallet and doctor access is tracked in Firebase when enabled.'
    }

    status_code = 200 if not pinata_error and not asa_error else 207
    return jsonify(result), status_code


if __name__ == '__main__':
    app.run(debug=True)
