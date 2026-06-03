<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para la plantilla de requerimientos de calidad de software -->
# ControlCash – Monitorea tus gastos y tu balance.

**JEYLER ANTONIO MARTINEZ GRUESO**  
**DANA SOFIA TINTINAGO VALVERDE**

**PRESENTADO A:**  
**INGENIERO GABRIEL ÁNGEL OSORIO HOYOS**

**9 DE MARZO DE 2026**  
**FACULTAD DE INGENIERÍA**  
**PROGRAMA DE INGENIERÍA**  
![][image1]

---

## TABLA DE CONTENIDO

- Portada
- Justificación
- Actores
- Diagrama de casos de uso
- Modelo entidad relación
- Diccionario de datos

---

## JUSTIFICACIÓN

El desarrollo de la aplicación **ControlCash** nace de la necesidad de contar con herramientas digitales que permitan a las personas llevar un mejor control de sus finanzas personales de manera moderna e inteligente. Actualmente, muchas personas no registran de manera organizada sus ingresos y gastos.

La finalidad de ControlCash es proporcionar una aplicación que facilite el registro, seguimiento y control de los movimientos, soportando múltiples monedas (COP y USD) y proporcionando asistencia con inteligencia artificial (Gemini), así como captura automática de recibos por OCR. 

En cuanto a su funcionamiento, la aplicación permitirá a los usuarios registrar sus datos (con presupuesto mensual y moneda principal), iniciar sesión y acceder a un sistema donde podrán agregar, modificar o consultar sus ingresos y gastos. Además, cuenta con un asistente de chat de IA, recordatorios (Notificaciones Push Web) y reportes de progreso del presupuesto.

De esta manera, ControlCash se plantea como una solución tecnológica avanzada, accesible y 1:1 funcional para llevar un control estricto de los presupuestos y la información financiera personal.

---

## ACTORES

### **Usuario** 
**Quién es:** Es la persona que utiliza el sistema de control de gastos para registrar y consultar su información financiera.

**Funciones:**
**1. Registrarse:** Permite al usuario crear una cuenta ingresando nombre, email, password, moneda (COP/USD) y presupuesto mensual base.
**2. Iniciar sesión:** Permite al usuario autenticarse en el sistema utilizando sus credenciales (JWT).
**3. Gestionar movimientos:** El usuario puede registrar (manualmente o mediante escaneo OCR de recibos) ingresos o gastos en diversas categorías (con descripciones detalladas).
**4. Configurar su perfil:** Ajustar su presupuesto mensual o consultar su balance, total de ingresos, total de gastos y el saldo disponible.
**5. Asistencia IA:** Interactuar con un asistente virtual basado en LLM para recibir consejos financieros personalizados.

### **Sistema**
**Quién es:** Es la aplicación y API backend (Flask) que procesa y almacena la información.

**Funciones:**
**1. Validar datos:** Verifica que la información y estructura de datos (email, budget, montos, monedas) sea correcta (Validators).
**2. Procesamiento Inteligente:** Llama al API de OCR para transcribir recibos, y al API LLM (Gemini) para chats interactivos.
**3. Notificaciones:** Envía Web Push Notifications utilizando VAPID keys para recordatorios recurrentes y alertas de presupuestos.
**4. Resumen y Balance:** Calcula el total de ingresos, gastos y avance del presupuesto y los serializa en JSON al Dashboard Frontend (Chart.js y Glass UI).

---

## DIAGRAMA DE CASOS DE USO
*(Diagrama documentado en anexos/imágenes)*

---

## MODELO ENTIDAD-RELACIÓN

El MER define la estructura de datos que soporta la aplicación (en MySQL/PostgreSQL mediante repository pattern), permitiendo almacenar, organizar y relacionar la información generada por los actores del sistema y sus funcionalidades.

### **Actor: Usuario**

El usuario interactúa con el sistema registrando y consultando información financiera.

**1. Usuarios:**
*Atributos:* `id (PK)`, `nombre`, `email`, `password_hash`, `moneda (COP/USD)`, `presupuesto_mensual`, `fecha_creacion`, `activo`.

### **Actor: Sistema**

El sistema es el eje principal que soporta y asocia:

**2. Movimientos:**
Registra ingresos y gastos del usuario.
*Atributos:* `id (PK)`, `usuario_id (FK)`, `categoria_id (FK)`, `tipo (ingreso/gasto)`, `monto`, `descripcion`, `fecha`, `fecha_registro`, `imagen_recibo`.

**3. Categorías:**
Clasifica los movimientos.
*Atributos:* `id (PK)`, `nombre`, `tipo_id`, `descripcion`, `icono`, `activo`.

**4. Notificaciones/Suscripciones (Push):**
Envío de avisos al usuario.
*Atributos:* `id (PK)`, `usuario_id (FK)`, `endpoint`, `p256dh`, `auth`.

**5. Recurrencias:**
Operaciones programadas.
*Atributos:* `id (PK)`, `usuario_id`, `tipo`, `monto`, `frecuencia`, `proxima_fecha`.

**6. Insights e Inteligencia Artificial:**
Generación de análisis de progreso y soporte LLM.
*Atributos (Insights):* `id (PK)`, `usuario_id`, `tipo`, `contenido`, `fecha_generacion`.

