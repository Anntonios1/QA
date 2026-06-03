"""
============================================================
  REPOSITORIO DE NOTIFICACIONES — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Proceso de Implementación
    - ISO/IEC 20000: Gestión de comunicación
    - CMMI Nivel 3: Proceso estándar implementado
============================================================
"""

from ..base_repository import BaseNotificacionRepository
from ._connection import _get_conn, _fetch_one, _fetch_all, _execute


class MySQLNotificacionRepository(BaseNotificacionRepository):
    """
    Repositorio de notificaciones para MySQL/MariaDB.
    Gestiona creación, listado y marcado de notificaciones.
    [NORMA: ISO/IEC 20000 - Gestión de Comunicación]
    """

    def crear(self, usuario_id, titulo, mensaje, tipo="info"):
        """
        Crea una nueva notificación para el usuario.
        Retorna dict con el id de la notificación creada.
        """
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO notificaciones (usuario_id, titulo, mensaje, tipo) VALUES (%s, %s, %s, %s)",
                    (usuario_id, titulo.strip(), mensaje.strip(), tipo),
                )
                notif_id = cur.lastrowid
            conn.commit()
            return {"id": notif_id}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar_por_usuario(self, usuario_id, solo_no_leidas=False):
        """
        Lista notificaciones del usuario ordenadas por fecha descendente.
        Opcionalmente filtra solo las no leídas.
        """
        conn = _get_conn()
        try:
            q = "SELECT * FROM notificaciones WHERE usuario_id = %s"
            p = [usuario_id]
            if solo_no_leidas:
                q += " AND leida = 0"
            q += " ORDER BY fecha DESC LIMIT 50"
            rows = _fetch_all(conn, q, p)
            for r in rows:
                if hasattr(r.get("fecha"), "isoformat"):
                    r["fecha"] = r["fecha"].isoformat()
            return rows
        finally:
            conn.close()

    def marcar_leida(self, notificacion_id, usuario_id):
        """Marca una notificación como leída. Retorna True si se actualizó."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE notificaciones SET leida = 1 WHERE id = %s AND usuario_id = %s",
                (notificacion_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def contar_no_leidas(self, usuario_id):
        """Retorna el número de notificaciones no leídas del usuario."""
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT COUNT(*) AS total FROM notificaciones WHERE usuario_id = %s AND leida = 0",
                (usuario_id,),
            )
            return int(row["total"]) if row else 0
        finally:
            conn.close()
