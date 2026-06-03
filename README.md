<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para la Descripción General del Proyecto (README) -->
# ControlCash - Sistema Profesional de Control Financiero

Sistema de control financiero personal de 3 capas con IA integrada (NVIDIA NIM), OCR de recibos (Nemotron Parse), autenticacion JWT + biometrica (Capacitor), asistente de voz (Gemini Live), reportes exportables y UI glassmorphism.

## Estadisticas del Proyecto

| Metrica | Valor |
|---------|-------|
| Lineas de codigo totales | ~20,000 LOC |
| Endpoints REST | 48 |
| Features implementadas | 129 |
| Tablas en base de datos | 10 |
| Modulos frontend JS | 8 |
| Archivos Python (API) | 7 |
| Archivos Python (DB) | 18 |

### Desglose por Capa

| Capa | Archivos | LOC |
|------|----------|-----|
| **api/** | app.py (2,002), ocr.py (1,165), llm.py (1,056), validators.py (237), jwt_auth.py (251), push.py (163) | ~4,874 |
| **app/js/** | presupuestos.js (725), gemini_live.js (713), state.js (649), movimientos.js (536), ia.js (507), charts.js (469), auth.js (441) | ~4,056 |
| **app/** (core) | styles.css (4,452), index.html (2,306), app.js (354) | ~7,112 |
| **db/** | pg_repository.py (1,484), crypto.py (364), categoria.py (257), movimiento.py (421), schema.dbml (210), + 13 archivos | ~3,905 |

## Arquitectura de 3 Capas

```
├── db/          → Capa de Datos (PostgreSQL/MySQL + Repositories + AES-256-GCM)
├── api/         → Capa de Negocio (Flask REST API + JWT + OCR + LLM)
├── app/         → Capa de Presentacion (HTML/CSS/JS + Chart.js + PWA)
├── docs/        → Documentacion bajo normas internacionales
└── test/        → Pruebas unitarias e integracion
```

## Features Implementadas (129)

### Autenticacion y Seguridad (17)
- Registro con nombre, email, contrasena, moneda y presupuesto mensual
- Login con email + contrasena
- JWT Access Token (HS256, 15 min de expiracion)
- JWT Refresh Token (7 dias, hash SHA-256 en DB, revocacion en logout)
- Autenticacion biometrica via Capacitor (huella digital / Face ID)
- Password strength meter en tiempo real (weak/fair/good/strong)
- Toggle de visibilidad de contrasena (ojo icono)
- Session timeout por inactividad (15 min, ISO 27001)
- Cambio de contrasena (actual + nueva + confirmacion)
- Cifrado AES-256-GCM con PBKDF2 para datos sensibles
- Headers de seguridad (X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
- Rate limiting con Flask-Limiter (300/min default, limites por endpoint)
- Validacion de inputs (registro, login, movimientos, categorias)
- Endpoint de estado de seguridad
- Hashing de contrasenas con PBKDF2-SHA256 (100k iteraciones, salt por usuario)

### Perfil de Usuario (3)
- Ver perfil (nombre, email, moneda, fecha de registro)
- Editar perfil (nombre + moneda)
- UI de perfil (avatar con inicial, grid de datos, formulario de edicion)

### Dashboard Financiero (11)
- Balance display (total balance, ingresos, gastos, conteo de movimientos)
- Contador animado (balance number anima al cargar)
- Widget de presupuesto mensual en home (barra de progreso, gastado vs limite)
- Botones de modulos rapidos (Historial, Presupuesto, Reportes)
- Menu de navegacion por secciones (Inicio, Presupuestos, Reportes, Categorias, Historial, Perfil)
- Bottom navigation bar mobile (Inicio, Historial, Perfil, Ajustes)
- FAB con bottom sheet (acciones rapidas: Ingreso, Egreso, OCR, Chat, Categorias)
- Onboarding rapido (registrar gasto, crear categoria, definir presupuesto)
- Dark/Light mode toggle (persistido en localStorage)
- Efecto 3D tilt en tarjetas de estadisticas (hover con perspectiva)
- Atajos de teclado (Alt+G gasto, Alt+I ingreso, Alt+P presupuestos)

### Movimientos Financieros (9)
- Crear movimiento (ingreso/gasto con monto, categoria, descripcion, fecha)
- Listar movimientos (paginados, con skeleton loaders)
- Editar movimiento (modal con datos pre-rellenados)
- Eliminar movimiento (modal de confirmacion)
- Filtrar por tipo (tabs: Todos, Ingresos, Gastos)
- Filtros avanzados (rango de fechas, categoria, rango de monto)
- Paginacion (anterior/siguiente, info de pagina)
- Exportar CSV (con filtros activos aplicados)
- Vista expandible/colapsable ("Ver todos" / "Ver menos")

### Categorias (6)
- Crear categoria (nombre, tipo, emoji icono, descripcion)
- Listar categorias (catalogo admin con conteo de uso)
- Editar categoria (formulario pre-rellenado)
- Eliminar/Desactivar categoria
- Icon picker (16 emojis preset + texto libre)
- Deteccion de categorias duplicadas (nombre normalizado)

### Presupuestos (7)
- Crear/Actualizar presupuesto (global o por categoria, mensual)
- Listar presupuestos (barras de progreso, estados: OK/alerta 80%/excedido)
- Eliminar presupuesto
- Comparativo mes actual vs anterior (con variacion porcentual)
- Verificacion de presupuestos
- Alertas visuales (80% warning, 100% excedido)
- Auto-creacion de presupuesto inicial al registrarse

### Recurrencias / Automatizacion (6)
- Crear recurrencia (tipo, categoria, monto, frecuencia, proxima fecha, dia de ejecucion)
- Listar recurrencias (estado activo/pausado)
- Pausar recurrencia
- Reactivar recurrencia (con nueva fecha)
- Ejecutar recurrencias pendientes (batch crea movimientos para items vencidos)
- Frecuencias: diaria, semanal, quincenal, mensual, anual

### Resumen Financiero y Graficos (5)
- Resumen mensual (promedio diario, proyeccion 30 dias, variacion vs anterior, conteo)
- Top 3 gastos (mayores gastos individuales)
- Donut chart - gastos por categoria (Chart.js v4)
- Line chart - tendencia diaria 30 dias (ingresos vs gastos, Chart.js)
- Panel de resumen expandible (toggle "Ver"/"Ocultar")

### Reportes (4)
- Reportes por periodo (diario, semanal, mensual)
- Top categorias con tendencia (flechas variacion: sube/baja/estable)
- Exportar PDF (jsPDF + autoTable, iconos emoji via Twemoji)
- Exportar Excel (XLSX via SheetJS)

### Inteligencia Artificial - NVIDIA NIM (12)
- Perfil financiero IA (arquetipo, score 0-100, tags, narrativa, habitos, areas de mejora)
- Skeleton loader para perfil IA
- Refresh de perfil IA (forzar regeneracion, limpiar cache)
- Insight diario (mensaje motivador tipo Duolingo con datos reales)
- Toast de notificacion de insight (animado con accion "Ver perfil")
- Chat asistente IA (LLM con contexto financiero inyectado)
- Chat tool-calling (8 tools: balance, resumen 30d, resumen 7d, top categorias, estado presupuestos, movimientos recientes, comparativo periodos, proyeccion fin de mes)
- Renderizado de markdown en chat (con sanitizacion DOMPurify)
- Animacion de streaming en chat (efecto typewriter)
- Catalogo de tools del chat (endpoint)
- Deteccion de disponibilidad IA (verifica NVIDIA_API_KEY, muestra badge si no configurada)
- Perfil fallback deterministico (basado en reglas cuando LLM no disponible)

### Gemini Live - Voz en Tiempo Real (10)
- Chat de voz bidireccional por WebSocket con Gemini Live
- Captura de microfono (AudioWorkletNode con ScriptProcessor fallback)
- Cola de reproduccion de audio (PCM 24kHz, scheduling suave)
- Tool-calling de voz (4 tools: balance, resumen 30d, movimientos recientes, presupuestos)
- Mute/Unmute microfono
- Transcripcion en tiempo real (texto usuario + bot en panel)
- Animacion Nebula Sphere (estados visuales: listening/speaking)
- Visualizador de ondas de audio (10 barras animadas desde AnalyserNode)
- Indicador de pensamiento/razonamiento (muestra cuando Gemini esta procesando)
- Indicador de tool call (pulso visual al consultar datos)

### OCR - Escaneo de Recibos (9)
- OCR de recibos (upload de imagen, NVIDIA Nemotron Parse + normalizacion GPT)
- OCR multi-ronda (hasta 3 rondas con scoring de precision)
- Pipeline de tool calls OCR (extraccion numerica, extraccion de fechas, deteccion de comercio, refinamiento, scoring)
- Inferencia de tipo de movimiento (del lenguaje del recibo: "envio realizado" = gasto, "dinero recibido" = ingreso)
- Modal OCR UI (drag-and-drop, captura de camara, preview, resultados editables)
- Sugerencia de categoria OCR (matching por keywords de la descripcion)
- Confirmar y guardar OCR (validar + persistir en DB como movimiento)
- Integracion Nemotron Parse (parsing estructurado con tools: markdown_bbox, markdown_no_bbox, detection_only)
- Deteccion Page Elements CV (NVIDIA computer vision para zonas del documento)

### Notificaciones (8)
- Notificaciones in-app (lista, badge de no leidos, marcar como leido)
- Panel de notificaciones (dropdown con items no leidos)
- Polling de notificaciones (auto-refresh cada 60 segundos)
- Notificaciones nativas del navegador (Web Notifications API)
- Web Push VAPID (gestion de suscripciones, envio desde servidor)
- Notificacion de bienvenida (auto-creada al registrarse)
- Alertas de presupuesto (generadas cuando se exceden limites)
- Sistema de toast notifications (4 tipos: success, error, warning, info)

### Webhooks (1)
- Webhooks salientes (registrar URL, disparar eventos a servicios externos)

### Exportacion de Datos (3)
- Export CSV (movimientos filtrados desde Flask)
- Export PDF (reporte con jsPDF + autoTable, iconos emoji via Twemoji)
- Export Excel (XLSX via SheetJS)

### Multi-Moneda (4)
- Soporte COP/USD (con formato locale-aware)
- Seleccion de moneda al registrarse
- Cambio de moneda en perfil
- Etiquetas de moneda dinamicas (actualiza todos los placeholders de la UI)

### Base de Datos e Infraestructura (7)
- Multi-backend DB (PostgreSQL + MySQL/MariaDB con auto-seleccion)
- 10 tablas (usuarios, refresh_tokens, tipos_movimiento, categorias, movimientos, presupuestos, recurrencias, notificaciones, perfiles_ia, insights_diarios)
- PWA Service Worker (registrado en produccion, deshabilitado en localhost)
- Health check endpoint (uptime, conectividad DB, estado IA)
- Configuracion CORS (pattern-based origin matching para localhost/dev)
- Servido estatico del frontend (Flask sirve directorio app/)
- Job diario en background (generacion de insights + ejecucion de recurrencias)

### UX/UI (7)
- Diseno glassmorphism (paneles, botones, inputs con glass effect)
- Skeleton loaders (lista de movimientos, perfil IA)
- Ripple effect en botones
- IntersectionObserver con animaciones staggered
- Transicion auth-to-dashboard (fade animation)
- Orbes de luz ambientales (decorativos de fondo)
- Persistencia de seccion activa (localStorage)

## Normas Internacionales Aplicadas

| Norma | Aplicacion |
|-------|-----------|
| CMMI | Niveles de madurez del proceso de desarrollo |
| ISO 9001 | Sistema de gestion de calidad |
| IEEE 730 | Plan de aseguramiento de calidad del software |
| ISO 9001:2000 | Enfoque basado en procesos |
| ISO 9126 | Modelo de calidad del software |
| ISO 14598 | Evaluacion del producto software |
| ISO/IEC 25000 (SQuaRE) | Calidad del producto software |
| ISO/IEC 12207 | Procesos del ciclo de vida del software |
| ISO/IEC 15504 (SPICE) | Evaluacion y mejora de procesos |
| ISO/IEC 20000 | Gestion de servicios de TI |
| ISO/IEC 27001 | Seguridad de la informacion |
| OWASP Mobile Top 10 | Seguridad en aplicaciones moviles |

## Actores del Sistema

### Usuario
- **Quien es:** Persona que utiliza el sistema para registrar y consultar su informacion financiera.
- **Que hace:** Ingresa datos, registra movimientos, consulta balance, escanea recibos, interactua con IA.

### Sistema
- **Quien es:** Aplicacion que procesa, almacena y organiza la informacion financiera.
- **Que hace:** Recibe datos, valida, guarda, genera notificaciones/resumenes, procesa OCR, ejecuta IA.

## Seguridad
- JWT Access Token (HS256, 15 min) + Refresh Token (7 dias, SHA-256 hash en DB)
- Autenticacion biometrica via Capacitor (huella digital / Face ID)
- Session timeout por inactividad (15 min, ISO 27001)
- Cifrado AES-256-GCM con PBKDF2 para datos sensibles
- Hashing de contrasenas con PBKDF2-SHA256 (100k iteraciones, salt por usuario)
- Rate limiting con Flask-Limiter (300/min default)
- Headers de seguridad (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, CSP)
- Indicador de fortaleza de contrasena en tiempo real (OWASP)

## Requisitos
- Python 3.8+
- Flask + Flask-CORS + Flask-Limiter
- PostgreSQL (o MySQL/MariaDB como alternativa)
- pg8000 (driver PostgreSQL puro Python) o mysql-connector-python
- Navegador moderno (Chrome, Firefox, Edge)
- NVIDIA API Key (para OCR y features de IA)
- Node.js (para Capacitor mobile, opcional)

## Instalacion

```bash
# 1. Instalar dependencias de la API
cd api
pip install -r requirements.txt

# 2. Configurar base de datos
# Crear base de datos 'gastos_db' en PostgreSQL
# Copiar .env.example a .env y configurar credenciales

# 3. (Opcional) Configurar NVIDIA API Key para OCR e IA
# NVIDIA_API_KEY=tu_api_key_aqui en .env

# 4. Ejecutar la API (inicializa la BD automaticamente)
python app.py

# 5. Abrir la aplicacion en http://localhost:5000
```

## Endpoints REST (48)

### Auth
- `POST /api/auth/registro` - Registro de usuario
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/revoke` - Revocar refresh token
- `POST /api/auth/logout` - Logout
- `GET /api/auth/perfil` - Ver perfil
- `PUT /api/auth/perfil` - Editar perfil
- `PUT /api/auth/password` - Cambiar contrasena

### Movimientos
- `POST /api/movimientos` - Crear movimiento
- `GET /api/movimientos` - Listar (paginado + filtros)
- `PUT /api/movimientos/<id>` - Editar
- `DELETE /api/movimientos/<id>` - Eliminar
- `GET /api/movimientos/export/csv` - Exportar CSV

### Balance y Resumen
- `GET /api/balance` - Balance actual
- `GET /api/resumen` - Resumen financiero 30 dias
- `GET /api/reportes/resumen` - Reportes por periodo

### Categorias
- `GET /api/categorias` - Listar
- `POST /api/categorias` - Crear
- `PUT /api/categorias/<id>` - Editar
- `DELETE /api/categorias/<id>` - Eliminar

### Presupuestos
- `POST /api/presupuestos` - Crear/Actualizar
- `GET /api/presupuestos` - Listar
- `GET /api/presupuestos/comparativo` - Comparativo mensual
- `DELETE /api/presupuestos/<id>` - Eliminar
- `GET /api/presupuestos/verificar` - Verificar

### Recurrencias
- `POST /api/recurrencias` - Crear
- `GET /api/recurrencias` - Listar
- `DELETE /api/recurrencias/<id>` - Pausar
- `POST /api/recurrencias/<id>/reactivar` - Reactivar
- `POST /api/recurrencias/ejecutar` - Ejecutar pendientes

### IA (NVIDIA NIM)
- `POST /api/chat` - Chat financiero con IA
- `GET /api/chat/tools` - Catalogo de tools
- `GET /api/ai/perfil` - Perfil financiero IA
- `POST /api/ai/daily-insight` - Insight diario
- `GET /api/chat/live/config` - Config Gemini Live

### OCR
- `POST /api/ocr/recibo` - Escanear recibo

### Notificaciones y Push
- `GET /api/notificaciones` - Listar notificaciones
- `POST /api/notificaciones/read` - Marcar como leida
- `POST /api/push/subscribe` - Suscribir push
- `POST /api/webhooks` - Registrar webhook

### Seguridad y Salud
- `GET /api/security/status` - Estado de seguridad
- `GET /api/health` - Health check
