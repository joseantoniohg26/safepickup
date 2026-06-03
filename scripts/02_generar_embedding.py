"""
SafePickup - Script de prueba 02
==================================
Generar el embedding facial de un rostro.

El embedding es la representación numérica del rostro: un vector de
512 dimensiones que captura las características únicas de la persona.

Uso:
    python scripts/02_generar_embedding.py

Qué demuestra:
    - Que FaceNet convierte un rostro en un vector
    - Que el vector tiene 512 elementos
    - Que el embedding se puede guardar para futuras comparaciones
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.detector import DetectorFacial
from app.ai.embedder import GeneradorEmbeddings


def main():
    ruta_foto = "data/fotos_prueba/foto1.jpg"

    if not os.path.exists(ruta_foto):
        print(f"[ERROR] No se encuentra: {ruta_foto}")
        print(f"        Ejecute primero: python scripts/01_detectar_rostro.py")
        return

    print("=" * 60)
    print("  Generación de embedding facial con FaceNet")
    print("=" * 60)
    print()

    # Paso 1: detectar el rostro
    print("Paso 1/2: Detectando rostro con MTCNN...")
    detector = DetectorFacial()
    rostro = detector.detectar_un_rostro(ruta_foto)

    if rostro is None:
        print("[ERROR] No se detectó ningún rostro en la imagen.")
        return

    print(f"[OK] Rostro detectado con confianza {rostro['confianza']:.4f}")
    print()

    # Paso 2: generar el embedding
    print("Paso 2/2: Generando embedding con FaceNet...")
    generador = GeneradorEmbeddings()
    embedding = generador.generar(rostro['rostro_tensor'])

    print(f"[OK] Embedding generado")
    print()
    print(f"Dimensiones del vector: {embedding.shape[0]}")
    print(f"Tipo de dato: {embedding.dtype}")
    print(f"Valor mínimo: {embedding.min():.6f}")
    print(f"Valor máximo: {embedding.max():.6f}")
    print(f"Media: {embedding.mean():.6f}")
    print()

    # Mostrar los primeros 10 valores del embedding
    print("Primeros 10 valores del embedding:")
    for i in range(10):
        print(f"  embedding[{i}] = {embedding[i]:+.6f}")
    print(f"  ... ({embedding.shape[0] - 10} valores más)")
    print()

    # Guardar el embedding en disco
    # En el sistema final, este embedding se guardará en MySQL
    # asociado al apoderado correspondiente.
    ruta_embedding = "data/embeddings/foto1_embedding.npy"
    os.makedirs(os.path.dirname(ruta_embedding), exist_ok=True)
    np.save(ruta_embedding, embedding)

    print(f"Embedding guardado en: {ruta_embedding}")
    print(f"Tamaño del archivo: {os.path.getsize(ruta_embedding)} bytes")
    print()
    print("Este vector representa matemáticamente el rostro de la persona.")
    print("En el sistema final, se almacenará en MySQL como BLOB para")
    print("compararlo con futuros rostros capturados por la cámara.")


if __name__ == "__main__":
    main()
