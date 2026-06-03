"""
============================================================
  REPOSITORIO DE CATEGORÍAS — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Proceso de Implementación
    - ISO 9001:2000: Enfoque basado en procesos
    - CMMI Nivel 3: Proceso estándar implementado
============================================================
"""

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None

from ..base_repository import BaseCategoriaRepository
from ._connection import _get_conn, _fetch_one, _fetch_all, _execute
from ._schema import SEED_CATEGORIAS


class MySQLCategoriaRepository(BaseCategoriaRepository):
    """
    Repositorio de categorías para MySQL/MariaDB.
    Gestiona creación, listado, actualización y desactivación de categorías.
    [NORMA: ISO/IEC 12207 - Proceso de Implementación]
    """

    def asegurar_para_usuario(self, usuario_id):
        """
        Garantiza que el usuario tenga categorías base.
        Migra categorías legacy (sin usuario_id) y aplica el seed.
        [NORMA: CMMI Nivel 3 - Gestión de Configuración] Migración controlada de datos
        """
        conn = _get_conn()
        try:
            # Intentar agregar columna si no existe (migración legacy)
            try:
                with conn.cursor() as cur:
                    cur.execute("ALTER TABLE categorias ADD COLUMN usuario_id INT NULL")
                conn.commit()
            except Exception:
                conn.rollback()

            # Intentar crear índice único si no existe
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "CREATE UNIQUE INDEX categorias_usuario_nombre_unique "
                        "ON categorias(usuario_id, nombre)"
                    )
                conn.commit()
            except Exception:
                conn.rollback()

            # Verificar si el usuario ya tiene categorías
            row = _fetch_one(
                conn,
                "SELECT COUNT(*) AS total FROM categorias WHERE usuario_id = %s",
                (usuario_id,),
            )
            tiene_categorias = row and int(row.get("total") or 0) > 0

            # Migrar categorías legacy vinculadas a movimientos del usuario
            legacy = []
            if not tiene_categorias:
                legacy = _fetch_all(
                    conn,
                    "SELECT DISTINCT c.id, c.nombre, t.codigo AS tipo, c.icono "
                    "FROM categorias c "
                    "JOIN tipos_movimiento t ON c.tipo_id = t.id "
                    "JOIN movimientos m ON m.categoria_id = c.id "
                    "WHERE c.usuario_id IS NULL AND m.usuario_id = %s",
                    (usuario_id,),
                )

            with conn.cursor() as cur:
                if legacy:
                    for cat in legacy:
                        cur.execute(
                            "INSERT INTO categorias (usuario_id, nombre, tipo_id, icono, activo) "
                            "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, 1) "
                            "ON DUPLICATE KEY UPDATE activo = 1",
                            (usuario_id, cat["nombre"], cat["tipo"], cat.get("icono") or ""),
                        )
                        cur.execute(
                            "SELECT id FROM categorias WHERE usuario_id = %s AND nombre = %s",
                            (usuario_id, cat["nombre"]),
                        )
                        nuevo = cur.fetchone()
                        if nuevo and nuevo.get("id"):
                            cur.execute(
                                "UPDATE movimientos SET categoria_id = %s "
                                "WHERE usuario_id = %s AND categoria_id = %s",
                                (nuevo["id"], usuario_id, cat["id"]),
                            )

                # Aplicar seed de categorías por defecto
                for nombre, tipo, icono in SEED_CATEGORIAS:
                    cur.execute(
                        "INSERT INTO categorias (usuario_id, nombre, tipo_id, icono, activo) "
                        "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, 1) "
                        "ON DUPLICATE KEY UPDATE activo = 1",
                        (usuario_id, nombre, tipo, icono),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def listar(self, usuario_id, tipo=None):
        """
        Lista categorías activas del usuario.
        Opcionalmente filtra por tipo ('ingreso' o 'gasto').
        Incluye contador de usos.
        """
        conn = _get_conn()
        try:
            if tipo:
                rows = _fetch_all(
                    conn,
                    "SELECT c.id, c.nombre, t.codigo AS tipo, c.icono, c.descripcion, c.activo, "
                    "COALESCE(COUNT(m.id), 0) AS usos "
                    "FROM categorias c "
                    "JOIN tipos_movimiento t ON c.tipo_id = t.id "
                    "LEFT JOIN movimientos m ON m.categoria_id = c.id AND m.usuario_id = %s "
                    "WHERE c.activo = 1 AND c.usuario_id = %s AND t.codigo = %s "
                    "GROUP BY c.id, c.nombre, t.codigo, c.icono, c.descripcion, c.activo "
                    "ORDER BY c.nombre",
                    (usuario_id, usuario_id, tipo),
                )
            else:
                rows = _fetch_all(
                    conn,
                    "SELECT c.id, c.nombre, t.codigo AS tipo, c.icono, c.descripcion, c.activo, "
                    "COALESCE(COUNT(m.id), 0) AS usos "
                    "FROM categorias c "
                    "JOIN tipos_movimiento t ON c.tipo_id = t.id "
                    "LEFT JOIN movimientos m ON m.categoria_id = c.id AND m.usuario_id = %s "
                    "WHERE c.activo = 1 AND c.usuario_id = %s "
                    "GROUP BY c.id, c.nombre, t.codigo, c.icono, c.descripcion, c.activo "
                    "ORDER BY t.codigo, c.nombre",
                    (usuario_id, usuario_id),
                )
            for r in rows:
                r["usos"] = int(r.get("usos") or 0)
            return rows
        finally:
            conn.close()

    def obtener_por_id(self, categoria_id, usuario_id):
        """Obtiene una categoría por ID verificando que pertenezca al usuario."""
        conn = _get_conn()
        try:
            return _fetch_one(
                conn,
                "SELECT c.id, c.nombre, t.codigo AS tipo, c.icono, c.descripcion, c.activo "
                "FROM categorias c "
                "JOIN tipos_movimiento t ON c.tipo_id = t.id "
                "WHERE c.id = %s AND c.usuario_id = %s",
                (categoria_id, usuario_id),
            )
        finally:
            conn.close()

    def crear(self, usuario_id, nombre, tipo, icono="", descripcion=""):
        """
        Crea una nueva categoría para el usuario.
        Retorna dict con la categoría creada o None si ya existe.
        """
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO categorias (usuario_id, nombre, tipo_id, icono, descripcion, activo) "
                    "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, %s, 1)",
                    (usuario_id, nombre.strip(), tipo, icono, descripcion),
                )
                categoria_id = cur.lastrowid
            conn.commit()
            return {
                "id": categoria_id,
                "nombre": nombre.strip(),
                "tipo": tipo,
                "icono": icono,
                "descripcion": descripcion,
                "activo": 1,
                "usos": 0,
            }
        except pymysql.err.IntegrityError:
            conn.rollback()
            return None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def actualizar(
        self,
        usuario_id,
        categoria_id,
        nombre=None,
        tipo=None,
        icono=None,
        descripcion=None,
    ):
        """
        Actualiza campos de una categoría.
        Solo actualiza los campos que no sean None.
        Retorna {"updated": bool} o {"error": "duplicate"}.
        """
        conn = _get_conn()
        try:
            # Verificar nombre duplicado
            if nombre:
                duplicado = _fetch_one(
                    conn,
                    "SELECT id FROM categorias WHERE usuario_id = %s AND nombre = %s AND id <> %s",
                    (usuario_id, nombre.strip(), categoria_id),
                )
                if duplicado:
                    return {"error": "duplicate"}

            sets = []
            params = []
            if nombre is not None:
                sets.append("nombre = %s")
                params.append(nombre.strip())
            if tipo is not None:
                sets.append("tipo_id = (SELECT id FROM tipos_movimiento WHERE codigo = %s)")
                params.append(tipo)
            if icono is not None:
                sets.append("icono = %s")
                params.append(icono)
            if descripcion is not None:
                sets.append("descripcion = %s")
                params.append(descripcion)

            if not sets:
                return {"updated": False}

            params.extend([categoria_id, usuario_id])
            rc = _execute(
                conn,
                f"UPDATE categorias SET {', '.join(sets)} WHERE id = %s AND usuario_id = %s",
                params,
            )
            conn.commit()
            return {"updated": rc > 0}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def desactivar(self, usuario_id, categoria_id):
        """Desactiva una categoría del usuario (soft delete)."""
        conn = _get_conn()
        try:
            rc = _execute(
                conn,
                "UPDATE categorias SET activo = 0 WHERE id = %s AND usuario_id = %s",
                (categoria_id, usuario_id),
            )
            conn.commit()
            return rc > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
