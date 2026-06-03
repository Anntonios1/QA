<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para la Historia de Usuario 04 -->
# Historia de Usuario: HU04 - Solicitar Balance

Esta es la historia de usuario **HU04 - Solicitar Balance** generada para cumplir con los requerimientos de calidad y especificaciones de diseño.

| Historia de Usuario |  |
| ----- | :---- |
| **Número:** HU04 | **Usuario:** Usuario |
| **Nombre Historia:** Solicitar Balance |  |
| **Prioridad en Negocio:** Alta | **Riesgo en desarrollo:** Baja |
| **Puntos Estimados:** 5 | **Interacción Asignada:** Sprint 2 |
| **Programador Responsable:** Antonio Martínez, Dana Tintinago |  |
| **Descripción:** Como usuario, quiero solicitar y consultar mi balance general para visualizar de forma precisa el historial de mis movimientos, monitorear el progreso de mis presupuestos con alertas preventivas y generar reportes financieros detallados que me permitan tomar decisiones informadas sobre mi dinero. |  |
| **Validación:** <br>- **Historial de movimiento:** Dado que el usuario tiene ingresos y gastos registrados, cuando solicita el balance, entonces el sistema muestra de forma secuencial y cronológica el historial completo de movimientos asociados, detallando monto, categoría, descripción y fecha de registro.<br>- **Gestión de presupuestos y alertas:** Dado que el usuario ha definido presupuestos para el periodo de consulta, cuando el balance es calculado, entonces el sistema compara automáticamente el acumulado de gastos contra los límites asignados, emitiendo alertas visuales e instantáneas (del 80% o de exceso) para notificar cualquier riesgo de sobrecosto.<br>- **Generación de reportes:** Dado que el usuario visualiza su balance, cuando selecciona la opción de exportar o generar reportes, entonces el sistema compila y genera documentos en formatos estandarizados (CSV/PDF) que reflejan el estado del balance del periodo seleccionado sin pérdida de datos.<br>- **Precisión de cálculo:** Dado que el sistema procesa transacciones en múltiples monedas (COP y USD), cuando realiza las sumatorias de balance, ingresos, egresos y presupuestos consumidos, entonces el cálculo se efectúa con precisión matemática de centavos (double/decimal con dos decimales), evitando redondeos inconsistentes y garantizando que el saldo mostrado coincida exactamente con la diferencia entre la suma de ingresos y la de gastos en la base de datos. |  |
