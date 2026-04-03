# BreathAI — Demo Script for Judges

Quick one-page demo steps to show the BreathAI end-to-end pipeline (Breath device → AI prediction → IPFS → Algorand ASA).

1) Prepare (one-time)
   - Ensure you have the project and dependencies installed. The provided helper script sets up the environment:

     ```powershell
     cd D:\BreathAI_Project
     .\setup_and_run.ps1
     ```

   - Edit `.env` (created from `.env.template`) to add your `PINATA_API_KEY`, `PINATA_API_SECRET`, `ALGOD_TOKEN`, and `CREATOR_MNEMONIC` if you want the full IPFS + ASA demo.
   - Place your Firebase service account JSON at `backend/firebase-key.json` and set the `databaseURL` inside `backend/app.py` to enable Firebase logging.

2) Start demo (fast path / recommended for judges)
   - Open the UI: http://127.0.0.1:5000/
   - Enter sample sensor values and placeholder patient/doctor wallets (you can use TestNet wallets).
   - Click **Run Full Pipeline**. Watch the result panel for:
     - `prediction` (ML result)
     - `record_id` (UUID)
     - `ipfs_cid` (clickable via `https://ipfs.io/ipfs/<CID>`)
     - `asset_id` and `asset_txid` (Algorand ASA minted)

3) Wallet opt-in & share (show on browser)
   - Install AlgoSigner in your browser (for the audience demo) and show the **Patient Opt-in** and **Doctor Opt-in** buttons.
   - Demonstrate clicking **Share access on-chain** (server-side transfer) to assign the asset to the doctor — show the returned txid.

4) Fallback (if no Algorand keys available)
   - To avoid on-chain steps during the judging demo, you may run only `/predict` to show fast ML results.
   - Explain that `process-v1` mints an ASA with metadata containing the IPFS CID and transfers tokens to patient and doctor when configured.

5) Where to look
   - IPFS record: https://ipfs.io/ipfs/<CID>
   - Algorand asset: search Asset ID on TestNet explorer (https://testnet.explorer.algorand.io)
   - Firebase: Realtime Database paths `/medical_records/<record_id>` and `/access_control/<record_id>`

6) Talking points (30–60 seconds)
   - "We capture breath sensor readings, run a lightweight ML model to predict a health label, and create a verifiable medical record stored on IPFS.
   - We mint an Algorand ASA per record and embed the IPFS CID in the asset metadata — this gives an immutable, tokenized proof of the medical record.
   - The patient receives the token, and access can be shared to the doctor on-chain; we also track metadata and access in Firebase for indexing.
   - We implemented rollback so if ASA creation fails after IPFS pin, the CID is unpinned to avoid orphaned content."

7) Quick troubleshooting
   - If server doesn't start, run:
     ```powershell
     cd D:\BreathAI_Project\backend
     ..\venv\Scripts\python.exe app.py
     ```
   - If scikit-learn wheels mismatch the Python version, the app falls back to a dummy predictor — install a compatible Python runtime or rebuild the venv with Python 3.11 for full model accuracy.

Contact: Developer will be available to assist live during the demo.
