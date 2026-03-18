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
        fecha_creacion  TIMESTAMP    NOT NULL DEFAULT NOW(),
        activo          SMALLINT     NOT NULL DEFAULT 1 CHECK(activo IN (0, 1))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS categorias (
        id          SERIAL       PRIMARY KEY,
        nombre      VARCHAR(100) NOT NULL UNIQUE CHECK(length(nombre) >= 2),
        tipo        VARCHAR(10)  NOT NULL CHECK(tipo IN ('ingreso', 'gasto')),
        icono       VARCHAR(10)  DEFAULT '💰',
        activo      SMALLINT     NOT NULL DEFAULT 1 CHECK(activo IN (0, 1))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS movimientos (
        id              SERIAL       PRIMARY KEY,
        usuario_id      INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        categoria_id    INTEGER      NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
        tipo            VARCHAR(10)  NOT NULL CHECK(tipo IN ('ingreso', 'gasto')),
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
    "CREATE INDEX IF NOT EXISTS idx_mov_usuario   ON movimientos(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_mov_fecha     ON movimientos(fecha)",
    "CREATE INDEX IF NOT EXISTS idx_mov_tipo      ON movimientos(tipo)",
    "CREATE INDEX IF NOT EXISTS idx_notif_usuario ON notificaciones(usuario_id)",
    "CREATE INDEX IF NOT EXISTS idx_notif_leida   ON notificaciones(usuario_id, leida)",
    "CREATE INDEX IF NOT EXISTS idx_perfiles_ia_usuario ON perfiles_ia(usuario_id, fecha)",
    "CREATE INDEX IF NOT EXISTS idx_insights_usuario    ON insights_diarios(usuario_id, fecha)",
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

        for nombre, tipo, icono in SEED_CATEGORIAS:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO categorias (nombre, tipo, icono) VALUES (%s, %s, %s) "
                    "ON CONFLICT (nombre) DO NOTHING",
                    (nombre, tipo, icono),
                )
                cur.close()
            except Exception:
                conn.rollback()

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

class PGUsuarioRepository(BaseUsuarioRepository, PasswordMixin):

    def crear(self, nombre, email, password):
        conn = _get_conn()
        try:
            pw_hash, _ = self.hash_password(password)
            row = _execute_returning(
                conn,
                "INSERT INTO usuarios (nombre, email, password_hash) "
                "VALUES (%s, %s, %s) RETURNING id, nombre, email",
                (nombre.strip(), email.strip().lower(), pw_hash),
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
                "SELECT id, nombre, email, password_hash, activo FROM usuarios "
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
                "SELECT id, nombre, email, fecha_creacion, activo "
                "FROM usuarios WHERE id = %s",
                (usuario_id,),
            )
        finally:
            conn.close()


class PGCategoriaRepository(BaseCategoriaRepository):

    def listar(self, tipo=None):
        conn = _get_conn()
        try:
            if tipo:
                return _fetch_all(
                    conn,
                    "SELECT * FROM categorias WHERE activo = 1 AND tipo = %s ORDER BY nombre",
                    (tipo,),
                )
            return _fetch_all(
                conn,
                "SELECT * FROM categorias WHERE activo = 1 ORDER BY tipo, nombre",
            )
        finally:
            conn.close()

    def obtener_por_id(self, categoria_id):
        conn = _get_conn()
        try:
            return _fetch_one(
                conn, "SELECT * FROM categorias WHERE id = %s", (categoria_id,)
            )
        finally:
            conn.close()


class PGMovimientoRepository(BaseMovimientoRepository):

    def crear(self, usuario_id, categoria_id, tipo, monto, descripcion="", fecha=None):
        conn = _get_conn()
        try:
            if fecha is None:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = _execute_returning(
                conn,
                "INSERT INTO movimientos (usuario_id, categoria_id, tipo, monto, descripcion, fecha) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, tipo, monto",
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

    def listar_por_usuario(self, usuario_id, limite=50, tipo=None,
                           fecha_desde=None, fecha_hasta=None):
        conn = _get_conn()
        try:
            q = (
                "SELECT m.id, m.usuario_id, m.tipo, m.monto, m.descripcion, m.fecha, "
                "m.fecha_registro, m.categoria_id, "
                "c.nombre AS categoria_nombre, c.icono AS categoria_icono "
                "FROM movimientos m JOIN categorias c ON m.categoria_id = c.id "
                "WHERE m.usuario_id = %s"
            )
            p = [usuario_id]
            if tipo:
                q += " AND m.tipo = %s"
                p.append(tipo)
            if fecha_desde:
                q += " AND m.fecha >= %s"
                p.append(fecha_desde)
            if fecha_hasta:
                q += " AND m.fecha <= %s"
                p.append(fecha_hasta)
            q += " ORDER BY m.fecha DESC LIMIT %s"
            p.append(limite)
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
                sets.append("tipo = %s")
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
                "RETURNING id, tipo, monto, descripcion, fecha, categoria_id"
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
                    COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS total_ingresos,
                    COALESCE(SUM(CASE WHEN tipo = 'gasto'   THEN monto ELSE 0 END), 0) AS total_gastos,
                    COUNT(*) AS total_movimientos
                FROM movimientos WHERE usuario_id = %s
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

    def obtener_resumen(self, usuario_id, dias=30):
        conn = _get_conn()
        try:
            fi = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
            fi_prev = (datetime.now() - timedelta(days=dias * 2)).strftime("%Y-%m-%d")

            cats = _fetch_all(conn, """
                SELECT c.nombre, c.icono, m.tipo, SUM(m.monto) AS total, COUNT(*) AS cantidad
                FROM movimientos m JOIN categorias c ON m.categoria_id = c.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
                GROUP BY c.nombre, c.icono, m.tipo ORDER BY total DESC
            """, (usuario_id, fi))

            diario = _fetch_all(conn, """
                SELECT fecha::date AS dia, tipo, SUM(monto) AS total
                FROM movimientos WHERE usuario_id = %s AND fecha >= %s
                GROUP BY fecha::date, tipo ORDER BY dia
            """, (usuario_id, fi))

            totales = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN tipo = 'gasto'   THEN monto ELSE 0 END), 0) AS gastos,
                    COUNT(*) AS movimientos
                FROM movimientos WHERE usuario_id = %s AND fecha >= %s
            """, (usuario_id, fi))

            prev = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN tipo = 'gasto'   THEN monto ELSE 0 END), 0) AS gastos
                FROM movimientos WHERE usuario_id = %s AND fecha >= %s AND fecha < %s
            """, (usuario_id, fi_prev, fi))

            top3 = _fetch_all(conn, """
                SELECT m.monto, m.descripcion, m.fecha, c.nombre AS categoria, c.icono
                FROM movimientos m JOIN categorias c ON m.categoria_id = c.id
                WHERE m.usuario_id = %s AND m.tipo = 'gasto' AND m.fecha >= %s
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
        conn = _get_conn()
        try:
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
            conn.rollback()
            raise
        finally:
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
        conn = _get_conn()
        try:
            _execute_returning(conn, """
                INSERT INTO insights_diarios (usuario_id, fecha, enviado, mensaje)
                VALUES (%s, CURRENT_DATE, 1, %s)
                ON CONFLICT (usuario_id, fecha) DO UPDATE SET enviado = 1, mensaje = EXCLUDED.mensaje
                RETURNING id
            """, (usuario_id, mensaje))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
