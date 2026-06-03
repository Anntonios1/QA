"""
============================================================
  CAPA DE VALIDACIÓN - Sistema de Control de Gastos
============================================================
  Normas aplicadas:
    - ISO 9126: Funcionalidad - Exactitud
    - ISO/IEC 25000: Calidad de datos de entrada
    - IEEE 730: Verificación de datos
    - ISO 9001: Control de producto no conforme
    - ISO/IEC 27001: Seguridad - Validación de entrada
============================================================
  Módulo encargado de validar todos los datos de entrada
  antes de ser procesados por el sistema.
============================================================
"""

import re
import math
import unicodedata
from datetime import datetime

# ISO/IEC 25000 - Restricciones de calidad de datos
MAX_NOMBRE_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MAX_DESCRIPCION_LENGTH = 500
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_MONTO = 999999999.99
MIN_MONTO = 0.01
MAX_CATEGORIA_LENGTH = 60
MAX_ICONO_LENGTH = 32
MAX_CATEGORIA_DESC_LENGTH = 255
VALID_MONEDAS = ("COP", "USD")

EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# ============================================================
#  SANITIZACIÓN UNICODE
#  ISO/IEC 27001 - Validación de entrada vs spoofing Unicode
# ============================================================

def sanitizar_unicode(texto: str) -> tuple:
    """
    Sanitiza y normaliza Unicode.
    Detecta caracteres invisibles/peligrosos.
    Retorna (texto_limpio: str, es_seguro: bool)
    
    [NORMA: ISO/IEC 27001] Prevención de Unicode spoofing y bidi attacks
    """
    if not isinstance(texto, str):
        return "", False
    
    # Normalizar a NFC (forma compuesta canónica)
    # Evita caracteres equivalentes duplicados
    texto = unicodedata.normalize("NFC", texto)
    
    # Caracteres invisibles peligrosos a filtrar
    caracteres_peligrosos = [
        '\u200B',  # Zero-width space
        '\u200C',  # Zero-width non-joiner
        '\u200D',  # Zero-width joiner
        '\u202E',  # Right-to-left override (bidi attack)
        '\u202D',  # Left-to-right override
        '\u2066',  # Left-to-right isolate
        '\u2067',  # Right-to-left isolate
        '\u2068',  # First strong isolate
        '\u2069',  # Pop directional isolate
        '\u061C',  # Arabic letter mark
        '\u180E',  # Mongolian vowel separator
    ]
    
    texto_limpio = texto
    es_seguro = True
    
    for char_peligroso in caracteres_peligrosos:
        if char_peligroso in texto_limpio:
            texto_limpio = texto_limpio.replace(char_peligroso, "")
            es_seguro = False
    
    return texto_limpio, es_seguro


# [NORMA: ISO 9126 - Funcionalidad/Exactitud] Validación de datos de entrada para garantizar integridad funcional en el registro
# [NORMA: ISO/IEC 25000 - Usabilidad] Retroalimentación clara al usuario ante datos incorrectos
def validar_registro(datos: dict) -> tuple:
    """
    Valida los datos de registro de usuario.
    Retorna (es_valido: bool, errores: list)
    """
    errores = []

    nombre = datos.get('nombre', '').strip()
    if not nombre:
        errores.append("El nombre es obligatorio.")
    elif len(nombre) < 2:
        errores.append("El nombre debe tener al menos 2 caracteres.")
    elif len(nombre) > MAX_NOMBRE_LENGTH:
        errores.append(f"El nombre no puede exceder {MAX_NOMBRE_LENGTH} caracteres.")
    elif not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$", nombre):
        errores.append("El nombre solo puede contener letras, espacios y guiones.")

    email = datos.get('email', '').strip()
    if not email:
        errores.append("El email es obligatorio.")
    elif len(email) > MAX_EMAIL_LENGTH:
        errores.append("El email es demasiado largo.")
    elif not EMAIL_REGEX.match(email):
        errores.append("El formato del email no es válido.")

    password = datos.get('password', '')
    if not password:
        errores.append("La contraseña es obligatoria.")
    elif len(password) < MIN_PASSWORD_LENGTH:
        errores.append(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.")
    elif len(password) > MAX_PASSWORD_LENGTH:
        errores.append(f"La contraseña no puede exceder {MAX_PASSWORD_LENGTH} caracteres.")

    moneda = str(datos.get('moneda', '')).strip().upper()
    if moneda not in VALID_MONEDAS:
        errores.append("La moneda debe ser COP o USD.")

    presupuesto_mensual = datos.get('presupuesto_mensual')
    if presupuesto_mensual is None:
        errores.append("El presupuesto mensual es obligatorio.")
    else:
        try:
            if isinstance(presupuesto_mensual, bool):
                raise ValueError()
            monto = float(presupuesto_mensual)
            if not math.isfinite(monto):
                errores.append("El presupuesto mensual debe ser un número finito válido.")
            elif math.isnan(monto):
                errores.append("El presupuesto mensual no puede ser NaN.")
            if monto < MIN_MONTO:
                errores.append(f"El presupuesto mensual mínimo es {MIN_MONTO}.")
            elif monto > MAX_MONTO:
                errores.append(f"El presupuesto mensual máximo es {MAX_MONTO}.")
        except (ValueError, TypeError):
            errores.append("El presupuesto mensual debe ser un número válido.")

    return (len(errores) == 0, errores)


# [NORMA: ISO 9126 - Funcionalidad/Exactitud] Validación de datos de entrada para garantizar integridad funcional en el login
# [NORMA: ISO/IEC 25000 - Usabilidad] Retroalimentación clara al usuario ante credenciales vacías o incorrectas
def validar_login(datos: dict) -> tuple:
    """Valida los datos de inicio de sesión."""
    errores = []

    if not datos.get('email', '').strip():
        errores.append("El email es obligatorio.")
    if not datos.get('password', ''):
        errores.append("La contraseña es obligatoria.")

    return (len(errores) == 0, errores)


# [NORMA: ISO 9126 - Funcionalidad/Exactitud] Validación de datos de entrada para garantizar integridad funcional en transacciones
# [NORMA: ISO/IEC 25000 - Usabilidad] Mensaje descriptivo ante datos de transacción inválidos o incompletos
def validar_movimiento(datos: dict) -> tuple:
    """
    Valida los datos de un movimiento financiero.
    Retorna (es_valido: bool, errores: list)
    """
    errores = []

    tipo = datos.get('tipo', '')
    if tipo not in ('ingreso', 'gasto'):
        errores.append("El tipo debe ser 'ingreso' o 'gasto'.")

    monto = datos.get('monto')
    if monto is None:
        errores.append("El monto es obligatorio.")
    else:
        try:
            if isinstance(monto, bool):
                raise ValueError()
            monto = float(monto)
            if not math.isfinite(monto):
                errores.append("El monto debe ser un número finito válido.")
            elif math.isnan(monto):
                errores.append("El monto no puede ser NaN.")
            if monto < MIN_MONTO:
                errores.append(f"El monto mínimo es {MIN_MONTO}.")
            elif monto > MAX_MONTO:
                errores.append(f"El monto máximo es {MAX_MONTO}.")
        except (ValueError, TypeError):
            errores.append("El monto debe ser un número válido.")

    categoria_id = datos.get('categoria_id')
    if categoria_id is None:
        errores.append("La categoría es obligatoria.")
    else:
        try:
            int(categoria_id)
        except (ValueError, TypeError):
            errores.append("La categoría no es válida.")

    descripcion = datos.get('descripcion', '')
    if len(descripcion) > MAX_DESCRIPCION_LENGTH:
        errores.append(f"La descripción no puede exceder {MAX_DESCRIPCION_LENGTH} caracteres.")
    elif descripcion and re.search(r"[<>{}\[\]]", descripcion):
        errores.append("La descripción contiene caracteres no permitidos.")

    fecha = datos.get('fecha')
    if fecha:
        try:
            datetime.strptime(fecha, '%Y-%m-%d')
        except ValueError:
            errores.append("El formato de fecha debe ser YYYY-MM-DD.")

    return (len(errores) == 0, errores)


# [NORMA: ISO 9126 - Funcionalidad/Exactitud] Validación de datos de entrada para garantizar integridad funcional de categorías
# [NORMA: ISO/IEC 25000 - Usabilidad] Mensaje descriptivo ante datos de categoría inválidos o incompletos
def validar_categoria(datos: dict, parcial: bool = False) -> tuple:
    """
    Valida los datos de una categoria.
    Sanitiza emojis según ISO/IEC 27001.
    Retorna (es_valido: bool, errores: list)
    """
    errores = []

    nombre = datos.get("nombre")
    tipo = datos.get("tipo")
    icono = datos.get("icono")
    descripcion = datos.get("descripcion")

    if not parcial or nombre is not None:
        nombre_txt = (nombre or "").strip()
        if not nombre_txt:
            errores.append("El nombre de la categoria es obligatorio.")
        elif len(nombre_txt) > MAX_CATEGORIA_LENGTH:
            errores.append(
                f"El nombre de la categoria no puede exceder {MAX_CATEGORIA_LENGTH} caracteres."
            )
        elif not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s\-]+$", nombre_txt):
            errores.append("El nombre de la categoría contiene caracteres no permitidos.")

    if not parcial or tipo is not None:
        tipo_txt = (tipo or "").strip().lower()
        if tipo_txt not in ("ingreso", "gasto"):
            errores.append("El tipo debe ser 'ingreso' o 'gasto'.")

    if icono is not None:
        icono_txt = str(icono).strip()
        if icono_txt:
            # [NORMA: ISO/IEC 27001] Sanitizar Unicode en emojis
            icono_sanitizado, es_seguro = sanitizar_unicode(icono_txt)
            
            if not es_seguro:
                errores.append("El icono contiene caracteres invisibles o peligrosos. Usar solo emojis simples.")
            elif len(icono_sanitizado) > MAX_ICONO_LENGTH:
                errores.append(
                    f"El icono no puede exceder {MAX_ICONO_LENGTH} caracteres."
                )

    if descripcion is not None:
        desc_txt = str(descripcion).strip()
        if len(desc_txt) > MAX_CATEGORIA_DESC_LENGTH:
            errores.append(
                f"La descripción no puede exceder {MAX_CATEGORIA_DESC_LENGTH} caracteres."
            )
        elif desc_txt and re.search(r"[<>{}\[\]]", desc_txt):
            errores.append("La descripción contiene caracteres no permitidos.")

    return (len(errores) == 0, errores)
