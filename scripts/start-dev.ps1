# PowerShell helper to create venv, install deps and show commands to run the app/UI
# Run this from the project root in PowerShell (Windows)

$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

Write-Host "Activate the virtual environment and install dependencies:"
Write-Host "  .\$venvPath\Scripts\Activate.ps1"
Write-Host "  pip install -r requirements.txt"
Write-Host "(optional) pip install -r requirements-dev.txt"
Write-Host "Initialize DB:"
Write-Host "  python -c \"from db import init_db; init_db()\""
Write-Host "Run the API (in one terminal):"
Write-Host "  python app.py"
Write-Host "Run the UI (in another terminal):"
Write-Host "  python ui.py"
