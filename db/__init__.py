"""
============================================================
  Capa de Base de Datos - Multi-Backend
============================================================
  Normas: ISO/IEC 12207, CMMI Nivel 3, ISO/IEC 25000
============================================================
  Soporta PostgreSQL (producción) y MySQL/MariaDB (XAMPP).
  Selección automática mediante variable DB_BACKEND.
============================================================
"""

from .config import DB_BACKEND

# Seleccionar backend según configuración
if DB_BACKEND == "mysql":
    # MySQL/MariaDB (XAMPP)
    from .mysql_repository import (
        init_mysql as init_database,
        MySQLUsuarioRepository       as _UsuarioRepo,
        MySQLCategoriaRepository     as _CategoriaRepo,
        MySQLMovimientoRepository    as _MovimientoRepo,
        MySQLNotificacionRepository  as _NotificacionRepo,
        MySQLPerfilIARepository      as _PerfilIARepo,
        MySQLInsightDiarioRepository as _InsightDiarioRepo,
        MySQLPresupuestoRepository   as _PresupuestoRepo,
        MySQLRecurrenciaRepository   as _RecurrenciaRepo,
        MySQLRefreshTokenRepository  as _RefreshTokenRepo,
    )
    print(f"[DB] Backend: MySQL/MariaDB (XAMPP)")
else:
    # PostgreSQL (default)
    from .pg_repository import (
        init_postgres as init_database,
        PGUsuarioRepository       as _UsuarioRepo,
        PGCategoriaRepository     as _CategoriaRepo,
        PGMovimientoRepository    as _MovimientoRepo,
        PGNotificacionRepository  as _NotificacionRepo,
        PGPerfilIARepository      as _PerfilIARepo,
        PGInsightDiarioRepository as _InsightDiarioRepo,
        PGPresupuestoRepository   as _PresupuestoRepo,
        PGRecurrenciaRepository   as _RecurrenciaRepo,
        PGRefreshTokenRepository  as _RefreshTokenRepo,
    )
    print(f"[DB] Backend: PostgreSQL")

from .crypto import (
    encrypt,
    decrypt,
    encrypt_if_enabled,
    decrypt_if_encrypted,
    encrypt_dict_fields,
    decrypt_dict_fields,
    is_crypto_available,
    get_crypto_backend,
    generate_master_key,
)

# Instancias únicas — la API las usa directamente
UsuarioRepository       = _UsuarioRepo()
CategoriaRepository     = _CategoriaRepo()
MovimientoRepository    = _MovimientoRepo()
NotificacionRepository  = _NotificacionRepo()
PerfilIARepository      = _PerfilIARepo()
InsightDiarioRepository = _InsightDiarioRepo()
PresupuestoRepository   = _PresupuestoRepo()
RecurrenciaRepository   = _RecurrenciaRepo()
RefreshTokenRepository  = _RefreshTokenRepo()

__all__ = [
    # Repositorios
    'init_database',
    'UsuarioRepository',
    'CategoriaRepository',
    'MovimientoRepository',
    'NotificacionRepository',
    'PerfilIARepository',
    'InsightDiarioRepository',
    'PresupuestoRepository',
    'RecurrenciaRepository',
    'RefreshTokenRepository',
    # Cifrado AES-256
    'encrypt',
    'decrypt',
    'encrypt_if_enabled',
    'decrypt_if_encrypted',
    'encrypt_dict_fields',
    'decrypt_dict_fields',
    'is_crypto_available',
    'get_crypto_backend',
    'generate_master_key',
    # Config
    'DB_BACKEND',
]
