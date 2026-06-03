<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para la Historia de Usuario de Presupuestos -->
# Historia de presupuestos

## Objetivo

Describir la validacion funcional del modulo de presupuestos, incluyendo la creacion, el listado, el comparativo y las alertas por consumo.

## Presupuestos

### Validación

Dado que el usuario accede a la seccion de presupuestos, cuando el sistema inicializa el formulario con el mes actual, entonces el usuario puede registrar o consultar presupuestos del periodo seleccionado.

Dado que el usuario ingresa un monto limite mayor a cero, cuando completa el formulario de presupuesto, entonces el sistema guarda el presupuesto mensual.

Dado que el usuario selecciona una categoria, cuando guarda el presupuesto, entonces el sistema crea un presupuesto por categoria para ese mes.

Dado que el usuario no selecciona categoria, cuando guarda el presupuesto, entonces el sistema crea un presupuesto global del mes.

Dado que el usuario cambia el filtro de mes, cuando consulta la lista de presupuestos, entonces el sistema muestra los presupuestos correspondientes a ese mes.

Dado que no existen presupuestos definidos, cuando se renderiza la lista, entonces el sistema muestra el mensaje "Sin presupuestos definidos".

Dado que existen presupuestos globales y por categoria, cuando se renderiza el listado, entonces el sistema los separa en sus respectivas secciones.

### Comportamiento esperado

- El presupuesto debe guardarse por mes.
- El presupuesto puede ser global o por categoria.
- El formulario debe rechazar montos vacios, invalidos o menores o iguales a cero.
- El listado debe reflejar el mes seleccionado por el usuario.

## Monitoreo del consumo

### Validación

Dado que el usuario visualiza un presupuesto, cuando el sistema calcula el gasto actual frente al limite, entonces muestra el porcentaje usado.

Dado que el consumo alcanza el 80% del limite, cuando se actualiza el presupuesto en pantalla, entonces el sistema marca el estado como alerta.

Dado que el consumo supera el 100% del limite, cuando se actualiza el presupuesto en pantalla, entonces el sistema marca el estado como excedido.

Dado que el presupuesto se encuentra dentro del rango permitido, cuando se renderiza la tarjeta, entonces el sistema lo muestra como en rango.

Dado que el usuario revisa un presupuesto por categoria o global, cuando se muestran los valores, entonces ve el gasto actual y el monto limite en la misma tarjeta.

### Comportamiento esperado

- Cada presupuesto debe mostrar gasto actual, limite y porcentaje usado.
- El estado visual debe cambiar segun el nivel de consumo.
- El usuario debe poder identificar rapidamente si esta cerca del limite o si ya lo excedio.

## Comparativo de presupuestos

### Validación

Dado que el usuario selecciona un mes y una categoria opcional, cuando consulta el comparativo, entonces el sistema muestra el gasto actual, el gasto anterior y la variacion.

Dado que el usuario no selecciona categoria, cuando consulta el comparativo, entonces el sistema muestra la variacion del periodo para el mes completo.

Dado que existe variacion positiva, cuando se renderiza el comparativo, entonces el sistema la muestra como aumento.

Dado que existe variacion negativa, cuando se renderiza el comparativo, entonces el sistema la muestra como disminucion.

Dado que el usuario cambia el filtro de mes o categoria, cuando el comparativo se vuelve a cargar, entonces la informacion se actualiza en pantalla.

### Comportamiento esperado

- El comparativo debe operar por mes.
- El usuario puede comparar el mes seleccionado con el anterior.
- La categoria es opcional para afinar el analisis.

## Alertas de presupuesto

### Validación

Dado que el usuario registra un nuevo movimiento de gasto, cuando el sistema revisa el estado del presupuesto, entonces valida si el consumo supera el 80% o si ya fue excedido.

Dado que un presupuesto alcanza el 80% o mas, cuando se registra el movimiento, entonces el sistema genera una alerta de cercania al limite.

Dado que un presupuesto supera el monto limite, cuando se registra el movimiento, entonces el sistema genera una alerta de presupuesto excedido.

Dado que la alerta corresponde a una categoria especifica, cuando se emite la notificacion, entonces el sistema informa el nombre de la categoria afectada.

Dado que la alerta corresponde al presupuesto global, cuando se emite la notificacion, entonces el sistema informa que el limite del mes completo fue alcanzado o superado.

### Comportamiento esperado

- Las alertas deben dispararse al registrar gastos nuevos.
- El sistema debe diferenciar entre presupuesto por categoria y presupuesto global.
- El usuario debe recibir un mensaje claro sobre el estado del presupuesto.

## Eliminacion de presupuestos

### Validación

Dado que el usuario decide eliminar un presupuesto, cuando confirma la accion, entonces el sistema lo desactiva.

Dado que un presupuesto fue eliminado, cuando se vuelve a cargar la lista, entonces ya no debe aparecer como activo.

### Comportamiento esperado

- La eliminacion debe ser logica para conservar el historial.
- La lista debe actualizarse despues de eliminar un presupuesto.

## Flujo resumido del usuario

1. El usuario entra a presupuestos.
2. Selecciona el mes actual o un mes especifico.
3. Crea un presupuesto global o por categoria.
4. Revisa el porcentaje usado y el estado visual.
5. Consulta el comparativo del mes.
6. Si registra nuevos gastos, el sistema emite alertas si el presupuesto llega al 80% o lo excede.
7. Si elimina un presupuesto, la lista se actualiza inmediatamente.

## Nota de implementacion

La pantalla de presupuestos usa `GET /api/presupuestos?mes=YYYY-MM-01` para listar, `POST /api/presupuestos` para crear o actualizar, `DELETE /api/presupuestos/{id}` para desactivar y `GET /api/presupuestos/comparativo` para comparar el periodo con el mes anterior.

El comportamiento actual del modulo esta pensado para que el usuario pueda controlar sus metas financieras mensuales de forma rapida, visual y con alertas claras cuando el consumo se acerca o supera el limite.