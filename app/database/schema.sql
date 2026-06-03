-- ============================================================
-- SafePickup — Schema MySQL
-- Base de datos para el sistema de verificación facial
-- Ejecutar una sola vez para crear todas las tablas
-- ============================================================

CREATE DATABASE IF NOT EXISTS safepickup CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE safepickup;

-- ------------------------------------------------------------
-- AULAS
-- Almacena las aulas del nivel inicial con sus secciones
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aulas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(50)  NOT NULL,              -- Ej: Mariposas, Pollitos
    edad        TINYINT      NOT NULL,               -- 3, 4 o 5 años
    secciones   VARCHAR(10)  NOT NULL DEFAULT 'A',  -- Ej: 'A', 'A,B', 'A,B,C'
    color       VARCHAR(20)  NOT NULL DEFAULT 'blue',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Aulas por defecto del nivel inicial
INSERT INTO aulas (nombre, edad, secciones, color) VALUES
('Mariposas',  3, 'A,B',   'amber'),
('Pollitos',   4, 'A,B',   'green'),
('Ositos',     5, 'A',     'blue'),
('Estrellitas',4, 'A,B,C', 'purple')
ON DUPLICATE KEY UPDATE nombre = nombre;

-- ------------------------------------------------------------
-- ESTUDIANTES
-- Niños del nivel inicial registrados en el sistema
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estudiantes (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    nombres      VARCHAR(80)  NOT NULL,
    apellidos    VARCHAR(80)  NOT NULL,
    fecha_nac    DATE,
    sexo         CHAR(1),                            -- 'M' o 'F'
    dni          VARCHAR(8),
    matricula    VARCHAR(20)  NOT NULL,
    aula_id      INT          NOT NULL,
    seccion      CHAR(1)      NOT NULL DEFAULT 'A',
    turno        VARCHAR(10)  NOT NULL DEFAULT 'Mañana',
    estado_hoy   VARCHAR(20)  NOT NULL DEFAULT 'presente',
    hora_recojo  TIME,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aula_id) REFERENCES aulas(id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- APODERADOS
-- Personas autorizadas a recoger estudiantes
-- El embedding es un vector de 512 floats almacenado como JSON
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS apoderados (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombres         VARCHAR(80)  NOT NULL,
    apellidos       VARCHAR(80)  NOT NULL,
    dni             VARCHAR(8)   NOT NULL,
    telefono        VARCHAR(12),
    parentesco      VARCHAR(30)  NOT NULL,           -- Madre, Padre, Tutor...
    estudiante_id   INT,                             -- Estudiante a cargo (opcional)
    embedding       JSON,                            -- Array de 512 floats
    tiene_embedding TINYINT(1)   NOT NULL DEFAULT 0,
    estado          VARCHAR(20)  NOT NULL DEFAULT 'activo',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- EVENTOS
-- Historial de todas las verificaciones y alertas del sistema
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS eventos (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    tipo           VARCHAR(30)  NOT NULL,            -- autorizado | no_autorizado | spoofing_detectado
    apoderado_id   INT,                              -- NULL si no fue identificado
    nombre         VARCHAR(160),                     -- nombre del apoderado (cache)
    confianza      DECIMAL(5,2),                     -- % de similitud
    motivo         VARCHAR(255),                     -- motivo de rechazo o detalles
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (apoderado_id) REFERENCES apoderados(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- USUARIOS
-- Personal autorizado a usar el sistema
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario     VARCHAR(30)  NOT NULL UNIQUE,
    password    VARCHAR(60)  NOT NULL,               -- bcrypt hash
    nombre      VARCHAR(80)  NOT NULL,
    rol         VARCHAR(20)  NOT NULL DEFAULT 'admin',
    activo      TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Usuarios por defecto (passwords: safepickup2026 y director123)
INSERT IGNORE INTO usuarios (usuario, password, nombre, rol) VALUES
('admin',    'safepickup2026', 'Directora Sánchez', 'admin'),
('director', 'director123',    'Director General',  'director');

-- ------------------------------------------------------------
-- ÍNDICES para consultas frecuentes
-- ------------------------------------------------------------
CREATE INDEX idx_eventos_tipo     ON eventos  (tipo);
CREATE INDEX idx_eventos_fecha    ON eventos  (created_at);
CREATE INDEX idx_apoderados_dni   ON apoderados (dni);
CREATE INDEX idx_estudiantes_aula ON estudiantes (aula_id);
