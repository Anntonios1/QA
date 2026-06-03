"""
============================================================
  ESQUEMA SQL y SEEDS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Implementación conforme a interfaz
    - ISO 9126: Fiabilidad, Seguridad, Eficiencia
    - CMMI Nivel 3: Proceso estándar implementado
    - ISO/IEC 25000: Portabilidad - Adaptabilidad
============================================================
"""

# ============================================================
#  ESQUEMA SQL (MySQL/MariaDB)
# ============================================================

SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        nombre          VARCHAR(100) NOT NULL,
        email           VARCHAR(254) NOT NULL UNIQUE,
        password_hash   TEXT NOT NULL,
        moneda          VARCHAR(3) NOT NULL DEFAULT 'COP',
        fecha_creacion  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        activo          TINYINT NOT NULL DEFAULT 1,
        CHECK (CHAR_LENGTH(nombre) >= 2),
        CHECK (activo IN (0, 1)),
        CHECK (moneda IN ('COP', 'USD'))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS tipos_movimiento (
        id          TINYINT PRIMARY KEY,
        codigo      VARCHAR(10) NOT NULL UNIQUE,
        CHECK (codigo IN ('ingreso', 'gasto'))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    INSERT IGNORE INTO tipos_movimiento (id, codigo) VALUES
        (1, 'ingreso'),
        (2, 'gasto')
    """,
    """
    CREATE TABLE IF NOT EXISTS categorias (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id  INT,
        nombre      VARCHAR(100) NOT NULL,
        tipo_id     TINYINT NOT NULL,
        icono       VARCHAR(32) DEFAULT '💰',
        descripcion VARCHAR(255) DEFAULT '',
        activo      TINYINT NOT NULL DEFAULT 1,
        CHECK (CHAR_LENGTH(nombre) >= 2),
        CHECK (activo IN (0, 1)),
        UNIQUE KEY unique_categoria_usuario (usuario_id, nombre),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (tipo_id) REFERENCES tipos_movimiento(id) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS movimientos (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id      INT NOT NULL,
        categoria_id    INT NOT NULL,
        tipo_id         TINYINT NOT NULL,
        monto           DECIMAL(12,2) NOT NULL,
        descripcion     TEXT,
        fecha           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        fecha_registro  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT,
        FOREIGN KEY (tipo_id) REFERENCES tipos_movimiento(id) ON DELETE RESTRICT,
        CHECK (monto > 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
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
        CHECK (leida IN (0, 1))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS perfiles_ia (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id   INT NOT NULL,
        fecha        DATE NOT NULL DEFAULT (CURRENT_DATE),
        tipo_label   VARCHAR(100),
        score        INT,
        tags         TEXT,
        narrativa    TEXT,
        habitos      TEXT,
        areas_mejora TEXT,
        creado_en    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        UNIQUE KEY unique_perfil_dia (usuario_id, fecha),
        CHECK (score BETWEEN 0 AND 100)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS insights_diarios (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT NOT NULL,
        fecha      DATE NOT NULL DEFAULT (CURRENT_DATE),
        enviado    TINYINT NOT NULL DEFAULT 0,
        mensaje    TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        UNIQUE KEY unique_insight_dia (usuario_id, fecha),
        CHECK (enviado IN (0, 1))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS presupuestos (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id      INT NOT NULL,
        categoria_id    INT,
        monto_limite    DECIMAL(12,2) NOT NULL,
        mes             DATE NOT NULL,
        activo          TINYINT NOT NULL DEFAULT 1,
        creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
        UNIQUE KEY unique_presupuesto (usuario_id, categoria_id, mes),
        CHECK (monto_limite > 0),
        CHECK (activo IN (0, 1))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS recurrencias (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id      INT NOT NULL,
        categoria_id    INT NOT NULL,
        tipo_id         TINYINT NOT NULL,
        monto           DECIMAL(12,2) NOT NULL,
        descripcion     TEXT,
        frecuencia      VARCHAR(20) NOT NULL,
        dia_ejecucion   INT,
        proxima_fecha   DATE NOT NULL,
        activo          TINYINT NOT NULL DEFAULT 1,
        creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT,
        FOREIGN KEY (tipo_id) REFERENCES tipos_movimiento(id) ON DELETE RESTRICT,
        CHECK (monto > 0),
        CHECK (frecuencia IN ('diario', 'semanal', 'quincenal', 'mensual', 'anual')),
        CHECK (dia_ejecucion BETWEEN 1 AND 31),
        CHECK (activo IN (0, 1))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id      INT NOT NULL,
        token_hash      VARCHAR(64) NOT NULL UNIQUE,
        expires_at      TIMESTAMP NOT NULL,
        created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        revoked         TINYINT NOT NULL DEFAULT 0,
        device_info     VARCHAR(255),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        CHECK (revoked IN (0, 1))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    # Migraciones ligeras (compatibles con instalaciones existentes)
    "ALTER TABLE usuarios ADD COLUMN moneda VARCHAR(3) NOT NULL DEFAULT 'COP'",
    "ALTER TABLE categorias ADD COLUMN descripcion VARCHAR(255)",
    "ALTER TABLE categorias MODIFY COLUMN icono VARCHAR(32) DEFAULT '💰'",
    # Índices
    "CREATE INDEX IF NOT EXISTS idx_mov_usuario ON movimientos(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_mov_fecha ON movimientos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_mov_tipo_id ON movimientos(tipo_id)",
    "CREATE INDEX IF NOT EXISTS idx_cat_tipo_id ON categorias(tipo_id)",
    "CREATE INDEX IF NOT EXISTS idx_cat_usuario ON categorias(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_notif_usuario ON notificaciones(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_notif_leida ON notificaciones(usuario_id, leida)",
    "CREATE INDEX IF NOT EXISTS idx_perfiles_ia_usuario ON perfiles_ia(usuario_id, fecha)",
    "CREATE INDEX IF NOT EXISTS idx_insights_usuario ON insights_diarios(usuario_id, fecha)",
    "CREATE INDEX IF NOT EXISTS idx_presupuestos_usuario ON presupuestos(usuario_id, mes)",
    "CREATE INDEX IF NOT EXISTS idx_recurrencias_usuario ON recurrencias(usuario_id, activo)",
    "CREATE INDEX IF NOT EXISTS idx_recurrencias_proxima ON recurrencias(proxima_fecha, activo)",
    "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_usuario ON refresh_tokens(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at)",
]

# [NORMA: ISO/IEC 12207 - Proceso de Implementación] Datos semilla de categorías por defecto
SEED_CATEGORIAS = [
    ('Salario',         'ingreso', '💼'),
    ('Freelance',       'ingreso', '💻'),
    ('Inversiones',     'ingreso', '📈'),
    ('Otros ingresos',  'ingreso', '💵'),
    ('Alimentación',    'gasto',   '🍔'),
    ('Transporte',      'gasto',   '🚗'),
    ('Vivienda',        'gasto',   '🏠'),
    ('Servicios',       'gasto',   '💡'),
    ('Salud',           'gasto',   '🏥'),
    ('Educación',       'gasto',   '📚'),
    ('Entretenimiento', 'gasto',   '🎮'),
    ('Ropa',            'gasto',   '👕'),
    ('Otros gastos',    'gasto',   '📦'),
]
