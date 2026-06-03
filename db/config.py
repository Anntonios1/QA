"""
============================================================
  CONFIGURACIÓN DE BASE DE DATOS - Multi-Backend
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Gestión de configuración
    - CMMI Nivel 3: Definición de procesos estándar
    - ISO 9001: Gestión de cambios controlados
    - ISO/IEC 25000: Portabilidad - Adaptabilidad
============================================================
  Soporta PostgreSQL (producción) y MySQL/MariaDB (XAMPP)
  Configuración mediante variables de entorno.
============================================================
"""

import os

# ============================================================
#  SELECTOR DE BACKEND
#  DB_BACKEND = "postgresql" | "mysql"
# ============================================================

# [NORMA: ISO/IEC 27001 - Control A.9.4.3] Credenciales de base de datos almacenadas en variables de entorno, no en código fuente
# [NORMA: CMMI - Área de Proceso: Gestión de Configuración] Separación de configuración del código ejecutable
DB_BACKEND = os.environ.get("DB_BACKEND", "postgresql").lower()

# ============================================================
#  CONFIGURACIÓN PostgreSQL
# ============================================================

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

# ============================================================
#  CONFIGURACIÓN MySQL/MariaDB (XAMPP)
# ============================================================

MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "gastos_db")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")

def get_mysql_dsn() -> str:
    """Construye el DSN de MySQL desde variables de entorno."""
    return f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# ============================================================
#  JWT CONFIGURACIÓN
# ============================================================

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "ControlCash_JWT_Secret_CHANGE_IN_PRODUCTION")
JWT_ACCESS_EXPIRES_MINUTES = int(os.environ.get("JWT_ACCESS_EXPIRES_MINUTES", "15"))
JWT_REFRESH_EXPIRES_DAYS = int(os.environ.get("JWT_REFRESH_EXPIRES_DAYS", "7"))

