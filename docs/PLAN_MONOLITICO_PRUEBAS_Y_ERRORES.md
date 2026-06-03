<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para el Plan Monolítico de Pruebas y Errores -->
# Plan Monolitico de Pruebas y Errores - ControlCash

## Objetivo
Cerrar el desarrollo de la app con un unico plan ejecutable end-to-end, orientado a detectar errores reales, corregirlos y liberar con criterios de calidad verificables.

## Restriccion Operativa
- No crear entorno virtual nuevo.
- Ejecutar con herramientas ya instaladas en el equipo.

## Estado Actual Detectado
- No existe suite de pruebas automatizadas en el repo.
- El flujo JWT del backend no esta integrado en el frontend.
- El healthcheck de API valida solo PostgreSQL aunque hay soporte MySQL.
- El script inject_db_xampp.bat tiene un flujo de etiquetas que puede terminar mal el proceso.
- El arbol Git esta en estado sucio con multiples cambios pendientes.

## Fase 0 - Congelar baseline
### Objetivo
Asegurar trazabilidad de todo cambio a partir del estado actual.

### Acciones
1. Guardar snapshot de estado Git (status + diff resumido).
2. Definir una rama de estabilizacion QA.
3. No mezclar nuevas features durante este plan.

### Evidencia requerida
- Archivo de bitacora con fecha, hash y lista de archivos cambiados.

## Fase 1 - Corregir bloqueo de autenticacion (P0)
### Problema
Backend por defecto en modo JWT, frontend no envia Authorization Bearer.

### Acciones
1. Implementar almacenamiento seguro de access_token y refresh_token en frontend.
2. Enriquecer apiRequest para adjuntar Authorization cuando haya token.
3. Implementar refresh automatico al recibir 401 por expiracion.
4. En logout, revocar refresh token y limpiar estado local.
5. Mantener modo session como fallback controlado por variable.

### Pruebas de error (deben fallar antes y pasar despues)
1. Login exitoso y llamada inmediata a /api/balance.
- Antes: 401 por no_auth en modo JWT.
- Despues: 200 con balance.
2. Token expirado y refresh.
- Antes: sesion rota sin recuperacion.
- Despues: refresh transparente y reintento exitoso.
3. Logout.
- Antes: refresh token sigue utilizable.
- Despues: token revocado y refresh falla con 401.

### Criterio de salida
- 100% de endpoints protegidos accesibles tras login JWT desde frontend.

## Fase 2 - Corregir healthcheck por backend (P1)
### Problema
/api/health marca BD desconectada si se usa MySQL porque solo prueba pg8000.

### Acciones
1. Leer DB_BACKEND en healthcheck.
2. Si backend es postgresql, probar pg8000.
3. Si backend es mysql, probar pymysql.
4. Reportar backend, estado y latencia basica en respuesta health.

### Pruebas de error
1. DB_BACKEND=mysql con MySQL arriba.
- Antes: base_datos desconectada.
- Despues: base_datos conectada.
2. DB_BACKEND=postgresql con PostgreSQL arriba.
- Debe seguir en conectada.

### Criterio de salida
- /api/health refleja correctamente el backend activo.

## Fase 3 - Corregir script inject_db_xampp.bat (P1)
### Problema
Tras import exitosa, el flujo cae al label :test_connection por falta de salto explicito.

### Acciones
1. Agregar salto a :end justo despues de exito de importacion.
2. Mantener :test_connection solo para llamadas con call.
3. Unificar salida por EXIT_CODE y respetar --no-pause.

### Pruebas de error
1. Importacion exitosa.
- Antes: ejecucion adicional no intencional de :test_connection.
- Despues: finalizacion limpia con EXIT_CODE=0.
2. MySQL caido.
- Debe finalizar con EXIT_CODE=1 y mensaje claro.

### Criterio de salida
- Script deterministico en rutas de exito y fallo.

## Fase 4 - Crear base de pruebas automatizadas minima (P0)
### Objetivo
Eliminar regresion silenciosa.

### Alcance minimo obligatorio
1. Tests unitarios de validators.py.
2. Tests de integracion de auth (login, refresh, revoke, logout).
3. Tests de endpoints criticos: movimientos CRUD, balance, resumen, health.
4. Tests de recurrencias mensuales (dias 29, 30, 31).
5. Test de filtros invalidos (categoria_id, monto_min, monto_max).

### Pruebas de error clave
1. Inputs invalidos deben retornar 4xx, nunca 500.
2. Reuso de refresh token debe fallar por revocacion one-time use.
3. Monto minimo mayor que maximo debe retornar 400.

### Criterio de salida
- Suite ejecutable con resultado verde y reporte almacenado.

## Fase 5 - Seguridad y configuracion (P1)
### Objetivo
Reducir riesgo operativo antes de liberar.

### Acciones
1. Verificar que secretos no esten en archivos versionados.
2. Confirmar .env ignorado y uso de .env.example como plantilla.
3. Revisar mensajes de error para no filtrar trazas internas.
4. Documentar politica de JWT_SECRET_KEY para produccion.

### Pruebas de error
1. ENVIRONMENT=production sin JWT_SECRET_KEY.
- Debe fallar al arranque con mensaje claro.
2. Token manipulado.
- Debe responder 401 sin stacktrace.

### Criterio de salida
- Checklist de seguridad completado al 100%.

## Fase 6 - Pruebas E2E funcionales (P0)
### Flujo unico de aceptacion
1. Registro.
2. Login.
3. Crear ingreso y gasto.
4. Editar y eliminar movimiento.
5. Consultar balance y resumen.
6. Probar OCR con archivo valido e invalido.
7. Probar chat IA sin API key y con API key.
8. Logout y validacion de token revocado.

### Criterio de salida
- Flujo completo pasa sin errores bloqueantes.

## Fase 7 - Gate de liberacion
### Condiciones duras de salida
1. Sin fallos P0/P1 abiertos.
2. Tests automatizados en verde.
3. Healthcheck correcto para backend activo.
4. Script de inicializacion DB validado.
5. Evidencia de pruebas archivada.

### Entregables finales
1. Reporte de pruebas con casos, resultado y timestamp.
2. Lista de bugs corregidos y riesgos residuales.
3. Version candidata con changelog.

## Priorizacion sugerida
1. Fase 1 (JWT-frontend)
2. Fase 4 (suite minima)
3. Fase 2 (healthcheck)
4. Fase 3 (script bat)
5. Fases 5, 6, 7

## Tiempo estimado
- Fase 1: 0.5-1 dia
- Fase 2: 0.5 dia
- Fase 3: 0.25 dia
- Fase 4: 1-2 dias
- Fase 5: 0.5 dia
- Fase 6: 0.5-1 dia
- Fase 7: 0.25 dia
- Total: 3.5 a 5.5 dias
