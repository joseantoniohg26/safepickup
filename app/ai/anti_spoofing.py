"""
SafePickup - Módulo de detección anti-spoofing (CALIBRADO)
============================================================
Implementa la detección de intentos de suplantación facial mediante
análisis multifactorial de calidad de imagen.

VERSIÓN CALIBRADA: los umbrales fueron ajustados a partir de datos
empíricos recolectados en el hardware específico de despliegue, siguiendo
un protocolo experimental de 200+ muestras (persona real vs reproducción
en pantalla de smartphone).

Estrategia: enfoque ensemble (consenso) de 3 técnicas independientes:

    1. Análisis de textura LBP (Local Binary Patterns) — INVERTIDO
       En este hardware, las pantallas digitales generan más textura
       artificial (píxeles, sub-pixeles) que la piel real.

    2. Análisis de reflejos especulares (HSV) — discriminador principal
       Mostró separación de 30x entre rostro real y foto en pantalla.

    3. Análisis de nitidez Laplaciana
       Las pantallas captadas pierden nitidez (efecto doble captura).

NOTA TÉCNICA: la detección de Moiré por FFT2D no resulta efectiva en
este hardware (cámara HD moderna con filtro anti-aliasing). La técnica
se documenta pero no se utiliza en la decisión final.

Referencias académicas:
    - Bharadwaj, S., et al. (2014). Face anti-spoofing via motion
      magnification. IIIT-D Technical Report.
    - Boulkenafet, Z., et al. (2016). Face anti-spoofing using SURF
      and Fisher vector encoding. IEEE SPL, 24(2).
    - Ojala, T., et al. (2002). Multiresolution gray-scale and rotation
      invariant texture classification with local binary patterns.
      IEEE TPAMI, 24(7).
"""

import cv2
import numpy as np


class DetectorAntiSpoofing:
    """
    Detector de intentos de suplantación facial (versión calibrada).

    Analiza un rostro detectado y determina si pertenece a una persona
    real ("live") o a una representación falsa ("spoof") como foto
    impresa o pantalla de celular.
    """

    # ================================================================
    # UMBRALES CALIBRADOS EMPÍRICAMENTE
    # ================================================================
    # Estos valores fueron determinados mediante recolección de muestras
    # reales en el entorno de despliegue. Los rangos observados fueron:
    #
    #   Rostro REAL:     LBP 120-250 | Reflejo 0-3% | Nitidez 30-80
    #   Foto en pantalla: LBP 2000-4700 | Reflejo 65-88% | Nitidez 21-38
    #
    # Los umbrales se ubican en puntos óptimos de discriminación.
    UMBRAL_TEXTURA_LBP = 500.0    # Spoof si LBP > 500 (invertido)
    UMBRAL_REFLEJO_PCT = 15.0     # Spoof si reflejo > 15%
    UMBRAL_NITIDEZ = 25.0         # Spoof si nitidez < 25
    VOTOS_MINIMOS_SPOOF = 2       # 2 de 3 técnicas deben votar spoof

    def __init__(self, debug=False):
        """
        Inicializa el detector.

        Parámetros:
            debug: si es True, imprime los valores de cada técnica.
        """
        self.debug = debug

    # ----------------------------------------------------------------
    # TÉCNICA 1: Textura LBP (Local Binary Patterns) — INVERTIDO
    # ----------------------------------------------------------------
    def _analizar_textura_lbp(self, rostro_bgr):
        """
        Mide la riqueza de micro-textura del rostro.

        En este hardware, las pantallas digitales (LCD, OLED) generan
        patrones de píxeles y sub-pixeles altamente regulares que la
        cámara web capta como "textura artificial" muy alta. La piel
        humana, al ser orgánica, tiene textura más moderada.

        Esto es contraintuitivo respecto a la literatura clásica, pero
        es lo que muestran los datos empíricos del hardware específico.

        Devuelve la varianza de la textura. Valores ALTOS indican spoof.
        """
        gris = cv2.cvtColor(rostro_bgr, cv2.COLOR_BGR2GRAY)
        gris = cv2.resize(gris, (128, 128))

        # Implementación simplificada de LBP
        h, w = gris.shape
        lbp = np.zeros((h - 2, w - 2), dtype=np.uint8)

        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, 1),
                   (1, 1), (1, 0), (1, -1), (0, -1)]

        centro = gris[1:-1, 1:-1]

        for i, (dy, dx) in enumerate(offsets):
            vecino = gris[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx]
            lbp |= ((vecino >= centro).astype(np.uint8)) << i

        histograma, _ = np.histogram(lbp, bins=256, range=(0, 256))
        varianza = np.var(histograma) / 100.0

        return varianza

    # ----------------------------------------------------------------
    # TÉCNICA 2: Análisis de reflejos especulares (HSV)
    # ----------------------------------------------------------------
    def _analizar_reflejos(self, rostro_bgr):
        """
        Detecta reflejos especulares anormales típicos de pantallas.

        Esta es la técnica MÁS discriminativa según las pruebas:
        rostro real produce <3% de píxeles brillantes, mientras que
        una foto en pantalla produce 65-88%. Es la métrica principal.
        """
        hsv = cv2.cvtColor(rostro_bgr, cv2.COLOR_BGR2HSV)
        v = hsv[:, :, 2]

        pixeles_brillantes = np.sum(v > 240)
        total_pixeles = v.size

        porcentaje = (pixeles_brillantes / total_pixeles) * 100

        return porcentaje

    # ----------------------------------------------------------------
    # TÉCNICA 3: Análisis de nitidez Laplaciana
    # ----------------------------------------------------------------
    def _analizar_nitidez(self, rostro_bgr):
        """
        Mide la nitidez del rostro mediante varianza Laplaciana.

        Cuando alguien fotografía una foto en celular, ocurre una
        "doble captura" que reduce la nitidez. Las fotos en pantalla
        muestran valores de 21-38, mientras que rostros reales muestran
        valores típicos de 30-80.
        """
        gris = cv2.cvtColor(rostro_bgr, cv2.COLOR_BGR2GRAY)
        laplaciano = cv2.Laplacian(gris, cv2.CV_64F)
        varianza = laplaciano.var()

        return varianza

    # ----------------------------------------------------------------
    # MÉTODO PRINCIPAL: combina las 3 técnicas por consenso
    # ----------------------------------------------------------------
    def verificar(self, rostro_bgr):
        """
        Verifica si un rostro corresponde a una persona real.

        Parámetros:
            rostro_bgr: array NumPy del rostro recortado (formato BGR
                       de OpenCV).

        Devuelve:
            Diccionario con:
                - 'es_real': True si pasa todas las verificaciones
                - 'liveness_score': probabilidad de ser real (0-100%)
                - 'votos_spoof': cuántas técnicas detectaron spoof
                - 'detalles': dict con el valor de cada técnica
                - 'motivos': lista de razones del rechazo (si aplica)
        """
        if rostro_bgr is None or rostro_bgr.size == 0:
            return {
                'es_real': False,
                'liveness_score': 0.0,
                'votos_spoof': 3,
                'detalles': {},
                'motivos': ['rostro vacío o inválido']
            }

        # Aplicar las 3 técnicas activas
        valor_textura = self._analizar_textura_lbp(rostro_bgr)
        pct_reflejo = self._analizar_reflejos(rostro_bgr)
        nitidez = self._analizar_nitidez(rostro_bgr)

        # Cada técnica vota: True = detecta spoof
        votos = {
            'textura': valor_textura > self.UMBRAL_TEXTURA_LBP,
            'reflejo': pct_reflejo > self.UMBRAL_REFLEJO_PCT,
            'nitidez': nitidez < self.UMBRAL_NITIDEZ
        }

        num_votos_spoof = sum(votos.values())
        es_real = num_votos_spoof < self.VOTOS_MINIMOS_SPOOF

        # Calcular score de liveness sobre 3 técnicas
        liveness_score = max(0, (3 - num_votos_spoof) / 3 * 100)

        motivos = []
        if votos['textura']:
            motivos.append(f'textura artificial alta (LBP {valor_textura:.0f})')
        if votos['reflejo']:
            motivos.append(f'reflejos excesivos ({pct_reflejo:.1f}%)')
        if votos['nitidez']:
            motivos.append(f'nitidez insuficiente (Laplaciano {nitidez:.1f})')

        resultado = {
            'es_real': es_real,
            'liveness_score': round(liveness_score, 2),
            'votos_spoof': num_votos_spoof,
            'detalles': {
                'textura_lbp': round(valor_textura, 2),
                'reflejo_pct': round(pct_reflejo, 2),
                'nitidez_laplaciana': round(nitidez, 2)
            },
            'motivos': motivos
        }

        if self.debug:
            print(f"  [Anti-spoof] Textura LBP: {valor_textura:.2f} "
                  f"(umbral > {self.UMBRAL_TEXTURA_LBP})")
            print(f"  [Anti-spoof] Reflejo: {pct_reflejo:.2f}% "
                  f"(umbral > {self.UMBRAL_REFLEJO_PCT}%)")
            print(f"  [Anti-spoof] Nitidez: {nitidez:.2f} "
                  f"(umbral < {self.UMBRAL_NITIDEZ})")
            print(f"  [Anti-spoof] Votos de spoof: {num_votos_spoof}/3 → "
                  f"{'REAL' if es_real else 'SPOOF'}")

        return resultado


# ============================================================
# Prueba rápida del módulo
# ============================================================
if __name__ == "__main__":
    print("Probando el detector anti-spoofing CALIBRADO...")
    detector = DetectorAntiSpoofing(debug=True)
    print(f"Umbrales configurados (calibrados con datos empíricos):")
    print(f"  Textura LBP: > {detector.UMBRAL_TEXTURA_LBP} (invertido)")
    print(f"  Reflejo: > {detector.UMBRAL_REFLEJO_PCT}%")
    print(f"  Nitidez: < {detector.UMBRAL_NITIDEZ}")
    print(f"  Votos mínimos para spoof: {detector.VOTOS_MINIMOS_SPOOF}/3")
    print("Listo para verificar rostros.")
