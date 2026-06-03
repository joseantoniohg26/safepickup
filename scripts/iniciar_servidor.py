"""
SafePickup — Iniciador del servidor
=====================================
Ejecuta el servidor FastAPI con un solo comando.

Uso:
    python scripts/iniciar_servidor.py

URLs:
    Frontend: http://localhost:8000/
    API docs: http://localhost:8000/docs
"""

import sys, os, webbrowser, time, threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from app.main import app

def abrir_navegador():
    time.sleep(4)
    webbrowser.open("http://localhost:8000/")

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  SafePickup — Iniciando sistema...")
    print("=" * 60)
    print("  Frontend:  http://localhost:8000/")
    print("  API docs:  http://localhost:8000/docs")
    print("  Detener:   Ctrl + C")
    print("=" * 60)
    print()
    threading.Thread(target=abrir_navegador, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
