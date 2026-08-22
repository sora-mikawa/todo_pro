@echo off
cd /d %~dp0

echo Vue サーバーを起動します...
start /min cmd /k "cd /d %~dp0todo_vue && npm run dev"

echo FastAPI サーバーを起動します...
start /min cmd /k "cd /d %~dp0todo_fastapi && call venv\Scripts\activate && uvicorn main:app --reload"

echo ブラウザを自動起動します...
start "" microsoft-edge:http://localhost:5173/

pause