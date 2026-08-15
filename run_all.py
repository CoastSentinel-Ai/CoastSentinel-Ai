# run_all.py
import subprocess
import sys
import os
import time

def run_project():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")
    models_dir = os.path.join(backend_dir, "models")

    ceri_model_path = os.path.join(models_dir, "ceri_model.pkl")
    ppds_model_path = os.path.join(models_dir, "ppds_model.pkl")

    print("\n==================================================")
    print("🌊 Launching CoastSentinel AI Ecosystem")
    print("==================================================\n")

    # Step 0: Auto-train ML models if missing
    if not (os.path.exists(ceri_model_path) and os.path.exists(ppds_model_path)):
        print("⚙️  ML model files missing in backend/models/. Triggering automated training...")
        train_script = os.path.join(backend_dir, "train_model.py")
        if os.path.exists(train_script):
            train_proc = subprocess.run([sys.executable, "train_model.py"], cwd=backend_dir)
            if train_proc.returncode != 0:
                print("❌ Model training failed. Aborting startup sequence.")
                sys.exit(1)
            print("✅ Models trained and serialized successfully.\n")
        else:
            print("⚠️  Warning: train_model.py not found in backend/. Continuing without pre-training.\n")

    processes = []

    try:
        # 1. Flask Main ML Backend (Port 5000)
        print("📡 Starting Flask ML Engine (http://localhost:5000)...")
        flask_proc = subprocess.Popen([sys.executable, "app.py"], cwd=backend_dir)
        processes.append(("Flask ML API", flask_proc))

        # 2. FastAPI Analytics Service (Port 8000) - If available
        fastapi_script = os.path.join(backend_dir, "fastapi_app.py")
        if os.path.exists(fastapi_script):
            print("⚡ Starting FastAPI Service (http://localhost:8000)...")
            fastapi_proc = subprocess.Popen([sys.executable, "fastapi_app.py"], cwd=backend_dir)
            processes.append(("FastAPI Service", fastapi_proc))

        # 3. Simple Python Web Server for HTML/JS Frontend (Port 5173)
        print("💻 Launching Frontend Server (http://localhost:5173)...")
        frontend_proc = subprocess.Popen([sys.executable, "-m", "http.server", "5173"], cwd=frontend_dir)
        processes.append(("Frontend Server", frontend_proc))

        time.sleep(2)
        print("\n==================================================")
        print("✅ All CoastSentinel AI systems online!")
        print("🌐 Dashboard URL: http://localhost:5173")
        print("📡 Flask ML API:  http://localhost:5000")
        print("==================================================")
        print("Press Ctrl+C to stop all services cleanly.\n")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down CoastSentinel AI services...")
    finally:
        for name, proc in processes:
            print(f"  • Terminating {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("✨ All services stopped gracefully. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    run_project()