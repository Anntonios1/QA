<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para la Historia de Usuario del Resumen del Mes e Historial de Movimientos -->
# Historia del resumen del mes y del historial de movimientos

## Objetivo

Describir la validacion funcional del resumen mensual que aparece en el Home y del historial de movimientos, usando el mismo patron de redaccion basado en condiciones, accion y resultado.

## Resumen del mes en el Home

### Validación

Dado que el usuario accede al Home, cuando el frontend solicita el resumen de los ultimos 30 dias con `GET /api/resumen?dias=30`, entonces el sistema muestra el estado financiero del periodo reciente.

Dado que el backend calcula el resumen a partir de los movimientos del usuario, cuando responde la peticion, entonces incluye `total_ingresos`, `total_gastos`, `total_movimientos`, `promedio_diario_gasto`, `proyeccion_30_dias`, `variacion_vs_anterior_pct`, `por_categoria`, `top_gastos` y `balance`.

Dado que existen movimientos registrados en el periodo, cuando se renderiza el Home, entonces el usuario ve metricas rapidas, lista de top gastos, grafico por categoria, grafico de tendencia y el resumen detallado.

Dado que no existen movimientos registrados, cuando se carga el Home, entonces el sistema oculta los componentes dependientes de datos y muestra un estado vacio.

Dado que el usuario crea, edita o elimina un movimiento, cuando el sistema actualiza la informacion, entonces el Home recarga el resumen para reflejar el cambio en ingresos, gastos, promedio, proyeccion y variacion.

### Comportamiento esperado

- Si hay datos, el Home funciona como una vista ejecutiva del mes.
- Si no hay datos, la interfaz muestra un empty state claro.
- Cada cambio sobre movimientos debe actualizar el resumen visible.

## Historial de movimientos

### Validación

Dado que el usuario entra a la seccion de movimientos, cuando el frontend solicita `GET /api/movimientos`, entonces el sistema devuelve el historial asociado a su cuenta.

Dado que el usuario aplica filtros por tipo, fecha, categoria o monto, cuando la consulta incluye esos criterios, entonces el listado se ajusta a la busqueda realizada.

Dado que el usuario usa paginacion con `page` y `page_size`, cuando existen muchos registros, entonces el historial se distribuye en paginas para no cargar todo de una vez.

Dado que el usuario visualiza el historial desde el Home, cuando la vista esta compacta, entonces el sistema muestra solo los primeros 3 movimientos y permite expandir la lista completa.

Dado que cada movimiento contiene categoria, descripcion, monto, fecha, icono y acciones, cuando se renderiza el listado, entonces el usuario puede revisar, editar o eliminar cada registro.

Dado que el usuario exporta los movimientos filtrados, cuando presiona la opcion de exportacion CSV, entonces el sistema descarga el archivo con el resultado actual.

Dado que el usuario cambia un filtro, pagina, edita o elimina un movimiento, cuando se actualiza la informacion, entonces el historial se recarga y tambien se refresca el resumen del Home.

### Comportamiento esperado

- El historial debe respetar filtros combinados.
- La paginacion debe evitar saturar la interfaz con demasiados registros.
- Cualquier accion de mantenimiento debe mantenerse sincronizada con el resumen del Home.

## Relacion entre ambos modulos

Dado que el historial muestra el detalle operativo y el resumen consolida la informacion del mismo periodo, cuando el usuario interactua con un movimiento, entonces ambos modulos deben mantenerse sincronizados.

## Flujo resumido del usuario

1. El usuario inicia sesion y entra al Home.
2. El sistema carga el resumen de los ultimos 30 dias.
3. El usuario revisa metricas, graficos y top gastos.
4. Si necesita mas detalle, abre el historial de movimientos.
5. Desde el historial puede filtrar, editar, eliminar o exportar movimientos.
6. Cada cambio actualiza tanto el historial como el resumen del Home.

## Nota de implementacion

La pantalla de Home utiliza `apiRequest("/resumen?dias=30")` para el bloque resumen y `apiRequest("/movimientos?...")` para la lista de movimientos.

El comportamiento actual del frontend esta diseñado para que la vista principal sea rapida, visual y util, sin obligar al usuario a entrar al historial completo para entender su situacion financiera.

## Reportes

### Validación

Dado que el usuario accede a la seccion de reportes, cuando selecciona el periodo diario, semanal o mensual, entonces el sistema muestra el rango correspondiente en pantalla.

Dado que el frontend solicita `GET /api/reportes/resumen?periodo=diario|semanal|mensual`, cuando el backend responde con los datos del periodo, entonces el sistema muestra ingresos, gastos y total de movimientos del reporte.

Dado que el usuario visualiza el panel de reportes, cuando existen categorias con movimientos en el periodo seleccionado, entonces el sistema muestra el top de categorias con su tendencia comparada frente al periodo anterior.

Dado que no existen categorias con movimientos en el periodo seleccionado, cuando se renderiza el listado, entonces el sistema muestra el mensaje "Sin categorías con movimientos en este periodo".

Dado que el usuario exporta el reporte, cuando presiona la opcion PDF o Excel, entonces el sistema genera el archivo con el resumen y el top de categorias.

### Comportamiento esperado

- Si el periodo es diario, semanal o mensual, el reporte debe mostrar el rango correspondiente al periodo seleccionado.
- Si el reporte tiene datos, deben verse ingresos, gastos, movimientos y categorias con tendencia.
- Si no hay categorias en el periodo seleccionado, debe mostrarse un empty state claro.
- La exportacion debe usar la informacion cargada en pantalla para mantener consistencia entre vista y archivo.
