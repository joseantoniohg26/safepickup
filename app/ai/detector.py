"""
SafePickup — Detector facial con MTCNN + CLAHE
================================================
Detecta rostros en imágenes usando MTCNN
(Multi-task Cascaded Convolutional Networks).

Mejoras sobre la versión anterior:
  1. Corrige el bug de desempaquetado (return_prob=True devuelve 2 valores, no 3)
  2. Aplica CLAHE para mejorar detección en mala iluminación
  3. Umbrales más permisivos para condiciones reales
  4. Diagnóstico útil cuando falla la detección

Uso:
    detector = DetectorFacial()
    rostro   = detector.detectar_un_rostro(imagen_bgr)

    # rostro es None si no detectó nada, o un dict:
    {
      'rostro_tensor': tensor PIL listo para FaceNet,
      'coordenadas':   [x1, y1, x2, y2],
      'confianza':     0.99
    }
"""

import cv2
import numpy as np
from PIL import Image
from facenet_pytorch import MTCNN
import torch


class DetectorFacial:
    """Wrapper sobre MTCNN para detección facial."""

    def __init__(self, image_size=160, margin=20):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.image_size = image_size
        self.margin = margin

        # MTCNN con umbrales más permisivos
        # Default: [0.6, 0.7, 0.9] (muy estricto)
        # Nuevo:   [0.6, 0.7, 0.7] (acepta condiciones reales)
        self.mtcnn = MTCNN(
            image_size=image_size,
            margin=margin,
            keep_all=False,
            device=self.device,
            post_process=True,
            select_largest=True,
            thresholds=[0.6, 0.7, 0.7]
        )

        # CLAHE: mejora contraste local sin sobreexponer
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

    def _mejorar_iluminacion(self, imagen_bgr):
        """
        Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization)
        para compensar mala iluminación, contraluz y baja luz.
        """
        lab = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_mejorado = self.clahe.apply(l)
        lab_mejorado = cv2.merge([l_mejorado, a, b])
        return cv2.cvtColor(lab_mejorado, cv2.COLOR_LAB2BGR)

    def _diagnosticar(self, imagen_bgr):
        """Analiza la imagen para dar feedback útil al usuario."""
        gris = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)
        brillo = float(np.mean(gris))
        contraste = float(np.std(gris))

        problemas = []
        if brillo < 60:
            problemas.append("muy oscura - encienda más luz")
        elif brillo > 200:
            problemas.append("sobreexpuesta - reduzca la luz directa")
        if contraste < 30:
            problemas.append("poco contraste/contraluz")
        if not problemas:
            problemas.append("rostro no visible o demasiado pequeño")

        return {'brillo': brillo, 'contraste': contraste, 'problemas': problemas}

    def detectar_un_rostro(self, imagen):
        """
        Detecta el rostro más prominente en una imagen.

        Estrategia:
          1. Intenta detectar con la imagen original
          2. Si falla, aplica CLAHE y vuelve a intentar
          3. Si sigue fallando, muestra diagnóstico en consola

        Parámetros:
            imagen: numpy array BGR (OpenCV) o string con ruta a archivo

        Retorna:
            dict con rostro_tensor, coordenadas, confianza
            None si no se detectó ningún rostro
        """
        # Cargar imagen si se recibió una ruta
        if isinstance(imagen, str):
            imagen = cv2.imread(imagen)
            if imagen is None:
                return None

        # PRIMER INTENTO: imagen original
        resultado = self._detectar_interno(imagen)
        if resultado is not None:
            return resultado

        # SEGUNDO INTENTO: con CLAHE aplicado
        if len(imagen.shape) == 3:
            imagen_mejorada = self._mejorar_iluminacion(imagen)
            resultado = self._detectar_interno(imagen_mejorada)
            if resultado is not None:
                print("[Detector] Rostro detectado tras aplicar CLAHE")
                return resultado

        # Diagnóstico final si nada funcionó
        diag = self._diagnosticar(imagen)
        print(f"[Detector] Sin rostro. Brillo={diag['brillo']:.0f} Contraste={diag['contraste']:.0f}")
        for p in diag['problemas']:
            print(f"           -> {p}")

        return None

    def _detectar_interno(self, imagen_bgr):
        """
        Detección interna de MTCNN sobre una imagen BGR.
        Aquí está el FIX del bug de desempaquetado.
        """
        # Convertir BGR -> RGB (MTCNN trabaja en RGB)
        if len(imagen_bgr.shape) == 3 and imagen_bgr.shape[2] == 3:
            imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
        else:
            imagen_rgb = imagen_bgr

        imagen_pil = Image.fromarray(imagen_rgb)

        try:
            # FIX: return_prob=True devuelve SOLO 2 valores (tensor, prob)
            # El bug anterior intentaba desempaquetar 3 valores
            resultado = self.mtcnn(imagen_pil, return_prob=True)
            if resultado is None:
                return None

            rostro_tensor, prob = resultado

            if rostro_tensor is None or prob is None:
                return None

            # Obtener coordenadas con detect() (devuelve cajas y probs)
            cajas, probs = self.mtcnn.detect(imagen_pil)
            if cajas is None or len(cajas) == 0:
                return None

            x1, y1, x2, y2 = [int(v) for v in cajas[0]]

            return {
                'rostro_tensor': rostro_tensor,
                'coordenadas':   [x1, y1, x2, y2],
                'confianza':     float(prob)
            }

        except Exception as e:
            print(f"[Detector] Error tecnico: {e}")
            return None