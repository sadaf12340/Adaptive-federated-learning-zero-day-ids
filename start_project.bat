@echo off
setlocal
cd /d "%~dp0"
start "AFL IDS Backend" cmd /k "cd backend && py -3.11 -m uvicorn app.main:app --reload"
start "AFL IDS Frontend" cmd /k "cd frontend && npm.cmd run dev"
echo Backend: http://localhost:8000/docs
echo Frontend: http://localhost:5173
