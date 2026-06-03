"""
SafePickup — Verificar instalación
=====================================
Comprueba que todas las dependencias estén correctamente instaladas.

Ejecutar antes de iniciar el servidor:
    python scripts/verificar_instalacion.py
"""

import sys
print()
print("=" * 60)
print("  SafePickup — Verificando instalación")
print("=" * 60)

errores = []

# 1. Python
v = sys.version_info
print(f"  Python: {v.major}.{v.minor}.{v.micro}", end="")
if v.major == 3 and 9 <= v.minor <= 12:
    print(" [OK]")
else:
    print(" [WARN] — Recomendado Python 3.9-3.12")

# 2. PyTorch
try:
    import torch
    print(f"  PyTorch: {torch.__version__} [OK]")
    gpu = torch.cuda.is_available()
    print(f"  GPU (CUDA): {'Disponible ✓' if gpu else 'No disponible — usando CPU'}")
except ImportError:
    print("  PyTorch: [ERROR] — ejecuta: pip install torch")
    errores.append('torch')

# 3. facenet-pytorch
try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
    print("  facenet-pytorch: [OK]")
except ImportError:
    print("  facenet-pytorch: [ERROR] — ejecuta: pip install facenet-pytorch")
    errores.append('facenet-pytorch')

# 4. OpenCV
try:
    import cv2
    print(f"  OpenCV: {cv2.__version__} [OK]")
except ImportError:
    print("  OpenCV: [ERROR] — ejecuta: pip install opencv-python")
    errores.append('opencv-python')

# 5. FastAPI
try:
    import fastapi
    print(f"  FastAPI: {fastapi.__version__} [OK]")
except ImportError:
    print("  FastAPI: [ERROR] — ejecuta: pip install fastapi")
    errores.append('fastapi')

# 6. Uvicorn
try:
    import uvicorn
    print(f"  Uvicorn: {uvicorn.__version__} [OK]")
except ImportError:
    print("  Uvicorn: [ERROR] — ejecuta: pip install uvicorn[standard]")
    errores.append('uvicorn')

# 7. PyMySQL
try:
    import pymysql
    print(f"  PyMySQL: {pymysql.__version__} [OK]")
except ImportError:
    print("  PyMySQL: [ERROR] — ejecuta: pip install pymysql")
    errores.append('pymysql')

# 8. NumPy
try:
    import numpy as np
    print(f"  NumPy: {np.__version__} [OK]")
except ImportError:
    print("  NumPy: [ERROR] — ejecuta: pip install numpy")
    errores.append('numpy')

# 9. Pillow
try:
    import PIL
    print(f"  Pillow: {PIL.__version__} [OK]")
except ImportError:
    print("  Pillow: [ERROR] — ejecuta: pip install Pillow")
    errores.append('Pillow')

# 10. MySQL
print()
print("  Verificando MySQL...")
try:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.database.mysql_db import verificar_conexion
    if verificar_conexion():
        print("  MySQL: Conectado [OK]")
    else:
        print("  MySQL: Sin conexión [WARN]")
        print("         Ejecuta: python scripts/configurar_mysql.py")
except Exception as e:
    print(f"  MySQL: Error — {e}")

print()
print("=" * 60)
if errores:
    print(f"  ERRORES ({len(errores)}): {', '.join(errores)}")
    print()
    print("  Instala todo con:")
    print("  pip install -r requirements.txt")
else:
    print("  ¡Todo listo! Ejecuta:")
    print("  python scripts/iniciar_servidor.py")
print("=" * 60)
print()
