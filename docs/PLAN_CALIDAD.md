# Plan de Aseguramiento de Calidad del Software
## Sistema de Control de Gastos - ControlCash

---

## 1. CMMI (Capability Maturity Model Integration)

### Nivel de Madurez Aplicado: Nivel 2 - Gestionado → Nivel 3 - Definido

| Área de Proceso | Aplicación en el Proyecto |
|----------------|--------------------------|
| **Gestión de Requisitos (REQM)** | Los 7 requisitos funcionales están documentados y trazados en el código |
| **Planificación del Proyecto (PP)** | Estructura de 3 capas definida: DB, API, APP |
| **Gestión de Configuración (CM)** | Separación de archivos por capa, esquema versionable |
| **Aseguramiento de Calidad (PPQA)** | Validaciones en capa API, tests documentados |
| **Definición de Procesos (OPD)** | Patrones Repository y MVC aplicados |

---

## 2. ISO 9001 - Sistema de Gestión de Calidad

### Principios Aplicados

| Principio ISO 9001 | Implementación |
|---------------------|---------------|
| **Enfoque al cliente** | Interfaz intuitiva ControlCash, 7 funciones centradas en el usuario |
| **Enfoque basado en procesos** | Flujo claro: Registro → Login → Gestionar → Consultar → Notificar |
| **Mejora continua** | Arquitectura modular permite iteración independiente por capa |
| **Toma de decisiones basada en evidencia** | Resumen financiero con datos reales (F7) |
| **Trazabilidad** | Cada movimiento registra fecha, tipo, categoría y usuario |

### Evidencia en el Código
- **Archivo**: `db/init_db.py` → Trazabilidad con campos `fecha_registro` y `fecha_creacion`
- **Archivo**: `api/app.py` → Respuestas estandarizadas con `respuesta_exito()` y `respuesta_error()`

---

## 3. IEEE 730 - Plan de Aseguramiento de Calidad del Software

### 3.1 Propósito
Garantizar que el Sistema de Control de Gastos cumpla con los requisitos de calidad establecidos.

### 3.2 Documentos de Referencia
- Especificación de requisitos (7 funciones documentadas)
- Esquema de base de datos normalizado (3NF)
- Endpoints REST documentados

### 3.3 Gestión
| Elemento | Responsable |
|----------|------------|
| Diseño de BD | Capa DB (`db/`) |
| Lógica de negocio | Capa API (`api/`) |
| Interfaz de usuario | Capa APP (`app/`) |
| Validación de datos | `api/validators.py` |

### 3.4 Actividades de SQA
1. Revisión de requisitos vs implementación
2. Validación de datos de entrada (F5)
3. Pruebas de integración API-DB
4. Pruebas de interfaz de usuario
5. Revisión de seguridad (hashing de contraseñas)

---

## 4. ISO 9001:2000 - Enfoque Basado en Procesos

### Mapa de Procesos del Sistema

```
USUARIO                         SISTEMA
  │                                │
  ├─→ [F1] Registrarse ──────────→ Crear cuenta + Notificación bienvenida
  │                                │
  ├─→ [F2] Iniciar sesión ───────→ Autenticar + Crear sesión
  │                                │
  ├─→ [F3] Gestionar movimiento ─→ Validar (F5) + Guardar + Notificar (F6)
  │                                │
  ├─→ [F4] Solicitar balance ────→ Calcular ingresos - gastos
  │                                │
  └─→ [F7] Ver resumen ─────────→ Generar reporte por categoría
```

### Interacción entre Procesos
- F1 → F6: Al registrarse, se genera notificación de bienvenida
- F3 → F5: Antes de guardar, se validan los datos
- F3 → F6: Gastos grandes generan notificación de alerta
- F3 → F4: Cada movimiento afecta el balance
- F3 → F7: Cada movimiento se refleja en el resumen

---

## 5. ISO 9126 - Modelo de Calidad del Software

### Características de Calidad Implementadas

| Característica | Sub-característica | Implementación |
|---------------|-------------------|----------------|
| **Funcionalidad** | Adecuación | 7 funciones cubren todos los requisitos |
| | Exactitud | Validación de datos con reglas estrictas |
| | Seguridad | Hash PBKDF2 + salt para contraseñas |
| | Interoperabilidad | API REST estándar con JSON |
| **Fiabilidad** | Madurez | Manejo de errores en todas las capas |
| | Tolerancia a fallos | Validación antes de operaciones DB |
| | Recuperabilidad | PostgreSQL transacciones ACID para integridad |
| **Usabilidad** | Comprensibilidad | UI ControlCash intuitiva |
| | Aprendibilidad | Iconos y etiquetas claras |
| | Operabilidad | Responsive, accesible por teclado |
| **Eficiencia** | Comportamiento temporal | Índices en consultas frecuentes |
| | Utilización de recursos | PostgreSQL optimizado, CSS optimizado |
| **Mantenibilidad** | Analizabilidad | Código documentado y modular |
| | Cambiabilidad | 3 capas independientes |
| | Estabilidad | Foreign keys y constraints |
| **Portabilidad** | Adaptabilidad | Responsive design |
| | Facilidad de instalación | pip install + python |

---

## 6. ISO 14598 - Evaluación del Producto Software

### Proceso de Evaluación

#### 6.1 Establecer Requisitos de Evaluación
- El sistema debe procesar registro, login, movimientos, balance, notificaciones y resumen
- Tiempo de respuesta < 2 segundos por operación
- Interfaz responsiva en dispositivos móviles y desktop

#### 6.2 Especificar la Evaluación
| Métrica | Criterio de Aceptación | Método de Medición |
|---------|----------------------|-------------------|
| Completitud funcional | 7/7 funciones implementadas | Revisión de código |
| Validación de datos | 100% inputs validados | Test con datos inválidos |
| Seguridad de contraseñas | Hash + Salt aplicado | Inspección de BD |
| Responsividad UI | Compatible mobile/desktop | Test en navegadores |
| Integridad de datos | FK constraints activos | Test de eliminación |

#### 6.3 Diseñar la Evaluación
1. Pruebas funcionales por cada caso de uso
2. Pruebas de validación con datos límite
3. Pruebas de seguridad (inyección SQL, XSS)
4. Pruebas de rendimiento
5. Pruebas de usabilidad

---

## 7. ISO/IEC 25000 (SQuaRE) - Calidad del Producto Software

### División de Calidad del Producto (ISO 25010)

```
Calidad del Producto
├── Adecuación Funcional
│   ├── Completitud: 7 funciones implementadas
│   ├── Corrección: Validadores en api/validators.py
│   └── Pertinencia: Cada función resuelve necesidad del usuario
├── Eficiencia de Desempeño
│   ├── Tiempo: Consultas optimizadas con índices
│   └── Recursos: PostgreSQL como motor relacional
├── Compatibilidad
│   ├── Coexistencia: API independiente del frontend
│   └── Interoperabilidad: REST + JSON estándar
├── Usabilidad
│   ├── Reconocibilidad: ControlCash UI con iconos
│   ├── Aprendibilidad: Flujo simple de 3 pasos
│   └── Protección contra errores: Validación en frontend y backend
├── Fiabilidad
│   ├── Madurez: Try/catch en todas las operaciones
│   ├── Disponibilidad: Sin dependencias externas pesadas
│   └── Tolerancia a fallos: Mensajes de error informativos
├── Seguridad
│   ├── Confidencialidad: Contraseñas hasheadas (PBKDF2)
│   ├── Integridad: Foreign keys + constraints
│   ├── No repudio: Registro con timestamp
│   └── Autenticidad: Sesiones con secret_key
└── Mantenibilidad
    ├── Modularidad: 3 capas separadas (DB/API/APP)
    ├── Reusabilidad: Patrón Repository
    ├── Analizabilidad: Código documentado
    └── Modificabilidad: Componentes independientes
```

### División de Calidad en Uso (ISO 25022)
| Factor | Métrica |
|--------|---------|
| Efectividad | Tasa de tareas completadas |
| Eficiencia | Tiempo por operación |
| Satisfacción | Diseño ControlCash atractivo |
| Libertad de riesgo | Validación previene errores |
| Cobertura de contexto | Responsive para múltiples dispositivos |

---

## 8. ISO/IEC 12207 - Procesos del Ciclo de Vida del Software

### Procesos Implementados

| Proceso | Actividad | Evidencia |
|---------|-----------|-----------|
| **Adquisición** | Definición de necesidades | 7 funciones + 2 actores documentados |
| **Suministro** | Entrega del producto | Estructura de carpetas lista para deploy |
| **Desarrollo** | | |
| → Análisis de requisitos | Identificación de actores y funciones | README.md |
| → Diseño arquitectónico | Arquitectura de 3 capas | db/, api/, app/ |
| → Diseño detallado | Esquema BD, endpoints, UI | Archivos fuente |
| → Codificación | Implementación SOLID | Código Python + JS |
| → Integración | API conecta DB con APP | Endpoints REST |
| → Pruebas | Validación de datos | validators.py |
| **Operación** | Ejecución del sistema | Scripts de inicio |
| **Mantenimiento** | Modificabilidad | Capas independientes |

### Procesos de Soporte
- **Documentación**: README.md, comentarios en código, este documento
- **Gestión de configuración**: Estructura de archivos organizada
- **Aseguramiento de calidad**: Validaciones, constraints, hashing
- **Verificación**: Validadores de entrada
- **Validación**: Pruebas de integración

---

## 9. ISO/IEC 15504 (SPICE) - Evaluación y Mejora de Procesos

### Evaluación de Capacidad de Procesos

| Proceso | Nivel Actual | Evidencia |
|---------|-------------|-----------|
| **PA 1.1** Realización del proceso | Nivel 1 (Realizado) | Las 7 funciones están implementadas |
| **PA 2.1** Gestión del rendimiento | Nivel 2 (Gestionado) | Índices DB, respuestas estandarizadas |
| **PA 2.2** Gestión del producto de trabajo | Nivel 2 (Gestionado) | Separación de capas clara |
| **PA 3.1** Definición del proceso | Nivel 2 (Gestionado) | Patrones Repository, validadores |
| **PA 3.2** Despliegue del proceso | Nivel 1 (Realizado) | Scripts de instalación |

### Atributos de Proceso Evaluados
- **Realización**: ✅ Todas las funciones operativas
- **Gestión**: ✅ Estructura organizada con normas
- **Definición**: ✅ Procesos documentados

---

## 11. EXPANSIÓN DEL SISTEMA - Fases Implementadas

### F1: Abstracción de Base de Datos (ISO/IEC 25000 - Portabilidad)
| Componente | Archivo | Norma |
|-----------|---------|-------|
| Configuración | `db/config.py` | ISO/IEC 12207 - Gestión de configuración |
| Interfaces abstractas (ABC) | `db/base_repository.py` | CMMI Nivel 3 - Definición de procesos |
| Implementación PostgreSQL | `db/pg_repository.py` | ISO 9126 - Fiabilidad |
| Implementación PostgreSQL | `db/pg_repository.py` | ISO/IEC 25000 - Portabilidad |
| Selector de engine | `db/__init__.py` | ISO/IEC 12207 - Modularidad |

### F2: Progressive Web App (ISO/IEC 25000 - Disponibilidad)
| Componente | Archivo | Norma |
|-----------|---------|-------|
| Manifest | `app/manifest.json` | ISO/IEC 20000 - Gestión de servicios |
| Service Worker | `app/service-worker.js` | ISO/IEC 25000 - Fiabilidad, Disponibilidad |
| Íconos | `app/icons/` | ISO 9126 - Usabilidad |

### F3: Web Push + Webhooks (ISO/IEC 20000 - Comunicación)
| Componente | Archivo | Norma |
|-----------|---------|-------|
| Push + Webhooks | `api/push.py` | ISO/IEC 20000 - Gestión de comunicación |
| Endpoints Push/Webhooks | `api/app.py` | ISO/IEC 12207 |

### F4: OCR de Recibos - NVIDIA NIM (ISO/IEC 25000 - Completitud)
| Componente | Archivo | Norma |
|-----------|---------|-------|
| Módulo OCR | `api/ocr.py` | ISO/IEC 25000 - Funcionalidad |
| Modelo: nemotron-page-elements-v3 | NVIDIA NIM API | CMMI - Integración externa |

### F5: Asistente Financiero LLM (ISO/IEC 25000 - Usabilidad)
| Componente | Archivo | Norma |
|-----------|---------|-------|
| Módulo LLM | `api/llm.py` | ISO/IEC 25000 - Funcionalidad |
| Modelo: openai/gpt-oss-120b | NVIDIA NIM API | CMMI - Integración externa |
| Chat UI | `app/app.js` + `app/index.html` | ISO 9126 - Usabilidad |

### F6: Resumen Mejorado (ISO 14598 - Evaluación)
| Métrica | Descripción | Norma |
|---------|-------------|-------|
| % por categoría | Proporción de gasto/ingreso por categoría | ISO 14598 |
| Promedio diario | Gasto promedio por día | ISO/IEC 25000 |
| Proyección 30d | Estimación de gasto mensual | ISO 14598 |
| Variación vs anterior | Comparación con periodo previo | ISO 9001 - Mejora continua |
| Top 3 gastos | Mayores gastos individuales | ISO 14598 |

### F7: Empaquetado Capacitor APK (ISO/IEC 12207 - Distribución)
| Componente | Archivo | Norma |
|-----------|---------|-------|
| Config Capacitor | `capacitor.config.json` | ISO/IEC 12207 |
| Package NPM | `package.json` | ISO/IEC 12207 |
| Guía compilación | `docs/GUIA_APK.md` | ISO 9001 - Documentación |
- **Medición**: ⚠️ Pendiente métricas en producción
- **Optimización**: ⚠️ Pendiente retroalimentación de usuarios

---

## 10. ISO/IEC 20000 - Gestión de Servicios de TI

### Procesos de Gestión Implementados

| Proceso ISO 20000 | Implementación |
|-------------------|----------------|
| **Gestión de incidentes** | Manejo de errores con respuestas HTTP estandarizadas |
| **Gestión de problemas** | Validación preventiva en `validators.py` |
| **Gestión de la configuración** | Estructura modular de 3 capas |
| **Gestión de cambios** | Capas independientes permiten cambios aislados |
| **Gestión de la disponibilidad** | PostgreSQL como motor relacional robusto |
| **Gestión de la capacidad** | Límites de consulta (200 max), paginación |
| **Gestión de la continuidad** | PostgreSQL transacciones ACID, foreign keys |
| **Gestión de la seguridad** | PBKDF2 hash, sesiones, CORS configurado |
| **Gestión de relaciones** | API REST desacoplada del frontend |

### Catálogo de Servicios

| Servicio | Endpoint | Método | Descripción |
|----------|----------|--------|-------------|
| Registro | `/api/auth/registro` | POST | Crear cuenta de usuario |
| Login | `/api/auth/login` | POST | Iniciar sesión |
| Logout | `/api/auth/logout` | POST | Cerrar sesión |
| Crear movimiento | `/api/movimientos` | POST | Registrar ingreso/gasto |
| Listar movimientos | `/api/movimientos` | GET | Consultar historial |
| Eliminar movimiento | `/api/movimientos/:id` | DELETE | Eliminar registro |
| Balance | `/api/balance` | GET | Consultar balance |
| Notificaciones | `/api/notificaciones` | GET | Listar avisos |
| Marcar leída | `/api/notificaciones/:id` | PUT | Marcar notificación |
| Resumen | `/api/resumen` | GET | Reporte financiero |
| Categorías | `/api/categorias` | GET | Catálogo de categorías |
| Health check | `/api/health` | GET | Estado del servicio |

---

## Matriz de Trazabilidad: Funciones ↔ Normas ↔ Código

| Función | Norma Principal | Archivo DB | Archivo API | Archivo APP |
|---------|----------------|------------|-------------|-------------|
| F1: Registrarse | IEEE 730, ISO 9001 | `repository.py` (UsuarioRepository.crear) | `app.py` (registro) | `app.js` (register-form) |
| F2: Iniciar sesión | ISO 9126 Seguridad | `repository.py` (UsuarioRepository.autenticar) | `app.py` (login) | `app.js` (login-form) |
| F3: Gestionar movimiento | ISO 9001 Trazabilidad | `repository.py` (MovimientoRepository) | `app.py` (crear/listar/eliminar) | `app.js` (modal + lista) |
| F4: Solicitar balance | ISO/IEC 25000 | `repository.py` (obtener_balance) | `app.py` (obtener_balance) | `app.js` (cargarBalance) |
| F5: Validar datos | ISO 9126 Exactitud | `init_db.py` (CHECK constraints) | `validators.py` | `app.js` (frontend val.) |
| F6: Notificación | ISO/IEC 20000 | `repository.py` (NotificacionRepository) | `app.py` (endpoints notif.) | `app.js` (toast + panel) |
| F7: Resumen | ISO 14598 | `repository.py` (obtener_resumen) | `app.py` (obtener_resumen) | `app.js` (cargarResumen) |

---

*Documento generado conforme a las normas internacionales de calidad del software.*
*Versión 1.0 - Marzo 2026*
