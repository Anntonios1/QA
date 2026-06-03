"""
============================================================
  PAQUETE db/mysql — MySQL/MariaDB Repository
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Implementación conforme a interfaz
    - ISO/IEC 25000: Portabilidad - Adaptabilidad
    - CMMI Nivel 3: Proceso estándar implementado
============================================================
  Re-exporta todos los repositorios y utilidades MySQL.
  Mantiene compatibilidad total con db/__init__.py y
  cualquier código que importe desde db/mysql_repository.py.

  Estructura de submódulos:
    _schema.py       — SCHEMA_SQL, SEED_CATEGORIAS
    _connection.py   — helpers de conexión, init_mysql()
    usuario.py       — MySQLUsuarioRepository
    categoria.py     — MySQLCategoriaRepository
    movimiento.py    — MySQLMovimientoRepository (bug commit corregido)
    notificacion.py  — MySQLNotificacionRepository
    perfil_ia.py     — MySQLPerfilIARepository
    insight_diario.py— MySQLInsightDiarioRepository
    presupuesto.py   — MySQLPresupuestoRepository
    recurrencia.py   — MySQLRecurrenciaRepository
    refresh_token.py — MySQLRefreshTokenRepository
============================================================
"""

# Esquema y seeds
from ._schema import SCHEMA_SQL, SEED_CATEGORIAS

# Inicialización de la base de datos
from ._connection import (
    init_mysql,
    _get_conn,
    _fetch_one,
    _fetch_all,
    _execute,
    _execute_lastid,
    MYSQL_AVAILABLE,
)

# Repositorios
from .usuario       import MySQLUsuarioRepository
from .categoria     import MySQLCategoriaRepository
from .movimiento    import MySQLMovimientoRepository
from .notificacion  import MySQLNotificacionRepository
from .perfil_ia     import MySQLPerfilIARepository
from .insight_diario import MySQLInsightDiarioRepository
from .presupuesto   import MySQLPresupuestoRepository
from .recurrencia   import MySQLRecurrenciaRepository
from .refresh_token import MySQLRefreshTokenRepository

__all__ = [
    # Esquema
    "SCHEMA_SQL",
    "SEED_CATEGORIAS",
    # Inicialización
    "init_mysql",
    # Helpers internos (por compatibilidad)
    "_get_conn",
    "_fetch_one",
    "_fetch_all",
    "_execute",
    "_execute_lastid",
    "MYSQL_AVAILABLE",
    # Repositorios
    "MySQLUsuarioRepository",
    "MySQLCategoriaRepository",
    "MySQLMovimientoRepository",
    "MySQLNotificacionRepository",
    "MySQLPerfilIARepository",
    "MySQLInsightDiarioRepository",
    "MySQLPresupuestoRepository",
    "MySQLRecurrenciaRepository",
    "MySQLRefreshTokenRepository",
]
