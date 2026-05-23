@echo off
chcp 65001 >nul
title RIADAH ERP v0 - التشغيل المحلي

echo ═══════════════════════════════════════════════════════
echo        RIADAH ERP v0 - Local Development Setup
echo ═══════════════════════════════════════════════════════
echo.

:: ── Check Python ──
echo [1/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed. Install Python 3.10+ from python.org
    pause
    exit /b 1
)
python --version
echo OK: Python found
echo.

:: ── Check Node.js ──
echo [2/7] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed. Install Node.js 18+ from nodejs.org
    pause
    exit /b 1
)
node --version
echo OK: Node.js found
echo.

:: ── Backend Setup ──
echo [3/7] Setting up Backend...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing requirements...
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo OK: Backend ready
echo.

:: ── Database Setup ──
echo [4/7] Setting up Database...
python manage.py migrate --noinput
echo OK: Database ready
echo.

:: ── Create Admin User ──
echo [5/7] Creating Admin User...
python manage.py shell -c "from users.models import User; User.objects.filter(role='owner').exists() or User.objects.create_superuser(username='admin', email='admin@riadah.com', password='Admin@123', role='owner', phone='+966500000000', full_name='System Admin')"
echo OK: Admin user ready
echo.

:: ── Frontend Setup ──
echo [6/7] Setting up Frontend...
cd ..\frontend
if not exist "node_modules" (
    echo Installing npm packages...
    npm install
)
echo OK: Frontend ready
echo.

:: ── Start Servers ──
echo [7/7] Starting Servers...
echo.
echo ═══════════════════════════════════════════════════════
echo           Setup Complete!
echo ═══════════════════════════════════════════════════════
echo.
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://localhost:5173
echo   Admin:    http://127.0.0.1:8000/admin
echo.
echo   Username: admin
echo   Password: Admin@123
echo.
echo ═══════════════════════════════════════════════════════
echo.

:: Start Backend in new window
cd ..\backend
start "RIADAH Backend" cmd /k "call venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:8000"

:: Start Frontend in new window
cd ..\frontend
start "RIADAH Frontend" cmd /k "npm run dev"

echo.
echo Backend and Frontend are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
