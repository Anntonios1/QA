<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para el Análisis Detallado de Normas -->
# ANÁLISIS DETALLADO: IMPLEMENTACIÓN DE 9 NORMAS EN CONTROLCASH

**Proyecto:** C:\Users\teamp\Documents\WORKS UNI I\QUALITY
**Sistema:** ControlCash - Sistema de Control de Gastos
**Fecha:** 2026

---

## MATRIZ DE ANÁLISIS: Norma | Ubicación | Implementación Concreta | Evidencia | GAPS

### 1. ✅ CMMI (Capability Maturity Model Integration) — Niveles de Madurez

| Aspecto | Evidencia | Archivo:Línea | Estado | GAPS |
|---------|-----------|--------------|--------|------|
| **Mención explícita** | "CMMI Nivel 3: Definición de procesos estándar" | db/config.py:6-8 | ✅ Explícito | - |
| | "Normas: ISO/IEC 12207, CMMI Nivel 3, ISO/IEC 25000" | db/__init__.py:5 | ✅ Explícito | - |
| **Gestión de Requisitos (REQM)** | 13 historias de usuario y 12 requerimientos funcionales documentados y mapeados | docs/LEVANTAMIENTO_REQUERIMIENTOS.md:1-250 | ✅ Implementado | Falta trazabilidad bidireccional formal en matriz |
| **Planificación del Proyecto (PP)** | Estructura 3 capas: DB, API, APP definida | README.md:5-11 | ✅ Implementado | Falta plan de proyecto formal con hitos |
| **Gestión de Configuración (CM)** | Separación de archivos por capa, db/config.py centraliza variables | db/config.py:22-26 | ✅ Implementado | Falta control de versiones de esquema SQL |
| **Aseguramiento de Calidad (PPQA)** | Validadores en capa API, constraints en BD | api/validators.py:19-62 | ✅ Implementado | Falta plan formal de auditoría de calidad |
| **Definición de Procesos (OPD)** | Patrón Repository (ABC) y MVC aplicados | db/base_repository.py:1-50 | ✅ Implementado | Falta documentación de procesos estándar |
| **Integración con servicios externos** | NVIDIA NIM OCR/LLM integrados | api/ocr.py, api/llm.py:3-5 | ✅ Nivel 3 | Falta SLA y mecanismos de fallback |

---

### 2. ✅ ISO 9001 (Gestión de Calidad) — Sistema de Gestión de Calidad

| Aspecto | Evidencia | Archivo:Línea | Estado | GAPS |
|---------|-----------|--------------|--------|------|
| **Mención explícita** | "ISO 9001: Sistema de gestion de calidad" | README.md:18 | ✅ Explícito | - |
| **Enfoque basado en procesos** | "Enfoque basado en procesos: Flujo claro: Registro → Login → Gestionar → Consultar → Notificar" | docs/PLAN_CALIDAD.md:27 | ✅ Documentado | Falta mapa de interacción de procesos formal |
| **Estandarización de respuestas** | función respuesta_exito() con formato {"status": "success", ...} | api/app.py:120-125 | ✅ Implementado | Falta respuestas multilengua |
| **Trazabilidad de registros** | Campos fecha_registro y fecha_creacion en todas las tablas | db/pg_repository.py:44,66 | ✅ Implementado | Falta auditoría centralizada de cambios |
| **Gestión de cambios controlados** | Archivos .env.example para configuración reproducible | api/app.py:32-34 | ✅ Implementado | Falta control formal de cambios (CHANGELOG) |
| **Mejora continua** | Arquitectura modular permite iteración | docs/PLAN_CALIDAD.md:28 | ⚠️ Documentado | Falta métricas de mejora continua y KPIs |
| **Toma de decisiones basada en evidencia** | Resumen financiero con datos reales (F7) | docs/PLAN_CALIDAD.md:80 | ✅ Implementado | Falta dashboard de métricas en tiempo real |
| **Documentación del sistema** | PLAN_CALIDAD.md, LEVANTAMIENTO_REQUERIMIENTOS.md completos | docs/ | ✅ Documentado | Falta manual de usuario final |

---

### 3. ✅ IEEE 730 (Aseguramiento de Calidad del Software)

| Aspecto | Evidencia | Archivo:Línea | Estado | GAPS |
|---------|-----------|--------------|--------|------|
| **Mención explícita** | "IEEE 730: Plan de aseguramiento de calidad" | api/app.py:11 | ✅ Explícito | - |
| | "IEEE 730 - Trazabilidad del proceso de registro" | api/app.py:139 | ✅ Explícito | - |
| **Propósito del plan** | "Garantizar que el Sistema cumpla con requisitos de calidad" | docs/PLAN_CALIDAD.md:41 | ✅ Documentado | - |
| **Documentos de referencia** | "13 funciones documentadas", "esquema BD normalizado (3NF)", "endpoints REST documentados" | docs/PLAN_CALIDAD.md:44-46 | ✅ Documentado | Falta especificación formal de referencias |
| **Gestión de SQA por elemento** | Tabla con responsables: Capa DB, API, APP, validadores | docs/PLAN_CALIDAD.md:48-54 | ✅ Asignado | Falta matriz de responsabilidades detallada |
| **Actividades de SQA** | 5 actividades listadas (revisión requisitos, validación, integración, interfaz, seguridad) | docs/PLAN_CALIDAD.md:56-61 | ✅ Definidas | Falta cronograma de actividades |
| **Validación de datos** | validators.py con validación de entrada (RF-05) | api/validators.py:1-100 | ✅ Implementado | Falta validación de salida (output validation) |
| **Seguridad** | Hash PBKDF2-SHA256 + salt aplicado | db/base_repository.py:32-38 | ✅ Implementado | Falta rotación de secrets y auditoría de acceso |
| **Trazabilidad de interfaz** | Interfaces abstractas (ABC) en base_repository.py | db/base_repository.py:52-100 | ✅ Implementado | Falta versionado de interfaces |

---

### 4. ✅ ISO 9126 (Calidad del Software) — 6 Características Principales

| Característica | Sub-característica | Evidencia | Archivo:Línea | Status | GAPS |
|---|---|---|---|---|---|
| **FUNCIONALIDAD** | Adecuación | "13 funciones cubren todos los requisitos" | docs/PLAN_CALIDAD.md:98 | ✅ | Falta matriz de cobertura de requisitos |
| | Exactitud | validar_registro(), validar_movimiento() con reglas estrictas | api/validators.py:33-100 | ✅ | Falta tests de exactitud documentados |
| | Seguridad | "Hash PBKDF2 + salt para contraseñas" | db/base_repository.py:32-38 | ✅ | Falta penetration testing |
| | Interoperabilidad | "API REST estándar con JSON" | api/app.py:61,120-125 | ✅ | Falta OpenAPI/Swagger documentation |
| **FIABILIDAD** | Madurez | "Manejo de errores en todas las capas" | api/app.py:128-133 | ⚠️ | Falta try/catch en capa APP (JavaScript) |
| | Tolerancia a fallos | "Validación antes de operaciones DB" | api/app.py:141-150 | ✅ | Falta circuit breaker para servicios externos |
| | Recuperabilidad | "PostgreSQL transacciones ACID para integridad" | db/pg_repository.py:37-68 | ✅ | Falta plan de recuperación ante desastres |
| **USABILIDAD** | Comprensibilidad | "UI ControlCash intuitiva" | README.md:1-2 | ✅ | Falta estudio de usabilidad formal |
| | Aprendibilidad | "Iconos y etiquetas claras" en app/icons/ | docs/PLAN_CALIDAD.md:106 | ✅ | Falta tutorial interactivo |
| | Operabilidad | "Responsive, accesible por teclado" | app/styles.css | ⚠️ Parcial | Falta validación WCAG 2.1 AA |
| **EFICIENCIA** | Comportamiento temporal | "Índices en consultas frecuentes" | db/pg_repository.py (mencionado) | ⚠️ | Falta índices explícitos en schema |
| | Utilización de recursos | "PostgreSQL optimizado, CSS optimizado" | docs/PLAN_CALIDAD.md:109 | ✅ | Falta perfil de carga y pruebas de stress |
| **MANTENIBILIDAD** | Analizabilidad | "Código documentado y modular" | db/base_repository.py (comentarios extensos) | ✅ | Falta métricas de complejidad ciclomática |
| | Cambiabilidad | "3 capas independientes" | README.md:6-8 | ✅ | Falta test coverage > 80% |
| | Estabilidad | "Foreign keys y constraints" | db/pg_repository.py:60-62 | ✅ | Falta regresión tests automatizados |
| **PORTABILIDAD** | Adaptabilidad | "Responsive design" | app/styles.css | ✅ | Falta testing en múltiples dispositivos |
| | Facilidad de instalación | "pip install + python" | README.md:69-80 | ✅ | Falta Docker/containerización |

---

### 5. ✅ ISO 14598 (Evaluación del Producto Software)

| Aspecto | Evidencia | Archivo:Línea | Status | GAPS |
|---------|-----------|--------------|--------|------|
| **Mención explícita** | "ISO 14598 - Evaluación del producto" | api/app.py:151 | ✅ | - |
| **Establecer requisitos de evaluación** | "Sistema debe procesar: registro, login, movimientos, balance, notificaciones, resumen" | docs/PLAN_CALIDAD.md:123 | ✅ | Falta matriz de criterios cuantitativos |
| | "Tiempo de respuesta < 2 segundos" | docs/PLAN_CALIDAD.md:124 | ✅ | Falta baseline de benchmarks |
| | "Interfaz responsiva en móviles y desktop" | docs/PLAN_CALIDAD.md:125 | ✅ | Falta matriz de navegadores probados |
| **Especificar la evaluación (métricas)** | Tabla con 5 métricas: completitud, validación, seguridad, responsividad, integridad | docs/PLAN_CALIDAD.md:128-134 | ✅ | Falta valores objetivo específicos (SLAs) |
| **Diseñar la evaluación (5 tipos de prueba)** | "1. Funcionales, 2. Validación, 3. Seguridad, 4. Rendimiento, 5. Usabilidad" | docs/PLAN_CALIDAD.md:137-141 | ✅ | Falta casos de prueba formales (test cases) |
| **Evaluación de F7: Resumen** | Métricas: % por categoría, promedio diario, proyección 30d, top 3 gastos | docs/PLAN_CALIDAD.md:278-282 | ✅ | Falta dashboard de monitoreo en tiempo real |
| **Implementación del resumen** | Endpoint /api/resumen realiza cálculos | api/app.py | ✅ Presente | Falta validación de exactitud de cálculos |

---

### 6. ✅ ISO/IEC 25000 (SQuaRE) — Calidad del Producto Software

| Aspecto | Evidencia | Archivo:Línea | Status | GAPS |
|---------|-----------|--------------|--------|------|
| **Mención explícita** | "ISO/IEC 25000 (SQuaRE): Calidad del producto software" | README.md:23 | ✅ | - |
| | "Normas: ISO/IEC 12207, CMMI Nivel 3, ISO/IEC 25000" | db/__init__.py:5 | ✅ | - |
| **Calidad del Producto (ISO 25010)** | Tabla exhaustiva: Adecuación Funcional, Eficiencia, Compatibilidad, Usabilidad, Fiabilidad, Seguridad, Mantenibilidad | docs/PLAN_CALIDAD.md:147-179 | ✅ Completo | Falta desglose de métricas por característica |
| **Adecuación Funcional** | - Completitud: 13 funciones | docs/PLAN_CALIDAD.md:152 | ✅ | - |
| | - Corrección: validadores en api/validators.py | docs/PLAN_CALIDAD.md:153 | ✅ | - |
| | - Pertinencia: cada función resuelve necesidad de usuario | docs/PLAN_CALIDAD.md:154 | ✅ | Falta matriz de trazabilidad Reqs↔Funcs |
| **Eficiencia de Desempeño** | - Tiempo: consultas optimizadas con índices | docs/PLAN_CALIDAD.md:156 | ⚠️ | Falta índices explícitos documentados |
| | - Recursos: PostgreSQL relacional | docs/PLAN_CALIDAD.md:157 | ✅ | Falta métricas de consumo de recursos |
| **Compatibilidad** | - Coexistencia: API independiente del frontend | docs/PLAN_CALIDAD.md:159 | ✅ | - |
| | - Interoperabilidad: REST + JSON estándar | docs/PLAN_CALIDAD.md:160 | ✅ | Falta especificación OpenAPI 3.0 |
| **Usabilidad** | - Reconocibilidad: ControlCash UI con iconos | docs/PLAN_CALIDAD.md:162 | ✅ | Falta estudio de usabilidad con usuarios reales |
| | - Aprendibilidad: flujo simple de 3 pasos | docs/PLAN_CALIDAD.md:163 | ✅ | Falta SUS (System Usability Scale) |
| | - Protección contra errores: validación doble (front+back) | docs/PLAN_CALIDAD.md:164 | ✅ | Falta casos de borde documentados |
| **Fiabilidad** | - Madurez: try/catch en operaciones | docs/PLAN_CALIDAD.md:166 | ⚠️ | Falta logging centralizado |
| | - Disponibilidad: sin dependencias externas pesadas | docs/PLAN_CALIDAD.md:167 | ✅ | Falta uptime monitoring (SLA 99.9%) |
| | - Tolerancia a fallos: mensajes informativos | docs/PLAN_CALIDAD.md:168 | ✅ | Falta graceful degradation |
| **Seguridad** | - Confidencialidad: contraseñas PBKDF2 | docs/PLAN_CALIDAD.md:170 | ✅ | Falta TLS/HTTPS enforcement |
| | - Integridad: FK + constraints | docs/PLAN_CALIDAD.md:171 | ✅ | Falta firma digital de transacciones |
| | - No repudio: timestamp en registro | docs/PLAN_CALIDAD.md:172 | ✅ | Falta auditoría log inmutable |
| | - Autenticidad: sesiones con secret_key | docs/PLAN_CALIDAD.md:173 | ✅ | Falta 2FA / MFA |
| **Mantenibilidad** | - Modularidad: 3 capas separadas | docs/PLAN_CALIDAD.md:175 | ✅ | Falta análisis de acoplamiento |
| | - Reusabilidad: patrón Repository | docs/PLAN_CALIDAD.md:176 | ✅ | Falta librería reutilizable |
| | - Analizabilidad: código documentado | docs/PLAN_CALIDAD.md:177 | ✅ | Falta SonarQube analysis |
| | - Modificabilidad: componentes independientes | docs/PLAN_CALIDAD.md:178 | ✅ | Falta regression test suite |
| **Calidad en Uso (ISO 25022)** | Factor: Efectividad, Eficiencia, Satisfacción, Libertad de riesgo, Cobertura de contexto | docs/PLAN_CALIDAD.md:182-188 | ✅ Documentado | Falta medición real con usuarios |

---

### 7. ✅ ISO/IEC 12207 (Ciclo de Vida del Software) — Procesos

| Proceso del Ciclo de Vida | Actividad | Evidencia | Archivo:Línea | Status | GAPS |
|---|---|---|---|---|---|
| **ADQUISICIÓN** | Definición de necesidades | "13 funciones + 2 actores documentados" | docs/PLAN_CALIDAD.md:198 | ✅ | Falta especificación formal de contrato |
| **SUMINISTRO** | Entrega del producto | "Estructura de carpetas lista para deploy" | docs/PLAN_CALIDAD.md:199 | ⚠️ | Falta release notes formalizadas |
| **DESARROLLO** | | | | | |
| → Análisis de requisitos | Identificación de actores y funciones | docs/LEVANTAMIENTO_REQUERIMIENTOS.md completo | ✅ | Falta trazabilidad en herramienta (Jira/Azure DevOps) |
| → Diseño arquitectónico | Arquitectura 3 capas | db/, api/, app/ | ✅ | Falta diagrama UML de arquitectura |
| → Diseño detallado | Esquema BD, endpoints, UI | db/pg_repository.py:37-100 | ✅ | Falta diseño de interfaz (mockups) |
| → Codificación | Implementación SOLID | db/base_repository.py, api/app.py | ✅ | Falta guía de estilo de código (PEP 8 formal) |
| → Integración | API conecta DB con APP | api/app.py (imports db) | ✅ | Falta plan de integración con CI/CD |
| → Pruebas | Validación de datos | api/validators.py:1-100 | ⚠️ | Falta test suite automatizado (pytest) |
| **OPERACIÓN** | Ejecución del sistema | "Scripts de inicio" | README.md:75-80 | ✅ | Falta monitoreo en tiempo real (APM) |
| **MANTENIMIENTO** | Modificabilidad | "Capas independientes" | docs/PLAN_CALIDAD.md:208 | ✅ | Falta plan de mantenimiento preventivo |
| **DOCUMENTACIÓN** | Completitud | README.md, comentarios, PLAN_CALIDAD.md | docs/ | ✅ | Falta manual técnico para desarrolladores |
| **GESTIÓN CONFIGURACIÓN** | Control de cambios | Archivo .env.example | api/app.py:32 | ✅ | Falta CHANGELOG.md con versionado semántico |
| **ASEGURAMIENTO CALIDAD** | Validaciones | validators.py + constraints SQL | db/pg_repository.py:41-65 | ✅ | Falta auditoría formal de cumplimiento |
| **VERIFICACIÓN** | Validadores de entrada | validar_registro(), validar_movimiento() | api/validators.py | ✅ | Falta casos de prueba formales |
| **VALIDACIÓN** | Pruebas de integración | "Validación: Pruebas de integración" | docs/PLAN_CALIDAD.md:215 | ⚠️ | Falta test de integración implementado |

---

### 8. ✅ ISO/IEC 15504 SPICE (Procesos) — Evaluación y Mejora

| Proceso | Nivel Actual | Evidencia | Archivo:Línea | Status | GAPS |
|---------|------------|-----------|--------------|--------|------|
| **PA 1.1 Realización del proceso** | Nivel 1 (Realizado) | "Las 13 funciones están implementadas" | docs/PLAN_CALIDAD.md:225 | ✅ | Falta métricas de ejecución |
| **PA 2.1 Gestión del rendimiento** | Nivel 2 (Gestionado) | "Índices DB, respuestas estandarizadas" | docs/PLAN_CALIDAD.md:226 | ✅ | Falta cuadro de mando de KPIs |
| **PA 2.2 Gestión del producto de trabajo** | Nivel 2 (Gestionado) | "Separación de capas clara" | docs/PLAN_CALIDAD.md:227 | ✅ | Falta trazabilidad de artefactos |
| **PA 3.1 Definición del proceso** | Nivel 2 (Gestionado) | "Patrones Repository, validadores" | docs/PLAN_CALIDAD.md:228 | ✅ | Falta procedimientos documentados |
| **PA 3.2 Despliegue del proceso** | Nivel 1 (Realizado) | "Scripts de instalación" | docs/PLAN_CALIDAD.md:229 | ✅ | Falta automatización con Ansible/Terraform |
| **Atributos evaluados** | | | | | |
| - Realización | ✅ Todas funciones operativas | docs/PLAN_CALIDAD.md:232 | ✅ | - |
| - Gestión | ✅ Estructura organizada con normas | docs/PLAN_CALIDAD.md:233 | ✅ | Falta auditoría de conformidad |
| - Definición | ✅ Procesos documentados | docs/PLAN_CALIDAD.md:234 | ✅ | Falta versionado de procesos |

---

### 9. ✅ ISO/IEC 20000 (Gestión de Servicios TI) — IT Service Management

| Proceso ISO 20000 | Implementación | Evidencia | Archivo:Línea | Status | GAPS |
|---|---|---|---|---|---|
| **Gestión de incidentes** | Manejo de errores con respuestas HTTP estandarizadas | respuesta_error() con código HTTP específico | api/app.py:128-133 | ✅ | Falta ticketing system (Jira Service Desk) |
| **Gestión de problemas** | Validación preventiva | api/validators.py:1-100 | ✅ | Falta RCA (Root Cause Analysis) process |
| **Gestión de configuración** | Estructura modular de 3 capas | db/config.py centraliza configuración | ✅ | Falta CMDB (Configuration Management DB) |
| **Gestión de cambios** | Capas independientes permiten cambios aislados | db/, api/, app/ separados | ✅ | Falta CAB (Change Advisory Board) formal |
| **Gestión de disponibilidad** | PostgreSQL como motor robusto | db/pg_repository.py:37-68 | ✅ | Falta disaster recovery plan (RTO/RPO) |
| **Gestión de capacidad** | Límites de consulta (200 max), paginación | docs/LEVANTAMIENTO_REQUERIMIENTOS.md:107 | ✅ | Falta capacity planning document |
| **Gestión de continuidad** | PostgreSQL transacciones ACID, FK | db/pg_repository.py:60-62 | ✅ | Falta BCP (Business Continuity Plan) |
| **Gestión de seguridad** | PBKDF2 hash, sesiones, CORS configurado | db/base_repository.py:32-38, api/app.py:63-64 | ✅ | Falta ISMS documentado formalmente |
| **Gestión de relaciones** | API REST desacoplada del frontend | api/app.py:61 | ✅ | Falta SLA formal con clientes |
| **Catálogo de Servicios** | 12 servicios documentados (registro, login, movimientos, balance, notificaciones, resumen, categorías, health check) | docs/PLAN_CALIDAD.md:313-326 | ✅ | Falta descripción detallada de cada servicio |
| | | | | Falta precios/costos por servicio |
| **Endpoints documentados** | /api/auth/registro, /api/auth/login, /api/movimientos, /api/balance, /api/notificaciones, /api/resumen, /api/categorias, /api/health | docs/PLAN_CALIDAD.md:314-326 | ✅ | Falta Swagger/OpenAPI spec |

---

## RESUMEN EJECUTIVO POR NORMA

### 📊 Tabla de Madurez General

| Norma | Nivel de Implementación | Grado de Documentación | Automatización | Score |
|-------|------------------------|----------------------|-----------------|-------|
| CMMI | 70% (Nivel 3 + gaps) | ✅ Excelente | ⚠️ Parcial | 7/10 |
| ISO 9001 | 75% | ✅ Muy Bueno | ⚠️ Parcial | 7.5/10 |
| IEEE 730 | 80% | ✅ Excelente | ⚠️ Manual | 8/10 |
| ISO 9126 | 85% (5.5/6 características) | ✅ Muy Bueno | ✅ Parcial | 8.5/10 |
| ISO 14598 | 70% | ✅ Documentado | ❌ Manual | 7/10 |
| ISO 25000 | 80% | ✅ Muy Detallado | ⚠️ Parcial | 8/10 |
| ISO 12207 | 75% | ✅ Muy Bueno | ⚠️ Parcial | 7.5/10 |
| SPICE 15504 | 60% (Nivel 2) | ✅ Bueno | ❌ Manual | 6/10 |
| ISO 20000 | 70% | ✅ Bueno | ⚠️ Parcial | 7/10 |
| **PROMEDIO** | **74%** | **✅ Muy Bueno** | **⚠️ Manual/Parcial** | **7.4/10** |

---

## 🔴 GAPS CRÍTICOS POR CATEGORÍA

### Falta Total (Implementación < 20%)
- ❌ Swagger/OpenAPI specification
- ❌ Test suite automatizado (pytest)
- ❌ CI/CD pipeline
- ❌ Penetration testing formal
- ❌ WCAG 2.1 AA compliance
- ❌ Docker containerization
- ❌ Monitoring/APM (New Relic, Datadog)
- ❌ Centralized logging (ELK stack)
- ❌ 2FA/MFA authentication

### Implementación Parcial (20%-70%)
- ⚠️ Validación de datos (existe pero sin test coverage)
- ⚠️ Índices SQL (mencionados pero no explícitos)
- ⚠️ Manejo de errores (API sí, APP no)
- ⚠️ Documentación (buena pero sin manual técnico)
- ⚠️ Responsividad (CSS sí, pero sin testing formal)

### Implementación Completa (>70%)
- ✅ Seguridad de contraseñas (PBKDF2)
- ✅ Estructura de capas
- ✅ Validadores de entrada
- ✅ Trazabilidad de datos
- ✅ Constraints SQL
- ✅ Documentación funcional

---

## 📋 RECOMENDACIONES PRÁCTICAS

### Inmediato (1-2 semanas)
1. Crear test suite pytest para validadores (RFC-05)
2. Documentar índices SQL explícitamente en SCHEMA_SQL
3. Generar Swagger spec desde comentarios Flask
4. Implementar centralized logging con print → syslog

### Corto plazo (1 mes)
5. Crear GitHub Actions CI/CD básico (lint + test)
6. Implementar 2FA con TOTP (pyotp)
7. Validación WCAG 2.1 AA con aXe
8. Crear manual técnico (wiki interno)

### Mediano plazo (2-3 meses)
9. Docker + docker-compose para reproducibilidad
10. Monitoring básico (health checks cada 5 min)
11. Penetration testing (OWASP Top 10)
12. Disaster recovery plan con backup automático

### Largo plazo (> 3 meses)
13. Escalar a nivel CMMI 4 (Medido)
14. ISO 27001 certification
15. APM tool (New Relic trial)
16. Terraform para IaC

---

## 📁 MATRIZ FINAL: ARCHIVO → NORMA → LÍNEA

| Archivo | Normas asociadas | Líneas clave | Tipo |
|---------|------------------|-------------|------|
| db/base_repository.py | ISO 12207, ISO 9001, CMMI, IEEE 730, ISO 25000 | 1-50 | Interfaz |
| db/pg_repository.py | ISO 12207, ISO 9126, CMMI, ISO 25000, ISO 20000 | 1-100 | Implementación |
| db/config.py | ISO 12207, CMMI, ISO 9001 | 1-34 | Configuración |
| api/app.py | ISO 12207, ISO 9001, ISO 20000, CMMI, IEEE 730, ISO 15504 | 1-150+ | Endpoints |
| api/validators.py | ISO 9126, ISO 25000, IEEE 730, ISO 9001 | 1-100 | Validación |
| db/__init__.py | ISO 12207, CMMI, ISO 25000 | 1-38 | Módulo |
| docs/PLAN_CALIDAD.md | TODAS (9 normas) | 1-346 | Meta-documentación |
| docs/LEVANTAMIENTO_REQUERIMIENTOS.md | CMMI, ISO 9001, ISO 9126, IEEE 730, ISO 25000, ISO 12207 | 1-150+ | Especificación |
| README.md | Todas las normas (listadas en línea 15-29) | 1-81 | Proyecto |

