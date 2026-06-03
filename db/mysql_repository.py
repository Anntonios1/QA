"""
============================================================
  SHIM DE COMPATIBILIDAD — MySQL/MariaDB Repository
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Implementación conforme a interfaz
    - ISO 9126: Fiabilidad, Seguridad, Eficiencia
    - CMMI Nivel 3: Proceso estándar implementado
    - ISO/IEC 25000: Portabilidad - Adaptabilidad
============================================================
  Compatible con XAMPP (MariaDB/MySQL)
  Driver: PyMySQL (puro Python, sin dependencias nativas)
  Requiere: pip install pymysql
============================================================

  REFACTORING (2026-05-28):
    Este archivo fue dividido en submódulos dentro de db/mysql/
    para seguir el principio de responsabilidad única (SRP).
    Este shim mantiene compatibilidad total con el código
    existente que importe desde db/mysql_repository.py.

  Estructura de submódulos:
    db/mysql/_schema.py        — SCHEMA_SQL, SEED_CATEGORIAS
    db/mysql/_connection.py    — helpers de conexión, init_mysql()
    db/mysql/usuario.py        — MySQLUsuarioRepository
    db/mysql/categoria.py      — MySQLCategoriaRepository
    db/mysql/movimiento.py     — MySQLMovimientoRepository (bug fix)
    db/mysql/notificacion.py   — MySQLNotificacionRepository
    db/mysql/perfil_ia.py      — MySQLPerfilIARepository
    db/mysql/insight_diario.py — MySQLInsightDiarioRepository
    db/mysql/presupuesto.py    — MySQLPresupuestoRepository
    db/mysql/recurrencia.py    — MySQLRecurrenciaRepository
    db/mysql/refresh_token.py  — MySQLRefreshTokenRepository

  BUG CORREGIDO (2026-05-28):
    MySQLMovimientoRepository.actualizar() — el conn.commit()
    estaba ubicado DESPUÉS del return (código muerto / dead code).
    El UPDATE se ejecutaba pero nunca se confirmaba, causando
    rollback implícito al cerrar la conexión. Ver movimiento.py.
============================================================
"""

# Re-exportar todo desde el paquete modular
from .mysql import (
    # Esquema y seeds
    SCHEMA_SQL,
    SEED_CATEGORIAS,
    # Inicialización
    init_mysql,
    # Helpers internos
    MYSQL_AVAILABLE,
    _get_conn,
    _fetch_one,
    _fetch_all,
    _execute,
    _execute_lastid,
    # Repositorios
    MySQLUsuarioRepository,
    MySQLCategoriaRepository,
    MySQLMovimientoRepository,
    MySQLNotificacionRepository,
    MySQLPerfilIARepository,
    MySQLInsightDiarioRepository,
    MySQLPresupuestoRepository,
    MySQLRecurrenciaRepository,
    MySQLRefreshTokenRepository,
)

__all__ = [
    "SCHEMA_SQL",
    "SEED_CATEGORIAS",
    "init_mysql",
    "MYSQL_AVAILABLE",
    "_get_conn",
    "_fetch_one",
    "_fetch_all",
    "_execute",
    "_execute_lastid",
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
