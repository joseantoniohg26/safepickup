"""
SafePickup - Script de prueba 07
==================================
Probar el anti-spoofing con una foto específica.

Útil para hacer pruebas controladas y documentar resultados para
la tesis (capítulo IV - resultados).

Uso:
    1. Coloca la foto a probar en data/fotos_prueba/test_spoof.jpg
       (puede ser un rostro real, una foto de pantalla, o una foto impresa)
    2. Ejecuta: python scripts/07_probar_antispoofing.py

Salida:
    - Detecta el rostro en la foto
    - Aplica las 4 técnicas anti-spoofing
    - Imprime los valores de cada técnica
    - Indica si es REAL o SPOOF
    - Lista los motivos en caso de rechazo
"""

import sys
import os
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.detector import DetectorFacial
from app.ai.anti_spoofing import DetectorAntiSpoofing


def main():
    print("=" * 60)
    print("  SafePickup - Análisis anti-spoofing en imagen")
    print("=" * 60)
    print()

    ruta = "data/fotos_prueba/test_spoof.jpg"

    if not os.path.exists(ruta):
        print(f"[ERROR] No se encuentra: {ruta}")
        print(f"        Coloque una foto a probar en esa ruta.")
        return

    print(f"Analizando: {ruta}")
    print()

    # Cargar componentes
    detector = DetectorFacial()
    anti_spoof = DetectorAntiSpoofing(debug=True)

    # Cargar imagen
    imagen = cv2.imread(ruta)
    if imagen is None:
        print("[ERROR] No se pudo abrir la imagen.")
        return

    print("Detectando rostro...")
    rostro = detector.detectar_un_rostro(imagen)

    if rostro is None:
        print("[ERROR] No se detectó ningún rostro.")
        return

    print(f"[OK] Rostro detectado (confianza {rostro['confianza']:.4f})")
    print()

    # Recortar rostro
    x1, y1, x2, y2 = rostro['coordenadas']
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(imagen.shape[1], x2)
    y2 = min(imagen.shape[0], y2)
    rostro_recortado = imagen[y1:y2, x1:x2]

    print("Aplicando análisis anti-spoofing...")
    print("-" * 60)
    resultado = anti_spoof.verificar(rostro_recortado)
    print("-" * 60)
    print()

    # Mostrar resultado
    print("=" * 60)
    if resultado['es_real']:
        print("  >>> RESULTADO: ROSTRO REAL <<<")
        print(f"  Liveness score: {resultado['liveness_score']:.1f}%")
        print(f"  Votos de spoof: {resultado['votos_spoof']}/4")
    else:
        print("  >>> RESULTADO: SPOOFING DETECTADO <<<")
        print(f"  Liveness score: {resultado['liveness_score']:.1f}%")
        print(f"  Votos de spoof: {resultado['votos_spoof']}/4")
        print()
        print("  Motivos del rechazo:")
        for motivo in resultado['motivos']:
            print(f"    • {motivo}")
    print("=" * 60)
    print()

    # Guardar imagen con resultado dibujado
    color = (74, 222, 128) if resultado['es_real'] else (87, 87, 248)
    etiqueta = "REAL" if resultado['es_real'] else "SPOOF"

    cv2.rectangle(imagen, (x1, y1), (x2, y2), color, 3)
    cv2.putText(imagen, f"{etiqueta} ({resultado['liveness_score']:.0f}%)",
                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, color, 2)

    ruta_salida = "data/fotos_prueba/test_spoof_resultado.jpg"
    cv2.imwrite(ruta_salida, imagen)
    print(f"Imagen con resultado guardada: {ruta_salida}")
    print()
    print("Mostrando resultado. Presione cualquier tecla para cerrar.")
    cv2.imshow("Anti-spoofing - Resultado", imagen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
