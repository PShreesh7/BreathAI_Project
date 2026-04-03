<#
setup_and_run.ps1
One-click PowerShell setup: creates virtualenv, installs dependencies,
creates .env from template (if missing), and starts the backend server

Usage:
  - Run once to prepare and start the server:
      .\setup_and_run.ps1

  - Skip dependency installation (if already installed):
      .\setup_and_run.ps1 -SkipInstall

Notes:
  - This script will NOT commit or push git changes.
  - Edit `.env` and `backend/firebase-key.json` manually to add secrets.
#>

[param(
    [switch]$SkipInstall
)]

Set-StrictMode -Version Latest
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Repository root: $root"

# ensure we are in repo root
Set-Location -Path $root

# allow local script execution for this session
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

# create venv if missing
if (-not (Test-Path .\venv)) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists."
}

# install/upgrade pip inside venv
Write-Host "Upgrading pip in venv..."
Start-Process -FilePath "" -NoNewWindow -ErrorAction SilentlyContinue
& .\venv\Scripts\python.exe -m pip install --upgrade pip

if (-not $SkipInstall) {
    if (Test-Path "requirements.txt") {
        Write-Host "Installing dependencies from requirements.txt..."
        & .\venv\Scripts\python.exe -m pip install -r requirements.txt
    } else {
        Write-Host "requirements.txt not found, installing core dependencies..."
        & .\venv\Scripts\python.exe -m pip install pandas numpy scikit-learn flask firebase-admin requests python-dotenv py-algorand-sdk joblib
    }
} else {
    Write-Host "Skipping dependency installation (SkipInstall set)."
}

# create .env from template if missing
if (-not (Test-Path ".env") -and (Test-Path ".env.template")) {
    Copy-Item .env.template .env -Force
    Write-Host ".env created from .env.template — edit .env to add secrets (Pinata / Algorand)."
}

if (-not (Test-Path ".\backend\firebase-key.json")) {
    Write-Warning "backend\firebase-key.json not found — Firebase features will be disabled until you add the service account file."
} else {
    Write-Host "Firebase service account detected."
}

Write-Host "Starting backend server in a new PowerShell window..."
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit","-Command","Set-Location -Path '$root'; .\venv\Scripts\python.exe .\backend\app.py"

Write-Host "If the server does not start, open a terminal and run:"
Write-Host "  cd `"$root\backend`"" -ForegroundColor Yellow
Write-Host "  ..\venv\Scripts\python.exe app.py" -ForegroundColor Yellow

Write-Host "Open http://127.0.0.1:5000/ in your browser after the server starts."
