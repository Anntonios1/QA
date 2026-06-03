<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para el Plan de Calidad -->
# Plan de Aseguramiento de Calidad del Software
## Sistema de Control de Gastos - ControlCash

---

## 1. CMMI (Capability Maturity Model Integration)

### Nivel de Madurez Aplicado: Nivel 2 - Gestionado → Nivel 3 - Definido

| Área de Proceso | Aplicación en el Proyecto |
|----------------|--------------------------|
| **Gestión de Requisitos (REQM)** | Las 13 historias de usuario están documentadas y trazadas 1:1 en el código |
| **Planificación del Proyecto (PP)** | Estructura de 3 capas definida: DB (MySQL/PG), API (Flask), APP (PWA/Capacitor) |
| **Gestión de Configuración (CM)** | Separación de archivos por capa, esquema versionable (DBML) |
| **Aseguramiento de Calidad (PPQA)** | Validaciones en capa API, tests documentados en pytest |
| **Definición de Procesos (OPD)** | Patrones Repository y arquitectura distribuida aplicados |

---

## 2. ISO 9001 - Sistema de Gestión de Calidad

### Principios Aplicados

| Principio ISO 9001 | Implementación |
|---------------------|---------------|
| **Enfoque al cliente** | Interfaz intuitiva ControlCash (Glass UI), alineada a las 13 funciones |
| **Enfoque basado en procesos** | Flujo claro: Perfil → Gestión (Manual/OCR) → Resumen → IA Assistant → Notificar |
| **Mejora continua** | Arquitectura modular permite integración de LLM y motores de OCR |
| **Toma de decisiones basada en evidencia** | Resumen financiero con datos reales, insights generados por Gemini IA |
| **Trazabilidad** | Cada movimiento registra monto, tipo, categoría, descripción y moneda del usuario |

---

## 3. ISO/IEC 12207 - Ciclo de Vida del Software

Procesos Primarios Aplicados:

1. **Adquisición**: Utilización de Flask (Python) y Vanilla JS (sin frameworks pesados).
2. **Suministro**: Base de datos entregable mediante un solo script SQL.
3. **Desarrollo**:
   - Análisis de requisitos: 13 US (Historias de Usuario).
   - Diseño: Arquitectura 3-Tiers, Single Page Application.
   - Construcción: API con Python, GUI con CSS/JS/HTML.
   - Pruebas: Validadores de entrada en Python e interfaces JS.
4. **Mantenimiento**: Estructura de componentes (app.js) documentada.

---

## 4. ISO/IEC 27001 - Seguridad de la Información

Normativas técnicas de seguridad en el proyecto:

### A. Confidencialidad
- **Hasheo de Contraseñas**: Uso de pbkdf2:sha256 con sales aleatorias (Werkzeug security).
- **Autenticación Fuerte**: Bearer Tokens (JWT) que expiran tras un ciclo corto, renovables por Refresh Tokens.

### B. Integridad
- **Validación Backend de Campos**: API previene números negativos, strings inválidos o monedas no permitidas (COP/USD) antes de guardarlos.
- **Transaccionalidad**: Consistencia mediante FK en base de datos.
- **Límites de Peticiones**: (Rate Limiting) previene ataques de fuerza bruta.

### C. Disponibilidad
- **Arquitectura Stateless**: La capa API no guarda sesiones en memoria RAM, soporta reinicios en frío.
- **PWA Off-line capabilities**: (Service-Worker), cacheo de assets locales para inicio inmediato.

---

## 5. Control de Pruebas (Test Plan)

El sistema pasó por diferentes enfoques de validación documentados:

1. **API Validations**: Pruebas de inyección maliciosa, payloads truncados y nulos. 
2. **End-to-End**: Simulación de registro → escaneo recibo OCR → creación ingreso → chat con IA → consulta en dashboard.
3. **Frontend Mocking**: Consistencia en moneda de visualización ($ vs COP), renderización interactiva en gráficos Chart.js.
