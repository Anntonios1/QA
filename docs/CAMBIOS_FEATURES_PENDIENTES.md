<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para el registro de Cambios y Características Pendientes -->
# Cambios aplicados: categorias y presupuestos

## Objetivo
Completar las 2 features pendientes solicitadas en las historias de usuario:
- Administrar categorias.
- Crear y monitorear presupuestos.

## Backend (API + repositorios)
- Se agrego CRUD de categorias en la API con validaciones y soft delete.
- Se implementaron metodos de repositorio para crear, actualizar y desactivar categorias en MySQL y PostgreSQL.
- Se agrego validacion de categoria en el modulo de validadores.
- Se agrego alerta automatica de presupuesto (>= 80% o excedido) al registrar gastos, generando notificacion.

### Endpoints nuevos
- POST /api/categorias
- PUT /api/categorias/{id}
- DELETE /api/categorias/{id}

## Frontend (UI + logica)
- Seccion nueva de presupuestos con formulario (mes, monto limite, categoria opcional) y listado con progreso.
- Seccion nueva de categorias con formulario de alta/edicion y catalogo activo con acciones.
- Se actualizo la carga del dashboard para inicializar categorias y presupuestos.
- Se refrescan presupuestos al crear/editar/eliminar movimientos (incluyendo OCR).

## Notas de uso
- Presupuestos: si ya existe un presupuesto para el mismo mes y categoria, el POST lo actualiza.
- Categorias: la desactivacion es logica (soft delete) y no borra movimientos existentes.

## Verificacion rapida sugerida
1. Crear una categoria nueva y verificar que aparece en filtros y en presupuestos.
2. Crear un presupuesto para una categoria y registrar un gasto para ver el progreso.
3. Desactivar la categoria y confirmar que deja de aparecer en selects.

## Menu interactivo de mejoras (producto + UX + tecnica)
Estas mejoras quedan organizadas en formato de menu interactivo para mantener la pagina limpia.

<details>
<summary><strong>Presupuestos</strong> - alertas, comparativos y progreso</summary>

- Alertas visuales y push al 80% y al exceder presupuesto.
- Comparativo mes vs mes (consumo y variacion).
- Presupuesto global vs por categoria con barras de progreso por seccion.

**Implementacion**
- Backend: eventos de alerta + endpoint de comparativos.
- Frontend: barras de progreso y panel comparativo.
- Datos: agregar campos de umbral y periodo de comparacion.

</details>

<details>
<summary><strong>Categorias</strong> - scope por usuario e iconos</summary>

- Categorias con scope por usuario (no global).
- Selector de icono en el alta/edicion.
- Validacion de duplicados en UI (case-insensitive).
- Contador de uso para decidir desactivar.

**Implementacion**
- Backend: filtrar por usuario y agregar conteo de uso.
- Frontend: selector de iconos y validaciones en formulario.

</details>

<details>
<summary><strong>Reportes</strong> - periodos y exportacion</summary>

- Selector de periodo diario / semanal / mensual.
- Exportar a PDF y Excel.
- Resumen de top categorias con tendencias.

**Implementacion**
- Backend: endpoints de reporte con agregaciones por periodo.
- Frontend: tabla y tarjetas con tendencia.
- Exportacion: generacion server-side o descarga client-side.

</details>

<details>
<summary><strong>Automatizaciones</strong> - recurrencias completas</summary>

- Recurrencias completas: crear, pausar y ejecutar.
- Job diario real para insight y resumen de 24h.

**Implementacion**
- Backend: scheduler diario y cola de ejecucion.
- Frontend: panel de estado y acciones de control.

</details>

<details>
<summary><strong>Seguridad</strong> - sesiones y 2FA</summary>

- Sesiones por dispositivo.
- Revocar sesiones activas.
- Opcion de 2FA o passkeys.

**Implementacion**
- Backend: tabla de sesiones y revocacion.
- Frontend: vista de dispositivos y control de sesiones.

</details>

<details>
<summary><strong>UX y accesibilidad</strong> - onboarding y performance</summary>

- Onboarding rapido.
- Empty states con CTA.
- Atajos de teclado.
- Paginacion en movimientos para mejorar performance.

**Implementacion**
- Frontend: flujos guiados y shortcuts.
- Backend: paginacion en endpoints de movimientos.

</details>

# Sincronización Versión 1.1 (1:1 Frontend/Backend)
- Sincronización completa de la base de código frontend y backend para incluir monedas (COP/USD), OCR (Gemini), notificaciones, descripciones de categorías.
- Ajuste y rescritura de las 13 historias de usuario para reflejar 1:1 el frontend.
- Documentación (MER, Quality, dbml, matrices de calidad) elevada a Versión 1.1.
