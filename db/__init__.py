"""
============================================================
  Capa de Base de Datos - PostgreSQL
============================================================
  Normas: ISO/IEC 12207, CMMI Nivel 3, ISO/IEC 25000
============================================================
  Instancia los repositorios PostgreSQL.
  La capa API no necesita saber detalles del engine.
============================================================
"""

from .pg_repository import (
    init_postgres as init_database,
    PGUsuarioRepository       as _UsuarioRepo,
    PGCategoriaRepository     as _CategoriaRepo,
    PGMovimientoRepository    as _MovimientoRepo,
    PGNotificacionRepository  as _NotificacionRepo,
    PGPerfilIARepository      as _PerfilIARepo,
    PGInsightDiarioRepository as _InsightDiarioRepo,
)

# Instancias únicas — la API las usa directamente
UsuarioRepository      = _UsuarioRepo()
CategoriaRepository    = _CategoriaRepo()
MovimientoRepository   = _MovimientoRepo()
NotificacionRepository = _NotificacionRepo()
PerfilIARepository     = _PerfilIARepo()
InsightDiarioRepository = _InsightDiarioRepo()

__all__ = [
    'init_database',
    'UsuarioRepository',
    'CategoriaRepository',
    'MovimientoRepository',
    'NotificacionRepository',
    'PerfilIARepository',
    'InsightDiarioRepository',
]
