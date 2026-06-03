"""
SafePickup — Generador de embeddings con FaceNet
=================================================
Convierte un rostro detectado en un vector de 512 dimensiones
(embedding) usando InceptionResnetV1 pre-entrenado con VGGFace2.

Distancia euclidiana entre dos embeddings:
    < 0.6  → misma persona  (MATCH)
    >= 0.6 → distinta persona (NO MATCH)
"""

import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1


class GeneradorEmbeddings:
    """Wrapper sobre FaceNet para generar y comparar embeddings."""

    UMBRAL_DEFAULT = 0.6   # distancia euclidiana máxima para match

    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.modelo = InceptionResnetV1(
            pretrained='vggface2'
        ).eval().to(self.device)

    def generar(self, rostro_tensor):
        """
        Genera un embedding de 512 dimensiones a partir de un tensor.

        Parámetros:
            rostro_tensor: tensor devuelto por DetectorFacial

        Retorna:
            numpy array de shape (512,)
        """
        with torch.no_grad():
            tensor = rostro_tensor.unsqueeze(0).to(self.device)
            embedding = self.modelo(tensor)
        return embedding.squeeze().cpu().numpy()

    def distancia(self, emb1, emb2):
        """Distancia euclidiana entre dos embeddings."""
        return float(np.linalg.norm(emb1 - emb2))

    def similitud_porcentual(self, distancia, umbral=None):
        """
        Convierte distancia euclidiana a porcentaje de similitud (0-100%).
        A menor distancia → mayor similitud.
        """
        umbral = umbral or self.UMBRAL_DEFAULT
        pct = max(0.0, (1.0 - distancia / (umbral * 2)) * 100)
        return round(pct, 2)

    def buscar_coincidencia(self, embedding_consulta, apoderados,
                             umbral=None):
        """
        Busca la coincidencia más cercana en la lista de apoderados.

        Parámetros:
            embedding_consulta : numpy array 512D del rostro detectado
            apoderados         : lista de dicts con 'embedding' y metadatos
            umbral             : distancia máxima para considerar match

        Retorna:
            {
              'coincidencia': bool,
              'mejor_match':  dict del apoderado (o None),
              'distancia':    float,
              'similitud_porcentual': float
            }
        """
        umbral = umbral or self.UMBRAL_DEFAULT

        if not apoderados:
            return {
                'coincidencia': False,
                'mejor_match': None,
                'distancia': 9.99,
                'similitud_porcentual': 0.0
            }

        mejor = None
        mejor_distancia = float('inf')

        for apo in apoderados:
            d = self.distancia(embedding_consulta, apo['embedding'])
            if d < mejor_distancia:
                mejor_distancia = d
                mejor = apo

        coincide = mejor_distancia < umbral

        return {
            'coincidencia': coincide,
            'mejor_match': mejor if coincide else None,
            'distancia': round(mejor_distancia, 4),
            'similitud_porcentual': self.similitud_porcentual(mejor_distancia, umbral)
        }
