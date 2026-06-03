"""
============================================================
  REPOSITORIO DE PRESUPUESTOS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 25000: Funcionalidad - Completitud de metas financieras
    - ISO 9001: Mejora continua - Control de límites por categoría
    - ISO/IEC 12207: Proceso de Implementación
============================================================
  Gestiona presupuestos mensuales por categoría.
  Permite establecer límites de gasto y monitorear cumplimiento.
============================================================
"""

from ._connection import _get_conn, _fetch_one, _fetch_all, _execute


class MySQLPresupuestoRepository:
    """
    Repositorio de presupuestos para MySQL/MariaDB.
    [NORMA: ISO/IEC 25000 - Funcionalidad, ISO 9001 - Control de procesos]
    """

    def crear(self, usuario_id, categoria_id, monto_limite, mes):
        """
        Crea o actualiza un presupuesto para una categoría en un mes específico.
        Args:
            usuario_id:   ID del usuario
            categoria_id: ID de la categoría (None = presupuesto global)
            monto_limite: Monto máximo permitido
            mes:          Fecha del primer día del mes (ej: '2026-03-01')
        """
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO presupuestos (usuario_id, categoria_id, monto_limite, mes)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE monto_limite = VALUES(monto_limite), activo = 1
                """, (usuario_id, categoria_id, float(monto_limite), mes))
                pres_id = cur.lastrowid
            conn.commit()
            return {"id": pres_id, "monto_limite": float(monto_limite), "mes": mes}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_por_usuario(self, usuario_id, mes=None):
        """
        Lista presupuestos activos del usuario con gasto actual vs límite.
        Opcionalmente filtrado por mes.
        """
        conn = _get_conn()
        try:
            q = """
                SELECT p.id, p.categoria_id, p.monto_limite, p.mes,
                       c.nombre AS categoria_nombre, c.icono AS categoria_icono,
                       COALESCE(SUM(m.monto), 0) AS gasto_actual
                FROM presupuestos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN movimientos m ON m.usuario_id = p.usuario_id
                    AND m.tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto')
                    AND DATE_FORMAT(m.fecha, '%%Y-%%m-01') = p.mes
                    AND (p.categoria_id IS NULL OR m.categoria_id = p.categoria_id)
                WHERE p.usuario_id = %s AND p.activo = 1
            """
            params = [usuario_id]
            if mes:
                q += " AND p.mes = %s"
                params.append(mes)
            q += " GROUP BY p.id, p.categoria_id, p.monto_limite, p.mes, c.nombre, c.icono"
            q += " ORDER BY p.mes DESC, c.nombre"

            rows = _fetch_all(conn, q, params)
            for r in rows:
                r["monto_limite"] = float(r["monto_limite"])
                r["gasto_actual"] = float(r["gasto_actual"])
                r["porcentaje_usado"] = round(r["gasto_actual"] / r["monto_limite"] * 100, 1) if r["monto_limite"] > 0 else 0
                r["excedido"] = r["gasto_actual"] > r["monto_limite"]
                if hasattr(r.get("mes"), "isoformat"):
                    r["mes"] = r["mes"].isoformat()
            return rows
        finally:
            conn.close()

    def eliminar(self, presupuesto_id, usuario_id):
        """Desactiva un presupuesto (soft delete)."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE presupuestos SET activo = 0 WHERE id = %s AND usuario_id = %s",
                (presupuesto_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def verificar_exceso(self, usuario_id, categoria_id, mes):
        """
        Verifica si el usuario ha excedido su presupuesto para una categoría.
        Retorna dict con estado o None si no hay presupuesto definido.
        """
        conn = _get_conn()
        try:
            row = _fetch_one(conn, """
                SELECT p.monto_limite,
                       COALESCE(SUM(m.monto), 0) AS gasto_actual
                FROM presupuestos p
                LEFT JOIN movimientos m ON m.usuario_id = p.usuario_id
                    AND m.tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = 'gasto')
                    AND DATE_FORMAT(m.fecha, '%%Y-%%m-01') = p.mes
                    AND (p.categoria_id IS NULL OR m.categoria_id = p.categoria_id)
                WHERE p.usuario_id = %s AND p.mes = %s AND p.activo = 1
                  AND ((%s IS NULL AND p.categoria_id IS NULL) OR p.categoria_id = %s)
                GROUP BY p.monto_limite
            """, (usuario_id, mes, categoria_id, categoria_id))
            if not row:
                return None
            limite = float(row["monto_limite"])
            actual = float(row["gasto_actual"])
            return {
                "monto_limite": limite,
                "gasto_actual": actual,
                "disponible": round(limite - actual, 2),
                "porcentaje_usado": round(actual / limite * 100, 1) if limite > 0 else 0,
                "excedido": actual > limite,
            }
        finally:
            conn.close()

    def comparar_mes(self, usuario_id, mes_actual, mes_anterior, categoria_id=None):
        """Compara el gasto entre dos meses para una categoría."""
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT COALESCE(SUM(m.monto), 0) AS total "
                "FROM movimientos m "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s AND t.codigo = 'gasto' "
                "AND DATE_FORMAT(m.fecha, '%%Y-%%m-01') = %s "
                "AND (%s IS NULL OR m.categoria_id = %s)",
                (usuario_id, mes_actual, categoria_id, categoria_id),
            )
            total_actual = float(row["total"]) if row else 0.0

            row_prev = _fetch_one(
                conn,
                "SELECT COALESCE(SUM(m.monto), 0) AS total "
                "FROM movimientos m "
                "JOIN tipos_movimiento t ON m.tipo_id = t.id "
                "WHERE m.usuario_id = %s AND t.codigo = 'gasto' "
                "AND DATE_FORMAT(m.fecha, '%%Y-%%m-01') = %s "
                "AND (%s IS NULL OR m.categoria_id = %s)",
                (usuario_id, mes_anterior, categoria_id, categoria_id),
            )
            total_prev = float(row_prev["total"]) if row_prev else 0.0

            variacion = total_actual - total_prev
            variacion_pct = (
                round((variacion / total_prev) * 100, 1)
                if total_prev > 0
                else (100.0 if total_actual > 0 else 0.0)
            )

            return {
                "gasto_actual": round(total_actual, 2),
                "gasto_anterior": round(total_prev, 2),
                "variacion_monto": round(variacion, 2),
                "variacion_pct": variacion_pct,
            }
        finally:
            conn.close()
