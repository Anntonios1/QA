"""
Smoke test HTTP de endpoints criticos, incluyendo PUT /api/movimientos/<id>
"""
import os, sys, json, time
from pathlib import Path
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"

def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req_obj = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req_obj, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def check(label, status, body, expected_status=200, key=None):
    ok = status == expected_status
    if key:
        ok = ok and (key in str(body))
    sign = "OK" if ok else "FAIL"
    print(f"  [{sign}] {label} -> HTTP {status}")
    if not ok:
        print(f"        Body: {body}")
    return ok

failures = []
def test(label, *args, **kwargs):
    result = check(label, *args, **kwargs)
    if not result:
        failures.append(label)
    return result

print("=" * 55)
print("SMOKE TEST DE ENDPOINTS - ControlCash API")
print("=" * 55)

# 1. Health check
print("\n[GRUPO 1] Health & Auth")
status, body = req("GET", "/api/health")
test("GET /api/health", status, body, 200)

# 2. Login con usuario demo
status, body = req("POST", "/api/auth/login", {
    "email": "demo_smoke@controlcash.com",
    "password": "Demo123!"
})
test("POST /api/auth/login", status, body, 200, "access_token")
token = body.get("data", {}).get("tokens", {}).get("access_token")
if not token:
    print("  FATAL: no se obtuvo token. Abortando tests HTTP.")
    sys.exit(1)
print(f"  Token obtenido (primeros 30 chars): {token[:30]}...")

# 3. Perfil
print("\n[GRUPO 2] Perfil de usuario")
status, body = req("GET", "/api/auth/perfil", token=token)
test("GET /api/auth/perfil", status, body, 200, "email")

# 4. Categorias
print("\n[GRUPO 3] Categorias")
status, body = req("GET", "/api/categorias", token=token)
test("GET /api/categorias", status, body, 200)
categorias = body.get("data", [])
cat_ingreso = next((c for c in categorias if c.get("tipo") == "ingreso"), None)
cat_gasto = next((c for c in categorias if c.get("tipo") == "gasto"), None)
print(f"  Categorias disponibles: {len(categorias)}")
if cat_ingreso:
    print(f"  Categoria ingreso: {cat_ingreso['nombre']} (id={cat_ingreso['id']})")
if cat_gasto:
    print(f"  Categoria gasto: {cat_gasto['nombre']} (id={cat_gasto['id']})")

# 5. Crear movimiento
print("\n[GRUPO 4] Movimientos - Crear")
cat_id = cat_ingreso["id"] if cat_ingreso else 1
status, body = req("POST", "/api/movimientos", {
    "categoria_id": cat_id,
    "tipo": "ingreso",
    "monto": 500.00,
    "descripcion": "Smoke test ingreso"
}, token=token)
test("POST /api/movimientos (ingreso)", status, body, 201)
mov_id = body.get("data", {}).get("id")
print(f"  Movimiento creado con ID: {mov_id}")

# 6. Listar movimientos
status, body = req("GET", "/api/movimientos", token=token)
test("GET /api/movimientos", status, body, 200)
movs = body.get("data", [])
print(f"  Total movimientos listados: {len(movs)}")

# 7. EDITAR movimiento — ESTE ES EL BUG CORREGIDO
print("\n[GRUPO 5] Movimientos - Editar (bug fix)")
if mov_id:
    nuevo_monto = 750.00
    status, body = req("PUT", f"/api/movimientos/{mov_id}", {
        "monto": nuevo_monto,
        "descripcion": "Editado por smoke test"
    }, token=token)
    test(f"PUT /api/movimientos/{mov_id} (editar monto)", status, body, 200)

    # Verificar que el cambio persiste
    time.sleep(0.3)
    status2, body2 = req("GET", "/api/movimientos", token=token)
    movs2 = body2.get("data", [])
    mov_editado = next((m for m in movs2 if m.get("id") == mov_id), None)
    if mov_editado:
        monto_guardado = float(mov_editado.get("monto", 0))
        if abs(monto_guardado - nuevo_monto) < 0.01:
            print(f"  [OK] MONTO PERSISTIO: {monto_guardado} (esperado {nuevo_monto})")
        else:
            print(f"  [FAIL] MONTO NO PERSISTIO: {monto_guardado} (esperado {nuevo_monto})")
            failures.append("Persistencia de edicion de monto")
        desc_guardada = mov_editado.get("descripcion", "")
        if "Editado por smoke test" in desc_guardada:
            print(f"  [OK] DESCRIPCION PERSISTIO: '{desc_guardada}'")
        else:
            print(f"  [FAIL] DESCRIPCION NO PERSISTIO: '{desc_guardada}'")
            failures.append("Persistencia de descripcion editada")
    else:
        print(f"  [FAIL] Movimiento {mov_id} no encontrado despues de editar")
        failures.append("Movimiento no encontrado post-edicion")

    # Editar categoria si hay gasto disponible
    if cat_gasto:
        status3, body3 = req("PUT", f"/api/movimientos/{mov_id}", {
            "categoria_id": cat_gasto["id"]
        }, token=token)
        test(f"PUT /api/movimientos/{mov_id} (cambiar categoria)", status3, body3, 200)

# 8. Balance
print("\n[GRUPO 6] Balance y Resumen")
status, body = req("GET", "/api/balance", token=token)
test("GET /api/balance", status, body, 200)

status, body = req("GET", "/api/resumen", token=token)
test("GET /api/resumen", status, body, 200)

# 9. Notificaciones
print("\n[GRUPO 7] Notificaciones")
status, body = req("GET", "/api/notificaciones", token=token)
test("GET /api/notificaciones", status, body, 200)

# 10. Eliminar el movimiento de prueba
print("\n[GRUPO 8] Eliminar movimiento de prueba")
if mov_id:
    status, body = req("DELETE", f"/api/movimientos/{mov_id}", token=token)
    test(f"DELETE /api/movimientos/{mov_id}", status, body, 200)

# Resumen final
print()
print("=" * 55)
if not failures:
    print("RESULTADO: TODOS LOS TESTS PASARON")
else:
    print(f"RESULTADO: {len(failures)} TESTS FALLARON:")
    for f in failures:
        print(f"  - {f}")
print("=" * 55)
sys.exit(0 if not failures else 1)
