"""
SafePickup - Script de prueba 04
==================================
Detección facial en tiempo real desde la webcam.

Este script abre la cámara web y muestra los rostros detectados con
un cuadro verde alrededor, junto con la confianza de cada detección.

Es la prueba más visual y la que se le muestra al docente o jurado
para demostrar que el sistema funciona "en vivo".

Uso:
    python scripts/04_camara_tiempo_real.py

Controles:
    - Presionar 'q' para salir
    - Presionar 's' para guardar el frame actual

Qué demuestra:
    - Captura de video en tiempo real con OpenCV
    - Detección continua con MTCNN sobre cada frame
    - Cálculo de FPS para medir el rendimiento
"""

import sys
import os
import time
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.detector import DetectorFacial


def main():
    print("=" * 60)
    print("  SafePickup - Detección facial en tiempo real")
    print("=" * 60)
    print()

    # Inicializar el detector (esto tarda unos segundos la primera vez)
    print("Cargando MTCNN...")
    detector = DetectorFacial()
    print(f"[OK] Detector listo en {detector.device.upper()}")
    print()

    # Abrir la webcam (0 = cámara por defecto)
    # Si tiene varias cámaras, probar con 1, 2, etc.
    print("Abriendo cámara...")
    camara = cv2.VideoCapture(0)

    if not camara.isOpened():
        print("[ERROR] No se pudo abrir la cámara.")
        print("        Verificar que esté conectada y no esté en uso.")
        return

    # Configurar resolución
    camara.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("[OK] Cámara abierta")
    print()
    print("Controles:")
    print("  - Presione 'q' para salir")
    print("  - Presione 's' para guardar el frame actual")
    print()

    # Variables para calcular FPS
    contador_frames = 0
    inicio_tiempo = time.time()
    fps = 0

    # Procesar 1 de cada N frames para no saturar la CPU
    # (MTCNN es pesado; no necesitamos detectar 30 veces por segundo)
    salto_frames = 2
    frame_actual = 0
    rostros_cache = []

    while True:
        ret, frame = camara.read()
        if not ret:
            print("[ERROR] No se pudo leer frame de la cámara.")
            break

        frame_actual += 1

        # Solo procesar cada N frames (mejora el rendimiento visual)
        if frame_actual % salto_frames == 0:
            rostros_cache = detector.detectar_rostros(frame)

        # Dibujar todos los rostros detectados
        for rostro in rostros_cache:
            x1, y1, x2, y2 = rostro['coordenadas']
            confianza = rostro['confianza']

            # Rectángulo verde alrededor del rostro
            cv2.rectangle(frame, (x1, y1), (x2, y2), (74, 222, 128), 2)

            # Etiqueta con la confianza
            etiqueta = f"Rostro {confianza*100:.1f}%"

            # Fondo de la etiqueta
            (ancho_texto, alto_texto), _ = cv2.getTextSize(
                etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                frame, (x1, y1 - alto_texto - 8),
                (x1 + ancho_texto + 6, y1), (74, 222, 128), -1
            )

            cv2.putText(
                frame, etiqueta, (x1 + 3, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1
            )

        # Calcular FPS cada 30 frames
        contador_frames += 1
        if contador_frames >= 30:
            fps = contador_frames / (time.time() - inicio_tiempo)
            contador_frames = 0
            inicio_tiempo = time.time()

        # Overlay informativo en la esquina superior
        overlay_texto = [
            f"SafePickup v0.1 - Modo demo",
            f"Rostros detectados: {len(rostros_cache)}",
            f"FPS: {fps:.1f}",
            f"Dispositivo: {detector.device.upper()}"
        ]

        for i, texto in enumerate(overlay_texto):
            y_pos = 25 + i * 22
            # Fondo semi-transparente
            cv2.rectangle(frame, (10, y_pos - 18), (300, y_pos + 4),
                         (0, 0, 0), -1)
            cv2.putText(frame, texto, (15, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # Indicador REC en la esquina superior derecha
        h, w = frame.shape[:2]
        cv2.circle(frame, (w - 30, 30), 7, (0, 0, 220), -1)
        cv2.putText(frame, "REC", (w - 75, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 220), 2)

        cv2.imshow("SafePickup - Cámara entrada (presione 'q' para salir)", frame)

        # Capturar tecla presionada
        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord('q'):
            print("Cerrando...")
            break

        if tecla == ord('s'):
            ruta = f"data/fotos_prueba/captura_{int(time.time())}.jpg"
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            cv2.imwrite(ruta, frame)
            print(f"Frame guardado en: {ruta}")

    camara.release()
    cv2.destroyAllWindows()
    print()
    print("Sesión finalizada.")


if __name__ == "__main__":
    main()
