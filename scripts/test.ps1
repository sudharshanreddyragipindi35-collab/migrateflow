$ErrorActionPreference = "Stop"
Push-Location backend
python -m ruff check app tests
python -m mypy app
python -m pytest -q
Pop-Location
Push-Location frontend
npm run lint
npm test
npm run build
Pop-Location
python scripts/evaluate.py
