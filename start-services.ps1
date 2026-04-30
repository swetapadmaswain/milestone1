# PowerShell script to start both backend and frontend services
# Usage: .\start-services.ps1

Write-Host "🚀 Starting DineSmart Full Stack Application..." -ForegroundColor Green
Write-Host ""

# Function to check if a command exists
function Test-CommandExists {
    param($Command)
    $exists = $false
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        $exists = $true
    } catch {
        $exists = $false
    }
    return $exists
}

# Check Python
if (-not (Test-CommandExists "python")) {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check Node.js
if (-not (Test-CommandExists "node")) {
    Write-Host "❌ Node.js is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python and Node.js are available" -ForegroundColor Green
Write-Host ""

# Create virtual environment if it doesn't exist
if (-not (Test-Path "backend\venv")) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv backend\venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& backend\venv\Scripts\Activate.ps1

# Install backend dependencies
Write-Host "📦 Installing backend dependencies..." -ForegroundColor Yellow
pip install -q -r backend\requirements.txt

# Check if frontend node_modules exists
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

Write-Host ""
Write-Host "🎯 Starting services..." -ForegroundColor Green
Write-Host ""

# Start Backend in new window
Write-Host "🐍 Starting Backend (FastAPI) on http://localhost:8000" -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\backend
    & ..\venv\Scripts\Activate.ps1
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start Frontend in new window
Write-Host "⚛️  Starting Frontend (Next.js) on http://localhost:3000" -ForegroundColor Cyan
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm run dev
}

Write-Host ""
Write-Host "✨ Both services are starting up!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Backend API:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "📍 Frontend App: http://localhost:3000" -ForegroundColor Yellow
Write-Host "📍 API Docs:     http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop both services" -ForegroundColor Magenta
Write-Host ""

# Monitor jobs
try {
    while ($true) {
        $backendStatus = Receive-Job -Job $backendJob -Keep
        $frontendStatus = Receive-Job -Job $frontendJob -Keep
        
        if ($backendStatus) {
            Write-Host "[BACKEND] $backendStatus" -ForegroundColor Gray
        }
        if ($frontendStatus) {
            Write-Host "[FRONTEND] $frontendStatus" -ForegroundColor Gray
        }
        
        Start-Sleep -Seconds 1
    }
} finally {
    # Cleanup
    Write-Host ""
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Write-Host "✅ Services stopped" -ForegroundColor Green
}
