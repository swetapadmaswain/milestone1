"""
Simple script to start both backend and frontend services.
Usage: python start_services.py
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 3000
BACKEND_DIR = Path("backend")
FRONTEND_DIR = Path("frontend")

def check_dependencies():
    """Check if required dependencies are installed."""
    print("[INFO] Checking dependencies...")
    
    # Check Python
    try:
        result = subprocess.run(["python", "--version"], capture_output=True, text=True)
        print(f"[OK] Python: {result.stdout.strip()}")
    except FileNotFoundError:
        print("[ERROR] Python is not installed or not in PATH")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"[OK] Node.js: {result.stdout.strip()}")
    except FileNotFoundError:
        print("[ERROR] Node.js is not installed or not in PATH")
        return False
    
    return True

def setup_backend():
    """Setup backend virtual environment and dependencies."""
    print("\n[SETUP] Setting up backend...")
    
    venv_path = BACKEND_DIR / "venv"
    
    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print("   Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    
    # Determine pip path
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:  # Unix/Mac
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Install dependencies
    print("   Installing dependencies...")
    subprocess.run([str(pip_path), "install", "-q", "-r", "requirements.txt"], 
                    cwd=BACKEND_DIR, check=True)
    
    return str(python_path)

def setup_frontend():
    """Setup frontend dependencies."""
    print("\n[SETUP] Setting up frontend...")
    
    node_modules = FRONTEND_DIR / "node_modules"
    
    if not node_modules.exists():
        print("   Installing npm dependencies...")
        # Use npm.cmd on Windows to avoid PowerShell execution policy issues
        npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
        subprocess.run([npm_cmd, "install"], cwd=FRONTEND_DIR, check=True, shell=True)
    else:
        print("   Dependencies already installed")

def start_services():
    """Start both backend and frontend services."""
    print("\n[START] Starting services...\n")
    
    processes = []
    
    try:
        # Start Backend
        print("[BACKEND] Starting Backend (FastAPI)...")
        backend_env = os.environ.copy()
        backend_env["PYTHONPATH"] = str(BACKEND_DIR.absolute())
        
        # Determine Python path
        venv_path = BACKEND_DIR / "venv"
        if os.name == 'nt':
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            python_path = venv_path / "bin" / "python"
        
        backend_proc = subprocess.Popen(
            [str(python_path), "-m", "uvicorn", "app.main:app", 
             "--host", "0.0.0.0", "--port", str(BACKEND_PORT), "--reload"],
            cwd=BACKEND_DIR,
            env=backend_env,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        processes.append(("Backend", backend_proc))
        print(f"   [OK] Backend started on http://localhost:{BACKEND_PORT}")
        
        # Wait a bit for backend to initialize
        time.sleep(3)
        
        # Start Frontend
        print("\n[FRONTEND] Starting Frontend (Next.js)...")
        frontend_env = os.environ.copy()
        frontend_env["NEXT_PUBLIC_API_URL"] = f"http://localhost:{BACKEND_PORT}"
        
        # Use npm.cmd on Windows to avoid PowerShell execution policy issues
        npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
        frontend_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=FRONTEND_DIR,
            env=frontend_env,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
            shell=True
        )
        processes.append(("Frontend", frontend_proc))
        print(f"   [OK] Frontend started on http://localhost:{FRONTEND_PORT}")
        
        # Print URLs
        print("\n" + "="*60)
        print("*** Services are running! ***")
        print("="*60)
        print(f"  Backend API:  http://localhost:{BACKEND_PORT}")
        print(f"  API Docs:     http://localhost:{BACKEND_PORT}/docs")
        print(f"  Frontend App: http://localhost:{FRONTEND_PORT}")
        print("="*60)
        print("\nPress Ctrl+C to stop both services\n")
        
        # Wait for interrupt
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"[WARN] {name} process exited with code {proc.returncode}")
                    return
                    
    except KeyboardInterrupt:
        print("\n\n[STOP] Stopping services...")
    finally:
        # Cleanup
        for name, proc in processes:
            print(f"   Stopping {name}...")
            try:
                if os.name == 'nt':
                    proc.terminate()
                else:
                    proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        
        print("\n[DONE] All services stopped")

def main():
    """Main entry point."""
    print("DineSmart - Full Stack Application Launcher\n")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup
    try:
        setup_backend()
        setup_frontend()
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)
    
    # Start services
    start_services()

if __name__ == "__main__":
    main()
