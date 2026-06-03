"""
============================================================
  REPOSITORIO DE PERFIL IA — MySQL/MariaDB
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Proceso de Implementación
    - ISO 9126: Eficiencia - Cache diario de perfiles
    - CMMI Nivel 3: Proceso estándar implementado
============================================================
  Almacena y recupera el perfil financiero generado por IA.
  Un perfil por usuario por día (cache diario).
============================================================
"""

import json
from datetime import datetime

from ._connection import _get_conn, _fetch_one


class MySQLPerfilIARepository:
    """
    Repositorio del perfil IA para MySQL/MariaDB.
    Almacena el perfil financiero generado por IA (un perfil/día).
    [NORMA: ISO/IEC 12207, ISO 9126 - Eficiencia]
    """

    def obtener_hoy(self, usuario_id):
        """
        Retorna el perfil de IA generado hoy o None si no existe.
        Usado para evitar regenerar el perfil más de una vez por día.
        """
        conn = _get_conn()
        try:
            return _fetch_one(
                conn,
                "SELECT * FROM perfiles_ia WHERE usuario_id = %s AND fecha = CURDATE()",
                (usuario_id,),
            )
        finally:
            conn.close()

    def guardar(self, usuario_id, tipo_label, score, tags, narrativa, habitos, areas_mejora):
        """
        Inserta o actualiza el perfil del día (UPSERT).
        tags/habitos/areas_mejora se almacenan como JSON string.
        [NORMA: ISO 9126 - Eficiencia: Evitar recálculo innecesario]
        """
        conn = _get_conn()
        try:
            tags_json = json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else tags
            hab_json  = json.dumps(habitos, ensure_ascii=False) if isinstance(habitos, list) else habitos
            am_json   = json.dumps(areas_mejora, ensure_ascii=False) if isinstance(areas_mejora, list) else areas_mejora

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO perfiles_ia (usuario_id, fecha, tipo_label, score, tags, narrativa, habitos, areas_mejora)
                    VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        tipo_label   = VALUES(tipo_label),
                        score        = VALUES(score),
                        tags         = VALUES(tags),
                        narrativa    = VALUES(narrativa),
                        habitos      = VALUES(habitos),
                        areas_mejora = VALUES(areas_mejora),
                        creado_en    = NOW()
                """, (usuario_id, tipo_label, int(score), tags_json, narrativa, hab_json, am_json))
            conn.commit()
            return {"fecha": datetime.now().strftime("%Y-%m-%d")}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
