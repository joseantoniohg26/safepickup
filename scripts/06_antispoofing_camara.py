"""
SafePickup - Script de prueba 06
==================================
Detección anti-spoofing en tiempo real con la webcam.

Este script ejecuta el pipeline completo:
    1. MTCNN detecta rostros
    2. Anti-spoofing verifica si son personas reales
    3. Muestra el resultado visualmente

Uso:
    python scripts/06_antispoofing_camara.py

DEMOSTRACIÓN PARA EL DOCENTE:
    1. Mira a la cámara con tu propio rostro
       → debe mostrar "REAL ✓" en verde

    2. Saca tu celular, busca una foto de cualquier persona,
       muestra la foto frente a la cámara
       → debe mostrar "SPOOF ✗" en rojo
       → mostrará los motivos del rechazo

    3. Prueba con una foto impresa si tienes
       → también debería detectarla como spoof

Controles:
    - 'q' para salir
    - 's' para guardar el frame actual
    - 'd' para activar/desactivar modo debug
"""

import sys
import os
import time
import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.detector import DetectorFacial
from app.ai.anti_spoofing import DetectorAntiSpoofing


def main():
    print("=" * 60)
    print("  SafePickup - Anti-spoofing en tiempo real")
    print("=" * 60)
    print()

    print("Cargando MTCNN...")
    detector = DetectorFacial()
    print(f"[OK] Detector listo en {detector.device.upper()}")

    print("Cargando módulo anti-spoofing...")
    anti_spoof = DetectorAntiSpoofing(debug=False)
    print(f"[OK] Anti-spoofing listo")
    print()

    print("Abriendo cámara...")
    camara = cv2.VideoCapture(0)
    camara.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not camara.isOpened():
        print("[ERROR] No se pudo abrir la cámara.")
        return

    print("[OK] Cámara abierta")
    print()
    print("Controles:")
    print("  'q' = salir   's' = guardar   'd' = debug on/off")
    print()
    print("PRUEBAS RECOMENDADAS:")
    print("  1. Mírate a la cámara → debe ser REAL")
    print("  2. Muestra una foto en celular → debe ser SPOOF")
    print()

    frame_actual = 0
    salto_frames = 3
    resultado_cache = None
    modo_debug = False
    contador_frames = 0
    inicio_tiempo = time.time()
    fps = 0

    while True:
        ret, frame = camara.read()
        if not ret:
            break

        frame_actual += 1

        if frame_actual % salto_frames == 0:
            rostro = detector.detectar_un_rostro(frame)

            if rostro is not None:
                # Extraer la región del rostro del frame original
                x1, y1, x2, y2 = rostro['coordenadas']
                # Asegurar que las coordenadas estén dentro del frame
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(frame.shape[1], x2)
                y2 = min(frame.shape[0], y2)

                rostro_recortado = frame[y1:y2, x1:x2]

                if rostro_recortado.size > 0:
                    # Pasar al detector anti-spoofing
                    anti_spoof.debug = modo_debug
                    resultado_spoof = anti_spoof.verificar(rostro_recortado)

                    resultado_cache = {
                        'coordenadas': rostro['coordenadas'],
                        'confianza_deteccion': rostro['confianza'],
                        'anti_spoof': resultado_spoof
                    }

                    if modo_debug:
                        print("---")
            else:
                resultado_cache = None

        # ============================================================
        # DIBUJAR RESULTADO EN EL FRAME
        # ============================================================
        if resultado_cache:
            x1, y1, x2, y2 = resultado_cache['coordenadas']
            spoof = resultado_cache['anti_spoof']

            if spoof['es_real']:
                # ✓ ROSTRO REAL - verde
                color = (74, 222, 128)
                etiqueta = "REAL"
                sub = f"Liveness: {spoof['liveness_score']:.0f}%"
            else:
                # ✗ SPOOFING - rojo
                color = (87, 87, 248)
                etiqueta = "SPOOF DETECTADO"
                sub = f"Votos: {spoof['votos_spoof']}/4"

            # Rectángulo principal del rostro
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

            # Caja superior con la etiqueta
            ancho_caja = max(280, x2 - x1)
            cv2.rectangle(frame, (x1, y1 - 60),
                          (x1 + ancho_caja, y1), color, -1)

            # Texto principal
            cv2.putText(frame, etiqueta, (x1 + 8, y1 - 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(frame, sub, (x1 + 8, y1 - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # Si es spoof, mostrar motivos
            if not spoof['es_real']:
                y_motivo = y2 + 25
                for motivo in spoof['motivos'][:3]:  # máximo 3 motivos
                    cv2.putText(frame, "• " + motivo, (x1, y_motivo),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                                (87, 87, 248), 1)
                    y_motivo += 22

        # ============================================================
        # OVERLAY INFORMATIVO
        # ============================================================
        contador_frames += 1
        if contador_frames >= 30:
            fps = contador_frames / (time.time() - inicio_tiempo)
            contador_frames = 0
            inicio_tiempo = time.time()

        info = [
            f"SafePickup - Anti-spoofing v1.0",
            f"FPS: {fps:.1f}",
            f"Debug: {'ON' if modo_debug else 'OFF'}"
        ]

        for i, texto in enumerate(info):
            y_pos = 25 + i * 22
            cv2.rectangle(frame, (10, y_pos - 18),
                          (260, y_pos + 4), (0, 0, 0), -1)
            cv2.putText(frame, texto, (15, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (255, 255, 255), 1)

        # Indicador REC
        h, w = frame.shape[:2]
        cv2.circle(frame, (w - 30, 30), 7, (0, 0, 220), -1)
        cv2.putText(frame, "REC", (w - 75, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 220), 2)

        # Leyenda inferior
        cv2.rectangle(frame, (0, h - 35), (w, h), (27, 58, 107), -1)
        leyenda = "Mire a la camara (real) o muestre foto en celular (spoof)"
        cv2.putText(frame, leyenda, (15, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("SafePickup - Anti-spoofing (q=salir, d=debug)", frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord('q'):
            break
        elif tecla == ord('d'):
            modo_debug = not modo_debug
            print(f"\nModo debug: {'ACTIVADO' if modo_debug else 'desactivado'}\n")
        elif tecla == ord('s'):
            ruta = f"data/fotos_prueba/antispoof_{int(time.time())}.jpg"
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            cv2.imwrite(ruta, frame)
            print(f"Frame guardado: {ruta}")

    camara.release()
    cv2.destroyAllWindows()
    print()
    print("Sesión finalizada.")


if __name__ == "__main__":
    main()
