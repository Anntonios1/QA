"""
============================================================
  CONFIGURACIÓN DE BASE DE DATOS - PostgreSQL
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Gestión de configuración
    - CMMI Nivel 3: Definición de procesos estándar
    - ISO 9001: Gestión de cambios controlados
============================================================
  Configuración de conexión a PostgreSQL mediante
  variables de entorno.
============================================================
"""

import os

# ============================================================
#  CONFIGURACIÓN - Leer de variables de entorno o .env
# ============================================================

# --- PostgreSQL ---
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = os.environ.get("PG_PORT", "5432")
PG_DATABASE = os.environ.get("PG_DATABASE", "gastos_db")
PG_USER = os.environ.get("PG_USER", "postgres")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "")

def get_pg_dsn() -> str:
    """Construye el DSN de PostgreSQL desde variables de entorno."""
    dsn = f"host={PG_HOST} port={PG_PORT} dbname={PG_DATABASE} user={PG_USER}"
    if PG_PASSWORD:
        dsn += f" password={PG_PASSWORD}"
    return dsn
