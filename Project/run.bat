@echo off
echo ICC Champions Trophy 2025 Dashboard
if not exist champions_trophy.db (
    echo Setting up database...
    python init_db.py
)
echo Starting server at http://localhost:5000
python app.py
pause
