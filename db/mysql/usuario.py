"""
============================================================
  REPOSITORIO DE USUARIOS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Proceso de Implementación
    - ISO 9001:2000: Enfoque basado en procesos
    - ISO/IEC 27001: Seguridad - Gestión de contraseñas
    - CMMI Nivel 3: Proceso estándar implementado
============================================================
"""

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None

from ..base_repository import BaseUsuarioRepository, PasswordMixin
from ._connection import _get_conn, _fetch_one, _fetch_all, _execute


# [NORMA: ISO/IEC 12207 - Proceso de Implementación] Implementación del repositorio de usuarios
# [NORMA: ISO 9001:2000 - Enfoque basado en procesos] Proceso estandarizado para persistencia de datos de usuario
class MySQLUsuarioRepository(BaseUsuarioRepository, PasswordMixin):
    """
    Repositorio de usuarios para MySQL/MariaDB.
    Gestiona registro, autenticación y actualización de perfil.
    """

    def crear(self, nombre, email, password, moneda="COP"):
        """
        Registra un nuevo usuario.
        Retorna dict con datos del usuario o None si el email ya existe.
        [NORMA: ISO/IEC 27001 - Control A.9.2.1] Registro y gestión de identidades de usuario
        """
        conn = _get_conn()
        try:
            pw_hash, _ = self.hash_password(password)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (nombre, email, password_hash, moneda) VALUES (%s, %s, %s, %s)",
                    (nombre.strip(), email.strip().lower(), pw_hash, moneda),
                )
                usuario_id = cur.lastrowid
            conn.commit()
            return {
                "id": usuario_id,
                "nombre": nombre.strip(),
                "email": email.strip().lower(),
                "moneda": moneda,
            }
        except pymysql.err.IntegrityError:
            conn.rollback()
            return None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def autenticar(self, email, password):
        """
        Autentica al usuario verificando email y contraseña.
        Retorna dict con datos del usuario o None si las credenciales son incorrectas.
        [NORMA: OWASP Mobile Top 10 - M4] Autenticación segura con verificación de hash
        """
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT id, nombre, email, moneda, password_hash, activo FROM usuarios "
                "WHERE email = %s AND activo = 1",
                (email.strip().lower(),),
            )
            if row and self.verify_password(password, row["password_hash"]):
                return row
            return None
        finally:
            conn.close()

    def obtener_por_id(self, usuario_id):
        """
        Obtiene un usuario por su ID.
        Retorna dict o None si no existe.
        """
        conn = _get_conn()
        try:
            return _fetch_one(
                conn,
                "SELECT id, nombre, email, moneda, fecha_creacion, activo FROM usuarios WHERE id = %s",
                (usuario_id,),
            )
        finally:
            conn.close()

    def listar_ids_activos(self):
        """Lista los IDs de todos los usuarios activos."""
        conn = _get_conn()
        try:
            rows = _fetch_all(conn, "SELECT id FROM usuarios WHERE activo = 1")
            return [int(r["id"]) for r in rows]
        finally:
            conn.close()

    def actualizar_perfil(self, usuario_id, nombre=None, moneda=None):
        """
        Actualiza nombre y/o moneda del usuario.
        Retorna dict con datos actualizados o None si no existe.
        """
        conn = _get_conn()
        try:
            sets = []
            params = []
            if nombre is not None:
                sets.append("nombre = %s")
                params.append(nombre.strip())
            if moneda is not None:
                sets.append("moneda = %s")
                params.append(moneda)

            if not sets:
                return _fetch_one(
                    conn,
                    "SELECT id, nombre, email, moneda, fecha_creacion FROM usuarios WHERE id = %s",
                    (usuario_id,),
                )

            params.append(usuario_id)
            rc = _execute(
                conn,
                f"UPDATE usuarios SET {', '.join(sets)} WHERE id = %s",
                params,
            )
            conn.commit()
            if rc == 0:
                return None
            return _fetch_one(
                conn,
                "SELECT id, nombre, email, moneda, fecha_creacion FROM usuarios WHERE id = %s",
                (usuario_id,),
            )
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def cambiar_password(self, usuario_id, password_actual, password_nueva):
        """
        Cambia la contraseña verificando la actual.
        Retorna {"updated": True}, {"error": "password_incorrecta"} o None.
        [NORMA: ISO/IEC 27001 - Control A.9.4.3] Gestión segura de credenciales
        """
        conn = _get_conn()
        try:
            row = _fetch_one(
                conn,
                "SELECT password_hash FROM usuarios WHERE id = %s",
                (usuario_id,),
            )
            if not row:
                return None
            if not self.verify_password(password_actual, row["password_hash"]):
                return {"error": "password_incorrecta"}
            nuevo_hash, _ = self.hash_password(password_nueva)
            _execute(
                conn,
                "UPDATE usuarios SET password_hash = %s WHERE id = %s",
                (nuevo_hash, usuario_id),
            )
            conn.commit()
            return {"updated": True}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
