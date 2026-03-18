# Levantamiento de Requerimientos
## Sistema de Control de Gastos — ControlCash

| Campo             | Detalle                                      |
|-------------------|----------------------------------------------|
| **Proyecto**      | ControlCash — Sistema de Control de Gastos   |
| **Versión**       | 1.0                                          |
| **Fecha**         | 11 de marzo de 2026                          |
| **Normas marco**  | CMMI N2/N3, ISO 9001, ISO 9126, IEEE 730, ISO/IEC 25000, ISO/IEC 12207 |
| **Clasificación** | Interno — Uso académico                      |

---

## 1. Propósito del Documento

El presente documento formaliza el levantamiento de requerimientos del proyecto **ControlCash**, una aplicación de control de gastos personales con interfaz ControlCash UI, arquitectura de tres capas (Presentación – Lógica de Negocio – Datos) y capacidad de instalación como aplicación móvil (APK/PWA). Su objetivo es identificar, describir y clasificar todos los requerimientos funcionales y no funcionales del sistema, estableciendo la trazabilidad entre las necesidades del usuario y las funciones implementadas.

---

## 2. Alcance del Sistema

ControlCash permite a un usuario gestionar sus finanzas personales desde un navegador web o dispositivo Android. El sistema cubre el ciclo completo: creación de cuenta, autenticación, registro de ingresos y gastos por categoría, consulta de balance, visualización de resúmenes financieros, notificaciones automáticas, escaneo de recibos mediante OCR y asesoría financiera con inteligencia artificial.

---

## 3. Actores del Sistema

| Actor            | Descripción                                                                              |
|------------------|------------------------------------------------------------------------------------------|
| **Usuario**      | Persona que utiliza la aplicación para registrar y consultar su información financiera. Interactúa mediante la interfaz web/móvil. |
| **Sistema**      | Conjunto de capas (APP + API + DB) que procesa, valida, almacena y notifica.             |
| **IA (NVIDIA NIM)** | Servicio externo que provee capacidades de OCR y chat conversacional financiero.      |

---

## 4. Requerimientos Funcionales

Los requerimientos funcionales se numeran como **RF-XX** y corresponden a las siete funciones principales del sistema más las capacidades de inteligencia artificial y notificaciones push.

---

### RF-01 — Registro de Usuario

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-01                                                                       |
| **Nombre**         | Registrarse                                                                 |
| **Prioridad**      | Alta                                                                        |
| **Actor**          | Usuario                                                                     |
| **Descripción**    | El sistema debe permitir que un nuevo usuario cree una cuenta personal proporcionando nombre completo, correo electrónico y contraseña. |
| **Precondición**   | El usuario no posee cuenta previa con ese correo electrónico.               |
| **Flujo principal**| 1. El usuario completa el formulario de registro. <br> 2. El sistema valida los datos (invoca RF-05). <br> 3. El sistema crea la cuenta y almacena la contraseña con hash PBKDF2 + salt. <br> 4. El sistema genera una notificación de bienvenida (invoca RF-06). <br> 5. El sistema retorna confirmación de registro exitoso. |
| **Flujo alterno**  | Si el correo ya está registrado, se retorna error 409 con mensaje informativo. |
| **Postcondición**  | La cuenta queda creada y disponible para autenticación.                     |
| **Endpoint REST**  | `POST /api/auth/registro`                                                   |

**Reglas de negocio RF-01:**
- Nombre: obligatorio, entre 2 y 100 caracteres.
- Correo electrónico: obligatorio, formato RFC válido, máximo 254 caracteres, único en el sistema.
- Contraseña: obligatoria, entre 8 y 128 caracteres.

---

### RF-02 — Inicio de Sesión

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-02                                                                       |
| **Nombre**         | Iniciar Sesión                                                              |
| **Prioridad**      | Alta                                                                        |
| **Actor**          | Usuario                                                                     |
| **Descripción**    | El sistema debe autenticar al usuario mediante su correo electrónico y contraseña, estableciendo una sesión activa. |
| **Precondición**   | El usuario posee una cuenta activa.                                         |
| **Flujo principal**| 1. El usuario ingresa correo y contraseña. <br> 2. El sistema valida el formato. <br> 3. El sistema verifica las credenciales contra la base de datos. <br> 4. Si son correctas, crea una sesión del lado del servidor. <br> 5. El sistema retorna datos del usuario y cantidad de notificaciones no leídas. |
| **Flujo alterno**  | Si las credenciales son incorrectas, retorna error 401. La sesión no se crea. |
| **Postcondición**  | El usuario está autenticado y puede acceder a todas las funciones del sistema. |
| **Endpoint REST**  | `POST /api/auth/login`                                                      |

**Requerimiento de seguridad RF-02:**
- Las sesiones se gestionan mediante cookies de servidor seguras.
- Todos los endpoints protegidos validan la sesión antes de procesar la solicitud.

---

### RF-03 — Gestión de Movimientos Financieros

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-03                                                                       |
| **Nombre**         | Gestionar Movimientos                                                       |
| **Prioridad**      | Alta                                                                        |
| **Actor**          | Usuario (autenticado)                                                       |
| **Descripción**    | El sistema debe permitir al usuario registrar, consultar y eliminar movimientos financieros de tipo ingreso o gasto, asociados a una categoría, monto, descripción y fecha. |
| **Precondición**   | El usuario ha iniciado sesión.                                              |
| **Flujo — Crear movimiento** | 1. El usuario indica tipo (ingreso/gasto), monto, categoría, descripción y fecha opcional. <br> 2. El sistema valida los datos (invoca RF-05). <br> 3. El sistema persiste el movimiento vinculado al usuario. <br> 4. Si el gasto es ≥ $1,000, el sistema genera una notificación de alerta (invoca RF-06). <br> 5. El sistema retorna el movimiento creado. |
| **Flujo — Listar movimientos** | 1. El usuario solicita su historial. <br> 2. El sistema aplica filtros opcionales (tipo, rango de fechas, límite). <br> 3. El sistema retorna la lista paginada. |
| **Flujo — Eliminar movimiento** | 1. El usuario selecciona un movimiento a eliminar. <br> 2. El sistema verifica que el movimiento pertenezca al usuario. <br> 3. El sistema elimina el registro. |
| **Postcondición**  | El balance y el resumen financiero del usuario quedan actualizados.         |
| **Endpoints REST** | `POST /api/movimientos` · `GET /api/movimientos` · `DELETE /api/movimientos/{id}` |

**Reglas de negocio RF-03:**
- Tipos válidos: `ingreso`, `gasto`.
- Monto: obligatorio, numérico, entre $0.01 y $999,999,999.99.
- Categoría: obligatoria, debe existir previamente en el catálogo.
- Descripción: opcional, máximo 500 caracteres.
- Fecha: opcional (formato `YYYY-MM-DD`); si se omite, se registra la fecha actual.
- Límite de listado: máximo 200 registros por consulta.

---

### RF-04 — Consulta de Balance Financiero

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-04                                                                       |
| **Nombre**         | Solicitar Balance                                                           |
| **Prioridad**      | Alta                                                                        |
| **Actor**          | Usuario (autenticado)                                                       |
| **Descripción**    | El sistema debe calcular y retornar el balance financiero del usuario: total de ingresos, total de gastos y saldo neto (ingresos − gastos). |
| **Precondición**   | El usuario ha iniciado sesión.                                              |
| **Flujo principal**| 1. El usuario accede a la sección de balance. <br> 2. El sistema consulta todos los movimientos del usuario. <br> 3. El sistema calcula totales. <br> 4. El sistema retorna las cifras en formato JSON. |
| **Postcondición**  | El usuario visualiza su situación financiera actualizada.                   |
| **Endpoint REST**  | `GET /api/balance`                                                          |

---

### RF-05 — Validación de Datos de Entrada

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-05                                                                       |
| **Nombre**         | Validar Datos                                                               |
| **Prioridad**      | Alta                                                                        |
| **Actor**          | Sistema                                                                     |
| **Descripción**    | El sistema debe validar todos los datos de entrada antes de procesarlos, retornando mensajes de error específicos por campo cuando los datos no cumplen las restricciones de calidad. |
| **Invocado por**   | RF-01, RF-02, RF-03                                                         |
| **Reglas cubiertas** | Nombre (longitud), correo electrónico (formato RFC), contraseña (longitud), monto (rango numérico), tipo de movimiento (enumeración), categoría (existencia), descripción (longitud), fecha (formato ISO 8601). |
| **Respuesta de error** | HTTP 422 con objeto `errores[]` detallado cuando la validación falla. |

---

### RF-06 — Sistema de Notificaciones

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-06                                                                       |
| **Nombre**         | Notificaciones                                                              |
| **Prioridad**      | Media                                                                       |
| **Actor**          | Sistema / Usuario (autenticado)                                             |
| **Descripción**    | El sistema debe generar, almacenar y entregar notificaciones al usuario ante eventos relevantes del sistema, tanto de forma in-app como mediante Web Push al navegador/dispositivo. |
| **Tipos de notificación** | `info`, `alerta`, `exito`, `error`                                 |
| **Eventos que generan notificaciones automáticas** | Alta de cuenta (bienvenida), registro de gasto mayor o igual a $1,000 (alerta). |
| **Flujo — Consultar notificaciones** | 1. El usuario accede al panel de notificaciones. <br> 2. El sistema retorna la lista, con filtro opcional de no leídas. |
| **Flujo — Marcar como leída** | 1. El usuario selecciona una notificación. <br> 2. El sistema actualiza su estado a leída. |
| **Flujo — Web Push** | 1. El usuario suscribe su navegador/dispositivo. <br> 2. El sistema almacena la suscripción VAPID. <br> 3. Ante un evento, el sistema envía notificación push al navegador. |
| **Endpoints REST** | `GET /api/notificaciones` · `PUT /api/notificaciones/{id}` · `POST /api/push/suscribir` |

---

### RF-07 — Resumen Financiero

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-07                                                                       |
| **Nombre**         | Resumen Financiero                                                          |
| **Prioridad**      | Media                                                                       |
| **Actor**          | Usuario (autenticado)                                                       |
| **Descripción**    | El sistema debe generar un resumen financiero del usuario para un período de tiempo configurable, mostrando gastos e ingresos desglosados por categoría, promedio diario de gasto y balance del período. |
| **Precondición**   | El usuario ha iniciado sesión y tiene al menos un movimiento registrado.    |
| **Parámetros**     | `dias`: período en días (1–365, por defecto 30).                           |
| **Datos devueltos**| Gastos por categoría (nombre, total, icono), promedio diario de gasto, balance del período. |
| **Endpoint REST**  | `GET /api/resumen?dias={n}`                                                 |

---

### RF-08 — Escaneo de Recibos con OCR (IA)

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-08                                                                       |
| **Nombre**         | Escaneo de Recibos                                                          |
| **Prioridad**      | Media                                                                       |
| **Actor**          | Usuario (autenticado) + Sistema + NVIDIA NIM                               |
| **Descripción**    | El sistema debe permitir al usuario fotografiar o adjuntar un recibo/ticket de compra. El sistema lo enviará al modelo de visión `nemotron-page-elements-v3` de NVIDIA NIM para extraer automáticamente el monto total, la fecha, la descripción del comercio y la lista de ítems del recibo. |
| **Precondición**   | El usuario ha iniciado sesión. La variable de entorno `NVIDIA_API_KEY` está configurada. |
| **Flujo principal**| 1. El usuario carga una imagen en formato base64. <br> 2. El sistema valida que la imagen no exceda 10 MB. <br> 3. El sistema envía la imagen al modelo OCR de NVIDIA NIM. <br> 4. El sistema parsea la respuesta JSON estructurada. <br> 5. El sistema retorna los datos extraídos (total, fecha, descripción, ítems). <br> 6. El usuario puede pre-cargar estos datos en el formulario de movimiento. |
| **Flujo alterno**  | Si el servicio no está disponible (API key ausente u error de red), retorna HTTP 503. |
| **Datos extraídos**| `total` (numérico), `fecha` (YYYY-MM-DD), `descripcion` (string), `items[]` ({nombre, precio}). |
| **Endpoint REST**  | `POST /api/ocr/recibo`  (body: `{ "imagen": "<base64>" }`)                 |

---

### RF-09 — Asistente Financiero con IA (Chat)

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-09                                                                       |
| **Nombre**         | Chat Asistente Financiero                                                   |
| **Prioridad**      | Media                                                                       |
| **Actor**          | Usuario (autenticado) + Sistema + NVIDIA NIM                               |
| **Descripción**    | El sistema debe ofrecer un chat conversacional con un asistente de inteligencia artificial especializado en finanzas personales, que responda preguntas en español y proporcione consejos personalizados basado en el balance y resumen financiero real del usuario. |
| **Precondición**   | El usuario ha iniciado sesión. La variable de entorno `NVIDIA_API_KEY` está configurada. |
| **Flujo principal**| 1. El usuario escribe un mensaje (máximo 2,000 caracteres). <br> 2. El sistema obtiene el balance y resumen de los últimos 30 días del usuario. <br> 3. El sistema construye el contexto financiero y lo envía al modelo `openai/gpt-oss-120b` vía NVIDIA NIM. <br> 4. El asistente responde en español con análisis o consejos (máximo 3 párrafos). <br> 5. El sistema retorna la respuesta al usuario. |
| **Flujo alterno**  | Si el servicio no está disponible, retorna HTTP 503.                        |
| **Endpoint REST**  | `POST /api/chat`  (body: `{ "mensaje": "..." }`)                           |

---

### RF-10 — Catálogo de Categorías

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-10                                                                       |
| **Nombre**         | Categorías de Movimientos                                                   |
| **Prioridad**      | Alta                                                                        |
| **Actor**          | Sistema / Usuario (autenticado)                                             |
| **Descripción**    | El sistema debe proveer un catálogo predefinido de categorías para clasificar ingresos y gastos. El usuario puede consultar el catálogo y filtrar por tipo. |
| **Categorías de ingreso** | Salario 💼, Freelance 💻, Inversiones 📈, Otros ingresos 💵         |
| **Categorías de gasto** | Alimentación 🍔, Transporte 🚗, Vivienda 🏠, Servicios 💡, Salud 🏥, Educación 📚, Entretenimiento 🎮, Ropa 👕, Otros gastos 📦 |
| **Endpoint REST**  | `GET /api/categorias?tipo={ingreso|gasto}`                                  |

---

### RF-11 — Cierre de Sesión

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-11                                                                       |
| **Nombre**         | Cerrar Sesión                                                               |
| **Prioridad**      | Alta                                                                        |
| **Actor**          | Usuario (autenticado)                                                       |
| **Descripción**    | El sistema debe permitir al usuario terminar su sesión activa de forma segura, eliminando los datos de sesión del servidor. |
| **Endpoint REST**  | `POST /api/auth/logout`                                                     |

---

### RF-12 — Webhooks Salientes

| Campo              | Descripción                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **ID**             | RF-12                                                                       |
| **Nombre**         | Webhooks Salientes                                                          |
| **Prioridad**      | Baja                                                                        |
| **Actor**          | Usuario (autenticado) + Servicio externo                                   |
| **Descripción**    | El sistema debe soportar el registro de URLs de webhook por usuario para enviar notificaciones de eventos a servicios externos (integraciones con terceros). |

---

## 5. Requerimientos No Funcionales

### RNF-01 — Seguridad

| ID       | Descripción                                                                          |
|----------|--------------------------------------------------------------------------------------|
| RNF-01.1 | Las contraseñas deben almacenarse con hash PBKDF2-HMAC-SHA256 + salt aleatorio.      |
| RNF-01.2 | Todos los endpoints de negocio deben requerir sesión activa (middleware `login_required`). |
| RNF-01.3 | Las respuestas de error no deben revelar detalles internos del sistema.              |
| RNF-01.4 | CORS debe restringirse a los orígenes autorizados del sistema.                       |
| RNF-01.5 | La `SECRET_KEY` de la sesión debe configurarse mediante variable de entorno, no estar hardcodeada. |

### RNF-02 — Disponibilidad y Compatibilidad

| ID       | Descripción                                                                          |
|----------|--------------------------------------------------------------------------------------|
| RNF-02.1 | La aplicación debe funcionar en Chrome, Firefox y Edge en sus versiones actuales.    |
| RNF-02.2 | La aplicación debe poder instalarse como APK en dispositivos Android (Capacitor).   |
| RNF-02.3 | La aplicación debe funcionar como PWA (Progressive Web App) con soporte offline básico mediante Service Worker. |

### RNF-03 — Usabilidad

| ID       | Descripción                                                                          |
|----------|--------------------------------------------------------------------------------------|
| RNF-03.1 | La interfaz debe ser responsiva y adaptarse a resoluciones móviles y de escritorio.  |
| RNF-03.2 | Los mensajes de error deben ser claros, en español, e indicar el campo afectado.     |
| RNF-03.3 | Las notificaciones toast deben desaparecer automáticamente después de ser mostradas. |

### RNF-04 — Portabilidad de Base de Datos

| ID       | Descripción                                                                          |
|----------|--------------------------------------------------------------------------------------|
| RNF-04.1 | El sistema utiliza PostgreSQL como base de datos relacional, implementada mediante el patrón Repository, sin cambios en la lógica de negocio. |
| RNF-04.2 | La conexión se configura mediante variables de entorno (`PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD`). |

### RNF-05 — Rendimiento

| ID       | Descripción                                                                          |
|----------|--------------------------------------------------------------------------------------|
| RNF-05.1 | Las consultas de movimientos deben estar limitadas a 200 registros por petición.     |
| RNF-05.2 | El tamaño máximo de imagen para OCR es de 10 MB (base64).                           |
| RNF-05.3 | El período máximo para el resumen financiero es de 365 días.                         |

### RNF-06 — Mantenibilidad

| ID       | Descripción                                                                          |
|----------|--------------------------------------------------------------------------------------|
| RNF-06.1 | El sistema debe seguir una arquitectura de tres capas claramente separadas: `db/`, `api/`, `app/`. |
| RNF-06.2 | La capa de datos debe implementarse mediante el patrón Repository con interfaces base definidas. |
| RNF-06.3 | Las respuestas de la API deben seguir el formato estándar `{ status, mensaje, data }`. |

---

## 6. Requerimientos de Integración Externa

| ID     | Servicio             | Propósito                                      | Variable de entorno  |
|--------|----------------------|------------------------------------------------|----------------------|
| RI-01  | NVIDIA NIM           | OCR de recibos (nemotron-page-elements-v3)     | `NVIDIA_API_KEY`     |
| RI-02  | NVIDIA NIM           | Chat financiero IA (openai/gpt-oss-120b)       | `NVIDIA_API_KEY`     |
| RI-03  | Web Push (VAPID)     | Notificaciones push al navegador/dispositivo   | `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CONTACT` |
| RI-04  | Webhooks externos    | Integración con servicios de terceros          | Configurable por usuario |

---

## 7. Restricciones Técnicas

| Restricción          | Valor                                      |
|----------------------|--------------------------------------------|
| Lenguaje backend     | Python 3.8+                                |
| Framework backend    | Flask                                      |
| Base de datos        | PostgreSQL                                 |
| Base de datos prod   | PostgreSQL                                 |
| Frontend             | HTML5, CSS3, JavaScript (Vanilla)          |
| Empaquetado móvil    | Capacitor (App ID: `com.controlcash.app`) |
| Comunicación         | REST / JSON                                |
| Autenticación        | Sesión de servidor (cookie)                |

---

## 8. Matriz de Trazabilidad

| Requerimiento | Archivo(s) de implementación                        | Norma relacionada                    |
|---------------|-----------------------------------------------------|--------------------------------------|
| RF-01         | `api/app.py` (ruta `/api/auth/registro`), `api/validators.py`, `db/` | IEEE 730, CMMI REQM          |
| RF-02         | `api/app.py` (ruta `/api/auth/login`)               | ISO 9126 – Seguridad                 |
| RF-03         | `api/app.py` (rutas `/api/movimientos`)             | ISO 9001 – Trazabilidad de registros |
| RF-04         | `api/app.py` (ruta `/api/balance`)                  | ISO/IEC 25000 – Completitud funcional|
| RF-05         | `api/validators.py`                                 | ISO 9126 – Exactitud, IEEE 730       |
| RF-06         | `api/app.py` (rutas `/api/notificaciones`), `api/push.py` | ISO/IEC 20000 – Comunicación    |
| RF-07         | `api/app.py` (ruta `/api/resumen`)                  | ISO 14598 – Evaluación del producto  |
| RF-08         | `api/ocr.py`, `api/app.py` (ruta `/api/ocr/recibo`)| ISO/IEC 25000 – Funcionalidad        |
| RF-09         | `api/llm.py`, `api/app.py` (ruta `/api/chat`)       | ISO/IEC 25000 – Usabilidad           |
| RF-10         | `db/` (tabla `categorias`), `api/app.py`            | ISO 9001 – Estandarización           |
| RF-11         | `api/app.py` (ruta `/api/auth/logout`)              | ISO 9126 – Seguridad                 |
| RF-12         | `api/push.py`                                       | ISO/IEC 20000 – Comunicación         |
| RNF-01        | `db/base_repository.py` (PBKDF2), `api/app.py` (middleware) | ISO 9126 – Seguridad          |
| RNF-04        | `db/pg_repository.py`, `db/config.py` | ISO/IEC 25000 – Portabilidad |

---

## 9. Glosario

| Término         | Definición                                                                          |
|-----------------|-------------------------------------------------------------------------------------|
| **Movimiento**  | Registro individual de un ingreso o gasto del usuario.                              |
| **Balance**     | Resultado de restar el total de gastos al total de ingresos del usuario.            |
| **Categoría**   | Clasificación del movimiento (ej. Alimentación, Salario).                           |
| **Notificación**| Mensaje generado automáticamente por el sistema ante un evento financiero relevante.|
| **OCR**         | Reconocimiento óptico de caracteres; extrae texto/datos de imágenes de recibos.     |
| **VAPID**       | Voluntary Application Server Identification; protocolo de autenticación para Web Push. |
| **PWA**         | Progressive Web App; aplicación web instalable con capacidades nativas.             |
| **Repository**  | Patrón de diseño que abstrae el acceso a datos detrás de una interfaz común.         |
| **NIM**         | NVIDIA Inference Microservices; plataforma de modelos de IA en la nube.             |
