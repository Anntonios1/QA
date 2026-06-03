<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para la Tabla Final de Evidencia por Norma -->
# TABLA FINAL: EVIDENCIA CONCRETA POR NORMA (Archivo:Línea + Implementación + GAPS)

## 1️⃣ CMMI (Niveles de Madurez)

| Evidencia | Archivo:Línea | Implementación Concreta | GAPS |
|-----------|---|---|---|
| Mención Nivel 3 | db/config.py:6-8 | "CMMI Nivel 3: Definición de procesos estándar" | ❌ Falta evaluación formal de nivel (SCAMPI assessment) |
| Mención en DB | db/__init__.py:5 | "Normas: ISO/IEC 12207, CMMI Nivel 3, ISO/IEC 25000" | ❌ No hay matriz CMMI-requisitos mapeada |
| Procesos estándar | db/base_repository.py:1-50 | Patrón Repository (ABC) + interfaces consistentes | ❌ Falta documentación de estándares de proceso |
| REQM (Gestión Requisitos) | docs/LEVANTAMIENTO_REQUERIMIENTOS.md:36-170 | 7 RF documentados con trazabilidad hacia código | ⚠️ Falta herramienta de trazabilidad (Jira/Azure DevOps) |
| PPQA (Aseguramiento) | api/validators.py:1-100 | Validadores en cada endpoint (RFC-05) | ❌ Falta auditoría de conformidad con estándares |
| Integración externa | api/llm.py, api/ocr.py:3-5 | NVIDIA NIM integrado (Nivel 3 de madurez) | ❌ Sin SLA, sin circuit breaker, sin fallback |

**Score: 7/10** | **Implementación: Buena** | **Automatización: Manual**

---

## 2️⃣ ISO 9001 (Sistema de Gestión de Calidad)

| Evidencia | Archivo:Línea | Implementación Concreta | GAPS |
|-----------|---|---|---|
| Enfoque procesos | docs/PLAN_CALIDAD.md:27 | "Flujo: Registro → Login → Gestionar → Consultar → Notificar" | ❌ Falta diagrama BPMN formal |
| Estandarización respuestas | api/app.py:120-125 | 
espuesta_exito() y 
espuesta_error() con formato JSON estándar | ❌ Falta multilengua y formatos alternativos |
| Trazabilidad datos | db/pg_repository.py:44,66 | echa_creacion TIMESTAMP DEFAULT NOW() en usuarios y movimientos | ❌ Falta auditoría centralizada (quién, qué, cuándo) |
| Gestión cambios | db/config.py:22-26 | .env.example con variables centralizadas | ❌ Falta CHANGELOG.md con versionado semántico |
| Mejora continua | docs/PLAN_CALIDAD.md:28-29 | "Arquitectura modular permite iteración independiente" | ❌ Sin métricas de mejora ni ciclos planificados |
| Documentación | docs/PLAN_CALIDAD.md + README.md | PLAN completo + requisitos + matriz de trazabilidad | ❌ Falta manual de usuario final |

**Score: 7.5/10** | **Implementación: Buena** | **Documentación: Excelente**

---

## 3️⃣ IEEE 730 (Aseguramiento de Calidad)

| Evidencia | Archivo:Línea | Implementación Concreta | GAPS |
|-----------|---|---|---|
| Plan SQA | docs/PLAN_CALIDAD.md:38-62 | Sección 3 define propósito, documentos, gestión y actividades | ✅ Completo |
| Trazabilidad registro | api/app.py:139 | Comentario "IEEE 730 - Trazabilidad del proceso de registro" en F1 | ✅ Documentado |
| Validación F5 | api/validators.py:33-100 | alidar_registro() + alidar_login() + alidar_movimiento() | ✅ Implementado |
| Seguridad contraseñas | db/base_repository.py:32-38 | hash_password() con PBKDF2-SHA256 + salt (100k iteraciones) | ✅ Implementado |
| Actividades SQA | docs/PLAN_CALIDAD.md:56-61 | 5 actividades: revisión requisitos, validación, integración, interfaz, seguridad | ⚠️ Sin cronograma |
| Responsables | docs/PLAN_CALIDAD.md:48-54 | Tabla asigna responsables por capa | ⚠️ Falta definición de roles RACI |
| Testing | api/validators.py | Validadores de entrada presentes | ❌ Sin test suite pytest automatizado |

**Score: 8/10** | **Implementación: Muy Buena** | **Gaps: Testing y Cronograma**

---

## 4️⃣ ISO 9126 (Características de Calidad - 6)

### ✅ Funcionalidad (Adecuación, Exactitud, Seguridad, Interoperabilidad)

| Sub-característica | Archivo:Línea | Evidencia | GAPS |
|---|---|---|---|
| Adecuación | docs/PLAN_CALIDAD.md:98 | "13 funciones cubren todos los requisitos" | Falta matriz cobertura |
| Exactitud | api/validators.py:19-62 | MIN_NOMBRE_LENGTH=2, MAX_EMAIL=254, MIN_MONTO=0.01 | Falta test de exactitud |
| Seguridad | db/base_repository.py:32-38 | PBKDF2-SHA256 + salt, 100k iterations | Falta 2FA, TLS |
| Interoperabilidad | api/app.py:61,120-125 | REST API + JSON + CORS | Falta OpenAPI/Swagger spec |

### ✅ Fiabilidad (Madurez, Tolerancia, Recuperabilidad)

| Sub-característica | Archivo:Línea | Evidencia | GAPS |
|---|---|---|---|
| Madurez | api/app.py:144-150 | 	ry/except en endpoints | Falta en app/app.js (JavaScript) |
| Tolerancia | api/validators.py | Pre-validación antes de DB | Falta circuit breaker |
| Recuperabilidad | db/pg_repository.py:37-68 | PostgreSQL ACID + FK constraints | Falta backup automático |

### ✅ Usabilidad (Comprensibilidad, Aprendibilidad, Operabilidad)

| Sub-característica | Archivo:Línea | Evidencia | GAPS |
|---|---|---|---|
| Comprensibilidad | README.md:1-2 | "ControlCash UI" mencionada | Falta estudio con usuarios reales |
| Aprendibilidad | docs/PLAN_CALIDAD.md:106 | "Iconos y etiquetas claras" | Falta tutorial interactivo |
| Operabilidad | app/styles.css | Responsive design | Falta WCAG 2.1 AA validation |

### ⚠️ Eficiencia (Comportamiento temporal, Recursos)

| Sub-característica | Archivo:Línea | Evidencia | GAPS |
|---|---|---|---|
| Comportamiento temporal | docs/PLAN_CALIDAD.md:108 | "Índices en consultas frecuentes" | ❌ Índices NO explícitos en SQL |
| Recursos | docs/PLAN_CALIDAD.md:109 | "PostgreSQL optimizado" | Falta profiling y stress testing |

### ✅ Mantenibilidad (Analizabilidad, Cambiabilidad, Estabilidad)

| Sub-característica | Archivo:Línea | Evidencia | GAPS |
|---|---|---|---|
| Analizabilidad | db/base_repository.py:1-50 | Comentarios extensos en código | Falta métricas de complejidad |
| Cambiabilidad | README.md:6-8 | "3 capas independientes" | Falta test coverage > 80% |
| Estabilidad | db/pg_repository.py:60-62 | FK ON DELETE CASCADE, constraints CHECK | Falta regression tests |

### ✅ Portabilidad (Adaptabilidad, Instalación)

| Sub-característica | Archivo:Línea | Evidencia | GAPS |
|---|---|---|---|
| Adaptabilidad | app/styles.css | CSS responsive, media queries | Falta testing en múltiples navegadores |
| Instalación | README.md:69-80 | pip install, configuración sencilla | Falta Docker, Dockerfile |

**Score: 8.5/10** | **5.5 de 6 características implementadas** | **Falta: Índices SQL, WCAG, Docker**

---

## 5️⃣ ISO 14598 (Evaluación del Producto)

| Evidencia | Archivo:Línea | Implementación Concreta | GAPS |
|-----------|---|---|---|
| Requisitos evaluación | docs/PLAN_CALIDAD.md:123-125 | "Tiempo < 2s", "interfaz responsiva", "13 funciones" | ⚠️ Falta baseline de benchmarks |
| Métricas de aceptación | docs/PLAN_CALIDAD.md:128-134 | Tabla con 5 métricas (completitud, validación, seguridad, responsividad, integridad) | ❌ Sin valores SLA cuantitativos |
| Diseño evaluación | docs/PLAN_CALIDAD.md:137-141 | "5 tipos de prueba: funcionales, validación, seguridad, rendimiento, usabilidad" | ❌ Falta casos de prueba formales |
| Evaluación F7 | docs/PLAN_CALIDAD.md:278-282 | Resumen con 5 métricas (%, promedio, proyección, variación, top3) | ❌ Sin validación de exactitud de cálculos |
| Implementación | api/app.py | Endpoint /api/resumen genera reportes | ✅ Presente |

**Score: 7/10** | **Evaluación: Documentada** | **Falta: Automatización de tests**

---

## 6️⃣ ISO/IEC 25000 (SQuaRE) - Calidad del Producto

### Calidad del Producto (ISO 25010)

| Característica | Archivo:Línea | Evidencia | GAPS |
|---|---|---|---|
| **Adecuación Funcional** | docs/PLAN_CALIDAD.md:151-154 | Completitud (13 funciones), Corrección (validadores), Pertinencia (cada RF tiene usuario) | Falta matriz trazabilidad |
| **Eficiencia Desempeño** | docs/PLAN_CALIDAD.md:156-157 | Índices BD, PostgreSQL relacional | Falta índices SQL explícitos |
| **Compatibilidad** | docs/PLAN_CALIDAD.md:159-160 | Coexistencia (API desacoplada), Interoperabilidad (REST+JSON) | Falta especificación OpenAPI 3.0 |
| **Usabilidad** | docs/PLAN_CALIDAD.md:162-164 | Reconocibilidad (UI ControlCash), Aprendibilidad (flujo 3-pasos), Protección errores (validación doble) | Falta estudio SUS (System Usability Scale) |
| **Fiabilidad** | docs/PLAN_CALIDAD.md:166-168 | Madurez (try/catch), Disponibilidad (sin deps externas pesadas), Tolerancia (mensajes informativos) | Falta logging centralizado |
| **Seguridad** | docs/PLAN_CALIDAD.md:170-173 | Confidencialidad (PBKDF2), Integridad (FK+constraints), No-repudio (timestamp), Autenticidad (sesiones secret_key) | Falta TLS enforcement, 2FA, audit log inmutable |
| **Mantenibilidad** | docs/PLAN_CALIDAD.md:175-178 | Modularidad (3 capas), Reusabilidad (patrón Repository), Analizabilidad (documentado), Modificabilidad (independiente) | Falta análisis acoplamiento, librería reutilizable |

### Calidad en Uso (ISO 25022)

| Factor | Archivo:Línea | Métrica | GAPS |
|---|---|---|---|
| Efectividad | docs/PLAN_CALIDAD.md:184 | Tasa tareas completadas | Falta medición real |
| Eficiencia | docs/PLAN_CALIDAD.md:185 | Tiempo por operación | Falta APM (Application Performance Monitoring) |
| Satisfacción | docs/PLAN_CALIDAD.md:186 | Diseño atractivo | Falta NPS (Net Promoter Score) |
| Libertad de riesgo | docs/PLAN_CALIDAD.md:187 | Validación previene errores | Falta penetration testing |
| Cobertura contexto | docs/PLAN_CALIDAD.md:188 | Responsive multidispositivos | Falta testing en 5+ navegadores |

**Score: 8/10** | **Características: 7/7 documentadas** | **Falta: Métricas en tiempo real**

---

## 7️⃣ ISO/IEC 12207 (Ciclo de Vida del Software)

| Proceso | Actividad | Archivo:Línea | Evidencia | GAPS |
|---------|-----------|---|---|---|
| **ADQUISICIÓN** | Definición necesidades | docs/LEVANTAMIENTO_REQUERIMIENTOS.md:7-22 | "13 funciones + 2 actores documentados" | Falta contrato formal |
| **SUMINISTRO** | Entrega | docs/PLAN_CALIDAD.md:199 | "Estructura lista para deploy" | Falta release notes, versionado |
| **DESARROLLO** | | | | |
| → Análisis | Requisitos | docs/LEVANTAMIENTO_REQUERIMIENTOS.md:1-150 | RF-01 a RF-07 detallados con flujos | Falta herramienta de trazabilidad |
| → Diseño arquitectónico | Arquitectura 3-capas | README.md:5-8 | db/, api/, app/ separados | Falta diagrama UML |
| → Diseño detallado | Esquema BD | db/pg_repository.py:37-100 | Tablas usuarios, categorias, movimientos, notificaciones | Falta diagrama ER |
| → Codificación | Implementación | api/app.py, db/base_repository.py | Código SOLID, patrones Repository | Falta guía PEP 8 formal |
| → Integración | API-DB-APP | api/app.py (imports db) | Flask conecta repositories | Falta plan CI/CD |
| → Pruebas | Validación | api/validators.py | RFC-05 implementada | Falta test suite pytest |
| **OPERACIÓN** | Ejecución | README.md:75-80 | python app.py | Falta APM, monitoring |
| **MANTENIMIENTO** | Cambios | docs/PLAN_CALIDAD.md:208 | Capas independientes | Falta plan preventivo |
| **DOCUMENTACIÓN** | Completitud | docs/ (3 archivos) | README.md, PLAN_CALIDAD.md, LEVANTAMIENTO_REQUERIMIENTOS.md | Falta manual técnico desarrollador |
| **GESTIÓN CONFIGURACIÓN** | Control cambios | db/config.py | .env.example centraliza vars | Falta CHANGELOG.md |
| **ASEGURAMIENTO CALIDAD** | Auditoría | api/validators.py + db constraints | Validadores + CHECK constraints | Falta auditoría formal |
| **VERIFICACIÓN** | Validadores entrada | api/validators.py | 3 funciones validación | Falta test de cada validator |
| **VALIDACIÓN** | Pruebas integración | docs/PLAN_CALIDAD.md:215 | Mencionado | Falta casos de prueba |

**Score: 7.5/10** | **Procesos: 8/8 implementados** | **Falta: Automatización, Diagramas**

---

## 8️⃣ ISO/IEC 15504 SPICE (Evaluación de Procesos)

| Proceso | Nivel Actual | Evidencia | Archivo:Línea | GAPS |
|---------|------|---|---|---|
| **PA 1.1 Realización** | **Nivel 1 ✅** | Las 13 funciones operativas | docs/PLAN_CALIDAD.md:225 | Falta métricas de ejecución |
| **PA 2.1 Gestión rendimiento** | **Nivel 2 ✅** | Índices BD, respuestas estandarizadas | docs/PLAN_CALIDAD.md:226 | Falta KPI dashboard |
| **PA 2.2 Gestión producto trabajo** | **Nivel 2 ✅** | Separación clara de capas | docs/PLAN_CALIDAD.md:227 | Falta trazabilidad artefactos |
| **PA 3.1 Definición proceso** | **Nivel 2 ✅** | Patrones Repository, validadores | docs/PLAN_CALIDAD.md:228 | Falta procedimientos documentados |
| **PA 3.2 Despliegue proceso** | **Nivel 1 ✅** | Scripts instalación (README.md) | docs/PLAN_CALIDAD.md:229 | Falta automatización Ansible/Terraform |
| **Atributos** | | | | |
| - Realización | ✅ | Todas funciones operativas | docs/PLAN_CALIDAD.md:232 | - |
| - Gestión | ✅ | Estructura con normas | docs/PLAN_CALIDAD.md:233 | Falta auditoría conformidad |
| - Definición | ✅ | Procesos documentados | docs/PLAN_CALIDAD.md:234 | Falta versionado |

**Score: 6/10** | **Nivel Promedio: 1.8/3 (Nivel 2)** | **Falta: Procedimientos, Automatización**

---

## 9️⃣ ISO/IEC 20000 (Gestión de Servicios TI)

| Proceso ISO 20000 | Implementación | Archivo:Línea | Evidencia | GAPS |
|---|---|---|---|---|
| **Gestión de incidentes** | HTTP error responses | api/app.py:128-133 | 
espuesta_error() con código HTTP y mensaje | Falta ticketing system (Jira) |
| **Gestión de problemas** | Validación preventiva | api/validators.py | Pre-validación de datos | Falta RCA (Root Cause Analysis) formal |
| **Gestión configuración** | Modular 3-capas | db/config.py:22-26 | .env centraliza configuración | Falta CMDB (Configuration Management DB) |
| **Gestión de cambios** | Capas independientes | db/, api/, app/ | Cambios aislados por capa | Falta CAB (Change Advisory Board) |
| **Gestión disponibilidad** | PostgreSQL robusto | db/pg_repository.py:37-68 | Transacciones ACID, FK, constraints | Falta DR plan (RTO/RPO) |
| **Gestión capacidad** | Límites 200 registros | docs/LEVANTAMIENTO_REQUERIMIENTOS.md:107 | "máximo 200 registros por consulta" | Falta capacity planning |
| **Gestión continuidad** | Transacciones ACID | db/pg_repository.py:60-62 | FK ON DELETE CASCADE, CHECK constraints | Falta BCP (Business Continuity) |
| **Gestión seguridad** | PBKDF2, CORS | db/base_repository.py:32-38, api/app.py:63-64 | Hash seguro, CORS configurado | Falta ISMS formal, 2FA |
| **Gestión relaciones** | API REST desacoplada | api/app.py:61 | Frontend independiente | Falta SLA contractual |
| **Catálogo Servicios** | 12 servicios | docs/PLAN_CALIDAD.md:313-326 | Endpoints listados con métodos | Falta descripción detallada, precios |

**Score: 7/10** | **Procesos: 9/9 documentados** | **Falta: Ticketing, SLA, Automatización**

---

## 📊 RESUMEN FINAL

### Escala de Colores
- 🟢 **✅ 8+/10**: Implementación sólida (IEEE 730, ISO 9126, ISO 25000)
- 🟡 **⚠️ 7-7.9/10**: Implementación buena (CMMI, ISO 9001, ISO 14598, ISO 12207, ISO 20000)
- 🔴 **❌ <7/10**: Implementación parcial (SPICE 15504 = 6/10)

### Top 5 Fortalezas
1. ✅ **Documentación**: Excelente (PLAN_CALIDAD.md exhaustivo, 346 líneas)
2. ✅ **Seguridad**: PBKDF2-SHA256 + salt, sesiones, CORS
3. ✅ **Arquitectura**: 3 capas desacopladas, patrón Repository (ABC)
4. ✅ **Validación**: Double-check (frontend + backend)
5. ✅ **Trazabilidad**: Timestamps en todos los registros

### Top 5 Gaps Críticos
1. ❌ **Testing**: Sin pytest, sin cases de prueba formales
2. ❌ **CI/CD**: Sin automatización (GitHub Actions, etc)
3. ❌ **OpenAPI/Swagger**: Falta especificación de API
4. ❌ **Monitoreo**: Sin APM, logging centralizado
5. ❌ **Dockerización**: Sin Dockerfile, sin reproducibilidad garantizada

### Roadmap de Mejora
- **Inmediato (1-2 semanas)**: pytest + test cases, índices SQL documentados, Swagger spec
- **Corto (1 mes)**: GitHub Actions CI/CD, 2FA, WCAG compliance
- **Mediano (2-3 meses)**: Docker, monitoring, penetration testing
- **Largo (>3 meses)**: ISO 27001, CMMI Nivel 4, Terraform IaC

