"""
============================================================
  REPOSITORIO DE MOVIMIENTOS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Proceso de Implementación
    - ISO 9001:2000: Trazabilidad de registros financieros
    - CMMI Nivel 3: Proceso estándar implementado
    - ISO/IEC 25000: Completitud funcional
============================================================

  BUG CORREGIDO (2026-05-28):
    MySQLMovimientoRepository.actualizar() — el conn.commit()
    estaba ubicado DESPUÉS del return, convirtiéndolo en código
    muerto (dead code). El UPDATE se ejecutaba pero nunca se
    confirmaba, causando rollback implícito al cerrar la conexión.
    Solución: mover conn.commit() ANTES del return dentro del
    bloque with, garantizando que la transacción se persista.
============================================================
"""

from datetime import datetime, timedelta

from ..base_repository import BaseMovimientoRepository
from ._connection import _get_conn, _fetch_one, _fetch_all, _execute


# [NORMA: ISO/IEC 12207 - Proceso de Implementación] Repositorio de movimientos bajo patrón Repository
# [NORMA: ISO 9001:2000 - Enfoque basado en procesos] Proceso estandarizado para persistencia de movimientos
class MySQLMovimientoRepository(BaseMovimientoRepository):
    """
    Repositorio de movimientos financieros para MySQL/MariaDB.
    Gestiona creación, listado, edición y eliminación de movimientos.
    """

    def crear(self, usuario_id, categoria_id, tipo, monto, descripcion="", fecha=None):
        """
        Registra un nuevo movimiento financiero.
        Retorna dict con id, tipo y monto del movimiento creado.
        """
        conn = _get_conn()
        try:
            if fecha is None:
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO movimientos (usuario_id, categoria_id, tipo_id, monto, descripcion, fecha) "
                    "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, %s, %s)",
                    (usuario_id, categoria_id, tipo, float(monto), descripcion.strip(), fecha),
                )
                mov_id = cur.lastrowid
            conn.commit()
            return {"id": mov_id, "tipo": tipo, "monto": float(monto)}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_por_usuario(
        self,
        usuario_id,
        limite=50,
        offset=0,
        tipo=None,
        fecha_desde=None,
        fecha_hasta=None,
        categoria_id=None,
        monto_min=None,
        monto_max=None,
    ):
        """
        Lista movimientos del usuario con filtros y paginación opcionales.
        Retorna lista de dicts con datos completos incluyendo nombre e icono de categoría.
        """
        conn = _get_conn()
        try:
            q = (
                "SELECT m.id, m.usuario_id, t.codigo AS tipo, m.monto, m.descripcion, m.fecha, "
                "m.fecha_registro, m.categoria_id, "
                "c.nombre AS categoria_nombre, c.icono AS categoria_icono "
                "FROM movimientos m "
                "JOIN categorias c ON m.categoria_id = c.id "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s"
            )
            p = [usuario_id]
            if tipo:
                q += " AND t.codigo = %s"
                p.append(tipo)
            if fecha_desde:
                q += " AND m.fecha >= %s"
                p.append(fecha_desde)
            if fecha_hasta:
                q += " AND m.fecha <= %s"
                p.append(fecha_hasta)
            if categoria_id is not None:
                q += " AND m.categoria_id = %s"
                p.append(int(categoria_id))
            if monto_min is not None:
                q += " AND m.monto >= %s"
                p.append(float(monto_min))
            if monto_max is not None:
                q += " AND m.monto <= %s"
                p.append(float(monto_max))
            q += " ORDER BY m.fecha DESC LIMIT %s"
            p.append(limite)
            if offset:
                q += " OFFSET %s"
                p.append(offset)
            rows = _fetch_all(conn, q, p)
            for r in rows:
                r["monto"] = float(r["monto"])
                if hasattr(r.get("fecha"), "isoformat"):
                    r["fecha"] = r["fecha"].isoformat()
                if hasattr(r.get("fecha_registro"), "isoformat"):
                    r["fecha_registro"] = r["fecha_registro"].isoformat()
            return rows
        finally:
            conn.close()

    def contar_por_usuario(
        self,
        usuario_id,
        tipo=None,
        fecha_desde=None,
        fecha_hasta=None,
        categoria_id=None,
        monto_min=None,
        monto_max=None,
    ):
        """
        Cuenta movimientos del usuario con filtros opcionales.
        Usado para calcular total de páginas en paginación.
        """
        conn = _get_conn()
        try:
            q = (
                "SELECT COUNT(*) AS total "
                "FROM movimientos m "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s"
            )
            p = [usuario_id]
            if tipo:
                q += " AND t.codigo = %s"
                p.append(tipo)
            if fecha_desde:
                q += " AND m.fecha >= %s"
                p.append(fecha_desde)
            if fecha_hasta:
                q += " AND m.fecha <= %s"
                p.append(fecha_hasta)
            if categoria_id is not None:
                q += " AND m.categoria_id = %s"
                p.append(int(categoria_id))
            if monto_min is not None:
                q += " AND m.monto >= %s"
                p.append(float(monto_min))
            if monto_max is not None:
                q += " AND m.monto <= %s"
                p.append(float(monto_max))
            row = _fetch_one(conn, q, p)
            return int(row["total"]) if row else 0
        finally:
            conn.close()

    def eliminar(self, movimiento_id, usuario_id):
        """Elimina un movimiento verificando que pertenezca al usuario."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "DELETE FROM movimientos WHERE id = %s AND usuario_id = %s",
                (movimiento_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def actualizar(self, movimiento_id, usuario_id, categoria_id=None, tipo=None,
                   monto=None, descripcion=None, fecha=None):
        """
        Actualiza campos del movimiento. Solo actualiza los campos que no sean None.
        Retorna dict con datos actualizados o None si no se encontró el movimiento.

        CORRECCIÓN DE BUG (2026-05-28):
        El commit() estaba ubicado después del return (código muerto).
        Ahora se llama ANTES del return, dentro del bloque with,
        para garantizar que la transacción se persista en MariaDB.
        [NORMA: ISO 9001 - Trazabilidad de modificaciones]
        """
        conn = None
        try:
            conn = _get_conn()
            sets, params = [], []
            if categoria_id is not None:
                sets.append("categoria_id = %s")
                params.append(int(categoria_id))
            if tipo is not None:
                sets.append("tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = %s)")
                params.append(tipo)
            if monto is not None:
                sets.append("monto = %s")
                params.append(float(monto))
            if descripcion is not None:
                sets.append("descripcion = %s")
                params.append(descripcion.strip())
            if fecha is not None:
                sets.append("fecha = %s")
                params.append(fecha)

            if not sets:
                return None

            params += [movimiento_id, usuario_id]
            q = (
                "UPDATE movimientos SET " + ", ".join(sets) +
                " WHERE id = %s AND usuario_id = %s"
            )

            with conn.cursor() as cur:
                cur.execute(q, params)
                if cur.rowcount > 0:
                    # ✅ BUG FIX: commit() ANTES del SELECT y return
                    # Antes estaba después del bloque with (dead code)
                    conn.commit()
                    cur.execute(
                        "SELECT m.id, t.codigo AS tipo, m.monto, m.descripcion, "
                        "m.fecha, m.categoria_id "
                        "FROM movimientos m "
                        "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                        "WHERE m.id = %s",
                        (movimiento_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        result = dict(row)
                        result["monto"] = float(result["monto"])
                        if hasattr(result.get("fecha"), "isoformat"):
                            result["fecha"] = result["fecha"].isoformat()
                        return result

            # rowcount == 0: movimiento no encontrado o no pertenece al usuario
            conn.commit()
            return None
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def obtener_balance(self, usuario_id):
        """Calcula el balance financiero total del usuario."""
        conn = _get_conn()
        try:
            row = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN t.codigo = 'ingreso' THEN m.monto ELSE 0 END), 0) AS total_ingresos,
                    COALESCE(SUM(CASE WHEN t.codigo = 'gasto' THEN m.monto ELSE 0 END), 0) AS total_gastos,
                    COUNT(*) AS total_movimientos
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s
            """, (usuario_id,))
            ing = float(row["total_ingresos"]) if row else 0.0
            gas = float(row["total_gastos"]) if row else 0.0
            tot = int(row["total_movimientos"]) if row else 0
            return {
                "total_ingresos": round(ing, 2),
                "total_gastos": round(gas, 2),
                "balance": round(ing - gas, 2),
                "total_movimientos": tot,
            }
        finally:
            conn.close()

    def obtener_resumen_24h(self, usuario_id):
        """Resumen de movimientos de las últimas 24 horas."""
        conn = _get_conn()
        try:
            limite = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            row = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN t.codigo = 'ingreso' THEN m.monto ELSE 0 END), 0) AS total_ingresos,
                    COALESCE(SUM(CASE WHEN t.codigo = 'gasto' THEN m.monto ELSE 0 END), 0) AS total_gastos,
                    COUNT(*) AS total_movimientos
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
            """, (usuario_id, limite))
            ing = float(row["total_ingresos"]) if row else 0.0
            gas = float(row["total_gastos"]) if row else 0.0
            tot = int(row["total_movimientos"]) if row else 0
            return {
                "total_ingresos": round(ing, 2),
                "total_gastos": round(gas, 2),
                "total_movimientos": tot,
            }
        finally:
            conn.close()

    def obtener_resumen(self, usuario_id, dias=30):
        """
        Genera resumen financiero por categoría para los últimos N días.
        Incluye totales, comparación vs período anterior, diario y top gastos.
        [NORMA: ISO 14598 - Evaluación del producto - Reportes]
        """
        conn = _get_conn()
        try:
            fi = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
            fi_prev = (datetime.now() - timedelta(days=dias * 2)).strftime("%Y-%m-%d")

            cats = _fetch_all(conn, """
                SELECT c.nombre, c.icono, t.codigo AS tipo, SUM(m.monto) AS total, COUNT(*) AS cantidad
                FROM movimientos m
                JOIN categorias c ON m.categoria_id = c.id
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
                GROUP BY c.nombre, c.icono, t.codigo ORDER BY total DESC
            """, (usuario_id, fi))

            totales = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN t.codigo = 'ingreso' THEN m.monto ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN t.codigo = 'gasto' THEN m.monto ELSE 0 END), 0) AS gastos,
                    COUNT(*) AS movimientos
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
            """, (usuario_id, fi))

            prev = _fetch_one(conn, """
                SELECT
                    COALESCE(SUM(CASE WHEN t.codigo = 'ingreso' THEN m.monto ELSE 0 END), 0) AS ingresos,
                    COALESCE(SUM(CASE WHEN t.codigo = 'gasto' THEN m.monto ELSE 0 END), 0) AS gastos
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s AND m.fecha < %s
            """, (usuario_id, fi_prev, fi))

            diario = _fetch_all(conn, """
                SELECT DATE(m.fecha) AS dia, t.codigo AS tipo, SUM(m.monto) AS total
                FROM movimientos m
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND m.fecha >= %s
                GROUP BY DATE(m.fecha), t.codigo ORDER BY dia
            """, (usuario_id, fi))

            top3 = _fetch_all(conn, """
                SELECT m.monto, m.descripcion, m.fecha, c.nombre AS categoria, c.icono
                FROM movimientos m
                JOIN categorias c ON m.categoria_id = c.id
                JOIN tipos_movimiento t ON m.tipo_id = t.id
                WHERE m.usuario_id = %s AND t.codigo = 'gasto' AND m.fecha >= %s
                ORDER BY m.monto DESC LIMIT 3
            """, (usuario_id, fi))

            gastos_actual = float(totales["gastos"]) if totales else 0.0
            gastos_prev = float(prev["gastos"]) if prev else 0.0
            ingresos_actual = float(totales["ingresos"]) if totales else 0.0
            total_mov = int(totales["movimientos"]) if totales else 0

            for c in cats:
                c["total"] = float(c["total"])
                ref = gastos_actual if c["tipo"] == "gasto" else ingresos_actual
                c["porcentaje"] = round(c["total"] / ref * 100, 1) if ref > 0 else 0

            for d in diario:
                d["total"] = float(d["total"])
                d["dia"] = str(d["dia"])

            for t in top3:
                t["monto"] = float(t["monto"])
                if hasattr(t.get("fecha"), "isoformat"):
                    t["fecha"] = t["fecha"].isoformat()

            promedio_diario = round(gastos_actual / max(dias, 1), 2)
            proyeccion_30 = round(promedio_diario * 30, 2)

            if gastos_prev > 0:
                variacion_pct = round((gastos_actual - gastos_prev) / gastos_prev * 100, 1)
            else:
                variacion_pct = 100.0 if gastos_actual > 0 else 0.0

            return {
                "periodo_dias": dias,
                "fecha_inicio": fi,
                "total_ingresos": round(ingresos_actual, 2),
                "total_gastos": round(gastos_actual, 2),
                "total_movimientos": total_mov,
                "promedio_diario_gasto": promedio_diario,
                "proyeccion_30_dias": proyeccion_30,
                "variacion_vs_anterior_pct": variacion_pct,
                "por_categoria": cats,
                "top_gastos": top3,
                "diario": diario,
            }
        finally:
            conn.close()

    def obtener_reporte_periodo(self, usuario_id, fecha_desde, fecha_hasta):
        """Genera reporte de movimientos entre dos fechas."""
        conn = _get_conn()
        try:
            totales_raw = _fetch_all(
                conn,
                "SELECT t.codigo AS tipo, COALESCE(SUM(m.monto), 0) AS total, COUNT(*) AS movimientos "
                "FROM movimientos m "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s AND m.fecha >= %s AND m.fecha <= %s "
                "GROUP BY t.codigo",
                (usuario_id, fecha_desde, fecha_hasta),
            )

            ingresos = 0.0
            gastos = 0.0
            total_mov = 0
            for row in totales_raw:
                if row["tipo"] == "ingreso":
                    ingresos = float(row["total"])
                elif row["tipo"] == "gasto":
                    gastos = float(row["total"])
                total_mov += int(row["movimientos"] or 0)

            categorias = _fetch_all(
                conn,
                "SELECT c.id AS categoria_id, c.nombre, c.icono, COALESCE(SUM(m.monto), 0) AS total "
                "FROM movimientos m "
                "JOIN categorias c ON m.categoria_id = c.id "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s AND t.codigo = 'gasto' AND m.fecha >= %s AND m.fecha <= %s "
                "GROUP BY c.id, c.nombre, c.icono "
                "ORDER BY total DESC",
                (usuario_id, fecha_desde, fecha_hasta),
            )

            for c in categorias:
                c["total"] = float(c["total"])

            return {
                "totales": {
                    "ingresos": round(ingresos, 2),
                    "gastos": round(gastos, 2),
                    "movimientos": int(total_mov),
                },
                "categorias": categorias,
            }
        finally:
            conn.close()
