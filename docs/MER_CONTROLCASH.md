<!-- [NORMA: IEEE 730 - Plan de Aseguramiento de Calidad] Este documento constituye el registro formal del plan de calidad del software y requerimientos de usuario -->
<!-- [NORMA: ISO/IEC 12207 - Proceso de Documentación] Documentación del ciclo de vida conforme al proceso estándar para el Modelo Entidad-Relación (MER) de ControlCash -->
# MER - ControlCash

## 1. Proposito
Este documento define el Modelo Entidad-Relacion (MER) de la aplicacion ControlCash.
El MER describe la estructura de datos que soporta la gestion de informacion para cada actor y sus funcionalidades.

## 2. Actores y gestion de datos

### Actor: Usuario final
Funcionalidades soportadas por el modelo de datos:
- Registro e inicio de sesion: `usuarios`, `refresh_tokens`
- Gestion de ingresos y gastos: `movimientos`, `categorias`
- Gestion de limites mensuales: `presupuestos`
- Programacion de operaciones recurrentes: `recurrencias`
- Recepcion y lectura de avisos: `notificaciones`
- Consulta de analisis inteligente: `perfiles_ia`, `insights_diarios`

### Actor: Sistema/API
Funcionalidades soportadas por el modelo de datos:
- Autenticacion y control de sesion: `usuarios`, `refresh_tokens`
- Persistencia transaccional de operaciones financieras: `movimientos`
- Control de integridad referencial y reglas de negocio: claves foraneas, checks e indices

### Actor: Motor IA
Funcionalidades soportadas por el modelo de datos:
- Generacion de perfiles financieros: `perfiles_ia`
- Generacion de insights diarios personalizados: `insights_diarios`
- Consumo de contexto historico del usuario: `movimientos`, `presupuestos`, `recurrencias`

## 3. Entidades principales
- `usuarios`: cuenta del usuario y estado de activacion.
- `refresh_tokens`: renovacion segura de sesiones JWT.
- `categorias`: clasificacion de movimientos por tipo.
- `movimientos`: ingresos y gastos registrados por usuario.
- `presupuestos`: limites mensuales globales o por categoria.
- `recurrencias`: transacciones programadas automaticas.
- `notificaciones`: mensajes in-app y alertas del sistema.
- `perfiles_ia`: evaluacion financiera diaria generada por IA.
- `insights_diarios`: recomendacion diaria personalizada.

## 4. Cardinalidades clave
- Un `usuario` tiene muchos `refresh_tokens`.
- Un `usuario` tiene muchos `movimientos`.
- Una `categoria` clasifica muchos `movimientos`.
- Un `usuario` tiene muchos `presupuestos`.
- Una `categoria` puede estar en muchos `presupuestos`.
- Un `usuario` tiene muchas `recurrencias`.
- Una `categoria` clasifica muchas `recurrencias`.
- Un `usuario` tiene muchas `notificaciones`.
- Un `usuario` tiene muchos `perfiles_ia`.
- Un `usuario` tiene muchos `insights_diarios`.

## 5. MER incluido (representacion textual)

### 5.1 Estructura de entidades

| Entidad | Clave primaria | Claves foraneas | Proposito funcional |
|---|---|---|---|
| usuarios | id | - | Gestion de cuentas y autenticacion del actor usuario |
| refresh_tokens | id | usuario_id -> usuarios.id | Control de sesiones y renovacion JWT |
| categorias | id | - | Catalogo para clasificar ingresos y gastos |
| movimientos | id | usuario_id -> usuarios.id; categoria_id -> categorias.id | Registro de operaciones financieras |
| presupuestos | id | usuario_id -> usuarios.id; categoria_id -> categorias.id (nullable) | Limites de gasto por mes y categoria/global |
| recurrencias | id | usuario_id -> usuarios.id; categoria_id -> categorias.id | Programacion de transacciones automaticas |
| notificaciones | id | usuario_id -> usuarios.id | Mensajeria in-app y alertas |
| perfiles_ia | id | usuario_id -> usuarios.id | Perfil financiero generado por IA |
| insights_diarios | id | usuario_id -> usuarios.id | Recomendaciones diarias personalizadas |

### 5.2 Relaciones del MER

- usuarios (1) a (N) refresh_tokens
- usuarios (1) a (N) movimientos
- categorias (1) a (N) movimientos
- usuarios (1) a (N) presupuestos
- categorias (1) a (N) presupuestos (opcional por presupuesto global)
- usuarios (1) a (N) recurrencias
- categorias (1) a (N) recurrencias
- usuarios (1) a (N) notificaciones
- usuarios (1) a (N) perfiles_ia
- usuarios (1) a (N) insights_diarios

### 5.3 Vista estructural del MER (sin notacion Mermaid)

USUARIOS
  |
  +--< REFRESH_TOKENS
  +--< MOVIMIENTOS >--+ CATEGORIAS
  +--< PRESUPUESTOS >-+
  +--< RECURRENCIAS >-+
  +--< NOTIFICACIONES
  +--< PERFILES_IA
  +--< INSIGHTS_DIARIOS

## 6. Trazabilidad con implementacion
Este MER corresponde a las tablas definidas en el script SQL de inicializacion para XAMPP/MySQL y mantiene integridad mediante claves foraneas, restricciones y reglas de dominio.
