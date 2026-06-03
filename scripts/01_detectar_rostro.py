"""
SafePickup - Script de prueba 01
==================================
Detectar un rostro en una foto y dibujar el cuadro de detección.

Este es el primer paso para validar que MTCNN funciona correctamente
en nuestro sistema. Si esto no funciona, nada de lo demás funcionará.

Uso:
    1. Colocar una foto con un rostro en: data/fotos_prueba/foto1.jpg
    2. Ejecutar: python scripts/01_detectar_rostro.py
    3. Se abrirá una ventana mostrando el rostro detectado con un cuadro verde.

Qué demuestra:
    - Que MTCNN logra localizar rostros en imágenes reales
    - Que podemos extraer las coordenadas del bounding box
    - Que el rostro queda recortado y listo para FaceNet
"""

import sys
import os
import cv2

# Agregar el directorio raíz al PATH para poder importar app/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.detector import DetectorFacial


def main():
    # Ruta a la foto de prueba
    ruta_foto = "data/fotos_prueba/foto1.jpg"

    if not os.path.exists(ruta_foto):
        print(f"[ERROR] No se encuentra la foto: {ruta_foto}")
        print(f"        Coloque una imagen con un rostro en esa ruta.")
        return

    print(f"Procesando: {ruta_foto}")
    print()

    # Inicializar el detector
    print("Cargando MTCNN...")
    detector = DetectorFacial()

    # Cargar la imagen con OpenCV (formato BGR)
    imagen = cv2.imread(ruta_foto)
    if imagen is None:
        print(f"[ERROR] No se pudo abrir la imagen.")
        return

    # Detectar rostros
    print("Detectando rostros...")
    rostros = detector.detectar_rostros(imagen)

    if not rostros:
        print("[INFO] No se detectó ningún rostro en la imagen.")
        return

    print(f"[OK] Se detectaron {len(rostros)} rostro(s):")
    print()

    # Dibujar cada rostro detectado
    for i, rostro in enumerate(rostros, 1):
        x1, y1, x2, y2 = rostro['coordenadas']
        confianza = rostro['confianza']

        print(f"  Rostro {i}:")
        print(f"    Coordenadas: ({x1}, {y1}) - ({x2}, {y2})")
        print(f"    Tamaño: {x2-x1}x{y2-y1} píxeles")
        print(f"    Confianza: {confianza:.4f} ({confianza*100:.2f}%)")
        print()

        # Dibujar rectángulo verde alrededor del rostro
        cv2.rectangle(imagen, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Etiqueta con la confianza
        etiqueta = f"Rostro #{i} - {confianza*100:.1f}%"
        cv2.putText(
            imagen, etiqueta, (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )

        # Dibujar puntos clave (ojos, nariz, boca) si están disponibles
        if rostro['puntos_clave']:
            for punto in rostro['puntos_clave']:
                px, py = int(punto[0]), int(punto[1])
                cv2.circle(imagen, (px, py), 3, (0, 0, 255), -1)

    # Guardar resultado
    ruta_salida = "data/fotos_prueba/foto1_detectada.jpg"
    cv2.imwrite(ruta_salida, imagen)
    print(f"Resultado guardado en: {ruta_salida}")

    # Mostrar en ventana
    print()
    print("Mostrando resultado. Presione cualquier tecla para cerrar.")
    cv2.imshow("SafePickup - Detección facial (MTCNN)", imagen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
