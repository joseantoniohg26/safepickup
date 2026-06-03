"""
SafePickup - Base de datos simple en JSON
==========================================
Implementación temporal de almacenamiento en archivos JSON.

En la versión final del proyecto esto se migrará a MySQL, pero para
la fase de integración HTML-Python usamos JSON porque:
    - No requiere instalación adicional de MySQL
    - Es portable (funciona en cualquier PC sin configurar)
    - Permite ver y editar los datos manualmente
    - Es suficiente para los volúmenes de un colegio inicial (<200 apoderados)

Las tablas se simulan como archivos JSON en data/database/.
"""

import json
import os
from datetime import datetime
from pathlib import Path
import numpy as np


# Ruta base de la "base de datos"
RUTA_DB = Path("data/database")
RUTA_DB.mkdir(parents=True, exist_ok=True)

# Archivos que simulan tablas
TABLA_APODERADOS = RUTA_DB / "apoderados.json"
TABLA_ESTUDIANTES = RUTA_DB / "estudiantes.json"
TABLA_EVENTOS = RUTA_DB / "eventos.json"


def _leer_tabla(ruta):
    """Lee un archivo JSON y devuelve su contenido."""
    if not ruta.exists():
        return []
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def _escribir_tabla(ruta, datos):
    """Guarda datos en un archivo JSON."""
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


# ============================================================
# APODERADOS
# ============================================================

def listar_apoderados():
    """Devuelve todos los apoderados registrados."""
    return _leer_tabla(TABLA_APODERADOS)


def obtener_apoderados_con_embedding():
    """
    Devuelve apoderados con su embedding convertido a numpy array.
    Útil para el motor de verificación.
    """
    apoderados = listar_apoderados()
    resultado = []
    for ap in apoderados:
        if 'embedding' in ap and ap['embedding']:
            resultado.append({
                'id_apoderado': ap['id'],
                'nombre': ap['nombre'],
                'parentesco': ap.get('parentesco', ''),
                'dni': ap.get('dni', ''),
                'embedding': np.array(ap['embedding'], dtype=np.float32)
            })
    return resultado


def registrar_apoderado(nombre, parentesco, dni, embedding, estudiante_id=None):
    """
    Registra un nuevo apoderado en el sistema.

    Parámetros:
        nombre: nombre completo del apoderado
        parentesco: 'Padre', 'Madre', 'Tutor', etc.
        dni: documento de identidad
        embedding: array NumPy de 512 dimensiones (FaceNet)
        estudiante_id: ID del estudiante asociado (opcional)
    """
    apoderados = listar_apoderados()

    nuevo_id = max([ap['id'] for ap in apoderados], default=0) + 1

    nuevo = {
        'id': nuevo_id,
        'nombre': nombre,
        'parentesco': parentesco,
        'dni': dni,
        'estudiante_id': estudiante_id,
        'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
        'fecha_registro': datetime.now().isoformat()
    }

    apoderados.append(nuevo)
    _escribir_tabla(TABLA_APODERADOS, apoderados)

    return nuevo_id


def eliminar_apoderado(id_apoderado):
    """Elimina un apoderado por ID."""
    apoderados = listar_apoderados()
    apoderados = [ap for ap in apoderados if ap['id'] != id_apoderado]
    _escribir_tabla(TABLA_APODERADOS, apoderados)


# ============================================================
# ESTUDIANTES
# ============================================================

def listar_estudiantes():
    return _leer_tabla(TABLA_ESTUDIANTES)


def registrar_estudiante(nombre, aula, turno='Mañana'):
    """Registra un nuevo estudiante."""
    estudiantes = listar_estudiantes()
    nuevo_id = max([e['id'] for e in estudiantes], default=0) + 1

    nuevo = {
        'id': nuevo_id,
        'nombre': nombre,
        'aula': aula,
        'turno': turno,
        'fecha_registro': datetime.now().isoformat()
    }

    estudiantes.append(nuevo)
    _escribir_tabla(TABLA_ESTUDIANTES, estudiantes)
    return nuevo_id


# ============================================================
# EVENTOS (historial de recojos)
# ============================================================

def registrar_evento(tipo, apoderado_id=None, nombre=None, confianza=None, motivo=None):
    """
    Registra un evento en el historial.

    Tipos:
        'autorizado'        : Acceso permitido
        'no_autorizado'     : Persona no registrada
        'spoofing_detectado': Intento de suplantación
    """
    eventos = _leer_tabla(TABLA_EVENTOS)
    nuevo_id = max([e['id'] for e in eventos], default=0) + 1

    nuevo = {
        'id': nuevo_id,
        'tipo': tipo,
        'apoderado_id': apoderado_id,
        'nombre': nombre,
        'confianza': confianza,
        'motivo': motivo,
        'fecha': datetime.now().isoformat()
    }

    eventos.append(nuevo)
    _escribir_tabla(TABLA_EVENTOS, eventos)
    return nuevo_id


def listar_eventos(limite=50):
    """Devuelve los últimos N eventos."""
    eventos = _leer_tabla(TABLA_EVENTOS)
    # Más recientes primero
    return list(reversed(eventos))[:limite]


def contar_eventos_hoy():
    """Cuenta eventos del día actual."""
    eventos = _leer_tabla(TABLA_EVENTOS)
    hoy = datetime.now().date().isoformat()
    return {
        'autorizados': sum(1 for e in eventos if e['tipo'] == 'autorizado' and e['fecha'].startswith(hoy)),
        'rechazados': sum(1 for e in eventos if e['tipo'] == 'no_autorizado' and e['fecha'].startswith(hoy)),
        'spoofing': sum(1 for e in eventos if e['tipo'] == 'spoofing_detectado' and e['fecha'].startswith(hoy)),
        'total': sum(1 for e in eventos if e['fecha'].startswith(hoy))
    }


if __name__ == "__main__":
    print("Verificando base de datos JSON...")
    print(f"Apoderados registrados: {len(listar_apoderados())}")
    print(f"Estudiantes registrados: {len(listar_estudiantes())}")
    print(f"Eventos totales: {len(_leer_tabla(TABLA_EVENTOS))}")
    print(f"Eventos hoy: {contar_eventos_hoy()}")
