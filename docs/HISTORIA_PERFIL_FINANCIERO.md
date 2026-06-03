<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para la Historia de Usuario del Perfil Financiero con IA -->
# Historia de perfil financiero

## Objetivo

Describir la validacion funcional del perfil financiero generado por IA, incluyendo la carga inicial, la regeneracion manual, la caché diaria y el comportamiento cuando el servicio no esta disponible.

## Perfil financiero IA

### Validación

Dado que el usuario accede al panel de perfil financiero, cuando el frontend solicita `GET /api/ai/perfil`, entonces el sistema muestra el perfil financiero del usuario.

Dado que existe un perfil generado en el dia, cuando el backend responde, entonces el sistema devuelve el perfil desde la caché diaria sin regenerarlo.

Dado que no existe un perfil en caché, cuando el sistema consulta el balance y el resumen de los ultimos 30 dias, entonces genera un nuevo perfil con IA.

Dado que el usuario presiona el boton de actualizar, cuando el frontend solicita `GET /api/ai/perfil?force=1`, entonces el sistema fuerza la regeneracion del perfil.

Dado que el servicio de IA no esta disponible o falta `NVIDIA_API_KEY`, cuando se intenta generar el perfil, entonces el sistema muestra el mensaje de configuracion correspondiente.

### Comportamiento esperado

- El perfil debe poder leerse desde caché diaria o generarse bajo demanda.
- El sistema debe mostrar un mensaje claro cuando la IA no este disponible.
- La actualizacion manual debe forzar una nueva generacion.

## Contenido del perfil

### Validación

Dado que el perfil se genera correctamente, cuando el frontend lo renderiza, entonces el usuario ve el tipo de perfil, el score, las etiquetas, la narrativa y los detalles de habitos y areas de mejora.

Dado que el score esta entre 0 y 100, cuando se visualiza el perfil, entonces el sistema ajusta avatar, color y barra de progreso segun el nivel obtenido.

Dado que existen etiquetas financieras, cuando se muestra el perfil, entonces el sistema las presenta como chips o tags visuales.

Dado que existen habitos positivos y areas de mejora, cuando se renderiza el panel, entonces el sistema los organiza en secciones separadas.

### Comportamiento esperado

- El score debe representar el estado financiero en una escala de 0 a 100.
- Las etiquetas deben resumir el comportamiento financiero del usuario.
- La narrativa debe explicar el perfil con lenguaje comprensible.

## Actualizacion y refresco

### Validación

Dado que el usuario crea, edita o elimina movimientos, cuando el sistema refresca el dashboard, entonces el perfil financiero se vuelve a generar para reflejar los nuevos datos.

Dado que el usuario toca la accion de actualizar, cuando el perfil se vuelve a calcular, entonces el sistema usa `force=1` para omitir la caché del dia.

Dado que la IA no puede generar el perfil, cuando ocurre un error de dependencia o disponibilidad, entonces el sistema muestra un mensaje de error sin romper la interfaz.

### Comportamiento esperado

- El perfil debe mantenerse sincronizado con los movimientos recientes.
- La regeneracion manual debe ser visible para el usuario.
- Los fallos de IA deben degradar de forma segura a un mensaje de aviso.

## Flujo resumido del usuario

1. El usuario entra al dashboard.
2. El sistema carga el perfil financiero IA.
3. Si existe caché del dia, la utiliza; si no, lo genera con IA.
4. El usuario revisa score, tags, narrativa y detalles.
5. Si presiona actualizar, el sistema fuerza una nueva version.
6. Si cambian sus movimientos, el perfil se refresca para reflejar el nuevo contexto.

## Nota de implementacion

La pantalla de perfil financiero usa `GET /api/ai/perfil` para obtener o generar el perfil y `GET /api/ai/perfil?force=1` para forzar una nueva version. El contenido se construye a partir del balance y del resumen de los ultimos 30 dias.

El comportamiento actual del modulo esta pensado para mostrar una lectura clara del estado financiero del usuario con apoyo de IA, pero sin bloquear la aplicacion si el servicio no esta disponible.