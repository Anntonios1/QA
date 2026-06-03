<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para el Plan de Pruebas Resumen -->
# Plan de Pruebas - ControlCash (3 Features)

## Alcance del proyecto
**3 Features principales a probar:**
1. Registro de usuario
2. Login / Autenticación
3. Balance financiero

## Fuera del alcance
- Pruebas de rendimiento (carga, stress, concurrencia)
- Pruebas de seguridad exhaustivas
- Pruebas de OCR y IA
- Historial de movimientos, presupuestos y reportes (aunque estén descritos en HU04)
- Autenticación biométrica

## Tipos de prueba / estrategia (Como ejecutar las pruebas?)
- Pruebas funcionales manuales basadas en historias de usuario
- Exploración dirigida
- Cross browser testing (Chrome, Firefox, Edge)
- Cross mobile testing (emulado con Chrome DevTools)
- Pruebas de Aceptación de usuario (UAT)
- Pruebas de sanidad del release en Producción

## Ambiente de prueba
- **Acceso VPN:** Se proporciona acceso remoto a PC del desarrollador
- **Alcance de VPN:** La app solo es accesible dentro de la sesión remota (no hay URL pública)
- **URL local:** http://127.0.0.1:5000 (Flask + MySQL XAMPP - accesible vía VPN)
- **Navegadores:** Chrome 120+, Firefox 121+, Edge 120+
- **Dispositivos:** Desktop (VPN), Mobile emulado en Chrome DevTools
- **Base de datos:** MySQL local (XAMPP)


## Datos de prueba
- Usuario de prueba (COP):
  - Email: test@example.com
  - Password: TestPassword123!
  - Nombre: Test User
  - Moneda: COP
  - Presupuesto inicial: 1,000,000
- Usuario de prueba (USD):
  - Email: test.usd@example.com
  - Password: TestPassword123!
  - Nombre: Test User USD
  - Moneda: USD
  - Presupuesto inicial: 1,000.00

## Casos de prueba por Feature

### Feature 1: Registro (**HU01**)
**Descripción:** Como usuario, quiero registrarme en la aplicación para crear una cuenta y gestionar mis finanzas personales.

**Criterios de aceptación de HU01:**
1. Dado que el usuario completa correctamente nombre, correo, contraseña (mínimo 8 caracteres), moneda y presupuesto > 0, cuando presiona "Crear Cuenta Segura", entonces el sistema crea la cuenta y muestra un mensaje de confirmación.
2. Dado que el usuario ingresa un correo ya registrado, cuando envía el formulario, entonces el sistema muestra un mensaje indicando que el email ya está registrado.
3. Dado que el usuario deja campos vacíos o ingresa datos inválidos, cuando intenta registrarse, entonces el sistema no permite continuar y muestra mensajes de validación.
4. Dado que el registro es exitoso, cuando el sistema guarda la información, entonces la contraseña se almacena con cifrado seguro.

| ID | Caso BDD | Dado que | Cuando | Entonces |
| --- | --- | --- | --- | --- |
| REG-001 | Registro exitoso con datos válidos | El usuario se encuentra en la pantalla de registro | Completa nombre, email, password (8+ caracteres), moneda y presupuesto > 0, y presiona "Crear Cuenta Segura" | El sistema crea la cuenta, muestra toast de confirmación "¡Bienvenido!" y lo redirige a login |
| REG-002 | Rechazo - Email duplicado | Un correo ya existe registrado en el sistema | El usuario intenta registrarse con ese email y presiona "Crear Cuenta Segura" | El sistema muestra mensaje de error "Email ya registrado" |
| REG-003 | Validación - Campos vacíos | El usuario no completa uno o más campos obligatorios | Intenta enviar el formulario sin llenar nombre, email, password, moneda o presupuesto | El sistema muestra validación de campos y no permite continuar |
| REG-004 | Validación - Password débil | El usuario ingresa una contraseña menor a 8 caracteres | Tipea password corto (ej: "Pass123") | El sistema muestra indicador de fortaleza en rojo "Débil" y bloquea envío |
| REG-005 | Validación - Presupuesto inválido | El usuario deja el campo presupuesto vacío o ingresa un valor <= 0 | Intenta presupuesto negativo (-100) o vacío | El sistema muestra error "El presupuesto mensual debe ser mayor a cero" |
| REG-006 | Cifrado de contraseña | El registro es exitoso con datos válidos | El sistema guarda la información en la base de datos | La contraseña almacenada se guarda encriptada, no en texto plano |
| REG-007 | Toggle a Login | El usuario está en pantalla de registro | Hace click en "Inicia sesión" o enlace equivalente | El formulario de registro desaparece y se muestra el formulario de login |

---

### Feature 2: Iniciar Sesión (**HU02**)
**Descripción:** Como usuario registrado, quiero iniciar sesión para acceder a mi información financiera.

**Criterios de aceptación de HU02:**
1. Dado que el usuario se encuentra en la pantalla de inicio de sesión, cuando ingresa un correo y contraseña válidos, entonces el sistema permite el acceso correctamente.
2. Dado que el usuario ingresa credenciales incorrectas, cuando intenta iniciar sesión, entonces el sistema muestra un mensaje de error sin revelar información sensible.
3. Dado que el usuario deja campos vacíos, cuando intenta iniciar sesión, entonces el sistema no permite el acceso y muestra mensajes de validación.
4. Dado que el inicio de sesión es exitoso, cuando el sistema valida las credenciales, entonces se crea una sesión segura para el usuario.

| ID | Caso BDD | Dado que | Cuando | Entonces |
| --- | --- | --- | --- | --- |
| LOG-001 | Login exitoso con credenciales válidas | El usuario está registrado y se encuentra en pantalla de login | Ingresa email y password correctos, presiona "Iniciar Sesión" | El sistema valida credenciales, crea sesión segura (JWT), muestra toast "Sesion iniciada" y abre dashboard |
| LOG-002 | Rechazo - Credenciales incorrectas | El usuario está registrado | Ingresa email correcto con password incorrecto | El sistema muestra error genérico "Email o contraseña incorrectos" sin revelar si el email existe |
| LOG-003 | Rechazo - Email no registrado | El email no existe en la base de datos | Ingresa email inexistente con cualquier password | El sistema muestra error "Email o contraseña incorrectos" |
| LOG-004 | Validación - Email vacío | El usuario no ingresa email | Deja campo email vacío y presiona "Iniciar Sesión" | El sistema muestra validación "Email requerido" y no permite continuar |
| LOG-005 | Validación - Password vacío | El usuario no ingresa contraseña | Deja campo password vacío y presiona "Iniciar Sesión" | El sistema muestra validación "Contraseña requerida" y no permite continuar |
| LOG-006 | Sesión segura se crea | El login es exitoso con credenciales válidas | El sistema valida las credenciales contra BD | Se crea token JWT en localStorage y se autoriza el acceso al dashboard |
| LOG-007 | Session timeout después de inactividad | El usuario ha iniciado sesión hace 20 minutos sin actividad | El tiempo de inactividad máximo se alcanza | El sistema cierra la sesión, limpia tokens y redirige a pantalla de login |

---

### Feature 3: Consultar Balance (**HU04**)
**Descripción:** Como usuario, quiero consultar mi balance para conocer mi estado financiero.

**Criterios de aceptación de HU04:**
1. Dado que existen movimientos registrados, cuando el sistema calcula el balance, entonces los valores mostrados coinciden con la información almacenada en la base de datos.

**Nota de alcance HU04:** Aunque la historia también menciona historial de movimientos, presupuestos y reportes, esas funcionalidades no se prueban en este plan.

| ID | Caso BDD | Dado que | Cuando | Entonces |
| --- | --- | --- | --- | --- |
| BAL-001 | Balance se carga correctamente al login | El usuario inicia sesión con cuenta que tiene movimientos registrados | El dashboard se carga y se ejecuta cargarBalance() | Se muestra card "Balance Disponible" con valor calculado: balance = ingresos - gastos |
| BAL-002 | Total de ingresos se muestra correcto | Existen movimientos de ingreso en la base de datos | El usuario navega a sección de balance | Se muestra campo "Ingresos" con suma correcta de todos los movimientos de tipo ingreso |
| BAL-003 | Total de gastos se muestra correcto | Existen movimientos de gasto en la base de datos | El usuario navega a sección de balance | Se muestra campo "Gastos" con suma correcta de todos los movimientos de tipo gasto |
| BAL-004 | Contador de movimientos | El usuario tiene N movimientos registrados | El balance se carga | Se muestra el número entero total_movimientos en la card de balance |
| BAL-005 | Balance positivo muestra color verde | balance >= 0 | El usuario hace login con balance positivo | Card de balance muestra gradient verde/success (background color positivo) |
| BAL-006 | Balance negativo muestra color rojo | balance < 0 | El usuario hace login con balance negativo | Card de balance muestra gradient rojo/danger (background color negativo) |
| BAL-007 | Animación del contador | El usuario ve la card de balance | El balance-total inicia animación desde 0 | El contador anima suavemente hasta el valor final en 900ms |
| BAL-008 | Moneda respeta preferencia (COP) | Usuario registrado con moneda COP | El usuario hace login | Balance, ingresos y gastos muestran formato "COP 1,234,567.89" |
| BAL-009 | Moneda respeta preferencia (USD) | Usuario registrado con moneda USD | El usuario hace login | Balance, ingresos y gastos muestran formato "USD 1,234.56" |
| BAL-010 | Balance coincide con BD | Datos en BD son: ingresos=100, gastos=30 | El sistema calcula el balance | Se muestra balance = 70 (100-30) |
| BAL-011 | Responsividad en móvil | Usuario visualiza en dispositivo móvil (320px) | Carga el dashboard | Card de balance se ajusta correctamente sin overflow, números legibles |

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigacion |
| --- | --- | --- | --- |
| Base de datos no disponible | Media | Alto | Verificar que MySQL en XAMPP está corriendo antes de cada prueba |
| Tokens JWT expirados | Baja | Medio | Limpiar localStorage y reintentar login |
| Balance no actualiza | Baja | Medio | Hacer refresh de la página (F5) |
| API backend no iniciado | Media | Alto | Verificar que el servicio Flask esté corriendo antes de la prueba |
| VPN inestable o desconectada | Media | Alto | Confirmar estabilidad de VPN; reconectar y reintentar |
| Puerto 5000 bloqueado por firewall local | Baja | Alto | Permitir el puerto 5000 en el firewall del equipo remoto |
| Datos de prueba contaminados | Media | Medio | Reiniciar datos o usar correos únicos para registro |
| Cache/localStorage desactualizado | Media | Medio | Limpiar cache y localStorage antes de repetir pruebas |
| Latencia alta en VPN | Media | Medio | Ejecutar pruebas en horarios de baja carga y registrar tiempos |

## Consideraciones de Cross-Browser
- Chrome 120+ (principal)
- Firefox 121+ (secondary)
- Edge 120+ (tertiary)
- Mobile: Chrome en emulador Pixel 4

## Criterios de aceptación
- ✅ Todos los casos REG-001 (Registro - HU01)
- ✅ Todos los casos LOG-001 (Login - HU02)
- ✅ Todos los casos BAL-001 (Balance - HU04)
- ✅ Sin errores en consola (F12 DevTools) que sean bloqueadores (ej: TypeError, ReferenceError)
- ✅ UI responsiva en mobile (320px), tablet (768px) y desktop (1024px+)
- ✅ Tiempos de respuesta < 2 segundos por acción principal (login, registro, cargar balance)
- ✅ Tokens JWT se almacenan y recuperan correctamente de localStorage
- ✅ Contraseñas se almacenan encriptadas en base de datos (verificable mediante hash en BD)
