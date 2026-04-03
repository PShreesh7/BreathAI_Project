# BreathAI Project

A machine learning-based health monitoring system that analyzes breath data to predict health conditions.

## Project Structure

- `backend/`: Flask API server
- `frontend/`: Web dashboard
- `model/`: Machine learning model training and saved model
- `data/`: Dataset for training

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```
   pip install pandas numpy scikit-learn flask firebase-admin requests python-dotenv py-algorand-sdk
   ```

3. Train the model:
   ```
   cd model
   python train_model.py
   ```

4. Set up Firebase:
   - Create a Firebase project at https://console.firebase.google.com/
   - Enable Realtime Database
   - Download the service account key as `firebase-key.json` and place it in the `backend/` folder
   - Update the `databaseURL` in `backend/app.py` with your Firebase database URL

5. Run the backend:
   ```
   cd backend
   python app.py
   ```

6. Open the frontend:
   - Open `frontend/index.html` in a web browser
   - Enter sensor data and patient/doctor info and submit to run end-to-end pipeline

## Additional configuration (IPFS + Algorand)

1. Create a `.env` file in the project root with:
   ```ini
   PINATA_API_KEY=your-pinata-api-key
   PINATA_API_SECRET=your-pinata-api-secret
   ALGOD_ADDRESS=https://testnet-algorand.api.purestake.io/ps2
   ALGOD_TOKEN=your-purestake-api-key
   CREATOR_MNEMONIC="your 25-word phrase"
   ```
2. Ensure `firebase-key.json` and `databaseURL` existing in `backend/app.py`.

## API Endpoints

- `GET /`: Home page
- `POST /predict`: Predict health condition from sensor data
- `POST /process-v1`: Full pipeline (prediction -> IPFS -> Algorand ASA + patient token + doctor access record)
- `POST /pinata-unpin`: Unpin a CID from Pinata (for rollback)
- `GET /algod-params`: Returns Algorand transaction parameters for wallet opt-in client use
- `POST /share-access`: Create/transfer ASA share to doctor via creator account

## Features

- Predicts health conditions: alcohol, fever, healthy, high_voc, smoker
- Stores predictions in Firebase Realtime Database
- Web interface for inputting sensor data</content>
<parameter name="filePath">c:\Users\Admin\Downloads\BreathAI_Project\README.md