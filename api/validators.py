"""
============================================================
  CAPA DE VALIDACIÓN - Sistema de Control de Gastos
============================================================
  Normas aplicadas:
    - ISO 9126: Funcionalidad - Exactitud
    - ISO/IEC 25000: Calidad de datos de entrada
    - IEEE 730: Verificación de datos
    - ISO 9001: Control de producto no conforme
============================================================
  Módulo encargado de validar todos los datos de entrada
  antes de ser procesados por el sistema.
============================================================
"""

import re
from datetime import datetime

# ISO/IEC 25000 - Restricciones de calidad de datos
MAX_NOMBRE_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MAX_DESCRIPCION_LENGTH = 500
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_MONTO = 999999999.99
MIN_MONTO = 0.01

EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


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

    return (len(errores) == 0, errores)


def validar_login(datos: dict) -> tuple:
    """Valida los datos de inicio de sesión."""
    errores = []

    if not datos.get('email', '').strip():
        errores.append("El email es obligatorio.")
    if not datos.get('password', ''):
        errores.append("La contraseña es obligatoria.")

    return (len(errores) == 0, errores)


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
            monto = float(monto)
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

    fecha = datos.get('fecha')
    if fecha:
        try:
            datetime.strptime(fecha, '%Y-%m-%d')
        except ValueError:
            errores.append("El formato de fecha debe ser YYYY-MM-DD.")

    return (len(errores) == 0, errores)
