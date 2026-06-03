"""
============================================================
  REPOSITORIO DE INSIGHTS DIARIOS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Proceso de Implementación
    - ISO/IEC 20000: Gestión de comunicación
============================================================
  Registra si el usuario ya recibió su insight diario.
  Evita duplicar notificaciones push en el mismo día.
============================================================
"""

from ._connection import _get_conn, _fetch_one


class MySQLInsightDiarioRepository:
    """
    Repositorio de insights diarios para MySQL/MariaDB.
    Controla el envío de insights (tipo Duolingo) una vez por día.
    [NORMA: ISO/IEC 20000 - Gestión de Comunicación]
    """

    def ya_enviado_hoy(self, usuario_id):
        """
        Retorna True si ya se generó un insight para el usuario hoy.
        Previene duplicados de notificaciones push diarias.
        """
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT id FROM insights_diarios WHERE usuario_id = %s AND fecha = CURDATE()",
                (usuario_id,),
            )
            return row is not None
        finally:
            conn.close()

    def marcar_enviado(self, usuario_id, mensaje):
        """Registra que el insight fue enviado hoy (UPSERT)."""
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO insights_diarios (usuario_id, fecha, enviado, mensaje)
                    VALUES (%s, CURDATE(), 1, %s)
                    ON DUPLICATE KEY UPDATE enviado = 1, mensaje = VALUES(mensaje)
                """, (usuario_id, mensaje))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
