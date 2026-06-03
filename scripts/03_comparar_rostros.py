"""
SafePickup - Script de prueba 03
==================================
Comparar dos rostros y determinar si son la misma persona.

Este script es el corazón del sistema de verificación: dado un rostro
capturado por la cámara y un rostro previamente registrado, decide
si pertenecen a la misma persona.

Uso:
    1. Colocar dos fotos en data/fotos_prueba/:
        - foto1.jpg  (rostro de la persona A)
        - foto2.jpg  (rostro a comparar)
    2. Ejecutar: python scripts/03_comparar_rostros.py

Qué demuestra:
    - El mecanismo de comparación por distancia euclidiana
    - Cómo el umbral decide si dos rostros son la misma persona
    - El concepto de "verificación facial 1:1"
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.detector import DetectorFacial
from app.ai.embedder import GeneradorEmbeddings


def procesar_imagen(ruta, detector, generador):
    """Detecta el rostro y genera su embedding. Devuelve None si falla."""
    if not os.path.exists(ruta):
        print(f"[ERROR] No se encuentra: {ruta}")
        return None

    rostro = detector.detectar_un_rostro(ruta)
    if rostro is None:
        print(f"[ERROR] No se detectó rostro en: {ruta}")
        return None

    embedding = generador.generar(rostro['rostro_tensor'])
    return embedding


def main():
    print("=" * 60)
    print("  Verificación facial 1:1 - Comparación de rostros")
    print("=" * 60)
    print()

    ruta1 = "data/fotos_prueba/foto1.jpg"
    ruta2 = "data/fotos_prueba/foto2.jpg"

    if not os.path.exists(ruta2):
        print(f"[INFO] Para esta prueba se necesita una segunda foto.")
        print(f"       Coloque foto2.jpg en: data/fotos_prueba/")
        print(f"       Pruebe con:")
        print(f"         - Misma persona, diferente foto (debe dar MATCH)")
        print(f"         - Persona distinta (debe dar NO MATCH)")
        return

    detector = DetectorFacial()
    generador = GeneradorEmbeddings()

    print(f"Procesando rostro 1: {ruta1}")
    emb1 = procesar_imagen(ruta1, detector, generador)
    if emb1 is None:
        return

    print(f"Procesando rostro 2: {ruta2}")
    emb2 = procesar_imagen(ruta2, detector, generador)
    if emb2 is None:
        return

    print()
    print("Comparando embeddings...")
    print()

    resultado = generador.comparar(emb1, emb2)

    # Visualización del resultado
    print("-" * 60)
    print(f"  Distancia euclidiana: {resultado['distancia']:.4f}")
    print(f"  Similitud aproximada: {resultado['similitud_porcentual']:.2f}%")
    print(f"  Umbral configurado:   {generador.UMBRAL_VERIFICACION}")
    print("-" * 60)
    print()

    if resultado['es_misma_persona']:
        print("  >>> RESULTADO: ES LA MISMA PERSONA <<<")
        print()
        print(f"  La distancia ({resultado['distancia']:.4f}) está por debajo")
        print(f"  del umbral ({generador.UMBRAL_VERIFICACION}), por lo que el")
        print(f"  sistema verifica positivamente la identidad.")
    else:
        print("  >>> RESULTADO: PERSONAS DISTINTAS <<<")
        print()
        print(f"  La distancia ({resultado['distancia']:.4f}) supera el umbral")
        print(f"  ({generador.UMBRAL_VERIFICACION}), por lo que el sistema")
        print(f"  rechaza la verificación.")

    print()
    print("Interpretación de la distancia euclidiana:")
    print("  0.0 - 0.6   :  Misma persona (alta confianza)")
    print("  0.6 - 0.9   :  Zona ambigua (la literatura sugiere rechazar)")
    print("  0.9 en adelante:  Personas claramente distintas")


if __name__ == "__main__":
    main()
