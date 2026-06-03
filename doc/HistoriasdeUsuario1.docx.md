<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para las Historias de Usuario -->
**HISTORIAS DE USUARIO**

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU01 | Usuario: Usuario |
| Nombre Historia: Registrarse |  |
| Prioridad en Negocio: Alta | Riesgo en desarrollo: Baja |
| Puntos Estimados:5 | Interacción Asignada: Sprint 1 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero registrarme con mis datos, mi moneda preferida y un presupuesto mensual inicial para empezar a usar la aplicación. |  |
| Validación: Dado que el usuario está en la pantalla de registro, cuando ingresa nombre, correo válido, contraseña (mínimo 8 caracteres), moneda y presupuesto mensual mayor a cero, entonces el sistema crea la cuenta y registra el presupuesto global del mes actual. Dado que el usuario intenta registrarse con un correo ya existente, cuando envía el formulario, entonces el sistema muestra el mensaje de correo duplicado. Dado que el usuario deja campos vacíos o datos inválidos, cuando intenta registrarse, entonces el sistema no permite continuar y muestra los mensajes de validación. Dado que el registro se realiza correctamente, cuando el sistema guarda la información, entonces la contraseña se almacena con cifrado seguro y la moneda queda aplicada al formato de montos. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU02 | Usuario: Usuario |
| Nombre Historia: Iniciar sesión |  |
| Prioridad en Negocio: Alta | Riesgo en desarrollo: Baja |
| Puntos Estimados:3 | Interacción Asignada: Sprint 1 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario registrado, quiero iniciar sesión para acceder a mi información financiera. |  |
| Validación: Dado que el usuario está en la pantalla de inicio de sesión, cuando ingresa correo y contraseña válidos, entonces el sistema permite el acceso. Dado que el usuario ingresa credenciales incorrectas, cuando intenta iniciar sesión, entonces el sistema muestra un mensaje de error sin revelar información sensible. Dado que el usuario deja campos vacíos, cuando intenta iniciar sesión, entonces el sistema no permite el acceso. Dado que el dispositivo soporta biométrico y el usuario lo habilita, cuando toca el botón de biométrico, entonces el sistema autentica y accede al dashboard. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU03 | Usuario: Usuario |
| Nombre Historia: Ver inicio y balance |  |
| Prioridad en Negocio: Alta | Riesgo en desarrollo: Baja |
| Puntos Estimados:3 | Interacción Asignada: Sprint 2 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero ver el balance, resumen mensual y accesos rapidos para entender mi estado financiero al entrar al dashboard. |  |
| Validación: Dado que el usuario inició sesión, cuando accede a la vista Inicio, entonces ve balance disponible, ingresos, gastos y total de movimientos. Dado que existen movimientos registrados, cuando el sistema calcula el balance, entonces los valores coinciden con la base de datos. Dado que el usuario usa los accesos rápidos (Registrar gasto, Crear categoría, Definir presupuesto), cuando hace clic, entonces el sistema abre el módulo correspondiente. Dado que hay datos suficientes, cuando se muestra el resumen del mes, entonces se visualizan métricas, top de gastos y gráficos por categoría y tendencia. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU04 | Usuario: Usuario |
| Nombre Historia: Gestionar movimientos |  |
| Prioridad en Negocio: Alta | Riesgo en desarrollo: Media |
| Puntos Estimados:5 | Interacción Asignada: Sprint 2 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero crear, editar, eliminar y filtrar movimientos para llevar control de mi dinero. |  |
| Validación: Dado que el usuario abre el modal de movimiento (FAB o atajos), cuando ingresa monto mayor a cero, selecciona categoría, fecha y descripción opcional, entonces el sistema guarda el movimiento. Dado que el usuario edita un movimiento desde la lista, cuando guarda cambios, entonces el sistema actualiza la información. Dado que el usuario elimina un movimiento, cuando confirma, entonces el registro desaparece del listado. Dado que el usuario aplica filtros por fecha, monto, categoría y tipo, cuando cambia los filtros, entonces el listado se actualiza y respeta paginación. Dado que el usuario exporta CSV, cuando presiona el botón, entonces el sistema descarga el archivo con los movimientos filtrados. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU05 | Usuario: Usuario |
| Nombre Historia: Escanear recibo con OCR |  |
| Prioridad en Negocio: Media | Riesgo en desarrollo: Media |
| Puntos Estimados:5 | Interacción Asignada: Sprint 3 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero escanear un recibo para registrar un movimiento mas rapido. |  |
| Validación: Dado que el usuario abre el modal OCR, cuando carga una imagen JPG/PNG menor a 10MB y toca "Analizar", entonces el sistema extrae datos y muestra campos prellenados. Dado que el usuario revisa los datos extraídos, cuando confirma, entonces el movimiento queda registrado. Dado que el archivo no es válido, cuando intenta escanear, entonces el sistema muestra una alerta de validación. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU06 | Usuario: Usuario |
| Nombre Historia: Usar asistente IA |  |
| Prioridad en Negocio: Media | Riesgo en desarrollo: Alta |
| Puntos Estimados:5 | Interacción Asignada: Sprint 4 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero consultar al asistente IA para recibir respuestas sobre mis finanzas. |  |
| Validación: Dado que el usuario abre el asistente IA desde el dashboard o acciones rápidas, cuando escribe una consulta y presiona enviar, entonces el sistema devuelve una respuesta basada en sus datos. Dado que el servicio IA no está disponible, cuando el usuario intenta abrir el asistente, entonces el sistema muestra el aviso correspondiente. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU07 | Usuario: Usuario |
| Nombre Historia: Administrar categorías |  |
| Prioridad en Negocio: Media | Riesgo en desarrollo: Baja |
| Puntos Estimados:3 | Interacción Asignada: Sprint 3 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero crear y gestionar categorías con icono y descripción para clasificar mis movimientos financieros. |  |
| Validación: Dado que el usuario está en la sección de categorías, cuando crea una nueva categoría con nombre, tipo, icono opcional y descripción opcional, entonces el sistema la guarda y la muestra en el catálogo. Dado que el usuario edita una categoría, cuando guarda cambios, entonces el catálogo y los selectores se actualizan. Dado que el usuario desactiva una categoría, cuando confirma la acción, entonces la categoría deja de estar disponible para nuevos movimientos, pero conserva su historial. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU08 | Usuario: Usuario |
| Nombre Historia: Crear y comparar presupuestos |  |
| Prioridad en Negocio: Alta | Riesgo en desarrollo: Media |
| Puntos Estimados:5 | Interacción Asignada: Sprint 3 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero definir presupuestos mensuales globales o por categoría y ver su avance. |  |
| Validación: Dado que el usuario está en presupuestos, cuando asigna un monto límite y un mes (global o por categoría), entonces el sistema guarda o actualiza el presupuesto. Dado que el presupuesto supera el 80%, cuando el sistema calcula el consumo, entonces se muestra la alerta. Dado que el usuario consulta el comparativo mes vs mes, cuando selecciona una categoría o global, entonces el sistema muestra la variación. Dado que el usuario elimina un presupuesto, cuando confirma, entonces el registro queda inactivo. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU09 | Usuario: Usuario |
| Nombre Historia: Automatizaciones (recurrencias) |  |
| Prioridad en Negocio: Media | Riesgo en desarrollo: Media |
| Puntos Estimados:5 | Interacción Asignada: Sprint 4 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero programar movimientos recurrentes para automatizar mis ingresos o gastos. |  |
| Validación: Dado que el usuario crea una recurrencia con tipo, categoría, monto, frecuencia y próxima fecha, entonces el sistema la guarda. Dado que la frecuencia es mensual o anual, cuando se solicita el día de ejecución, entonces el sistema valida el rango 1-31. Dado que el usuario pausa o reactiva una recurrencia, cuando confirma la acción, entonces el estado cambia y se refleja en el listado. Dado que el usuario ejecuta pendientes, cuando presiona el botón, entonces el sistema registra los movimientos correspondientes. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU10 | Usuario: Usuario |
| Nombre Historia: Consultar reportes |  |
| Prioridad en Negocio: Media | Riesgo en desarrollo: Media |
| Puntos Estimados:4 | Interacción Asignada: Sprint 4 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero ver reportes por periodo y exportarlos para analizar mis finanzas. |  |
| Validación: Dado que el usuario selecciona un periodo (diario, semanal, mensual), cuando solicita el reporte, entonces el sistema muestra rango, totales y top categorías con tendencia. Dado que el usuario exporta PDF o Excel, cuando presiona el botón, entonces el archivo se descarga correctamente. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU11 | Usuario: Usuario |
| Nombre Historia: Ver notificaciones |  |
| Prioridad en Negocio: Media | Riesgo en desarrollo: Media |
| Puntos Estimados:3 | Interacción Asignada: Sprint 4 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero recibir y marcar notificaciones para mantenerme informado de mi actividad financiera. |  |
| Validación: Dado que el usuario abre el panel de notificaciones, cuando existen mensajes, entonces se muestran ordenados con su estado. Dado que el usuario marca una notificación como leída, cuando hace clic, entonces el contador se actualiza. Dado que el usuario otorga permisos, cuando hay eventos relevantes, entonces se envían notificaciones nativas. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU12 | Usuario: Usuario |
| Nombre Historia: Ver perfil IA |  |
| Prioridad en Negocio: Media | Riesgo en desarrollo: Alta |
| Puntos Estimados:5 | Interacción Asignada: Sprint 5 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero visualizar mi perfil financiero generado por IA para obtener recomendaciones. |  |
| Validación: Dado que el usuario tiene movimientos registrados, cuando el sistema calcula el perfil, entonces se muestran score, etiquetas y narrativa. Dado que el usuario actualiza el perfil, cuando presiona el boton de actualizar, entonces el sistema recalcula la informacion. Dado que el servicio IA no está disponible, cuando el usuario entra a la sección, entonces ve un mensaje de configuración. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU13 | Usuario: Usuario |
| Nombre Historia: Preferencias y cierre de sesión |  |
| Prioridad en Negocio: Baja | Riesgo en desarrollo: Baja |
| Puntos Estimados:2 | Interacción Asignada: Sprint 5 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero alternar el tema y cerrar sesión para controlar mi experiencia y seguridad. |  |
| Validación: Dado que el usuario está en ajustes, cuando cambia el tema, entonces la interfaz se actualiza y guarda la preferencia. Dado que el usuario presiona cerrar sesión, cuando confirma, entonces el sistema termina la sesión y vuelve a la pantalla de autenticación. |  |

| Historia de Usuario |  |
| ----- | :---- |
| Número: HU14 | Usuario: Usuario |
| Nombre Historia: Solicitar Balance |  |
| Prioridad en Negocio: Alta | Riesgo en desarrollo: Baja |
| Puntos Estimados: 5 | Interacción Asignada: Sprint 2 |
| Programador Responsable: Antonio Martínez, Dana Tintinago |  |
| Descripción: Como usuario, quiero solicitar y consultar mi balance general para visualizar de forma precisa el historial de mis movimientos, monitorear el progreso de mis presupuestos con alertas preventivas y generar reportes financieros detallados que me permitan tomar decisiones informadas sobre mi dinero. |  |
| Validación: Dado que el usuario tiene ingresos y gastos registrados, cuando solicita el balance, entonces el sistema muestra de forma secuencial y cronológica el historial completo de movimientos asociados, detallando monto, categoría, descripción y fecha de registro. Dado que el usuario ha definido presupuestos para el periodo de consulta, cuando el balance es calculado, entonces el sistema compara automáticamente el acumulado de gastos contra los límites asignados, emitiendo alertas visuales e instantáneas (del 80% o de exceso) para notificar cualquier riesgo de sobrecosto. Dado que el usuario visualiza su balance, cuando selecciona la opción de exportar o generar reportes, entonces el sistema compila y genera documentos en formatos estandarizados (CSV/PDF) que reflejan el estado del balance del periodo seleccionado sin pérdida de datos. Dado que el sistema procesa transacciones en múltiples monedas (COP y USD), cuando realiza las sumatorias de balance, ingresos, egresos y presupuestos consumidos, entonces el cálculo se efectúa con precisión matemática de centavos (double/decimal con dos decimales), evitando redondeos inconsistentes y garantizando que el saldo mostrado coincida exactamente con la diferencia entre la suma de ingresos y la de gastos en la base de datos. |  |


