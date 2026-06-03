"""
============================================================
  CONEXIÓN Y HELPERS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Implementación conforme a interfaz
    - ISO 9126: Fiabilidad, Eficiencia
    - CMMI Nivel 3: Proceso estándar implementado
============================================================
  Centraliza la lógica de apertura de conexión y los
  helpers de query para evitar duplicación en cada
  repositorio (DRY — Don't Repeat Yourself).
============================================================
"""

try:
    import pymysql
    import pymysql.cursors
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

from ._schema import SCHEMA_SQL


# ============================================================
#  HELPER: APERTURA DE CONEXIÓN
# ============================================================

def _get_conn():
    """
    Abre una conexión MySQL/MariaDB usando PyMySQL.
    Usa DictCursor para que fetchone()/fetchall() retornen dicts.
    [NORMA: ISO/IEC 27001 - Control A.9.4.3] Credenciales desde entorno.
    """
    if not MYSQL_AVAILABLE:
        raise ImportError("pymysql no está instalado. Ejecuta: pip install pymysql")

    from ..config import (
        MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE,
        MYSQL_USER, MYSQL_PASSWORD,
    )

    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        database=MYSQL_DATABASE,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD or "",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    return conn


# ============================================================
#  HELPERS DE QUERY
# ============================================================

def _fetch_one(conn, query, params=None):
    """Ejecuta una query y retorna la primera fila como dict (o None)."""
    with conn.cursor() as cur:
        cur.execute(query, params or ())
        return cur.fetchone()


def _fetch_all(conn, query, params=None):
    """Ejecuta una query y retorna todas las filas como lista de dicts."""
    with conn.cursor() as cur:
        cur.execute(query, params or ())
        return cur.fetchall()


def _execute(conn, query, params=None):
    """Ejecuta una sentencia DML (INSERT/UPDATE/DELETE) y retorna rowcount."""
    with conn.cursor() as cur:
        cur.execute(query, params or ())
        return cur.rowcount


def _execute_lastid(conn, query, params=None):
    """
    Ejecuta un INSERT y retorna el lastrowid.
    Equivalente a RETURNING id en PostgreSQL.
    """
    with conn.cursor() as cur:
        cur.execute(query, params or ())
        return cur.lastrowid


# ============================================================
#  INICIALIZACIÓN DEL ESQUEMA
# ============================================================

def init_mysql():
    """
    Crea el esquema y siembra datos iniciales en MySQL/MariaDB.
    Maneja de forma segura statements que pueden fallar en instalaciones
    existentes (ALTER TABLE, CREATE INDEX duplicados, etc.).
    [NORMA: ISO/IEC 12207 - Proceso de Implementación]
    """
    conn = _get_conn()
    try:
        for stmt in SCHEMA_SQL:
            try:
                with conn.cursor() as cur:
                    # MySQL no soporta CREATE INDEX IF NOT EXISTS en todas las versiones
                    if "CREATE INDEX IF NOT EXISTS" in stmt:
                        stmt = stmt.replace("CREATE INDEX IF NOT EXISTS", "CREATE INDEX")
                        try:
                            cur.execute(stmt)
                        except pymysql.err.OperationalError as e:
                            if "Duplicate key name" not in str(e):
                                raise
                    else:
                        cur.execute(stmt)
            except Exception as e:
                print(f"[DB-MySQL] Advertencia en statement: {e}")
                conn.rollback()
                continue

        conn.commit()
        print("[DB-MySQL] Esquema inicializado correctamente.")
    except Exception as e:
        conn.rollback()
        print(f"[DB-MySQL] Error al inicializar: {e}")
        raise
    finally:
        conn.close()
