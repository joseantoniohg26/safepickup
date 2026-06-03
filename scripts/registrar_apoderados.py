"""
SafePickup — Registrar apoderados desde carpeta de fotos
==========================================================
Lee fotos de data/fotos_apoderados/ y los registra en MySQL.

Nombre de archivos: nombre_apellido_parentesco.jpg
Ejemplo:
    carmen_mamani_madre.jpg  → Carmen Mamani (Madre)
    juan_perez_padre.jpg     → Juan Perez (Padre)

Uso:
    python scripts/registrar_apoderados.py
"""

import sys, os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.detector  import DetectorFacial
from app.ai.embedder  import GeneradorEmbeddings
from app.database     import mysql_db as db


def parsear_nombre(filename):
    nombre_sin_ext = Path(filename).stem
    partes = nombre_sin_ext.split('_')
    parentesco = partes[-1].capitalize()
    nombre = ' '.join(p.capitalize() for p in partes[:-1])
    return nombre, parentesco


def main():
    print("=" * 60)
    print("  SafePickup — Registro de apoderados desde fotos")
    print("=" * 60)

    carpeta = Path("data/fotos_apoderados")
    if not carpeta.exists():
        carpeta.mkdir(parents=True, exist_ok=True)
        print(f"\nCarpeta creada: {carpeta}")
        print("Coloca fotos con el formato: nombre_apellido_parentesco.jpg")
        return

    fotos = list(carpeta.glob("*.jpg")) + list(carpeta.glob("*.jpeg")) + list(carpeta.glob("*.png"))
    if not fotos:
        print(f"\nNo se encontraron fotos en {carpeta}")
        return

    print(f"\nEncontradas {len(fotos)} foto(s). Cargando modelos de IA...")
    detector = DetectorFacial()
    embedder = GeneradorEmbeddings()
    print(f"[OK] Modelos listos en {detector.device.upper()}\n")

    ok = 0
    fallo = 0

    for foto in fotos:
        print(f"Procesando: {foto.name}")
        try:
            nombre, parentesco = parsear_nombre(foto.name)
            print(f"  → {nombre} ({parentesco})")
        except Exception:
            print(f"  [ERROR] Nombre de archivo inválido")
            fallo += 1
            continue

        rostro = detector.detectar_un_rostro(str(foto))
        if rostro is None:
            print(f"  [ERROR] No se detectó rostro")
            fallo += 1
            continue

        print(f"  Confianza MTCNN: {rostro['confianza']:.2%}")
        embedding = embedder.generar(rostro['rostro_tensor'])

        id_nuevo = db.registrar_apoderado(
            nombre=nombre, parentesco=parentesco,
            dni=f"{70000000 + ok * 137 % 9999999:08d}",
            embedding=embedding
        )
        print(f"  [OK] Registrado con ID {id_nuevo}\n")
        ok += 1

    print("=" * 60)
    print(f"  Registrados: {ok}")
    print(f"  Fallidos:    {fallo}")
    print("=" * 60)

    if ok > 0:
        print("\nApoderados en la base de datos:")
        for ap in db.listar_apoderados():
            print(f"  - {ap['nombre']} ({ap['parentesco']})")


if __name__ == '__main__':
    main()
