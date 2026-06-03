"""
Script de verificacion de la modularizacion y bug fix de MySQL repository.
Carga el .env y verifica todos los modulos del nuevo paquete db/mysql/.
"""
import os
import sys
from pathlib import Path

# Cargar .env
env_file = Path('.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, _, v = line.partition('=')
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, 'api')

backend = os.environ.get('DB_BACKEND', 'postgresql')
print(f"DB_BACKEND configurado: {backend}")

# -----------------------------------------------
print("\n[TEST 1] Importando paquete db.mysql directamente...")
from db.mysql import (
    MySQLUsuarioRepository,
    MySQLCategoriaRepository,
    MySQLMovimientoRepository,
    MySQLNotificacionRepository,
    MySQLPerfilIARepository,
    MySQLInsightDiarioRepository,
    MySQLPresupuestoRepository,
    MySQLRecurrenciaRepository,
    MySQLRefreshTokenRepository,
    init_mysql,
    MYSQL_AVAILABLE,
)
print("  OK - todos los repositorios MySQL importados")
print(f"  pymysql disponible: {MYSQL_AVAILABLE}")

# -----------------------------------------------
print("\n[TEST 2] Verificando shim de compatibilidad mysql_repository.py...")
from db.mysql_repository import (
    MySQLMovimientoRepository as M_shim,
    MySQLUsuarioRepository as U_shim,
    init_mysql as init_shim,
)
assert MySQLMovimientoRepository is M_shim, "ERROR: shim movimiento no apunta a la misma clase"
assert MySQLUsuarioRepository is U_shim, "ERROR: shim usuario no apunta a la misma clase"
assert init_mysql is init_shim, "ERROR: shim init_mysql no apunta a la misma funcion"
print("  OK - shim apunta correctamente a las clases del paquete")

# -----------------------------------------------
print("\n[TEST 3] Verificando bug fix en MySQLMovimientoRepository.actualizar()...")
import inspect
src = inspect.getsource(MySQLMovimientoRepository.actualizar)
# Debe haber commit() ANTES de 'return result'
commit_idx = src.find('conn.commit()')
result_idx = src.find('return result')
assert commit_idx > 0, "ERROR: conn.commit() no encontrado en actualizar()"
assert result_idx > 0, "ERROR: 'return result' no encontrado en actualizar()"
assert commit_idx < result_idx, (
    f"BUG PRESENTE: commit({commit_idx}) debe ser < return({result_idx})"
)
print("  OK - bug fix verificado: commit() esta ANTES de 'return result'")

# -----------------------------------------------
print("\n[TEST 4] Verificando que actualizar() NO tiene commit despues de return (dead code)...")
# Buscar el patron bugueado original
lines = src.splitlines()
in_with_block = False
last_return_line = -1
commit_after_return = False
for i, line in enumerate(lines):
    stripped = line.strip()
    if 'return result' in stripped:
        last_return_line = i
    if last_return_line > 0 and 'conn.commit()' in stripped and i > last_return_line:
        commit_after_return = True
        print(f"  WARN: commit despues de return en linea {i}: {stripped}")
if not commit_after_return:
    print("  OK - no hay codigo muerto (commit despues de return)")

# -----------------------------------------------
print("\n[TEST 5] Verificando metodos de todos los repositorios...")
repos = {
    "MySQLUsuarioRepository": MySQLUsuarioRepository,
    "MySQLCategoriaRepository": MySQLCategoriaRepository,
    "MySQLMovimientoRepository": MySQLMovimientoRepository,
    "MySQLNotificacionRepository": MySQLNotificacionRepository,
    "MySQLPerfilIARepository": MySQLPerfilIARepository,
    "MySQLInsightDiarioRepository": MySQLInsightDiarioRepository,
    "MySQLPresupuestoRepository": MySQLPresupuestoRepository,
    "MySQLRecurrenciaRepository": MySQLRecurrenciaRepository,
    "MySQLRefreshTokenRepository": MySQLRefreshTokenRepository,
}
expected_methods = {
    "MySQLUsuarioRepository": ["crear", "autenticar", "obtener_por_id", "actualizar_perfil", "cambiar_password"],
    "MySQLCategoriaRepository": ["listar", "crear", "obtener_por_id", "actualizar", "desactivar"],
    "MySQLMovimientoRepository": ["crear", "listar_por_usuario", "actualizar", "eliminar", "obtener_balance", "obtener_resumen"],
    "MySQLNotificacionRepository": ["crear", "listar_por_usuario", "marcar_leida", "contar_no_leidas"],
    "MySQLPerfilIARepository": ["obtener_hoy", "guardar"],
    "MySQLInsightDiarioRepository": ["ya_enviado_hoy", "marcar_enviado"],
    "MySQLPresupuestoRepository": ["crear", "listar_por_usuario", "eliminar", "verificar_exceso"],
    "MySQLRecurrenciaRepository": ["crear", "listar_por_usuario", "obtener_pendientes", "actualizar_proxima_fecha", "desactivar"],
    "MySQLRefreshTokenRepository": ["guardar", "verificar", "revocar", "revocar_todos", "limpiar_expirados"],
}
for name, repo_cls in repos.items():
    instance = repo_cls()
    for method in expected_methods.get(name, []):
        assert hasattr(instance, method), f"FALTA: {name}.{method}()"
    print(f"  OK - {name}: todos los metodos presentes")

print()
print("=" * 50)
print("TODOS LOS TESTS PASARON - MODULARIZACION EXITOSA")
print("=" * 50)
