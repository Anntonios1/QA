<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para la Historia de Usuario de Notificaciones -->
# Historia de notificaciones

## Objetivo

Describir la validacion funcional del modulo de notificaciones, incluyendo el panel de notificaciones, las alertas automaticas del sistema y las notificaciones nativas del navegador.

## Panel de notificaciones

### Validación

Dado que el usuario abre el panel de notificaciones, cuando el frontend solicita `GET /api/notificaciones?no_leidas=true`, entonces el sistema devuelve las notificaciones no leidas del usuario.

Dado que existen notificaciones no leidas, cuando se renderiza el panel, entonces el sistema muestra el contador, el titulo, el mensaje y la fecha de cada notificacion.

Dado que no existen notificaciones nuevas, cuando se renderiza el panel, entonces el sistema muestra el mensaje "Sin notificaciones nuevas".

Dado que el usuario hace clic en una notificacion, cuando el frontend ejecuta `PUT /api/notificaciones/{id}`, entonces el sistema la marca como leida y actualiza el contador.

Dado que el usuario abre y cierra el panel, cuando hace clic fuera del area de notificaciones, entonces el sistema lo oculta.

### Comportamiento esperado

- El contador solo debe mostrar notificaciones no leidas.
- El panel debe actualizarse despues de marcar una notificacion como leida.
- La vista vacia debe aparecer cuando no existan notificaciones pendientes.

## Alertas automaticas del sistema

### Validación

Dado que el usuario registra un gasto importante, cuando el monto es igual o superior al umbral definido por el sistema, entonces se crea una notificacion de alerta.

Dado que el usuario registra un gasto que alcanza el 80% de un presupuesto, cuando se revisa el estado del presupuesto, entonces el sistema crea una notificacion de cercania al limite.

Dado que el usuario registra un gasto que supera el monto limite, cuando el presupuesto se excede, entonces el sistema crea una notificacion de presupuesto excedido.

Dado que el usuario consulta el insight diario, cuando se genera el analisis del dia, entonces el sistema crea una notificacion informativa con el resumen financiero diario.

### Comportamiento esperado

- Las alertas deben generarse automaticamente desde los eventos del sistema.
- El usuario debe poder distinguir entre alertas, informacion y avisos de presupuesto.
- Las notificaciones deben mantenerse consistentes con el movimiento que las origino.

## Notificaciones nativas

### Validación

Dado que el navegador soporta notificaciones nativas, cuando el usuario concede permisos, entonces el sistema puede mostrar avisos emergentes.

Dado que el usuario ya concedio permisos, cuando llegan notificaciones nuevas, entonces el sistema muestra una notificacion nativa sin duplicar las ya vistas.

Dado que una notificacion nativa ya fue mostrada, cuando el sistema vuelve a consultar el panel, entonces no la vuelve a emitir.

Dado que el usuario no concede permisos, cuando el sistema intenta habilitar notificaciones nativas, entonces la funcion permanece desactivada.

### Comportamiento esperado

- Las notificaciones nativas solo deben mostrarse si el navegador lo permite.
- El sistema debe evitar duplicados mediante control local de notificaciones vistas.
- El usuario debe seguir viendo el panel web aunque no permita notificaciones nativas.

## Flujo resumido del usuario

1. El usuario entra al dashboard.
2. El sistema carga las notificaciones no leidas.
3. El usuario revisa el panel y marca una notificacion como leida.
4. Si ocurre una alerta de gasto, presupuesto o insight diario, el sistema la registra como nueva notificacion.
5. Si el navegador tiene permiso, el sistema tambien muestra el aviso nativo.

## Nota de implementacion

La pantalla de notificaciones usa `GET /api/notificaciones?no_leidas=true` para listar y `PUT /api/notificaciones/{id}` para marcar como leida. Las notificaciones del sistema se generan desde eventos de gasto importante, alertas de presupuesto e insights diarios.

El comportamiento actual del modulo esta pensado para que el usuario reciba avisos claros y rapidos sin perder el control del historial de notificaciones.