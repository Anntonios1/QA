"""
============================================================
  REPOSITORIO DE RECURRENCIAS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Automatización de procesos
    - ISO/IEC 20000: Gestión de servicios recurrentes
============================================================
  Gestiona movimientos recurrentes (suscripciones, salarios,
  rentas). Permite programar ingresos/gastos automáticos
  con frecuencia definida.
============================================================
"""

from ._connection import _get_conn, _fetch_one, _fetch_all, _execute


class MySQLRecurrenciaRepository:
    """
    Repositorio de recurrencias para MySQL/MariaDB.
    [NORMA: ISO/IEC 12207 - Automatización, ISO/IEC 20000 - Gestión de servicios]
    """

    def crear(self, usuario_id, categoria_id, tipo, monto, descripcion,
              frecuencia, dia_ejecucion, proxima_fecha):
        """
        Crea una nueva recurrencia.
        Args:
            tipo:           'ingreso' o 'gasto'
            frecuencia:     'diario' | 'semanal' | 'quincenal' | 'mensual' | 'anual'
            dia_ejecucion:  Día del mes (1-31) o día de la semana (1-7)
            proxima_fecha:  Fecha de la próxima ejecución
        """
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO recurrencias
                        (usuario_id, categoria_id, tipo_id, monto, descripcion, frecuencia, dia_ejecucion, proxima_fecha)
                    VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, %s, %s, %s, %s)
                """, (usuario_id, categoria_id, tipo, float(monto), descripcion.strip(),
                      frecuencia, dia_ejecucion, proxima_fecha))
                rec_id = cur.lastrowid
            conn.commit()
            return {"id": rec_id, "tipo": tipo, "monto": float(monto), "frecuencia": frecuencia}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_por_usuario(self, usuario_id, solo_activas=True):
        """Lista recurrencias del usuario con datos de categoría."""
        conn = _get_conn()
        try:
            q = """
                SELECT r.id, r.categoria_id, t.codigo AS tipo, r.monto, r.descripcion,
                       r.frecuencia, r.dia_ejecucion, r.proxima_fecha, r.activo,
                       c.nombre AS categoria_nombre, c.icono AS categoria_icono
                FROM recurrencias r
                JOIN categorias c ON r.categoria_id = c.id
                JOIN tipos_movimiento t ON r.tipo_id = t.id
                WHERE r.usuario_id = %s
            """
            params = [usuario_id]
            if solo_activas:
                q += " AND r.activo = 1"
            q += " ORDER BY r.proxima_fecha ASC"
            rows = _fetch_all(conn, q, params)
            for r in rows:
                r["monto"] = float(r["monto"])
                if hasattr(r.get("proxima_fecha"), "isoformat"):
                    r["proxima_fecha"] = r["proxima_fecha"].isoformat()
            return rows
        finally:
            conn.close()

    def obtener_pendientes(self, fecha_hasta):
        """
        Obtiene todas las recurrencias activas cuya próxima fecha es <= fecha_hasta.
        Usado por un job scheduler para ejecutar movimientos automáticos.
        """
        conn = _get_conn()
        try:
            rows = _fetch_all(conn, """
                SELECT r.id, r.usuario_id, r.categoria_id, t.codigo AS tipo, r.monto, r.descripcion,
                       r.frecuencia, r.dia_ejecucion, r.proxima_fecha, r.activo, r.creado_en,
                       c.nombre AS categoria_nombre
                FROM recurrencias r
                JOIN categorias c ON r.categoria_id = c.id
                JOIN tipos_movimiento t ON r.tipo_id = t.id
                WHERE r.activo = 1 AND r.proxima_fecha <= %s
                ORDER BY r.proxima_fecha ASC
            """, (fecha_hasta,))
            for r in rows:
                r["monto"] = float(r["monto"])
                if hasattr(r.get("proxima_fecha"), "isoformat"):
                    r["proxima_fecha"] = r["proxima_fecha"].isoformat()
            return rows
        finally:
            conn.close()

    def actualizar_proxima_fecha(self, recurrencia_id, nueva_fecha):
        """Actualiza la próxima fecha de ejecución después de procesar."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE recurrencias SET proxima_fecha = %s WHERE id = %s",
                (nueva_fecha, recurrencia_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def desactivar(self, recurrencia_id, usuario_id):
        """Desactiva una recurrencia (soft delete)."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE recurrencias SET activo = 0 WHERE id = %s AND usuario_id = %s",
                (recurrencia_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def reactivar(self, recurrencia_id, usuario_id, proxima_fecha):
        """Reactiva una recurrencia con nueva fecha."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE recurrencias SET activo = 1, proxima_fecha = %s WHERE id = %s AND usuario_id = %s",
                (proxima_fecha, recurrencia_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
