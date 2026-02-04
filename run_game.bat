@echo off
echo Exporting game data...
python scripts/export_game_data.py

echo.
echo Starting server at http://localhost:8000/
python -m http.server 8000 -d game -b localhost
