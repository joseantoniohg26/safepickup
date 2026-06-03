"""
SafePickup - Script de verificación de instalación
===================================================
Este script verifica que todas las librerías necesarias estén
correctamente instaladas y que los modelos de IA puedan cargarse.

Ejecutar con:
    python scripts/probar_instalacion.py

Si algún paso falla, revisar el README.md y reinstalar las dependencias.
"""

import sys


def verificar_pytorch():
    """Verifica que PyTorch esté instalado y detecta si hay GPU."""
    try:
        import torch
        print(f"[OK] PyTorch instalado correctamente (versión {torch.__version__})")

        if torch.cuda.is_available():
            print(f"     GPU detectada: {torch.cuda.get_device_name(0)}")
            print(f"     CUDA disponible. El sistema usará GPU.")
        else:
            print(f"     GPU no detectada. El sistema usará CPU (más lento pero funciona).")

        return True
    except ImportError as e:
        print(f"[ERROR] PyTorch no está instalado: {e}")
        return False


def verificar_facenet():
    """Verifica que facenet-pytorch esté disponible."""
    try:
        import facenet_pytorch
        print(f"[OK] facenet-pytorch funcional")
        return True
    except ImportError as e:
        print(f"[ERROR] facenet-pytorch no está instalado: {e}")
        return False


def verificar_opencv():
    """Verifica que OpenCV esté disponible."""
    try:
        import cv2
        print(f"[OK] OpenCV disponible (versión {cv2.__version__})")
        return True
    except ImportError as e:
        print(f"[ERROR] OpenCV no está instalado: {e}")
        return False


def cargar_mtcnn():
    """Carga el modelo MTCNN (detección facial)."""
    try:
        from facenet_pytorch import MTCNN
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        mtcnn = MTCNN(keep_all=True, device=device)
        print(f"[OK] MTCNN cargado en {device.upper()}")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo cargar MTCNN: {e}")
        return False


def cargar_facenet():
    """Carga el modelo FaceNet (generación de embeddings)."""
    try:
        from facenet_pytorch import InceptionResnetV1
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        # 'vggface2' es el dataset con el que viene preentrenado.
        # Devuelve embeddings de 512 dimensiones.
        modelo = InceptionResnetV1(pretrained='vggface2').eval().to(device)
        print(f"[OK] FaceNet cargado en {device.upper()}")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo cargar FaceNet: {e}")
        print(f"        (la primera vez descarga los pesos del modelo,")
        print(f"         requiere conexión a internet)")
        return False


def main():
    print("=" * 60)
    print("  SafePickup - Verificación de instalación")
    print("=" * 60)
    print()

    resultados = []

    print("Paso 1/5: Verificando PyTorch...")
    resultados.append(verificar_pytorch())
    print()

    print("Paso 2/5: Verificando facenet-pytorch...")
    resultados.append(verificar_facenet())
    print()

    print("Paso 3/5: Verificando OpenCV...")
    resultados.append(verificar_opencv())
    print()

    print("Paso 4/5: Cargando modelo MTCNN...")
    resultados.append(cargar_mtcnn())
    print()

    print("Paso 5/5: Cargando modelo FaceNet...")
    resultados.append(cargar_facenet())
    print()

    print("=" * 60)
    if all(resultados):
        print("  Listo. Puede comenzar el desarrollo.")
        print("=" * 60)
        print()
        print("Siguiente paso:")
        print("  1. Coloque una foto con un rostro en data/fotos_prueba/foto1.jpg")
        print("  2. Ejecute: python scripts/01_detectar_rostro.py")
    else:
        print("  Hay errores en la instalación. Revise los mensajes anteriores.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
