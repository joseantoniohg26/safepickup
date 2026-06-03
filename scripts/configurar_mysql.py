"""
SafePickup — Configurar MySQL
================================
Crea la base de datos 'safepickup' y todas las tablas necesarias.

ANTES de ejecutar:
  1. Tener MySQL Server instalado y corriendo
  2. Editar MYSQL_PASSWORD abajo con tu contraseña real
  3. Ejecutar: python scripts/configurar_mysql.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# EDITA SOLO ESTA LÍNEA — pon tu contraseña de MySQL
# ============================================================
MYSQL_PASSWORD = 'lizandro2009'
# ============================================================

MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_DB   = 'safepickup'


def main():
    try:
        import pymysql
    except ImportError:
        print("[ERROR] pymysql no instalado.")
        print("        Ejecuta: pip install pymysql")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  SafePickup — Configurando MySQL")
    print("=" * 60)
    print()

    # ---------------------------------------------------------
    # PASO 1: Conectar SIN base de datos y crear 'safepickup'
    # ---------------------------------------------------------
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST, port=MYSQL_PORT,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            charset='utf8mb4', autocommit=True
        )
        print(f"[OK] Conectado a MySQL en {MYSQL_HOST}:{MYSQL_PORT}")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        print()
        print("Verifica que:")
        print("  - MySQL Server esté corriendo (busca 'MySQL80' en Servicios)")
        print("  - La contraseña MYSQL_PASSWORD sea correcta")
        sys.exit(1)

    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    print(f"[OK] Base de datos '{MYSQL_DB}' lista")
    conn.close()

    # ---------------------------------------------------------
    # PASO 2: Conectar CON la base de datos y crear tablas
    # ---------------------------------------------------------
    conn = pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset='utf8mb4', autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

    with conn.cursor() as cur:

        # TABLA: aulas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS aulas (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                nombre     VARCHAR(50)  NOT NULL,
                edad       TINYINT      NOT NULL,
                secciones  VARCHAR(20)  NOT NULL DEFAULT 'A',
                color      VARCHAR(20)  NOT NULL DEFAULT 'blue',
                created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Tabla 'aulas' lista")

        # TABLA: estudiantes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS estudiantes (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                nombres     VARCHAR(80)  NOT NULL,
                apellidos   VARCHAR(80)  NOT NULL,
                fecha_nac   DATE,
                sexo        CHAR(1),
                dni         VARCHAR(8),
                matricula   VARCHAR(20)  NOT NULL,
                aula_id     INT          NOT NULL,
                seccion     CHAR(1)      NOT NULL DEFAULT 'A',
                turno       VARCHAR(10)  NOT NULL DEFAULT 'Mañana',
                estado_hoy  VARCHAR(20)  NOT NULL DEFAULT 'presente',
                hora_recojo TIME,
                created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (aula_id) REFERENCES aulas(id) ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Tabla 'estudiantes' lista")

        # TABLA: apoderados
        cur.execute("""
            CREATE TABLE IF NOT EXISTS apoderados (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                nombres         VARCHAR(80)  NOT NULL,
                apellidos       VARCHAR(80)  NOT NULL,
                dni             VARCHAR(8)   NOT NULL,
                telefono        VARCHAR(12),
                parentesco      VARCHAR(30)  NOT NULL,
                estudiante_id   INT,
                embedding       LONGTEXT,
                tiene_embedding TINYINT(1)   NOT NULL DEFAULT 0,
                estado          VARCHAR(20)  NOT NULL DEFAULT 'activo',
                created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Tabla 'apoderados' lista")

        # TABLA: eventos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS eventos (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                tipo         VARCHAR(30)   NOT NULL,
                apoderado_id INT,
                nombre       VARCHAR(160),
                confianza    DECIMAL(5,2),
                motivo       VARCHAR(255),
                created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (apoderado_id) REFERENCES apoderados(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Tabla 'eventos' lista")

        # TABLA: usuarios
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                usuario    VARCHAR(30)  NOT NULL UNIQUE,
                password   VARCHAR(60)  NOT NULL,
                nombre     VARCHAR(80)  NOT NULL,
                rol        VARCHAR(20)  NOT NULL DEFAULT 'admin',
                activo     TINYINT(1)   NOT NULL DEFAULT 1,
                created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] Tabla 'usuarios' lista")

        # Índices para consultas frecuentes
        for sql in [
            "CREATE INDEX IF NOT EXISTS idx_eventos_tipo  ON eventos(tipo)",
            "CREATE INDEX IF NOT EXISTS idx_eventos_fecha ON eventos(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_apo_dni       ON apoderados(dni)",
        ]:
            try:
                cur.execute(sql)
            except Exception:
                pass  # Ya existe el índice

        # ---------------------------------------------------------
        # DATOS INICIALES
        # ---------------------------------------------------------

        # Aulas del nivel inicial (solo si no existen)
        cur.execute("SELECT COUNT(*) AS n FROM aulas")
        if cur.fetchone()['n'] == 0:
            cur.executemany(
                "INSERT INTO aulas (nombre, edad, secciones, color) VALUES (%s,%s,%s,%s)",
                [
                    ('Mariposas',   3, 'A,B',   'amber'),
                    ('Pollitos',    4, 'A,B',   'green'),
                    ('Ositos',      5, 'A',     'blue'),
                    ('Estrellitas', 4, 'A,B,C', 'purple'),
                ]
            )
            print("[OK] Aulas por defecto insertadas (Mariposas, Pollitos, Ositos, Estrellitas)")
        else:
            print("[OK] Aulas ya existían — no se modificaron")

        # Usuarios del sistema (solo si no existen)
        cur.execute("SELECT COUNT(*) AS n FROM usuarios")
        if cur.fetchone()['n'] == 0:
            cur.executemany(
                "INSERT INTO usuarios (usuario, password, nombre, rol) VALUES (%s,%s,%s,%s)",
                [
                    ('admin',    'safepickup2026', 'Directora Sánchez', 'admin'),
                    ('director', 'director123',    'Director General',  'director'),
                ]
            )
            print("[OK] Usuarios por defecto insertados (admin, director)")
        else:
            print("[OK] Usuarios ya existían — no se modificaron")

    conn.close()

    # ---------------------------------------------------------
    # PASO 3: Actualizar mysql_db.py con la contraseña correcta
    # ---------------------------------------------------------
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'app', 'database', 'mysql_db.py'
    )
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Actualizar contraseña en MYSQL_CONFIG
        import re
        content = re.sub(
            r"'password':\s*os\.getenv\('MYSQL_PASSWORD',\s*'[^']*'\)",
            f"'password': os.getenv('MYSQL_PASSWORD', '{MYSQL_PASSWORD}')",
            content
        )
        with open(db_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("[OK] Contraseña actualizada en mysql_db.py")

    # ---------------------------------------------------------
    # RESUMEN FINAL
    # ---------------------------------------------------------
    print()
    print("=" * 60)
    print("  ¡Configuración completada!")
    print()
    print("  Base de datos: safepickup")
    print("  Tablas:        aulas, estudiantes, apoderados,")
    print("                 eventos, usuarios")
    print()
    print("  Próximo paso:")
    print("  python scripts/iniciar_servidor.py")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()