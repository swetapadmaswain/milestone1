@echo off
chcp 65001 >nul
echo 🚀 Starting DineSmart Full Stack Application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    exit /b 1
)

echo ✅ Python and Node.js are available
echo.

REM Create virtual environment if it doesn't exist
if not exist "backend\venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv backend\venv
)

REM Activate virtual environment and install dependencies
echo 📦 Installing backend dependencies...
call backend\venv\Scripts\activate.bat
pip install -q -r backend\requirements.txt

REM Check if frontend node_modules exists
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo 🎯 Starting services...
echo.

REM Start Backend in a new window
echo 🐍 Starting Backend (FastAPI) on http://localhost:8000
start "DineSmart Backend" cmd /k "cd backend && call ..\venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to initialize
timeout /t 3 /nobreak >nul

REM Start Frontend in a new window
echo ⚛️  Starting Frontend (Next.js) on http://localhost:3000
start "DineSmart Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ✨ Both services are starting up!
echo.
echo 📍 Backend API:  http://localhost:8000
echo 📍 Frontend App: http://localhost:3000
echo 📍 API Docs:     http://localhost:8000/docs
echo.
echo Press any key to stop both services...
pause >nul

REM Stop services
echo.
echo 🛑 Stopping services...
taskkill /FI "WINDOWTITLE eq DineSmart Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq DineSmart Frontend*" /F >nul 2>&1
echo ✅ Services stopped
echo.
pause
