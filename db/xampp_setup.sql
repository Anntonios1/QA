-- ============================================================
--  SCRIPT DE INSTALACIÓN - MySQL/MariaDB (XAMPP)
-- ============================================================
--  Sistema: ControlCash - Control de Gastos Personales
--  Versión: 1.0.0
--  Fecha: 2026-03-19
-- ============================================================
--  
--  INSTRUCCIONES:
--  1. Abrir XAMPP Control Panel
--  2. Iniciar Apache y MySQL
--  3. Abrir phpMyAdmin (http://localhost/phpmyadmin)
--  4. Ir a la pestaña "SQL"
--  5. Copiar y ejecutar este script completo
--
--  O desde terminal:
--    mysql -u root -p < db/xampp_setup.sql
--
-- ============================================================
--  Normas aplicadas:
--    - ISO/IEC 27001: Seguridad de información
--    - ISO/IEC 12207: Ciclo de vida del software
--    - ISO 9001:2015: Gestión de calidad
-- ============================================================

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS gastos_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE gastos_db;

-- ============================================================
-- TABLA: usuarios
-- Gestión de usuarios con autenticación segura
-- ============================================================
-- [NORMA: ISO 9126 - Funcionalidad/Seguridad] Restricción de unicidad para garantizar integridad de datos del usuario
-- [NORMA: ISO/IEC 25000] Atributo de confiabilidad: integridad referencial de la entidad Usuario
CREATE TABLE IF NOT EXISTS usuarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    email           VARCHAR(254) NOT NULL UNIQUE,
    -- [NORMA: ISO/IEC 27001 - Control A.10.1] Almacenamiento de credenciales cifradas, nunca en texto plano
    password_hash   TEXT NOT NULL COMMENT 'PBKDF2-SHA256 + 16-byte salt + 100k iterations',
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo          TINYINT NOT NULL DEFAULT 1,
    CHECK (CHAR_LENGTH(nombre) >= 2),
    CHECK (activo IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Usuarios del sistema con autenticación segura';

-- ============================================================
-- TABLA: refresh_tokens
-- Tokens JWT de refresco (ISO/IEC 27001)
-- ============================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    token_hash      VARCHAR(64) NOT NULL UNIQUE COMMENT 'SHA-256 del refresh token',
    expires_at      TIMESTAMP NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked         TINYINT NOT NULL DEFAULT 0,
    device_info     VARCHAR(255) COMMENT 'User-Agent o identificador del dispositivo',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CHECK (revoked IN (0, 1)),
    INDEX idx_refresh_usuario (usuario_id),
    INDEX idx_refresh_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tokens JWT de refresco para autenticación stateless';

-- ============================================================
-- TABLA: tipos_movimiento
-- Catalogo de tipos de movimiento
-- ============================================================
CREATE TABLE IF NOT EXISTS tipos_movimiento (
    id          TINYINT PRIMARY KEY,
    codigo      VARCHAR(10) NOT NULL UNIQUE,
    CHECK (codigo IN ('ingreso', 'gasto'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Catalogo de tipos de movimiento';

INSERT INTO tipos_movimiento (id, codigo) VALUES
    (1, 'ingreso'),
    (2, 'gasto')
ON DUPLICATE KEY UPDATE codigo = VALUES(codigo);

-- ============================================================
-- TABLA: categorias
-- Catálogo de categorías para movimientos
-- ============================================================
CREATE TABLE IF NOT EXISTS categorias (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    tipo_id     TINYINT NOT NULL,
    icono       VARCHAR(10) DEFAULT '💰',
    activo      TINYINT NOT NULL DEFAULT 1,
    CHECK (CHAR_LENGTH(nombre) >= 2),
    CHECK (activo IN (0, 1)),
    FOREIGN KEY (tipo_id) REFERENCES tipos_movimiento(id) ON DELETE RESTRICT,
    INDEX idx_cat_tipo_id (tipo_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Catálogo de categorías para clasificar movimientos';

-- ============================================================
-- TABLA: movimientos
-- Registro de ingresos y gastos
-- ============================================================
CREATE TABLE IF NOT EXISTS movimientos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    categoria_id    INT NOT NULL,
    tipo_id         TINYINT NOT NULL,
    monto           DECIMAL(12,2) NOT NULL,
    descripcion     TEXT COMMENT 'Puede cifrarse con AES-256-GCM',
    fecha           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_registro  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- [NORMA: ISO/IEC 25000 - Característica de Fiabilidad] Integridad referencial entre movimientos y usuario propietario
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT,
    FOREIGN KEY (tipo_id) REFERENCES tipos_movimiento(id) ON DELETE RESTRICT,
    CHECK (monto > 0),
    -- [NORMA: ISO 9126 - Eficiencia] Índice para optimizar consultas frecuentes de movimientos por usuario
    INDEX idx_mov_usuario (usuario_id),
    INDEX idx_mov_fecha (fecha),
    INDEX idx_mov_tipo_id (tipo_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Registro de ingresos y gastos del usuario';

-- ============================================================
-- TABLA: presupuestos
-- Límites de gasto mensuales
-- ============================================================
CREATE TABLE IF NOT EXISTS presupuestos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    categoria_id    INT COMMENT 'NULL = presupuesto global del mes',
    monto_limite    DECIMAL(12,2) NOT NULL,
    mes             DATE NOT NULL COMMENT 'Primer día del mes (YYYY-MM-01)',
    activo          TINYINT NOT NULL DEFAULT 1,
    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    UNIQUE KEY unique_presupuesto (usuario_id, categoria_id, mes),
    CHECK (monto_limite > 0),
    CHECK (activo IN (0, 1)),
    INDEX idx_presupuestos_usuario (usuario_id, mes)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Límites de gasto mensuales por categoría o globales';

-- ============================================================
-- TABLA: recurrencias
-- Transacciones programadas automáticas
-- ============================================================
CREATE TABLE IF NOT EXISTS recurrencias (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    categoria_id    INT NOT NULL,
    tipo_id         TINYINT NOT NULL,
    monto           DECIMAL(12,2) NOT NULL,
    descripcion     TEXT,
    frecuencia      VARCHAR(20) NOT NULL,
    dia_ejecucion   INT COMMENT 'Día del mes (1-31) para frecuencia mensual',
    proxima_fecha   DATE NOT NULL,
    activo          TINYINT NOT NULL DEFAULT 1,
    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT,
    FOREIGN KEY (tipo_id) REFERENCES tipos_movimiento(id) ON DELETE RESTRICT,
    CHECK (monto > 0),
    CHECK (frecuencia IN ('diario', 'semanal', 'quincenal', 'mensual', 'anual')),
    CHECK (dia_ejecucion BETWEEN 1 AND 31),
    CHECK (activo IN (0, 1)),
    INDEX idx_recurrencias_usuario (usuario_id, activo),
    INDEX idx_recurrencias_proxima (proxima_fecha, activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Transacciones programadas (salario, suscripciones, etc.)';

-- ============================================================
-- TABLA: notificaciones
-- Sistema de notificaciones push/in-app
-- ============================================================
CREATE TABLE IF NOT EXISTS notificaciones (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    titulo          VARCHAR(200) NOT NULL,
    mensaje         TEXT NOT NULL,
    tipo            VARCHAR(10) NOT NULL DEFAULT 'info',
    leida           TINYINT NOT NULL DEFAULT 0,
    fecha           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CHECK (tipo IN ('info', 'alerta', 'exito', 'error')),
    CHECK (leida IN (0, 1)),
    INDEX idx_notif_usuario (usuario_id),
    INDEX idx_notif_leida (usuario_id, leida)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Sistema de notificaciones push e in-app';

-- ============================================================
-- TABLA: perfiles_ia
-- Perfiles financieros generados por IA
-- ============================================================
CREATE TABLE IF NOT EXISTS perfiles_ia (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id   INT NOT NULL,
    fecha        DATE NOT NULL DEFAULT (CURRENT_DATE),
    tipo_label   VARCHAR(100) COMMENT 'Clasificación del perfil financiero',
    score        INT COMMENT 'Puntuación de salud financiera (0-100)',
    tags         TEXT COMMENT 'JSON array de etiquetas',
    narrativa    TEXT COMMENT 'Descripción generada por IA',
    habitos      TEXT COMMENT 'JSON array de hábitos positivos',
    areas_mejora TEXT COMMENT 'JSON array de áreas de mejora',
    creado_en    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_perfil_dia (usuario_id, fecha),
    CHECK (score BETWEEN 0 AND 100),
    INDEX idx_perfiles_ia_usuario (usuario_id, fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Perfiles financieros generados por IA (NVIDIA NIM)';

-- ============================================================
-- TABLA: insights_diarios
-- Consejos diarios personalizados por IA
-- ============================================================
CREATE TABLE IF NOT EXISTS insights_diarios (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    fecha      DATE NOT NULL DEFAULT (CURRENT_DATE),
    enviado    TINYINT NOT NULL DEFAULT 0,
    mensaje    TEXT COMMENT 'Insight personalizado del día',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_insight_dia (usuario_id, fecha),
    CHECK (enviado IN (0, 1)),
    INDEX idx_insights_usuario (usuario_id, fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Consejos diarios personalizados por IA';

-- ============================================================
-- DATOS SEMILLA: Categorías por defecto
-- ============================================================
INSERT INTO categorias (nombre, tipo_id, icono, activo) VALUES
    ('Salario', (SELECT id FROM tipos_movimiento WHERE codigo = 'ingreso'), '💼', 1),
    ('Freelance', (SELECT id FROM tipos_movimiento WHERE codigo = 'ingreso'), '💻', 1),
    ('Inversiones', (SELECT id FROM tipos_movimiento WHERE codigo = 'ingreso'), '📈', 1),
    ('Otros ingresos', (SELECT id FROM tipos_movimiento WHERE codigo = 'ingreso'), '💵', 1),
    ('Alimentación', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '🍔', 1),
    ('Transporte', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '🚗', 1),
    ('Vivienda', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '🏠', 1),
    ('Servicios', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '💡', 1),
    ('Salud', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '🏥', 1),
    ('Educación', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '📚', 1),
    ('Entretenimiento', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '🎮', 1),
    ('Ropa', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '👕', 1),
    ('Otros gastos', (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto'), '📦', 1)
ON DUPLICATE KEY UPDATE activo = 1;

-- ============================================================
-- VERIFICACIÓN DE INSTALACIÓN
-- ============================================================
SELECT 'Base de datos creada exitosamente' AS resultado;
SELECT table_name, table_rows, table_comment 
FROM information_schema.tables 
WHERE table_schema = 'gastos_db' 
ORDER BY table_name;

-- ============================================================
-- INFORMACIÓN DE CONFIGURACIÓN
-- ============================================================
-- 
-- Configura tu archivo .env con:
--
--   DB_BACKEND=mysql
--   MYSQL_HOST=localhost
--   MYSQL_PORT=3306
--   MYSQL_DATABASE=gastos_db
--   MYSQL_USER=root
--   MYSQL_PASSWORD=
--   AUTH_MODE=jwt
--   JWT_SECRET_KEY=tu-clave-secreta-de-64-caracteres-hex
--
-- ============================================================
