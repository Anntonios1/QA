"""
============================================================
  IMPLEMENTACIÓN PostgreSQL - Patrón Repository
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Implementación conforme a interfaz
    - ISO 9126: Fiabilidad, Seguridad, Eficiencia
    - CMMI Nivel 3: Proceso estándar implementado
    - ISO/IEC 25000: Portabilidad - Adaptabilidad
============================================================
  Driver: pg8000 (puro Python, sin dependencias nativas)
  Requiere: pip install pg8000
============================================================
"""

from datetime import datetime, timedelta

try:
    import pg8000
    import pg8000.dbapi as pg8000_dbapi
    PG_AVAILABLE = True
except ImportError:
    PG_AVAILABLE = False

from .base_repository import (
    PasswordMixin,
    BaseUsuarioRepository,
    BaseCategoriaRepository,
    BaseMovimientoRepository,
    BaseNotificacionRepository,
)

# ============================================================
#  ESQUEMA SQL (PostgreSQL)
# ============================================================

SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id              SERIAL PRIMARY KEY,
        nombre          VARCHAR(100) NOT NULL CHECK(length(nombre) >= 2),
        email           VARCHAR(254) NOT NULL UNIQUE,
        password_hash   TEXT         NOT NULL,
        moneda          VARCHAR(3)   NOT NULL DEFAULT 'COP' CHECK(moneda IN ('COP', 'USD')),
        fecha_creacion  TIMESTAMP    NOT NULL DEFAULT NOW(),
        activo          SMALLINT     NOT NULL DEFAULT 1 CHECK(activo IN (0, 1))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tipos_movimiento (
        id          SMALLINT PRIMARY KEY,
        codigo      VARCHAR(10) NOT NULL UNIQUE CHECK(codigo IN ('ingreso', 'gasto'))
    )
    """,
    """
    INSERT INTO tipos_movimiento (id, codigo)
    VALUES (1, 'ingreso'), (2, 'gasto')
    ON CONFLICT (id) DO NOTHING
    """,
    """
    CREATE TABLE IF NOT EXISTS categorias (
        id          SERIAL       PRIMARY KEY,
        usuario_id  INTEGER      REFERENCES usuarios(id) ON DELETE CASCADE,
        nombre      VARCHAR(100) NOT NULL CHECK(length(nombre) >= 2),
        tipo_id     SMALLINT     NOT NULL REFERENCES tipos_movimiento(id) ON DELETE RESTRICT,
        icono       VARCHAR(32)  DEFAULT '💰',
        descripcion VARCHAR(255) DEFAULT '',
        activo      SMALLINT     NOT NULL DEFAULT 1 CHECK(activo IN (0, 1)),
        UNIQUE(usuario_id, nombre)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS movimientos (
        id              SERIAL       PRIMARY KEY,
        usuario_id      INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        categoria_id    INTEGER      NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
        tipo_id         SMALLINT     NOT NULL REFERENCES tipos_movimiento(id) ON DELETE RESTRICT,
        monto           NUMERIC(12,2) NOT NULL CHECK(monto > 0),
        descripcion     TEXT         DEFAULT '',
        fecha           TIMESTAMP    NOT NULL DEFAULT NOW(),
        fecha_registro  TIMESTAMP    NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notificaciones (
        id              SERIAL       PRIMARY KEY,
        usuario_id      INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        titulo          VARCHAR(200) NOT NULL,
        mensaje         TEXT         NOT NULL,
        tipo            VARCHAR(10)  NOT NULL DEFAULT 'info' CHECK(tipo IN ('info', 'alerta', 'exito', 'error')),
        leida           SMALLINT     NOT NULL DEFAULT 0 CHECK(leida IN (0, 1)),
        fecha           TIMESTAMP    NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS perfiles_ia (
        id           SERIAL PRIMARY KEY,
        usuario_id   INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        fecha        DATE    NOT NULL DEFAULT CURRENT_DATE,
        tipo_label   VARCHAR(100),
        score        INTEGER CHECK(score BETWEEN 0 AND 100),
        tags         TEXT,
        narrativa    TEXT,
        habitos      TEXT,
        areas_mejora TEXT,
        creado_en    TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE(usuario_id, fecha)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS insights_diarios (
        id         SERIAL PRIMARY KEY,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        fecha      DATE    NOT NULL DEFAULT CURRENT_DATE,
        enviado    SMALLINT NOT NULL DEFAULT 0 CHECK(enviado IN (0, 1)),
        mensaje    TEXT,
        UNIQUE(usuario_id, fecha)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS presupuestos (
        id              SERIAL PRIMARY KEY,
        usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        categoria_id    INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
        monto_limite    NUMERIC(12,2) NOT NULL CHECK(monto_limite > 0),
        mes             DATE NOT NULL,
        activo          SMALLINT NOT NULL DEFAULT 1 CHECK(activo IN (0, 1)),
        creado_en       TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE(usuario_id, categoria_id, mes)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS recurrencias (
        id              SERIAL PRIMARY KEY,
        usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        categoria_id    INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
        tipo_id         SMALLINT NOT NULL REFERENCES tipos_movimiento(id) ON DELETE RESTRICT,
        monto           NUMERIC(12,2) NOT NULL CHECK(monto > 0),
        descripcion     TEXT DEFAULT '',
        frecuencia      VARCHAR(20) NOT NULL CHECK(frecuencia IN ('diario', 'semanal', 'quincenal', 'mensual', 'anual')),
        dia_ejecucion   INTEGER CHECK(dia_ejecucion BETWEEN 1 AND 31),
        proxima_fecha   DATE NOT NULL,
        activo          SMALLINT NOT NULL DEFAULT 1 CHECK(activo IN (0, 1)),
        creado_en       TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id              SERIAL PRIMARY KEY,
        usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        token_hash      VARCHAR(64) NOT NULL UNIQUE,
        expires_at      TIMESTAMP NOT NULL,
        created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
        revoked         SMALLINT NOT NULL DEFAULT 0 CHECK(revoked IN (0, 1)),
        device_info     VARCHAR(255)
    )
    """,
    # Migraciones ligeras (compatibles con instalaciones existentes)
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS moneda VARCHAR(3) DEFAULT 'COP'",
    "ALTER TABLE categorias ADD COLUMN IF NOT EXISTS descripcion VARCHAR(255)",
    "ALTER TABLE categorias ALTER COLUMN icono TYPE VARCHAR(32)",
    "CREATE INDEX IF NOT EXISTS idx_mov_usuario   ON movimientos(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_mov_fecha     ON movimientos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_mov_tipo_id   ON movimientos(tipo_id)",
    "CREATE INDEX IF NOT EXISTS idx_cat_tipo_id   ON categorias(tipo_id)",
    "CREATE INDEX IF NOT EXISTS idx_notif_usuario ON notificaciones(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_notif_leida   ON notificaciones(usuario_id, leida)",
    "CREATE INDEX IF NOT EXISTS idx_perfiles_ia_usuario ON perfiles_ia(usuario_id, fecha)",
    "CREATE INDEX IF NOT EXISTS idx_insights_usuario    ON insights_diarios(usuario_id, fecha)",
    "CREATE INDEX IF NOT EXISTS idx_presupuestos_usuario ON presupuestos(usuario_id, mes)",
    "CREATE INDEX IF NOT EXISTS idx_recurrencias_usuario ON recurrencias(usuario_id, activo)",
    "CREATE INDEX IF NOT EXISTS idx_recurrencias_proxima ON recurrencias(proxima_fecha, activo)",
    "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_usuario ON refresh_tokens(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at)",
]

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


# ============================================================
#  HELPERS DE CONEXIÓN Y RESULTADOS
# ============================================================

def _get_conn():
    """Abre una conexión PostgreSQL usando pg8000 (puro Python)."""
    if not PG_AVAILABLE:
        raise ImportError(
            "pg8000 no está instalado. Ejecuta: pip install pg8000"
        )
    from .config import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
    conn = pg8000.connect(
        host=PG_HOST,
        port=int(PG_PORT),
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD or "",
    )
    return conn


def _row_to_dict(cursor, row):
    """Convierte una fila de pg8000 (tupla) a diccionario usando cursor.description."""
    if row is None:
        return None
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))


def _rows_to_dicts(cursor, rows):
    """Convierte lista de filas pg8000 a lista de dicts."""
    if not rows:
        return []
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, row)) for row in rows]


def _fetch_one(conn, query, params=None):
    cur = conn.cursor()
    cur.execute(query, params or ())
    row = cur.fetchone()
    result = _row_to_dict(cur, row) if row else None
    cur.close()
    return result


def _fetch_all(conn, query, params=None):
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    result = _rows_to_dicts(cur, rows)
    cur.close()
    return result


def _execute(conn, query, params=None):
    """Ejecuta una sentencia DML y devuelve rowcount."""
    cur = conn.cursor()
    cur.execute(query, params or ())
    rc = cur.rowcount
    cur.close()
    return rc


def _execute_returning(conn, query, params=None):
    """Ejecuta INSERT/UPDATE RETURNING y devuelve la primera fila como dict."""
    cur = conn.cursor()
    cur.execute(query, params or ())
    row = cur.fetchone()
    result = _row_to_dict(cur, row) if row else None
    cur.close()
    return result


def init_postgres():
    """Crea el esquema y siembra datos iniciales."""
    conn = _get_conn()
    try:
        for stmt in SCHEMA_SQL:
            cur = conn.cursor()
            cur.execute(stmt)
            cur.close()

        conn.commit()
        print("[DB-PostgreSQL] Esquema inicializado correctamente.")
    except Exception as e:
        conn.rollback()
        print(f"[DB-PostgreSQL] Error al inicializar: {e}")
        raise
    finally:
        conn.close()


# ============================================================
#  IMPLEMENTACIONES
# ============================================================

# [NORMA: ISO/IEC 12207 - Proceso de Implementación] Implementación del repositorio de usuarios bajo patrón Repository
# [NORMA: ISO 9001:2000 - Enfoque basado en procesos] Proceso estandarizado para persistencia de datos de usuario en PostgreSQL
class PGUsuarioRepository(BaseUsuarioRepository, PasswordMixin):

    def crear(self, nombre, email, password, moneda="COP"):
        conn = _get_conn()
        try:
            pw_hash, _ = self.hash_password(password)
            row = _execute_returning(
                conn,
                "INSERT INTO usuarios (nombre, email, password_hash, moneda) "
                "VALUES (%s, %s, %s, %s) RETURNING id, nombre, email, moneda",
                (nombre.strip(), email.strip().lower(), pw_hash, moneda),
            )
            conn.commit()
            return row
        except pg8000_dbapi.IntegrityError:
            conn.rollback()
            return None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def autenticar(self, email, password):
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT id, nombre, email, moneda, password_hash, activo FROM usuarios "
                "WHERE email = %s AND activo = 1",
                (email.strip().lower(),),
            )
            if row and self.verify_password(password, row["password_hash"]):
                return row
            return None
        finally:
            conn.close()

    def obtener_por_id(self, usuario_id):
        conn = _get_conn()
        try:
            return _fetch_one(
                conn,
                "SELECT id, nombre, email, moneda, fecha_creacion, activo "
                "FROM usuarios WHERE id = %s",
                (usuario_id,),
            )
        finally:
            conn.close()

    def listar_ids_activos(self):
        conn = _get_conn()
        try:
            rows = _fetch_all(conn, "SELECT id FROM usuarios WHERE activo = 1")
            return [int(r["id"]) for r in rows]
        finally:
            conn.close()

    def actualizar_perfil(self, usuario_id, nombre=None, moneda=None):
        conn = _get_conn()
        try:
            sets = []
            params = []
            if nombre is not None:
                sets.append("nombre = %s")
                params.append(nombre.strip())
            if moneda is not None:
                sets.append("moneda = %s")
                params.append(moneda)

            if not sets:
                return _fetch_one(
                    conn,
                    "SELECT id, nombre, email, moneda, fecha_creacion FROM usuarios WHERE id = %s",
                    (usuario_id,),
                )

            params.append(usuario_id)
            rc = _execute(
                conn,
                f"UPDATE usuarios SET {', '.join(sets)} WHERE id = %s",
                params,
            )
            conn.commit()
            if rc == 0:
                return None
            return _fetch_one(
                conn,
                "SELECT id, nombre, email, moneda, fecha_creacion FROM usuarios WHERE id = %s",
                (usuario_id,),
            )
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def cambiar_password(self, usuario_id, password_actual, password_nueva):
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT password_hash FROM usuarios WHERE id = %s",
                (usuario_id,),
            )
            if not row:
                return None
            if not self.verify_password(password_actual, row["password_hash"]):
                return {"error": "password_incorrecta"}
            nuevo_hash, _ = self.hash_password(password_nueva)
            _execute(
                conn,
                "UPDATE usuarios SET password_hash = %s WHERE id = %s",
                (nuevo_hash, usuario_id),
            )
            conn.commit()
            return {"updated": True}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class PGCategoriaRepository(BaseCategoriaRepository):

    def asegurar_para_usuario(self, usuario_id):
        conn = _get_conn()
        try:
            _execute(
                conn,
                "ALTER TABLE categorias ADD COLUMN IF NOT EXISTS usuario_id INTEGER"
            )
            _execute(
                conn,
                "CREATE UNIQUE INDEX IF NOT EXISTS categorias_usuario_nombre_unique "
                "ON categorias(usuario_id, nombre)"
            )
            conn.commit()

            row = _fetch_one(
                conn,
                "SELECT COUNT(*) AS total FROM categorias WHERE usuario_id = %s",
                (usuario_id,),
            )
            tiene_categorias = row and int(row.get("total") or 0) > 0

            legacy = []
            if not tiene_categorias:
                legacy = _fetch_all(
                    conn,
                    "SELECT DISTINCT c.id, c.nombre, t.codigo AS tipo, c.icono "
                    "FROM categorias c "
                    "JOIN tipos_movimiento t ON c.tipo_id = t.id "
                    "JOIN movimientos m ON m.categoria_id = c.id "
                    "WHERE c.usuario_id IS NULL AND m.usuario_id = %s",
                    (usuario_id,),
                )

            if legacy:
                for cat in legacy:
                    row_new = _execute_returning(
                        conn,
                        "INSERT INTO categorias (usuario_id, nombre, tipo_id, icono, activo) "
                        "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, 1) "
                        "ON CONFLICT (usuario_id, nombre) DO UPDATE SET activo = 1 "
                        "RETURNING id",
                        (usuario_id, cat["nombre"], cat["tipo"], cat.get("icono") or ""),
                    )
                    if row_new and row_new.get("id"):
                        _execute(
                            conn,
                            "UPDATE movimientos SET categoria_id = %s WHERE usuario_id = %s AND categoria_id = %s",
                            (row_new["id"], usuario_id, cat["id"]),
                        )

            for nombre, tipo, icono in SEED_CATEGORIAS:
                _execute_returning(
                    conn,
                    "INSERT INTO categorias (usuario_id, nombre, tipo_id, icono, activo) "
                    "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, 1) "
                    "ON CONFLICT (usuario_id, nombre) DO UPDATE SET activo = 1",
                    (usuario_id, nombre, tipo, icono),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar(self, usuario_id, tipo=None):
        conn = _get_conn()
        try:
            if tipo:
                rows = _fetch_all(
                    conn,
                    "SELECT c.id, c.nombre, t.codigo AS tipo, c.icono, c.descripcion, c.activo, "
                    "COALESCE(COUNT(m.id), 0) AS usos "
                    "FROM categorias c "
                    "JOIN tipos_movimiento t ON c.tipo_id = t.id "
                    "LEFT JOIN movimientos m ON m.categoria_id = c.id AND m.usuario_id = %s "
                    "WHERE c.activo = 1 AND c.usuario_id = %s AND t.codigo = %s "
                    "GROUP BY c.id, c.nombre, t.codigo, c.icono, c.descripcion, c.activo "
                    "ORDER BY c.nombre",
                    (usuario_id, usuario_id, tipo),
                )
            else:
                rows = _fetch_all(
                    conn,
                    "SELECT c.id, c.nombre, t.codigo AS tipo, c.icono, c.descripcion, c.activo, "
                    "COALESCE(COUNT(m.id), 0) AS usos "
                    "FROM categorias c "
                    "JOIN tipos_movimiento t ON c.tipo_id = t.id "
                    "LEFT JOIN movimientos m ON m.categoria_id = c.id AND m.usuario_id = %s "
                    "WHERE c.activo = 1 AND c.usuario_id = %s "
                    "GROUP BY c.id, c.nombre, t.codigo, c.icono, c.descripcion, c.activo "
                    "ORDER BY t.codigo, c.nombre",
                    (usuario_id, usuario_id),
                )
            for r in rows:
                r["usos"] = int(r.get("usos") or 0)
            return rows
        finally:
            conn.close()

    def obtener_por_id(self, categoria_id, usuario_id):
        conn = _get_conn()
        try:
            return _fetch_one(
                conn,
                "SELECT c.id, c.nombre, t.codigo AS tipo, c.icono, c.descripcion, c.activo "
                "FROM categorias c "
                "JOIN tipos_movimiento t ON c.tipo_id = t.id "
                "WHERE c.id = %s AND c.usuario_id = %s",
                (categoria_id, usuario_id),
            )
        finally:
            conn.close()

    def crear(self, usuario_id, nombre, tipo, icono="", descripcion=""):
        conn = _get_conn()
        nombre_limpio = nombre.strip()
        try:
            row = _execute_returning(
                conn,
                "INSERT INTO categorias (usuario_id, nombre, tipo_id, icono, descripcion, activo) "
                "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, %s, 1) "
                "RETURNING id, nombre, icono, descripcion, activo",
                (usuario_id, nombre_limpio, tipo, icono, descripcion),
            )
            conn.commit()
            if row:
                row["tipo"] = tipo
                row["usos"] = 0
            return row
        except pg8000_dbapi.IntegrityError:
            conn.rollback()
            existente = _fetch_one(
                conn,
                "SELECT id, activo FROM categorias WHERE usuario_id = %s AND nombre = %s",
                (usuario_id, nombre_limpio),
            )
            if existente and int(existente.get("activo") or 0) == 0:
                row = _execute_returning(
                    conn,
                    "UPDATE categorias "
                    "SET activo = 1, tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = %s), "
                    "icono = %s, descripcion = %s "
                    "WHERE id = %s AND usuario_id = %s "
                    "RETURNING id, nombre, icono, descripcion, activo",
                    (tipo, icono, descripcion, existente["id"], usuario_id),
                )
                conn.commit()
                if row:
                    row["tipo"] = tipo
                    row["usos"] = 0
                return row
            return None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def actualizar(
        self,
        usuario_id,
        categoria_id,
        nombre=None,
        tipo=None,
        icono=None,
        descripcion=None,
    ):
        conn = _get_conn()
        try:
            if nombre:
                duplicado = _fetch_one(
                    conn,
                    "SELECT id FROM categorias WHERE usuario_id = %s AND nombre = %s AND id <> %s",
                    (usuario_id, nombre.strip(), categoria_id),
                )
                if duplicado:
                    return {"error": "duplicate"}

            sets = []
            params = []
            if nombre is not None:
                sets.append("nombre = %s")
                params.append(nombre.strip())
            if tipo is not None:
                sets.append(
                    "tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = %s)"
                )
                params.append(tipo)
            if icono is not None:
                sets.append("icono = %s")
                params.append(icono)
            if descripcion is not None:
                sets.append("descripcion = %s")
                params.append(descripcion)

            if not sets:
                return {"updated": False}

            params.extend([categoria_id, usuario_id])
            rc = _execute(
                conn,
                f"UPDATE categorias SET {', '.join(sets)} WHERE id = %s AND usuario_id = %s",
                params,
            )
            conn.commit()
            return {"updated": rc > 0}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def desactivar(self, usuario_id, categoria_id):
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE categorias SET activo = 0 WHERE id = %s AND usuario_id = %s",
                (categoria_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# [NORMA: ISO/IEC 12207 - Proceso de Implementación] Implementación del repositorio de movimientos bajo patrón Repository
# [NORMA: ISO 9001:2000 - Enfoque basado en procesos] Proceso estandarizado para persistencia de datos de movimientos en PostgreSQL
class PGMovimientoRepository(BaseMovimientoRepository):

    def crear(self, usuario_id, categoria_id, tipo, monto, descripcion="", fecha=None):
        conn = _get_conn()
        try:
            if fecha is None:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = _execute_returning(
                conn,
                "INSERT INTO movimientos (usuario_id, categoria_id, tipo_id, monto, descripcion, fecha) "
                "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, %s, %s) "
                "RETURNING id, (SELECT codigo FROM tipos_movimiento WHERE id = tipo_id) AS tipo, monto",
                (usuario_id, categoria_id, tipo, float(monto), descripcion.strip(), fecha),
            )
            conn.commit()
            if row:
                row["monto"] = float(row["monto"])
            return row
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_por_usuario(
        self,
        usuario_id,
        limite=50,
        offset=0,
        tipo=None,
        fecha_desde=None,
        fecha_hasta=None,
        categoria_id=None,
        monto_min=None,
        monto_max=None,
    ):
        conn = _get_conn()
        try:
            q = (
                "SELECT m.id, m.usuario_id, t.codigo AS tipo, m.monto, m.descripcion, m.fecha, "
                "m.fecha_registro, m.categoria_id, "
                "c.nombre AS categoria_nombre, c.icono AS categoria_icono "
                "FROM movimientos m "
                "JOIN categorias c ON m.categoria_id = c.id "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s"
            )
            p = [usuario_id]
            if tipo:
                q += " AND t.codigo = %s"
                p.append(tipo)
            if fecha_desde:
                q += " AND m.fecha >= %s"
                p.append(fecha_desde)
            if fecha_hasta:
                q += " AND m.fecha <= %s"
                p.append(fecha_hasta)
            if categoria_id is not None:
                q += " AND m.categoria_id = %s"
                p.append(int(categoria_id))
            if monto_min is not None:
                q += " AND m.monto >= %s"
                p.append(float(monto_min))
            if monto_max is not None:
                q += " AND m.monto <= %s"
                p.append(float(monto_max))
            q += " ORDER BY m.fecha DESC LIMIT %s"
            p.append(limite)
            if offset:
                q += " OFFSET %s"
                p.append(offset)
            rows = _fetch_all(conn, q, p)
            for r in rows:
                r["monto"] = float(r["monto"])
                if hasattr(r.get("fecha"), "isoformat"):
                    r["fecha"] = r["fecha"].isoformat()
                if hasattr(r.get("fecha_registro"), "isoformat"):
                    r["fecha_registro"] = r["fecha_registro"].isoformat()
            return rows
        finally:
            conn.close()

    def contar_por_usuario(
        self,
        usuario_id,
        tipo=None,
        fecha_desde=None,
        fecha_hasta=None,
        categoria_id=None,
        monto_min=None,
        monto_max=None,
    ):
        conn = _get_conn()
        try:
            q = (
                "SELECT COUNT(*) AS total "
                "FROM movimientos m "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s"
            )
            p = [usuario_id]
            if tipo:
                q += " AND t.codigo = %s"
                p.append(tipo)
            if fecha_desde:
                q += " AND m.fecha >= %s"
                p.append(fecha_desde)
            if fecha_hasta:
                q += " AND m.fecha <= %s"
                p.append(fecha_hasta)
            if categoria_id is not None:
                q += " AND m.categoria_id = %s"
                p.append(int(categoria_id))
            if monto_min is not None:
                q += " AND m.monto >= %s"
                p.append(float(monto_min))
            if monto_max is not None:
                q += " AND m.monto <= %s"
                p.append(float(monto_max))
            row = _fetch_one(conn, q, p)
            return int(row["total"]) if row else 0
        finally:
            conn.close()

    def actualizar(self, movimiento_id, usuario_id, categoria_id=None, tipo=None,
                   monto=None, descripcion=None, fecha=None):
        """Actualiza campos del movimiento. Solo actualiza los campos que no sean None."""
        conn = _get_conn()
        try:
            sets, params = [], []
            if categoria_id is not None:
                sets.append("categoria_id = %s")
                params.append(int(categoria_id))
            if tipo is not None:
                sets.append("tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = %s)")
                params.append(tipo)
            if monto is not None:
                sets.append("monto = %s")
                params.append(float(monto))
            if descripcion is not None:
                sets.append("descripcion = %s")
                params.append(descripcion.strip())
            if fecha is not None:
                sets.append("fecha = %s")
                params.append(fecha)
            if not sets:
                return None
            params += [movimiento_id, usuario_id]
            q = (
                "UPDATE movimientos SET " + ", ".join(sets) +
                " WHERE id = %s AND usuario_id = %s "
                "RETURNING id, (SELECT codigo FROM tipos_movimiento WHERE id = tipo_id) AS tipo, "
                "monto, descripcion, fecha, categoria_id"
            )
            row = _execute_returning(conn, q, params)
            conn.commit()
            if row:
                row["monto"] = float(row["monto"])
                if hasattr(row.get("fecha"), "isoformat"):
                    row["fecha"] = row["fecha"].isoformat()
            return row
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def eliminar(self, movimiento_id, usuario_id):
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "DELETE FROM movimientos WHERE id = %s AND usuario_id = %s",
                (movimiento_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def obtener_balance(self, usuario_id):
        conn = _get_conn()
        try:
            row = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN t.codigo = 'ingreso' THEN m.monto ELSE 0 END), 0) AS total_ingresos,
                    COALESCE(SUM(CASE WHEN t.codigo = 'gasto'   THEN m.monto ELSE 0 END), 0) AS total_gastos,
                    COUNT(*) AS total_movimientos
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s
            """, (usuario_id,))
            ing = float(row["total_ingresos"]) if row else 0.0
            gas = float(row["total_gastos"]) if row else 0.0
            tot = int(row["total_movimientos"]) if row else 0
            return {
                "total_ingresos": round(ing, 2),
                "total_gastos": round(gas, 2),
                "balance": round(ing - gas, 2),
                "total_movimientos": tot,
            }
        finally:
            conn.close()

    def obtener_resumen_24h(self, usuario_id):
        conn = _get_conn()
        try:
            limite = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            row = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN t.codigo = 'ingreso' THEN m.monto ELSE 0 END), 0) AS total_ingresos,
                    COALESCE(SUM(CASE WHEN t.codigo = 'gasto' THEN m.monto ELSE 0 END), 0) AS total_gastos,
                    COUNT(*) AS total_movimientos
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
            """, (usuario_id, limite))
            ing = float(row["total_ingresos"]) if row else 0.0
            gas = float(row["total_gastos"]) if row else 0.0
            tot = int(row["total_movimientos"]) if row else 0
            return {
                "total_ingresos": round(ing, 2),
                "total_gastos": round(gas, 2),
                "total_movimientos": tot,
            }
        finally:
            conn.close()

    def obtener_resumen(self, usuario_id, dias=30):
        conn = _get_conn()
        try:
            fi = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
            fi_prev = (datetime.now() - timedelta(days=dias * 2)).strftime("%Y-%m-%d")

            cats = _fetch_all(conn, """
                SELECT c.nombre, c.icono, t.codigo AS tipo, SUM(m.monto) AS total, COUNT(*) AS cantidad
                FROM movimientos m
                JOIN categorias c ON m.categoria_id = c.id
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
                GROUP BY c.nombre, c.icono, t.codigo ORDER BY total DESC
            """, (usuario_id, fi))

            diario = _fetch_all(conn, """
                SELECT fecha::date AS dia, t.codigo AS tipo, SUM(m.monto) AS total
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
                GROUP BY fecha::date, t.codigo ORDER BY dia
            """, (usuario_id, fi))

            totales = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN t.codigo = 'ingreso' THEN m.monto ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN t.codigo = 'gasto'   THEN m.monto ELSE 0 END), 0) AS gastos,
                    COUNT(*) AS movimientos
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
            """, (usuario_id, fi))

            prev = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN t.codigo = 'ingreso' THEN m.monto ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN t.codigo = 'gasto'   THEN m.monto ELSE 0 END), 0) AS gastos
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s AND m.fecha < %s
            """, (usuario_id, fi_prev, fi))

            top3 = _fetch_all(conn, """
                SELECT m.monto, m.descripcion, m.fecha, c.nombre AS categoria, c.icono
                FROM movimientos m
                JOIN categorias c ON m.categoria_id = c.id
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND t.codigo = 'gasto' AND m.fecha >= %s
                ORDER BY m.monto DESC LIMIT 3
            """, (usuario_id, fi))

            gastos_actual   = float(totales["gastos"])   if totales else 0.0
            gastos_prev     = float(prev["gastos"])      if prev     else 0.0
            ingresos_actual = float(totales["ingresos"]) if totales  else 0.0
            total_mov       = int(totales["movimientos"]) if totales  else 0

            for c in cats:
                c["total"] = float(c["total"])
                ref = gastos_actual if c["tipo"] == "gasto" else ingresos_actual
                c["porcentaje"] = round(c["total"] / ref * 100, 1) if ref > 0 else 0

            for d in diario:
                d["total"] = float(d["total"])
                d["dia"] = str(d["dia"])

            for t in top3:
                t["monto"] = float(t["monto"])
                if hasattr(t.get("fecha"), "isoformat"):
                    t["fecha"] = t["fecha"].isoformat()

            promedio_diario = round(gastos_actual / max(dias, 1), 2)
            proyeccion_30   = round(promedio_diario * 30, 2)

            if gastos_prev > 0:
                variacion_pct = round((gastos_actual - gastos_prev) / gastos_prev * 100, 1)
            else:
                variacion_pct = 100.0 if gastos_actual > 0 else 0.0

            return {
                "periodo_dias": dias,
                "fecha_inicio": fi,
                "total_ingresos": round(ingresos_actual, 2),
                "total_gastos": round(gastos_actual, 2),
                "total_movimientos": total_mov,
                "promedio_diario_gasto": promedio_diario,
                "proyeccion_30_dias": proyeccion_30,
                "variacion_vs_anterior_pct": variacion_pct,
                "por_categoria": cats,
                "top_gastos": top3,
                "diario": diario,
            }
        finally:
            conn.close()

    def obtener_reporte_periodo(self, usuario_id, fecha_desde, fecha_hasta):
        conn = _get_conn()
        try:
            totales_raw = _fetch_all(
                conn,
                "SELECT t.codigo AS tipo, COALESCE(SUM(m.monto), 0) AS total, COUNT(*) AS movimientos "
                "FROM movimientos m "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s AND m.fecha >= %s AND m.fecha <= %s "
                "GROUP BY t.codigo",
                (usuario_id, fecha_desde, fecha_hasta),
            )

            ingresos = 0.0
            gastos = 0.0
            total_mov = 0
            for row in totales_raw:
                if row["tipo"] == "ingreso":
                    ingresos = float(row["total"])
                elif row["tipo"] == "gasto":
                    gastos = float(row["total"])
                total_mov += int(row["movimientos"] or 0)

            categorias = _fetch_all(
                conn,
                "SELECT c.id AS categoria_id, c.nombre, c.icono, COALESCE(SUM(m.monto), 0) AS total "
                "FROM movimientos m "
                "JOIN categorias c ON m.categoria_id = c.id "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s AND t.codigo = 'gasto' AND m.fecha >= %s AND m.fecha <= %s "
                "GROUP BY c.id, c.nombre, c.icono "
                "ORDER BY total DESC",
                (usuario_id, fecha_desde, fecha_hasta),
            )

            for c in categorias:
                c["total"] = float(c["total"])

            return {
                "totales": {
                    "ingresos": round(ingresos, 2),
                    "gastos": round(gastos, 2),
                    "movimientos": int(total_mov),
                },
                "categorias": categorias,
            }
        finally:
            conn.close()


class PGNotificacionRepository(BaseNotificacionRepository):

    def crear(self, usuario_id, titulo, mensaje, tipo="info"):
        conn = _get_conn()
        try:
            row = _execute_returning(
                conn,
                "INSERT INTO notificaciones (usuario_id, titulo, mensaje, tipo) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (usuario_id, titulo.strip(), mensaje.strip(), tipo),
            )
            conn.commit()
            return row
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_por_usuario(self, usuario_id, solo_no_leidas=False):
        conn = _get_conn()
        try:
            q = "SELECT * FROM notificaciones WHERE usuario_id = %s"
            p = [usuario_id]
            if solo_no_leidas:
                q += " AND leida = 0"
            q += " ORDER BY fecha DESC LIMIT 50"
            rows = _fetch_all(conn, q, p)
            for r in rows:
                if hasattr(r.get("fecha"), "isoformat"):
                    r["fecha"] = r["fecha"].isoformat()
            return rows
        finally:
            conn.close()

    def marcar_leida(self, notificacion_id, usuario_id):
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE notificaciones SET leida = 1 WHERE id = %s AND usuario_id = %s",
                (notificacion_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def contar_no_leidas(self, usuario_id):
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT COUNT(*) AS total FROM notificaciones "
                "WHERE usuario_id = %s AND leida = 0",
                (usuario_id,),
            )
            return int(row["total"]) if row else 0
        finally:
            conn.close()


# ============================================================
#  PERFIL IA
# ============================================================

class PGPerfilIARepository:
    """
    Almacena y recupera el perfil financiero generado por IA.
    Un perfil por usuario por día (cache diario).
    Normas: ISO/IEC 12207, ISO 9126 - Eficiencia, CMMI Nivel 3
    """

    def obtener_hoy(self, usuario_id):
        """Devuelve el perfil de IA generado hoy o None si no existe."""
        conn = _get_conn()
        try:
            return _fetch_one(
                conn,
                "SELECT * FROM perfiles_ia WHERE usuario_id = %s AND fecha = CURRENT_DATE",
                (usuario_id,),
            )
        finally:
            conn.close()

    def guardar(self, usuario_id, tipo_label, score, tags, narrativa,
                habitos, areas_mejora):
        """
        Inserta o actualiza el perfil del día (UPSERT).
        tags/habitos/areas_mejora se almacenan como JSON string.
        """
        import json
        conn = None
        try:
            conn = _get_conn()
            tags_json = json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else tags
            hab_json  = json.dumps(habitos, ensure_ascii=False) if isinstance(habitos, list) else habitos
            am_json   = json.dumps(areas_mejora, ensure_ascii=False) if isinstance(areas_mejora, list) else areas_mejora

            row = _execute_returning(conn, """
                INSERT INTO perfiles_ia (usuario_id, fecha, tipo_label, score, tags, narrativa, habitos, areas_mejora)
                VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (usuario_id, fecha)
                DO UPDATE SET
                    tipo_label   = EXCLUDED.tipo_label,
                    score        = EXCLUDED.score,
                    tags         = EXCLUDED.tags,
                    narrativa    = EXCLUDED.narrativa,
                    habitos      = EXCLUDED.habitos,
                    areas_mejora = EXCLUDED.areas_mejora,
                    creado_en    = NOW()
                RETURNING id, fecha::text AS fecha
            """, (usuario_id, tipo_label, int(score), tags_json, narrativa, hab_json, am_json))
            conn.commit()
            return row
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()


# ============================================================
#  INSIGHT DIARIO
# ============================================================

class PGInsightDiarioRepository:
    """
    Registra si el usuario ya recibió su insight diario (tipo Duolingo).
    Evita duplicar notificaciones push en el mismo día.
    Normas: ISO/IEC 20000 - Gestión de comunicación
    """

    def ya_enviado_hoy(self, usuario_id):
        """Retorna True si ya se generó un insight para el usuario hoy."""
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT id FROM insights_diarios WHERE usuario_id = %s AND fecha = CURRENT_DATE",
                (usuario_id,),
            )
            return row is not None
        finally:
            conn.close()

    def marcar_enviado(self, usuario_id, mensaje):
        """Registra que el insight fue enviado hoy."""
        conn = None
        try:
            conn = _get_conn()
            _execute_returning(conn, """
                INSERT INTO insights_diarios (usuario_id, fecha, enviado, mensaje)
                VALUES (%s, CURRENT_DATE, 1, %s)
                ON CONFLICT (usuario_id, fecha) DO UPDATE SET enviado = 1, mensaje = EXCLUDED.mensaje
                RETURNING id
            """, (usuario_id, mensaje))
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()


# ============================================================
#  PRESUPUESTOS
#  ISO/IEC 25000 - Funcionalidad: Completitud de metas financieras
#  ISO 9001 - Mejora continua: Control de límites por categoría
# ============================================================

class PGPresupuestoRepository:
    """
    Gestiona presupuestos mensuales por categoría.
    Permite al usuario establecer límites de gasto y monitorear cumplimiento.
    Normas: ISO/IEC 25000 - Funcionalidad, ISO 9001 - Control de procesos
    """

    def crear(self, usuario_id, categoria_id, monto_limite, mes):
        """
        Crea o actualiza un presupuesto para una categoría en un mes específico.
        Args:
            usuario_id: ID del usuario
            categoria_id: ID de la categoría (None = presupuesto global)
            monto_limite: Monto máximo permitido
            mes: Fecha del primer día del mes (ej: '2026-03-01')
        Returns:
            Dict con id y datos del presupuesto o None si falla
        """
        conn = _get_conn()
        try:
            row = _execute_returning(conn, """
                INSERT INTO presupuestos (usuario_id, categoria_id, monto_limite, mes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (usuario_id, categoria_id, mes)
                DO UPDATE SET monto_limite = EXCLUDED.monto_limite, activo = 1
                RETURNING id, usuario_id, categoria_id, monto_limite, mes::text
            """, (usuario_id, categoria_id, float(monto_limite), mes))
            conn.commit()
            if row:
                row["monto_limite"] = float(row["monto_limite"])
            return row
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_por_usuario(self, usuario_id, mes=None):
        """
        Lista presupuestos activos del usuario, opcionalmente filtrados por mes.
        Incluye el gasto actual vs el límite.
        """
        conn = _get_conn()
        try:
            q = """
                SELECT p.id, p.categoria_id, p.monto_limite, p.mes::text,
                       c.nombre AS categoria_nombre, c.icono AS categoria_icono,
                       COALESCE(SUM(m.monto), 0) AS gasto_actual
                FROM presupuestos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN movimientos m ON m.usuario_id = p.usuario_id
                    AND m.tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto')
                    AND DATE_TRUNC('month', m.fecha) = p.mes
                    AND (p.categoria_id IS NULL OR m.categoria_id = p.categoria_id)
                WHERE p.usuario_id = %s AND p.activo = 1
            """
            params = [usuario_id]
            if mes:
                q += " AND p.mes = %s"
                params.append(mes)
            q += " GROUP BY p.id, p.categoria_id, p.monto_limite, p.mes, c.nombre, c.icono"
            q += " ORDER BY p.mes DESC, c.nombre"
            
            rows = _fetch_all(conn, q, params)
            for r in rows:
                r["monto_limite"] = float(r["monto_limite"])
                r["gasto_actual"] = float(r["gasto_actual"])
                r["porcentaje_usado"] = round(r["gasto_actual"] / r["monto_limite"] * 100, 1) if r["monto_limite"] > 0 else 0
                r["excedido"] = r["gasto_actual"] > r["monto_limite"]
            return rows
        finally:
            conn.close()

    def eliminar(self, presupuesto_id, usuario_id):
        """Desactiva un presupuesto (soft delete)."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE presupuestos SET activo = 0 WHERE id = %s AND usuario_id = %s",
                (presupuesto_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def verificar_exceso(self, usuario_id, categoria_id, mes):
        """
        Verifica si el usuario ha excedido su presupuesto para una categoría.
        Retorna dict con estado o None si no hay presupuesto definido.
        """
        conn = _get_conn()
        try:
            row = _fetch_one(conn, """
                SELECT p.monto_limite,
                       COALESCE(SUM(m.monto), 0) AS gasto_actual
                FROM presupuestos p
                LEFT JOIN movimientos m ON m.usuario_id = p.usuario_id
                    AND m.tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto')
                    AND DATE_TRUNC('month', m.fecha) = p.mes
                    AND (p.categoria_id IS NULL OR m.categoria_id = p.categoria_id)
                WHERE p.usuario_id = %s AND p.mes = %s AND p.activo = 1
                  AND ((%s IS NULL AND p.categoria_id IS NULL) OR p.categoria_id = %s)
                GROUP BY p.monto_limite
            """, (usuario_id, mes, categoria_id, categoria_id))
            if not row:
                return None
            limite = float(row["monto_limite"])
            actual = float(row["gasto_actual"])
            return {
                "monto_limite": limite,
                "gasto_actual": actual,
                "disponible": round(limite - actual, 2),
                "porcentaje_usado": round(actual / limite * 100, 1) if limite > 0 else 0,
                "excedido": actual > limite,
            }
        finally:
            conn.close()

    def comparar_mes(self, usuario_id, mes_actual, mes_anterior, categoria_id=None):
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT COALESCE(SUM(m.monto), 0) AS total "
                "FROM movimientos m "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s AND t.codigo = 'gasto' "
                "AND DATE_TRUNC('month', m.fecha) = %s "
                "AND (%s IS NULL OR m.categoria_id = %s)",
                (usuario_id, mes_actual, categoria_id, categoria_id),
            )
            total_actual = float(row["total"]) if row else 0.0

            row_prev = _fetch_one(
                conn,
                "SELECT COALESCE(SUM(m.monto), 0) AS total "
                "FROM movimientos m "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s AND t.codigo = 'gasto' "
                "AND DATE_TRUNC('month', m.fecha) = %s "
                "AND (%s IS NULL OR m.categoria_id = %s)",
                (usuario_id, mes_anterior, categoria_id, categoria_id),
            )
            total_prev = float(row_prev["total"]) if row_prev else 0.0

            variacion = total_actual - total_prev
            variacion_pct = round((variacion / total_prev) * 100, 1) if total_prev > 0 else (100.0 if total_actual > 0 else 0.0)

            return {
                "gasto_actual": round(total_actual, 2),
                "gasto_anterior": round(total_prev, 2),
                "variacion_monto": round(variacion, 2),
                "variacion_pct": variacion_pct,
            }
        finally:
            conn.close()


# ============================================================
#  RECURRENCIAS (Movimientos Automáticos)
#  ISO/IEC 12207 - Automatización de procesos
#  ISO/IEC 20000 - Gestión de servicios recurrentes
# ============================================================

class PGRecurrenciaRepository:
    """
    Gestiona movimientos recurrentes (suscripciones, salarios, rentas).
    Permite programar ingresos/gastos automáticos con frecuencia definida.
    Normas: ISO/IEC 12207 - Automatización, ISO/IEC 20000 - Gestión de servicios
    """

    def crear(self, usuario_id, categoria_id, tipo, monto, descripcion,
              frecuencia, dia_ejecucion, proxima_fecha):
        """
        Crea una nueva recurrencia.
        Args:
            usuario_id: ID del usuario
            categoria_id: ID de la categoría
            tipo: 'ingreso' o 'gasto'
            monto: Monto del movimiento
            descripcion: Descripción del movimiento
            frecuencia: 'diario', 'semanal', 'quincenal', 'mensual', 'anual'
            dia_ejecucion: Día del mes (1-31) o día de la semana (1-7)
            proxima_fecha: Fecha de la próxima ejecución
        Returns:
            Dict con datos de la recurrencia creada
        """
        conn = _get_conn()
        try:
            row = _execute_returning(conn, """
                INSERT INTO recurrencias 
                    (usuario_id, categoria_id, tipo_id, monto, descripcion, frecuencia, dia_ejecucion, proxima_fecha)
                VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, %s, %s, %s, %s)
                RETURNING id, (SELECT codigo FROM tipos_movimiento WHERE id = tipo_id) AS tipo,
                          monto, descripcion, frecuencia, proxima_fecha::text
            """, (usuario_id, categoria_id, tipo, float(monto), descripcion.strip(),
                  frecuencia, dia_ejecucion, proxima_fecha))
            conn.commit()
            if row:
                row["monto"] = float(row["monto"])
            return row
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_por_usuario(self, usuario_id, solo_activas=True):
        """Lista recurrencias del usuario con datos de categoría."""
        conn = _get_conn()
        try:
            q = """
                SELECT r.id, r.categoria_id, t.codigo AS tipo, r.monto, r.descripcion,
                       r.frecuencia, r.dia_ejecucion, r.proxima_fecha::text, r.activo,
                       c.nombre AS categoria_nombre, c.icono AS categoria_icono
                FROM recurrencias r
                JOIN categorias c ON r.categoria_id = c.id
                JOIN tipos_movimiento t ON r.tipo_id = t.id
                WHERE r.usuario_id = %s
            """
            params = [usuario_id]
            if solo_activas:
                q += " AND r.activo = 1"
            q += " ORDER BY r.proxima_fecha ASC"
            rows = _fetch_all(conn, q, params)
            for r in rows:
                r["monto"] = float(r["monto"])
            return rows
        finally:
            conn.close()

    def obtener_pendientes(self, fecha_hasta):
        """
        Obtiene todas las recurrencias activas cuya próxima fecha es <= fecha_hasta.
        Usado por un job scheduler para ejecutar movimientos automáticos.
        """
        conn = _get_conn()
        try:
            rows = _fetch_all(conn, """
                SELECT r.id, r.usuario_id, r.categoria_id, t.codigo AS tipo, r.monto, r.descripcion,
                       r.frecuencia, r.dia_ejecucion, r.proxima_fecha::text, r.activo, r.creado_en,
                       c.nombre AS categoria_nombre
                FROM recurrencias r
                JOIN categorias c ON r.categoria_id = c.id
                JOIN tipos_movimiento t ON r.tipo_id = t.id
                WHERE r.activo = 1 AND r.proxima_fecha <= %s
                ORDER BY r.proxima_fecha ASC
            """, (fecha_hasta,))
            for r in rows:
                r["monto"] = float(r["monto"])
                if hasattr(r.get("proxima_fecha"), "isoformat"):
                    r["proxima_fecha"] = r["proxima_fecha"].isoformat()
            return rows
        finally:
            conn.close()

    def actualizar_proxima_fecha(self, recurrencia_id, nueva_fecha):
        """Actualiza la próxima fecha de ejecución después de procesar."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE recurrencias SET proxima_fecha = %s WHERE id = %s",
                (nueva_fecha, recurrencia_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def desactivar(self, recurrencia_id, usuario_id):
        """Desactiva una recurrencia (soft delete)."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE recurrencias SET activo = 0 WHERE id = %s AND usuario_id = %s",
                (recurrencia_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def reactivar(self, recurrencia_id, usuario_id, proxima_fecha):
        """Reactiva una recurrencia con nueva fecha."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE recurrencias SET activo = 1, proxima_fecha = %s WHERE id = %s AND usuario_id = %s",
                (proxima_fecha, recurrencia_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# ============================================================
#  REFRESH TOKENS (JWT)
#  ISO/IEC 27001 - Gestión de tokens de sesión
# ============================================================

class PGRefreshTokenRepository:
    """
    Gestiona refresh tokens para autenticación JWT.
    ISO/IEC 27001 - Gestión de tokens de sesión
    """

    def guardar(self, usuario_id, token_hash, expires_at, device_info=None):
        """Almacena un nuevo refresh token en la base de datos."""
        conn = None
        try:
            conn = _get_conn()
            _execute_returning(conn, """
                INSERT INTO refresh_tokens (usuario_id, token_hash, expires_at, device_info)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (usuario_id, token_hash, expires_at, device_info))
            conn.commit()
            return True
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def verificar(self, token_hash):
        """Verifica si un refresh token es válido (existe, no expirado, no revocado)."""
        conn = _get_conn()
        try:
            return _fetch_one(
                conn,
                "SELECT usuario_id, expires_at FROM refresh_tokens "
                "WHERE token_hash = %s AND revoked = 0 AND expires_at > (NOW() AT TIME ZONE 'UTC')",
                (token_hash,),
            )
        finally:
            conn.close()

    def revocar(self, token_hash):
        """Revoca un refresh token específico."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = %s",
                (token_hash,),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def revocar_todos(self, usuario_id):
        """Revoca todos los refresh tokens de un usuario (logout global)."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE refresh_tokens SET revoked = 1 WHERE usuario_id = %s",
                (usuario_id,),
            )
            conn.commit()
            return rc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def limpiar_expirados(self):
        """Elimina tokens expirados de la base de datos."""
        conn = _get_conn()
        try:
            rc = _execute(conn, "DELETE FROM refresh_tokens WHERE expires_at < (NOW() AT TIME ZONE 'UTC')")
            conn.commit()
            return rc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
