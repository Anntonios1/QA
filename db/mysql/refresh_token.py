"""
============================================================
  REPOSITORIO DE REFRESH TOKENS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 27001: Gestión de tokens de sesión
    - ISO/IEC 12207: Proceso de Implementación
============================================================
  Gestiona refresh tokens para autenticación JWT.
  Permite revocar tokens individuales o todos los del usuario.
============================================================
"""

from ._connection import _get_conn, _fetch_one, _execute


class MySQLRefreshTokenRepository:
    """
    Repositorio de refresh tokens para MySQL/MariaDB.
    [NORMA: ISO/IEC 27001 - Gestión de tokens de sesión]
    """

    def guardar(self, usuario_id, token_hash, expires_at, device_info=None):
        """Almacena un nuevo refresh token en la base de datos."""
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO refresh_tokens (usuario_id, token_hash, expires_at, device_info) "
                    "VALUES (%s, %s, %s, %s)",
                    (usuario_id, token_hash, expires_at, device_info),
                )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def verificar(self, token_hash):
        """
        Verifica si un refresh token es válido (existe, no expirado, no revocado).
        Retorna dict con usuario_id y expires_at, o None.
        [NORMA: ISO/IEC 27001 - Control A.9.4.2] Gestión de sesiones seguras
        """
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT usuario_id, expires_at FROM refresh_tokens "
                "WHERE token_hash = %s AND revoked = 0 AND expires_at > UTC_TIMESTAMP()",
                (token_hash,),
            )
            return row
        finally:
            conn.close()

    def revocar(self, token_hash):
        """Revoca un refresh token específico."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = %s",
                (token_hash,),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def revocar_todos(self, usuario_id):
        """Revoca todos los refresh tokens de un usuario (logout global)."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE refresh_tokens SET revoked = 1 WHERE usuario_id = %s",
                (usuario_id,),
            )
            conn.commit()
            return rc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def limpiar_expirados(self):
        """Elimina tokens expirados de la base de datos."""
        conn = _get_conn()
        try:
            rc = _execute(conn, "DELETE FROM refresh_tokens WHERE expires_at < UTC_TIMESTAMP()")
            conn.commit()
            return rc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
