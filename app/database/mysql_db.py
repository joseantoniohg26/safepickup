"""
SafePickup — Capa de acceso a MySQL
=====================================
Reemplaza a json_db.py en la Fase 2 del proyecto.
Mantiene exactamente la misma interfaz pública (mismas funciones,
mismos parámetros, mismos valores de retorno) para que main.py
no necesite ningún cambio al migrar de JSON a MySQL.

Requiere:
    pip install pymysql

Variables de entorno necesarias (o modificar MYSQL_CONFIG):
    MYSQL_HOST      = localhost
    MYSQL_PORT      = 3306
    MYSQL_USER      = root
    MYSQL_PASSWORD  = tu_contraseña
    MYSQL_DB        = safepickup
"""

import os
import json
from datetime import datetime
import numpy as np
import pymysql
import pymysql.cursors


# ============================================================
# CONFIGURACIÓN DE CONEXIÓN
# ============================================================
# Cambia estos valores según tu instalación de MySQL
MYSQL_CONFIG = {
    # Railway usa MYSQLHOST/MYSQLPORT; local usa MYSQL_HOST/MYSQL_PORT
    'host':     os.getenv('MYSQL_HOST', os.getenv('MYSQLHOST', 'localhost')),
    'port':     int(os.getenv('MYSQL_PORT', os.getenv('MYSQLPORT', '3306'))),
    'user':     os.getenv('MYSQL_USER', os.getenv('MYSQLUSER', 'root')),
    'password': os.getenv('MYSQL_PASSWORD', os.getenv('MYSQLPASSWORD', 'lizandro2009')),
    'database': os.getenv('MYSQL_DATABASE', os.getenv('MYSQLDATABASE', os.getenv('MYSQL_DB', 'safepickup'))),
    'charset':  'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True
}


def _conexion():
    """Abre y retorna una conexión a MySQL."""
    return pymysql.connect(**MYSQL_CONFIG)


def inicializar_schema():
    """Crea las tablas si no existen. Se llama al arrancar la app."""
    try:
        with _conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("""CREATE TABLE IF NOT EXISTS aulas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(50) NOT NULL,
                    edad TINYINT NOT NULL,
                    secciones VARCHAR(10) NOT NULL DEFAULT 'A',
                    color VARCHAR(20) NOT NULL DEFAULT 'blue',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )""")
                cur.execute("""CREATE TABLE IF NOT EXISTS estudiantes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombres VARCHAR(80) NOT NULL,
                    apellidos VARCHAR(80) NOT NULL,
                    fecha_nac DATE,
                    sexo CHAR(1),
                    dni VARCHAR(8),
                    matricula VARCHAR(20) NOT NULL,
                    aula_id INT NOT NULL,
                    seccion CHAR(1) NOT NULL DEFAULT 'A',
                    turno VARCHAR(10) NOT NULL DEFAULT 'Mañana',
                    estado_hoy VARCHAR(20) NOT NULL DEFAULT 'presente',
                    hora_recojo TIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (aula_id) REFERENCES aulas(id) ON DELETE RESTRICT
                )""")
                cur.execute("""CREATE TABLE IF NOT EXISTS apoderados (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombres VARCHAR(80) NOT NULL,
                    apellidos VARCHAR(80) NOT NULL,
                    dni VARCHAR(8) NOT NULL,
                    telefono VARCHAR(12),
                    parentesco VARCHAR(30) NOT NULL,
                    estudiante_id INT,
                    embedding JSON,
                    tiene_embedding TINYINT(1) NOT NULL DEFAULT 0,
                    estado VARCHAR(20) NOT NULL DEFAULT 'activo',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE SET NULL
                )""")
                cur.execute("""CREATE TABLE IF NOT EXISTS eventos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tipo VARCHAR(30) NOT NULL,
                    apoderado_id INT,
                    nombre VARCHAR(160),
                    confianza DECIMAL(5,2),
                    motivo VARCHAR(255),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (apoderado_id) REFERENCES apoderados(id) ON DELETE SET NULL
                )""")
                cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario VARCHAR(30) NOT NULL UNIQUE,
                    password VARCHAR(60) NOT NULL,
                    nombre VARCHAR(80) NOT NULL,
                    rol VARCHAR(20) NOT NULL DEFAULT 'admin',
                    activo TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )""")
                cur.execute("""INSERT IGNORE INTO aulas (nombre, edad, secciones, color) VALUES
                    ('Mariposas',3,'A,B','amber'),('Pollitos',4,'A,B','green'),
                    ('Ositos',5,'A','blue'),('Estrellitas',4,'A,B,C','purple')""")
                cur.execute("""INSERT IGNORE INTO usuarios (usuario, password, nombre, rol) VALUES
                    ('admin','safepickup2026','Directora Sánchez','admin'),
                    ('director','director123','Director General','director')""")
        print("[OK] Schema inicializado correctamente")
    except Exception as e:
        print(f"[WARN] Error inicializando schema: {e}")


def verificar_conexion():
    """
    Verifica que la conexión a MySQL esté disponible.
    Retorna True si la conexión es exitosa, False si falla.
    """
    try:
        with _conexion() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"[MySQL] Error de conexión: {e}")
        return False


# ============================================================
# APODERADOS
# ============================================================

def registrar_apoderado(nombre, parentesco, dni, embedding,
                        estudiante_id=None, telefono=None):
    """
    Registra un nuevo apoderado con su embedding facial.

    Parámetros:
        nombre        : nombre completo (ej: "Carmen Mamani Quispe")
        parentesco    : "Madre", "Padre", "Tutor", etc.
        dni           : 8 dígitos
        embedding     : numpy array de 512 dimensiones
        estudiante_id : ID del estudiante a cargo (opcional)
        telefono      : número de celular (opcional)

    Retorna:
        id del nuevo apoderado insertado
    """
    # Separar nombres y apellidos (convenio: últimas 2 palabras = apellidos)
    partes = nombre.strip().split()
    if len(partes) >= 3:
        apellidos = ' '.join(partes[-2:])
        nombres   = ' '.join(partes[:-2])
    elif len(partes) == 2:
        nombres, apellidos = partes
    else:
        nombres, apellidos = nombre, ''

    # Convertir embedding a JSON para almacenar en MySQL
    embedding_json = json.dumps(
        embedding.tolist() if hasattr(embedding, 'tolist') else embedding
    )

    with _conexion() as conn:
        with conn.cursor() as cur:
            # Validar que estudiante_id exista antes de usarlo como FK
            estudiante_id_seguro = None
            if estudiante_id:
                cur.execute(
                    "SELECT id FROM estudiantes WHERE id = %s",
                    (estudiante_id,)
                )
                if cur.fetchone():
                    estudiante_id_seguro = estudiante_id
                else:
                    print(f"[AVISO] estudiante_id={estudiante_id} no existe en la tabla estudiantes. "
                          f"Verifique que el estudiante fue registrado correctamente en MySQL.")

            cur.execute("""
                INSERT INTO apoderados
                    (nombres, apellidos, dni, telefono, parentesco,
                     estudiante_id, embedding, tiene_embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """, (nombres, apellidos, dni, telefono, parentesco,
                  estudiante_id_seguro, embedding_json))
            return cur.lastrowid


def listar_apoderados():
    """Retorna todos los apoderados sin el embedding."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, CONCAT(a.nombres, ' ', a.apellidos) AS nombre,
                       a.dni, a.telefono, a.parentesco, a.tiene_embedding,
                       a.estado, a.created_at AS fecha_registro,
                       a.estudiante_id,
                       CONCAT(e.nombres, ' ', e.apellidos) AS estudiante_nombre
                FROM apoderados a
                LEFT JOIN estudiantes e ON a.estudiante_id = e.id
                ORDER BY a.created_at DESC
            """)
            return cur.fetchall()


def obtener_apoderados_con_embedding():
    """
    Retorna apoderados con su embedding como numpy array.
    Usado por el motor de verificación.
    """
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, CONCAT(nombres, ' ', apellidos) AS nombre,
                       parentesco, dni, estudiante_id, embedding
                FROM apoderados
                WHERE tiene_embedding = 1 AND estado = 'activo'
            """)
            rows = cur.fetchall()

    resultado = []
    for row in rows:
        if row['embedding']:
            embedding_list = json.loads(row['embedding'])
            resultado.append({
                'id_apoderado': row['id'],
                'nombre':       row['nombre'],
                'parentesco':   row['parentesco'],
                'dni':          row['dni'],
                'estudiante_id': row.get('estudiante_id'),
                'embedding':    np.array(embedding_list, dtype=np.float32)
            })
    return resultado


def eliminar_apoderado(id_apoderado):
    """Elimina un apoderado por ID."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM apoderados WHERE id = %s", (id_apoderado,))


# ============================================================
# ESTUDIANTES
# ============================================================

def listar_estudiantes():
    """Retorna todos los estudiantes con nombre de aula."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id,
                       CONCAT(e.nombres, ' ', e.apellidos) AS nombre,
                       e.nombres, e.apellidos,
                       e.fecha_nac, e.sexo, e.dni, e.matricula,
                       e.seccion, e.turno, e.estado_hoy, e.hora_recojo,
                       a.nombre AS aula, e.aula_id,
                       COUNT(ap.id) AS num_apoderados
                FROM estudiantes e
                LEFT JOIN aulas a ON e.aula_id = a.id
                LEFT JOIN apoderados ap ON ap.estudiante_id = e.id
                GROUP BY e.id
                ORDER BY e.apellidos, e.nombres
            """)
            return cur.fetchall()


def registrar_estudiante(nombres, apellidos, fecha_nac, sexo,
                         aula_id, seccion, turno, matricula, dni=None):
    """Registra un nuevo estudiante."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO estudiantes
                    (nombres, apellidos, fecha_nac, sexo, dni,
                     matricula, aula_id, seccion, turno)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (nombres, apellidos, fecha_nac, sexo, dni,
                  matricula, aula_id, seccion, turno))
            return cur.lastrowid


def eliminar_estudiante(id_estudiante):
    """Elimina un estudiante por ID."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM estudiantes WHERE id = %s", (id_estudiante,))


def editar_estudiante(id_estudiante, nombres, apellidos, fecha_nac, sexo,
                      aula_id, seccion, turno, matricula, dni=None):
    """Actualiza los datos de un estudiante existente."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE estudiantes
                SET nombres = %s, apellidos = %s, fecha_nac = %s,
                    sexo = %s, dni = %s, matricula = %s,
                    aula_id = %s, seccion = %s, turno = %s
                WHERE id = %s
            """, (nombres, apellidos, fecha_nac, sexo, dni,
                  matricula, aula_id, seccion, turno, id_estudiante))


def editar_apoderado(id_apoderado, nombre, dni, telefono, parentesco,
                     estudiante_id=None):
    """Actualiza datos del apoderado (sin tocar el embedding facial)."""
    partes = nombre.strip().split()
    if len(partes) >= 3:
        apellidos = ' '.join(partes[-2:])
        nombres   = ' '.join(partes[:-2])
    elif len(partes) == 2:
        nombres, apellidos = partes
    else:
        nombres, apellidos = nombre, ''

    with _conexion() as conn:
        with conn.cursor() as cur:
            # Validar que estudiante_id exista antes de usarlo como FK
            estudiante_id_seguro = None
            if estudiante_id:
                cur.execute("SELECT id FROM estudiantes WHERE id = %s", (estudiante_id,))
                if cur.fetchone():
                    estudiante_id_seguro = estudiante_id
                else:
                    print(f"[AVISO] editar_apoderado: estudiante_id={estudiante_id} no existe en MySQL.")

            cur.execute("""
                UPDATE apoderados
                SET nombres = %s, apellidos = %s, dni = %s,
                    telefono = %s, parentesco = %s, estudiante_id = %s
                WHERE id = %s
            """, (nombres, apellidos, dni, telefono, parentesco,
                  estudiante_id_seguro, id_apoderado))


def editar_aula(id_aula, nombre, edad, secciones, color='blue'):
    """Actualiza los datos de un aula existente."""
    secciones_str = ','.join(secciones) if isinstance(secciones, list) else secciones
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE aulas
                SET nombre = %s, edad = %s, secciones = %s, color = %s
                WHERE id = %s
            """, (nombre, edad, secciones_str, color, id_aula))


def marcar_recogido(id_estudiante):
    """Marca a un estudiante como recogido en el día actual."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE estudiantes
                SET estado_hoy = 'recogido', hora_recojo = CURTIME()
                WHERE id = %s
            """, (id_estudiante,))


# ============================================================
# AULAS
# ============================================================

def listar_aulas():
    """Retorna todas las aulas con conteo de estudiantes."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, a.nombre, a.edad, a.secciones, a.color,
                       COUNT(e.id) AS num_estudiantes
                FROM aulas a
                LEFT JOIN estudiantes e ON e.aula_id = a.id
                GROUP BY a.id
                ORDER BY a.edad, a.nombre
            """)
            return cur.fetchall()


def registrar_aula(nombre, edad, secciones, color='blue'):
    """
    Registra una nueva aula.

    Parámetros:
        secciones : lista de strings, ej: ['A', 'B', 'C']
    """
    secciones_str = ','.join(secciones) if isinstance(secciones, list) else secciones
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO aulas (nombre, edad, secciones, color)
                VALUES (%s, %s, %s, %s)
            """, (nombre, edad, secciones_str, color))
            return cur.lastrowid


def eliminar_aula(id_aula):
    """Elimina un aula. Falla si tiene estudiantes asignados."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM aulas WHERE id = %s", (id_aula,))


# ============================================================
# EVENTOS (historial de verificaciones)
# ============================================================

def registrar_evento(tipo, apoderado_id=None, nombre=None,
                     confianza=None, motivo=None):
    """
    Registra un evento en el historial.

    tipos válidos:
        'autorizado'         : recojo exitoso
        'no_autorizado'      : persona no registrada
        'spoofing_detectado' : intento de suplantación
    """
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO eventos
                    (tipo, apoderado_id, nombre, confianza, motivo)
                VALUES (%s, %s, %s, %s, %s)
            """, (tipo, apoderado_id, nombre, confianza, motivo))
            return cur.lastrowid


def listar_eventos(limite=50, fecha=None, tipo=None):
    """
    Retorna los últimos N eventos, con filtros opcionales.

    Parámetros:
        limite : máximo de resultados
        fecha  : filtrar por fecha (string 'YYYY-MM-DD')
        tipo   : filtrar por tipo de evento
    """
    where = []
    params = []

    if fecha:
        where.append("DATE(e.created_at) = %s")
        params.append(fecha)

    if tipo:
        where.append("e.tipo = %s")
        params.append(tipo)

    where_sql = 'WHERE ' + ' AND '.join(where) if where else ''
    params.append(limite)

    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT e.id, e.tipo, e.apoderado_id,
                       e.nombre, e.confianza, e.motivo,
                       e.created_at AS fecha
                FROM eventos e
                {where_sql}
                ORDER BY e.created_at DESC
                LIMIT %s
            """, params)
            rows = cur.fetchall()

    # Convertir created_at a string ISO para compatibilidad con el frontend
    for row in rows:
        if row['fecha']:
            row['fecha'] = row['fecha'].isoformat()
    return rows


def contar_eventos_hoy():
    """Cuenta eventos del día actual agrupados por tipo."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    SUM(tipo = 'autorizado')         AS autorizados,
                    SUM(tipo = 'recojo_confirmado')  AS recojos,
                    SUM(tipo = 'no_autorizado')      AS rechazados,
                    SUM(tipo = 'spoofing_detectado') AS spoofing,
                    COUNT(*)                          AS total
                FROM eventos
                WHERE DATE(created_at) = CURDATE()
            """)
            row = cur.fetchone()
            return {
                'autorizados': int(row['autorizados'] or 0),
                'recojos':     int(row['recojos']     or 0),
                'rechazados':  int(row['rechazados']  or 0),
                'spoofing':    int(row['spoofing']    or 0),
                'total':       int(row['total']       or 0)
            }


# ============================================================
# USUARIOS
# ============================================================

def verificar_usuario(usuario, password):
    """
    Verifica las credenciales de un usuario.
    Retorna los datos del usuario si son correctas, None si no.

    NOTA: En producción real usar bcrypt para el password.
    """
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, usuario, nombre, rol
                FROM usuarios
                WHERE usuario = %s AND password = %s AND activo = 1
            """, (usuario, password))
            return cur.fetchone()


# ============================================================
# UTILIDADES
# ============================================================

def estadisticas_completas():
    """Retorna estadísticas generales para el dashboard."""
    with _conexion() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM apoderados")
            total_apoderados = cur.fetchone()['total']

            cur.execute("SELECT COUNT(*) AS total FROM estudiantes")
            total_estudiantes = cur.fetchone()['total']

    eventos_hoy = contar_eventos_hoy()

    return {
        'apoderados_registrados': total_apoderados,
        'estudiantes_registrados': total_estudiantes,
        'eventos_hoy': eventos_hoy
    }


if __name__ == '__main__':
    print("Verificando conexión a MySQL...")
    if verificar_conexion():
        print("[OK] Conectado correctamente a MySQL")
        stats = estadisticas_completas()
        print(f"     Apoderados: {stats['apoderados_registrados']}")
        print(f"     Estudiantes: {stats['estudiantes_registrados']}")
        print(f"     Eventos hoy: {stats['eventos_hoy']['total']}")
    else:
        print("[ERROR] No se pudo conectar a MySQL")
        print("        Verifica host, puerto, usuario y contraseña en MYSQL_CONFIG")