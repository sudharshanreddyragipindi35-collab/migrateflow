$ErrorActionPreference = "Stop"
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m pip install -e "backend[dev]"
Push-Location frontend
npm ci
Pop-Location
Write-Host "MigrateFlow dependencies installed."
