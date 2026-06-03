<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para el Reporte de Bugs Corregidos -->
# Reporte de Bugs Corregidos - ControlCash API

**Fecha:** 2026-03-22
**Modelo:** Claude Opus 4.6
**Proyecto:** Quality System - Sistema de Control de Gastos

---

## Resumen Ejecutivo

Se identificaron **7 bugs críticos y 2 problemas de seguridad** en el código. **Todos han sido corregidos**.

| Estado | Cantidad |
|--------|----------|
| ✅ Corregidos | 9 |
| ⏳ Pendientes | 0 |

---

## Bugs Corregidos

### 1. ✅ Connection Leak - Cierre de Conexiones (P0 - Crítico)

**Archivo:** `db/pg_repository.py`

**Problema:**
Múltiples métodos abrían conexiones a PostgreSQL pero si ocurría una excepción antes del bloque `finally`, la conexión no se cerraba correctamente, causando agotamiento del pool de conexiones.

**Ubicaciones afectadas:**
- `PGRefreshTokenRepository.guardar()` - línea 1035-1050
- `PGPerfilIARepository.guardar()` - línea 672-705
- `PGInsightDiarioRepository.marcar_enviado()` - línea 732-747

**Solución aplicada:**
```python
# Antes (problemático)
conn = _get_conn()
try:
    # operaciones...
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()  # Error si _get_conn() falló

# Después (corregido)
conn = None
try:
    conn = _get_conn()
    # operaciones...
except Exception:
    if conn:
        conn.rollback()
    raise
finally:
    if conn:
        conn.close()
```

**Impacto:** Previene agotamiento de conexiones bajo carga.

---

### 2. ✅ Método actualizar() Faltante en MySQL (P0 - Crítico)

**Archivo:** `db/mysql_repository.py`

**Problema:**
`MySQLMovimientoRepository` no implementaba el método `actualizar()` pero `app.py` lo llamaba, causando `AttributeError` al editar movimientos.

**Error que ocurría:**
```
AttributeError: 'MySQLMovimientoRepository' object has no attribute 'actualizar'
```

**Solución aplicada:**
Se implementó el método `actualizar()` en `MySQLMovimientoRepository` con la misma firma que `PGMovimientoRepository`, permitiendo actualización parcial de campos (solo los que no son None).

**Impacto:** Funcionalidad de edición de movimientos ahora funciona en MySQL/MariaDB.

---

### 3. ✅ Race Condition en Refresh Token (P1 - Alta)

**Archivo:** `api/app.py` - Endpoint `/api/auth/refresh`

**Problema:**
El endpoint renovaba el access token pero no revocaba el refresh token usado. Esto permitía que un token comprometido pudiera usarse indefinidamente hasta su expiración.

**Flujo vulnerable:**
1. Usuario envía refresh token válido
2. Sistema genera nuevo access token
3. El mismo refresh token puede reutilizarse múltiples veces

**Solución aplicada:**
- El refresh token ahora se revoca después de usarse (one-time use)
- Se genera un nuevo refresh token con cada renovación (rotación de tokens)
- Se guarda el nuevo token en la base de datos

**Código agregado:**
```python
# Revocar el refresh token usado (one-time use)
RefreshTokenRepository.revocar(token_hash)

# Generar nuevo refresh token (rotación)
new_refresh_token, new_token_hash, new_expires_at = generate_refresh_token(usuario_id)
RefreshTokenRepository.guardar(usuario_id, new_token_hash, new_expires_at, device_info)
```

**Impacto:** Previene ataques de replay si el token es comprometido.

---

### 4. ✅ Bug en Cálculo de Fechas Mensuales (P1 - Alta)

**Archivo:** `api/app.py` - Función `ejecutar_recurrencias_pendientes`

**Problema:**
El código limitaba el día de ejecución a 28 para evitar fechas inválidas (ej: 31 de febrero), pero esto causaba que recurrencias programadas para días 29, 30, 31 **nunca se ejecutaran en esos días** - siempre se movían al día 28.

**Código problemático:**
```python
dia = min(rec['dia_ejecucion'] or fecha_actual.day, 28)  # Siempre limitaba a 28
```

**Solución aplicada:**
```python
import calendar
ultimo_dia_mes = calendar.monthrange(anio, mes)[1]
dia_deseado = rec['dia_ejecucion'] or fecha_actual.day
dia = min(dia_deseado, ultimo_dia_mes)  # Usa el último día válido del mes destino
```

**Ejemplos:**
- Recurrencia día 31 en enero → ejecuta el 31 de enero ✅
- Recurrencia día 31 en febrero → ejecuta el 28 de febrero (último día válido) ✅
- Recurrencia día 30 en febrero → ejecuta el 28 de febrero ✅

**Impacto:** Recurrencias mensuales ahora funcionan correctamente para todos los días.

---

### 5. ✅ Memory Leak en Suscripciones Push (P2 - Media)

**Archivo:** `api/push.py`

**Problema:**
Las suscripciones se almacenaban en memoria sin límite ni expiración, causando potencial agotamiento de memoria con muchos usuarios.

**Solución aplicada:**
- Límite de 5 dispositivos por usuario (`MAX_SUBSCRIPTIONS_PER_USER`)
- Expiración automática de suscripciones antiguas (`SUBSCRIPTION_TTL_DAYS = 90`)
- Timestamps `created_at` y `last_used` en cada suscripción
- Función `limpiar_suscripciones_expiradas()` para mantenimiento periódico
- Función `obtener_estadisticas_suscripciones()` para monitoreo

**Código agregado:**
```python
MAX_SUBSCRIPTIONS_PER_USER = 5
SUBSCRIPTION_TTL_DAYS = 90

def guardar_suscripcion(usuario_id: int, subscription_info: dict):
    # Elimina duplicados, limita a MAX_SUBSCRIPTIONS_PER_USER
    # Agrega timestamps de creación y último uso
    ...

def limpiar_suscripciones_expiradas():
    # Elimina suscripciones con más de TTL días sin usarse
    ...
```

**Impacto:** Previene crecimiento ilimitado de memoria en producción.

---

### 6. ✅ Zonas Horarias JWT vs PostgreSQL (P2 - Media)

**Archivos:** `db/pg_repository.py` y `db/mysql_repository.py`

**Problema:**
Los JWT generan timestamps UTC pero las bases de datos usaban `NOW()` que depende de la zona horaria del servidor, causando discrepancias en la expiración de tokens.

**Solución aplicada:**

**PostgreSQL:**
```sql
-- Antes
WHERE expires_at > NOW()

-- Después
WHERE expires_at > (NOW() AT TIME ZONE 'UTC')
```

**MySQL/MariaDB:**
```sql
-- Antes
WHERE expires_at > NOW()

-- Después
WHERE expires_at > UTC_TIMESTAMP()
```

**Impacto:** Los tokens ahora expiran consistentemente independientemente de la zona horaria del servidor.

---

### 7. ✅ JWT Secret Hardcodeado (P2 - Media)

**Archivo:** `api/jwt_auth.py`

**Problema:**
El secret JWT tenía un valor por defecto hardcodeado que podía usarse en producción si la variable de entorno no estaba configurada.

```python
# Problemático
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'ControlCash_JWT_Secret_CHANGE_IN_PRODUCTION_2026')
```

**Solución aplicada:**
```python
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development').lower()
IS_PRODUCTION = ENVIRONMENT in ('production', 'prod', 'staging')

# En producción: ERROR si no está configurado
if IS_PRODUCTION:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY no está configurada...")
    if JWT_SECRET_KEY == _DEFAULT_JWT_SECRET:
        raise RuntimeError("JWT_SECRET_KEY está usando el valor por defecto inseguro...")

# En desarrollo: warning si no está configurado
else:
    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = _DEFAULT_JWT_SECRET
        print("[WARN] JWT_SECRET_KEY no configurada. Usando valor de desarrollo.")
```

**Impacto:** Previene uso accidental de secret inseguro en producción.

---

## Bugs Pendientes (P3 - Baja Prioridad)

### 8. ✅ Validación Insuficiente en Carga de Imagen OCR

**Archivo:** `api/app.py:691-727`

**Problema:**
No había validación de tipo MIME real, resolución máxima ni formatos permitidos.

**Solución aplicada:**
- Decodificar base64 y validar tamaño real (máx 10 MB)
- Validar magic bytes para detectar formato real
- Solo permitir JPEG, PNG y WebP
- Rechazar formatos no soportados con mensaje claro

```python
# Magic bytes validados
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'RIFF': 'image/webp',
}

# Validación antes de procesar
imagen_bytes = base64.b64decode(imagen_b64)
formato_detectado = detectar_formato(imagen_bytes)
if not formato_detectado:
    return respuesta_error("Formato no soportado. Use JPEG, PNG o WebP.", codigo=400)
```

**Impacto:** Previene DoS con archivos maliciosos y mejora seguridad.

---

### 9. ✅ Filtros en Memoria sin Validación Estricta

**Archivo:** `api/app.py:481-530`

**Problema:**
Los filtros `categoria_id`, `monto_min`, `monto_max` se aplicaban sin validación de tipos, causando errores potenciales.

**Solución aplicada:**
- Validación estricta de tipos con try/except
- Mensajes de error descriptivos
- Validación de coherencia (monto_min <= monto_max)
- Conversión a tipos nativos antes de filtrar

```python
# Validar categoria_id
if cat_id_param:
    try:
        categoria_id = int(cat_id_param)
    except (ValueError, TypeError):
        return respuesta_error("'categoria_id' debe ser un número entero.", codigo=400)

# Validar coherencia
if monto_min is not None and monto_max is not None and monto_min > monto_max:
    return respuesta_error("'monto_min' no puede ser mayor que 'monto_max'.", codigo=400)
```

**Impacto:** Previene errores y mejora UX con mensajes claros.

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `db/pg_repository.py` | Connection leaks + timezone UTC |
| `db/mysql_repository.py` | Método `actualizar()` + timezone UTC |
| `api/app.py` | Refresh token rotation + bug fechas + validación OCR + validación filtros |
| `api/push.py` | Límites y expiración de suscripciones |
| `api/jwt_auth.py` | Validación de JWT_SECRET en producción |

---

## Resumen de Correcciones por Prioridad

| Prioridad | Bug | Estado |
|-----------|-----|--------|
| P0 | Connection leaks en PostgreSQL | ✅ Corregido |
| P0 | Método actualizar() faltante en MySQL | ✅ Corregido |
| P1 | Race condition en refresh token | ✅ Corregido |
| P1 | Bug fechas recurrencia mensual | ✅ Corregido |
| P2 | Memory leak en push subscriptions | ✅ Corregido |
| P2 | Zonas horarias JWT vs DB | ✅ Corregido |
| P2 | JWT secret hardcodeado | ✅ Corregido |
| P3 | Validación insuficiente OCR | ✅ Corregido |
| P3 | Filtros memoria sin validación | ✅ Corregido |

---

## Pruebas Recomendadas

```bash
# 1. Verificar conexión a PostgreSQL bajo carga
ab -n 1000 -c 10 http://localhost:5000/api/balance

# 2. Probar edición de movimientos en MySQL
curl -X PUT http://localhost:5000/api/movimientos/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"monto": 150.00}'

# 3. Verificar rotación de refresh tokens
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<token>"}'
# El token usado ya no debería funcionar en una segunda llamada

# 4. Probar recurrencias mensuales día 31
# Crear recurrencia día 31 y verificar que en febrero se ejecuta el 28

# 5. Verificar validación de JWT_SECRET en producción
ENVIRONMENT=production python -c "from api.jwt_auth import JWT_SECRET_KEY"
# Debería lanzar RuntimeError si no está configurado

# 6. Verificar limpieza de suscripciones expiradas
python -c "from api.push import limpiar_suscripciones_expiradas; print(limpiar_suscripciones_expiradas())"
```

---

## Configuración Requerida para Producción

Después de estas correcciones, asegúrate de configurar:

```env
# .env (PRODUCCIÓN)
ENVIRONMENT=production

# JWT - OBLIGATORIO
JWT_SECRET_KEY=<generar-con: python -c "import secrets; print(secrets.token_hex(32))">

# Base de datos
DB_BACKEND=postgresql  # o mysql
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=controlcash
PG_USER=app_user
PG_PASSWORD=<password-seguro>

# Opcional: Web Push
VAPID_PUBLIC_KEY=<clave-publica>
VAPID_PRIVATE_KEY=<clave-privada>
VAPID_CONTACT=mailto:admin@tudominio.com
```

---

**Generado por Claude Code**
*Análisis de código estático y corrección de bugs*
