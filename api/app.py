"""
============================================================
  API REST - Sistema de Control de Gastos
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Proceso de desarrollo - Implementación
    - ISO 9001:2000: Enfoque basado en procesos
    - ISO/IEC 20000: Gestión de servicios de TI
    - ISO/IEC 15504 SPICE: Evaluación de procesos
    - CMMI Nivel 3: Procesos definidos y estandarizados
    - IEEE 730: Plan de aseguramiento de calidad
============================================================
  Servidor Flask que expone los endpoints REST para
  las 7 funciones del sistema.
============================================================
"""

import base64
import calendar
import csv
import io
import os
import re
import secrets
import sys
import time
import threading
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, Response, jsonify, request, send_from_directory, session
from flask_cors import CORS

# Cargar variables de entorno desde .env (si existe)
_PROJECT_DIR_EARLY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_PROJECT_DIR_EARLY, ".env"))
except ImportError:
    pass

# Rutas base del proyecto
_API_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_API_DIR)
_APP_DIR = os.path.join(_PROJECT_DIR, "app")

# Agregar directorios al path
sys.path.insert(0, _API_DIR)  # para importar validators
sys.path.insert(0, _PROJECT_DIR)  # para importar db

# JWT Authentication
from jwt_auth import (
    generate_access_token,
    generate_refresh_token,
    get_token_hash,
    is_jwt_available,
    jwt_required,
    verify_token,
)
from validators import (
    validar_categoria,
    validar_login,
    validar_movimiento,
    validar_registro,
)

from db import (
    CategoriaRepository,
    InsightDiarioRepository,
    MovimientoRepository,
    NotificacionRepository,
    PerfilIARepository,
    PresupuestoRepository,
    RecurrenciaRepository,
    RefreshTokenRepository,
    UsuarioRepository,
    init_database,
)

# Modo de autenticación: "session" (legacy) o "jwt" (nuevo)
AUTH_MODE = os.environ.get("AUTH_MODE", "jwt").lower()

# ============================================================
#  CONFIGURACIÓN DE LA APLICACIÓN
#  ISO/IEC 20000 - Gestión de configuración del servicio
# ============================================================
# [NORMA: ISO/IEC 12207 - Proceso de Implementación] Punto de entrada principal del sistema de servicios REST
# [NORMA: ISO/IEC 20000 - Gestión de Servicios TI] Configuración del servicio de API para operación continua
app = Flask(__name__, static_folder=_APP_DIR, static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
_cors_origin_pattern = re.compile(
    r"^https?://("
    r"localhost"
    r"|127\.0\.0\.1"
    r"|100\.(?:6[4-9]|[7-9]\d|1\d\d)\.\d{1,3}\.\d{1,3}"
    r"|26\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r")(?:\:\d+)?$"
)
CORS(
    app,
    supports_credentials=True,
    origins=[
        _cors_origin_pattern,
        "null",  # file:// y algunos navegadores
    ],
)


# [NORMA: ISO/IEC 27001 - Control A.14.1.2] Política de seguridad de contenido para mitigar ataques de inyección
# [NORMA: OWASP Mobile Top 10 - M1] Protección contra uso inadecuado de la plataforma mediante headers seguros
@app.after_request
def set_security_headers(response):
    """Aplica headers de seguridad compatibles con navegador y asegura UTF-8."""
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    
    # Asegurar UTF-8 charset para HTML/JSON responses
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type or "application/json" in content_type:
        if "charset" not in content_type:
            response.headers["Content-Type"] = f"{content_type}; charset=utf-8"
    
    return response


# Tiempo de inicio para cálculo de uptime
_START_TIME = time.time()

# ============================================================
#  RATE LIMITING — Flask-Limiter
#  ISO/IEC 27001 - Protección contra ataques de fuerza bruta
# ============================================================
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["300 per minute"],
        storage_uri="memory://",
    )
    LIMITER_AVAILABLE = True
    # Desactivar rate limiting en desarrollo/testing para evitar 429
    if os.environ.get("FLASK_ENV") == "development":
        app.config["RATELIMIT_ENABLED"] = False
        print("[INFO] Rate limiting desactivado en entorno de desarrollo.")
except ImportError:
    LIMITER_AVAILABLE = False
    limiter = None
    print("[WARN] flask-limiter no instalado. Rate limiting desactivado.")

# ============================================================
#  CONFIGURACIÓN JSON Y ENCODING
#  ISO/IEC 27001 - Asegurar transmisión correcta de caracteres UTF-8
# ============================================================
app.config["JSON_AS_ASCII"] = False  # Permitir emojis y caracteres Unicode en JSON
app.json.sort_keys = False


def _rate_limit(limit_str):
    """Decorador de rate limit que funciona aunque flask-limiter no esté instalado."""

    def decorator(f):
        if LIMITER_AVAILABLE and limiter:
            return limiter.limit(limit_str)(f)
        return f

    return decorator


# Inicializar base de datos al arrancar
try:
    init_database()
except Exception as _db_err:
    print(f"[WARN] No se pudo inicializar DB: {_db_err}")


# ============================================================
#  MIDDLEWARE DE AUTENTICACIÓN
#  ISO 9126 - Seguridad: Control de acceso
#  Soporta ambos modos: session (legacy) y JWT (nuevo)
# ============================================================
def login_required(f):
    """
    Decorador que verifica que el usuario esté autenticado.
    Soporta autenticación por sesión (cookies) o JWT (Bearer token).
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        usuario_id = None

        # Primero intentar JWT si está disponible
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and is_jwt_available():
            token = auth_header[7:]
            try:
                import jwt as pyjwt

                payload = verify_token(token, expected_type="access")
                usuario_id = payload["sub"]
            except Exception:
                # [NORMA: ISO 9126 - Fiabilidad/Tolerancia a Fallos] Captura y manejo controlado de errores del sistema
                # [NORMA: IEEE 730 - Sección de Pruebas] Punto de control de calidad: respuesta de autenticación fallida
                # Token inválido o expirado
                return jsonify(
                    {
                        "ok": False,
                        "error": "Token inválido o expirado",
                        "codigo": "INVALID_TOKEN",
                    }
                ), 401

        # Fallback a sesión si no hay JWT
        if usuario_id is None:
            usuario_id = session.get("usuario_id")

        if not usuario_id:
            return jsonify(
                {
                    "ok": False,
                    "error": "Sesión no válida. Inicie sesión.",
                    "codigo": "NO_AUTH",
                }
            ), 401

        return f(usuario_id, *args, **kwargs)

    return decorated


def respuesta_exito(data=None, mensaje="Operación exitosa", codigo=200):
    """Formato estándar de respuesta exitosa (ISO 9001 - Estandarización)."""
    body = {"status": "success", "mensaje": mensaje}
    if data is not None:
        body["data"] = data
    return jsonify(body), codigo


def respuesta_error(mensaje="Error en la operación", errores=None, codigo=400):
    """Formato estándar de respuesta de error."""
    body = {"status": "error", "mensaje": mensaje}
    if errores:
        body["errores"] = errores
    return jsonify(body), codigo


@app.errorhandler(429)
def manejar_demasiadas_solicitudes(_error):
    """Devuelve un mensaje simple para evitar exponer detalles del rate limit."""
    if request.path.startswith("/api/"):
        return respuesta_error("Too Many Requests", codigo=429)
    return Response("Too Many Requests", status=429, mimetype="text/plain")


# ============================================================
#  F1: REGISTRARSE
#  POST /api/auth/registro
#  IEEE 730 - Trazabilidad del proceso de registro
# ============================================================
# [NORMA: ISO/IEC 12207 - Proceso de Operación del Software] Proceso de negocio: Registro de usuario
# [NORMA: ISO 9001:2000 - Enfoque basado en procesos] Proceso documentado y controlado para registro de usuarios y control de acceso
@app.route("/api/auth/registro", methods=["POST"])
@_rate_limit("3 per minute")
def registro():
    """Permite al usuario crear una cuenta en el sistema."""
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    # F5: Validar datos
    valido, errores = validar_registro(datos)
    if not valido:
        return respuesta_error("Datos inválidos.", errores=errores, codigo=422)

    moneda = str(datos.get("moneda", "COP")).strip().upper() or "COP"
    presupuesto_mensual = float(datos.get("presupuesto_mensual") or 0)

    usuario = UsuarioRepository.crear(
        nombre=datos["nombre"],
        email=datos["email"],
        password=datos["password"],
        moneda=moneda,
    )

    if usuario is None:
        return respuesta_error("El email ya está registrado.", codigo=409)

    mes_actual = datetime.now().strftime("%Y-%m-01")
    try:
        PresupuestoRepository.crear(
            usuario["id"], None, presupuesto_mensual, mes_actual
        )
    except Exception as _pres_err:
        print(f"[WARN] No se pudo crear presupuesto inicial: {_pres_err}")

    # F6: Notificación - Bienvenida
    NotificacionRepository.crear(
        usuario_id=usuario["id"],
        titulo="¡Bienvenido!",
        mensaje=f"Hola {usuario['nombre']}, tu cuenta ha sido creada exitosamente. "
        "Comienza a registrar tus movimientos financieros.",
        tipo="exito",
    )

    return respuesta_exito(
        data={
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "moneda": usuario.get("moneda", moneda),
        },
        mensaje="Registro exitoso.",
        codigo=201,
    )


# ============================================================
#  F2: INICIAR SESIÓN
#  POST /api/auth/login
#  ISO 9126 - Seguridad: Autenticación
#  Retorna JWT (access + refresh tokens) si JWT está habilitado
# ============================================================
@app.route("/api/auth/login", methods=["POST"])
@_rate_limit("60 per minute")
def login():
    """
    Permite al usuario autenticarse en el sistema.
    Retorna tokens JWT si AUTH_MODE=jwt, sino usa sesiones.
    """
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    valido, errores = validar_login(datos)
    if not valido:
        return respuesta_error("Datos inválidos.", errores=errores, codigo=422)

    usuario = UsuarioRepository.autenticar(
        email=datos["email"], password=datos["password"]
    )

    if usuario is None:
        return respuesta_error("Credenciales incorrectas.", codigo=401)

    no_leidas = NotificacionRepository.contar_no_leidas(usuario["id"])

    response_data = {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "moneda": usuario.get("moneda", "COP"),
        "notificaciones_no_leidas": no_leidas,
    }

    # Generar JWT si está disponible y habilitado
    if AUTH_MODE == "jwt" and is_jwt_available():
        # Access token (corta duración)
        access_token = generate_access_token(
            usuario["id"], usuario["nombre"], usuario["email"]
        )

        # Refresh token (larga duración, almacenado en DB)
        refresh_token, token_hash, expires_at = generate_refresh_token(usuario["id"])

        # Guardar refresh token en DB
        device_info = request.headers.get("User-Agent", "")[:255]
        RefreshTokenRepository.guardar(
            usuario["id"], token_hash, expires_at, device_info
        )

        response_data["tokens"] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutos en segundos
        }
    else:
        # Fallback a sesión tradicional
        session["usuario_id"] = usuario["id"]
        session["usuario_nombre"] = usuario["nombre"]

    return respuesta_exito(data=response_data, mensaje="Inicio de sesión exitoso.")


# ============================================================
#  JWT: REFRESH TOKEN
#  POST /api/auth/refresh
#  RFC 7519 - Renovación de tokens
# ============================================================
@app.route("/api/auth/refresh", methods=["POST"])
@_rate_limit("10 per minute")
def refresh_token():
    """
    Renueva el access token usando un refresh token válido.
    Body JSON: { refresh_token: "..." }

    Nota: El refresh token se revoca después de usarse (one-time use).
    Esto previene ataques de replay si el token es comprometido.
    """
    if not is_jwt_available():
        return respuesta_error("JWT no disponible.", codigo=503)

    datos = request.get_json(silent=True)
    if not datos or not datos.get("refresh_token"):
        return respuesta_error("Se requiere 'refresh_token'.", codigo=400)

    refresh_token_str = datos["refresh_token"]

    try:
        # Verificar firma y expiración del refresh token
        payload = verify_token(refresh_token_str, expected_type="refresh")
        usuario_id = payload["sub"]

        # Verificar que el token existe en DB y no está revocado
        token_hash = get_token_hash(refresh_token_str)
        token_record = RefreshTokenRepository.verificar(token_hash)

        if not token_record:
            return respuesta_error("Refresh token revocado o expirado.", codigo=401)

        # Obtener datos del usuario
        usuario = UsuarioRepository.obtener_por_id(usuario_id)
        if not usuario:
            return respuesta_error("Usuario no encontrado.", codigo=404)

        # Revocar el refresh token usado (one-time use)
        # Esto previene que un token comprometido pueda reutilizarse
        RefreshTokenRepository.revocar(token_hash)

        # Generar nuevo access token
        new_access_token = generate_access_token(
            usuario["id"], usuario["nombre"], usuario["email"]
        )

        # Generar nuevo refresh token (rotación)
        new_refresh_token, new_token_hash, new_expires_at = generate_refresh_token(
            usuario["id"]
        )

        # Guardar el nuevo refresh token en DB
        device_info = request.headers.get("User-Agent", "")[:255]
        RefreshTokenRepository.guardar(
            usuario_id, new_token_hash, new_expires_at, device_info
        )

        return respuesta_exito(
            data={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
                "expires_in": 900,
            },
            mensaje="Token renovado.",
        )

    except Exception as e:
        return respuesta_error(f"Token inválido: {str(e)}", codigo=401)


# ============================================================
#  JWT: REVOKE TOKEN
#  POST /api/auth/revoke
#  ISO/IEC 27001 - Gestión de sesiones
# ============================================================
@app.route("/api/auth/revoke", methods=["POST"])
@_rate_limit("10 per minute")
def revoke_token():
    """
    Revoca un refresh token específico o todos los tokens del usuario.
    Body JSON: { refresh_token: "..." } o { revoke_all: true }
    """
    if not is_jwt_available():
        return respuesta_error("JWT no disponible.", codigo=503)

    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Se requieren datos.", codigo=400)

    # Si se proporciona refresh_token, revocarlo
    if datos.get("refresh_token"):
        token_hash = get_token_hash(datos["refresh_token"])
        revocado = RefreshTokenRepository.revocar(token_hash)
        if revocado:
            return respuesta_exito(mensaje="Token revocado.")
        return respuesta_error("Token no encontrado.", codigo=404)

    # Si revoke_all=true, necesitamos el usuario autenticado
    if datos.get("revoke_all"):
        # Obtener usuario del access token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return respuesta_error(
                "Se requiere access token para revoke_all.", codigo=401
            )

        try:
            token = auth_header[7:]
            payload = verify_token(token, expected_type="access")
            usuario_id = payload["sub"]

            cantidad = RefreshTokenRepository.revocar_todos(usuario_id)
            return respuesta_exito(
                mensaje=f"Todos los tokens revocados ({cantidad}).",
                data={"tokens_revocados": cantidad},
            )
        except Exception as e:
            return respuesta_error(f"Token inválido: {str(e)}", codigo=401)

    return respuesta_error("Se requiere 'refresh_token' o 'revoke_all'.", codigo=400)


# ============================================================
#  CERRAR SESIÓN
#  POST /api/auth/logout
# ============================================================
@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout(usuario_id):
    """Cierra la sesión del usuario."""
    session.clear()
    return respuesta_exito(mensaje="Sesión cerrada correctamente.")


# ============================================================
#  PERFIL DE USUARIO
#  GET /api/auth/perfil       → Obtener perfil
#  PUT /api/auth/perfil       → Actualizar perfil
#  PUT /api/auth/password     → Cambiar contraseña
# ============================================================
@app.route("/api/auth/perfil", methods=["GET"])
@login_required
def obtener_perfil(usuario_id):
    """Devuelve los datos del usuario autenticado."""
    usuario = UsuarioRepository.obtener_por_id(usuario_id)
    if not usuario:
        return respuesta_error("Usuario no encontrado.", codigo=404)
    # Remove sensitive fields
    usuario.pop('password_hash', None)
    usuario.pop('activo', None)
    # Format fecha_creacion if exists
    if hasattr(usuario.get('fecha_creacion'), 'isoformat'):
        usuario['fecha_creacion'] = usuario['fecha_creacion'].isoformat()
    return respuesta_exito(data=usuario)


@app.route("/api/auth/perfil", methods=["PUT"])
@login_required
@_rate_limit("10 per minute")
def actualizar_perfil(usuario_id):
    """Actualiza nombre y/o moneda del usuario."""
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    nombre = datos.get('nombre')
    moneda = datos.get('moneda')

    # Validate nombre if provided
    if nombre is not None:
        nombre = str(nombre).strip()
        if len(nombre) < 2:
            return respuesta_error("El nombre debe tener al menos 2 caracteres.", codigo=422)
        if len(nombre) > 100:
            return respuesta_error("El nombre no puede exceder 100 caracteres.", codigo=422)
        # No numbers in name
        if re.search(r'\d', nombre):
            return respuesta_error("El nombre no puede contener números.", codigo=422)
        # Only letters, spaces, accents, hyphens
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-\']+$', nombre):
            return respuesta_error("El nombre contiene caracteres no permitidos.", codigo=422)

    # Validate moneda if provided
    if moneda is not None:
        moneda = str(moneda).strip().upper()
        if moneda not in ('COP', 'USD'):
            return respuesta_error("Moneda debe ser COP o USD.", codigo=422)

    resultado = UsuarioRepository.actualizar_perfil(usuario_id, nombre=nombre, moneda=moneda)
    if resultado is None:
        return respuesta_error("No se encontró el usuario.", codigo=404)

    return respuesta_exito(data=resultado, mensaje="Perfil actualizado correctamente.")


@app.route("/api/auth/password", methods=["PUT"])
@login_required
@_rate_limit("5 per minute")
def cambiar_password(usuario_id):
    """Cambia la contraseña del usuario verificando la actual."""
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    password_actual = datos.get('password_actual', '')
    password_nueva = datos.get('password_nueva', '')

    if not password_actual:
        return respuesta_error("Se requiere la contraseña actual.", codigo=422)
    if not password_nueva or len(password_nueva) < 8:
        return respuesta_error("La nueva contraseña debe tener al menos 8 caracteres.", codigo=422)
    if len(password_nueva) > 128:
        return respuesta_error("La contraseña no puede exceder 128 caracteres.", codigo=422)
    if password_actual == password_nueva:
        return respuesta_error("La nueva contraseña debe ser diferente a la actual.", codigo=422)

    resultado = UsuarioRepository.cambiar_password(usuario_id, password_actual, password_nueva)
    if resultado and resultado.get('error') == 'password_incorrecta':
        return respuesta_error("La contraseña actual es incorrecta.", codigo=401)
    if resultado and resultado.get('updated'):
        return respuesta_exito(mensaje="Contraseña actualizada correctamente.")
    return respuesta_error("No se pudo cambiar la contraseña.", codigo=500)


# ============================================================
#  F3: GESTIONAR MOVIMIENTO
#  POST   /api/movimientos          → Crear movimiento
#  GET    /api/movimientos          → Listar movimientos
#  PUT    /api/movimientos/<id>     → Editar movimiento  ← NUEVO
#  DELETE /api/movimientos/<id>     → Eliminar movimiento
#  GET    /api/movimientos/export/csv → Exportar CSV     ← NUEVO
#  ISO 9001 - Trazabilidad de registros financieros
# ============================================================
# [NORMA: ISO/IEC 12207 - Proceso de Operación del Software] Proceso de negocio: Registro de movimiento financiero
# [NORMA: ISO 9001:2000 - Enfoque basado en procesos] Proceso documentado y controlado para ingreso de datos
@app.route("/api/movimientos", methods=["POST"])
@login_required
def crear_movimiento(usuario_id):
    """El usuario registra un ingreso o gasto."""
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    # F5: Validar datos
    valido, errores = validar_movimiento(datos)
    if not valido:
        return respuesta_error("Datos inválidos.", errores=errores, codigo=422)

    # Verificar categoría
    categoria = CategoriaRepository.obtener_por_id(
        int(datos["categoria_id"]), usuario_id
    )
    if not categoria:
        return respuesta_error("La categoría no existe.", codigo=404)

    movimiento = MovimientoRepository.crear(
        usuario_id=usuario_id,
        categoria_id=int(datos["categoria_id"]),
        tipo=datos["tipo"],
        monto=float(datos["monto"]),
        descripcion=datos.get("descripcion", ""),
        fecha=datos.get("fecha"),
    )

    # F6: Notificación al registrar gasto grande
    if datos["tipo"] == "gasto" and float(datos["monto"]) >= 1000:
        titulo_notif = "Gasto importante registrado"
        mensaje_notif = (
            f"Has registrado un gasto de ${float(datos['monto']):,.2f} "
            f"en {categoria['nombre']}. Revisa tu balance."
        )

        NotificacionRepository.crear(
            usuario_id=usuario_id,
            titulo=titulo_notif,
            mensaje=mensaje_notif,
            tipo="alerta",
        )

        # Intentar push al sistema si el usuario está suscrito.
        try:
            from push import enviar_push

            enviar_push(
                usuario_id=usuario_id,
                titulo=titulo_notif,
                mensaje=mensaje_notif,
                tag="gasto-importante",
            )
        except Exception:
            pass

    # F6: Alertas por presupuesto (80% o excedido)
    if datos["tipo"] == "gasto":
        try:
            fecha_mov = datos.get("fecha") or datetime.now().strftime("%Y-%m-%d")
            mes_ref = datetime.strptime(fecha_mov, "%Y-%m-%d").strftime("%Y-%m-01")
        except ValueError:
            mes_ref = datetime.now().strftime("%Y-%m-01")

        def _emitir_alerta_presupuesto(estado_pres, alcance_label, tag_base):
            if not estado_pres or estado_pres.get("porcentaje_usado", 0) < 80:
                return

            excedido = estado_pres.get("excedido") is True
            porcentaje = estado_pres.get("porcentaje_usado", 0)
            titulo_pres = (
                "Presupuesto excedido" if excedido else "Presupuesto cerca del limite"
            )
            if alcance_label:
                mensaje_pres = (
                    f"Has usado {porcentaje}% de tu presupuesto en {alcance_label}."
                )
            else:
                mensaje_pres = (
                    f"Has usado {porcentaje}% de tu presupuesto global del mes."
                )
            tipo_notif = "alerta" if excedido else "info"

            NotificacionRepository.crear(
                usuario_id=usuario_id,
                titulo=titulo_pres,
                mensaje=mensaje_pres,
                tipo=tipo_notif,
            )

            try:
                from push import enviar_push

                enviar_push(
                    usuario_id=usuario_id,
                    titulo=titulo_pres,
                    mensaje=mensaje_pres,
                    tag=f"{tag_base}-excedido" if excedido else f"{tag_base}-80",
                )
            except Exception:
                pass

        try:
            estado_categoria = PresupuestoRepository.verificar_exceso(
                usuario_id, int(datos["categoria_id"]), mes_ref
            )
        except Exception:
            estado_categoria = None

        _emitir_alerta_presupuesto(
            estado_categoria, categoria.get("nombre"), "presupuesto-cat"
        )

        try:
            estado_global = PresupuestoRepository.verificar_exceso(
                usuario_id, None, mes_ref
            )
        except Exception:
            estado_global = None

        _emitir_alerta_presupuesto(estado_global, None, "presupuesto-global")

    return respuesta_exito(
        data=movimiento, mensaje="Movimiento registrado.", codigo=201
    )


@app.route("/api/movimientos", methods=["GET"])
@login_required
def listar_movimientos(usuario_id):
    """Lista los movimientos del usuario con filtros opcionales."""
    tipo = request.args.get("tipo")
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")

    # Paginación opcional
    page_param = request.args.get("page")
    page_size_param = request.args.get("page_size")
    usar_paginacion = page_param is not None or page_size_param is not None

    # Validar límite
    try:
        limite = min(int(request.args.get("limite", 50)), 200)
    except (ValueError, TypeError):
        limite = 50

    # Validar filtros con type checking
    categoria_id = None
    monto_min = None
    monto_max = None

    # Validar categoria_id
    cat_id_param = request.args.get("categoria_id")
    if cat_id_param:
        try:
            categoria_id = int(cat_id_param)
        except (ValueError, TypeError):
            return respuesta_error(
                "'categoria_id' debe ser un número entero.", codigo=400
            )

    # Validar monto_min
    monto_min_param = request.args.get("monto_min")
    if monto_min_param:
        try:
            monto_min = float(monto_min_param)
            if monto_min < 0:
                return respuesta_error("'monto_min' debe ser positivo.", codigo=400)
        except (ValueError, TypeError):
            return respuesta_error("'monto_min' debe ser un número.", codigo=400)

    # Validar monto_max
    monto_max_param = request.args.get("monto_max")
    if monto_max_param:
        try:
            monto_max = float(monto_max_param)
            if monto_max < 0:
                return respuesta_error("'monto_max' debe ser positivo.", codigo=400)
        except (ValueError, TypeError):
            return respuesta_error("'monto_max' debe ser un número.", codigo=400)

    # Validar coherencia entre monto_min y monto_max
    if monto_min is not None and monto_max is not None and monto_min > monto_max:
        return respuesta_error(
            "'monto_min' no puede ser mayor que 'monto_max'.", codigo=400
        )

    if usar_paginacion:
        try:
            page = max(int(page_param or 1), 1)
        except (ValueError, TypeError):
            return respuesta_error("'page' debe ser un número entero positivo.", codigo=400)

        try:
            page_size = min(max(int(page_size_param or 20), 1), 200)
        except (ValueError, TypeError):
            return respuesta_error(
                "'page_size' debe ser un número entero positivo.", codigo=400
            )

        offset = (page - 1) * page_size
        movimientos = MovimientoRepository.listar_por_usuario(
            usuario_id=usuario_id,
            limite=page_size,
            offset=offset,
            tipo=tipo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            categoria_id=categoria_id,
            monto_min=monto_min,
            monto_max=monto_max,
        )
        total = MovimientoRepository.contar_por_usuario(
            usuario_id=usuario_id,
            tipo=tipo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            categoria_id=categoria_id,
            monto_min=monto_min,
            monto_max=monto_max,
        )
        total_pages = max((total + page_size - 1) // page_size, 1)

        return respuesta_exito(
            data={
                "items": movimientos,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                },
            }
        )

    movimientos = MovimientoRepository.listar_por_usuario(
        usuario_id=usuario_id,
        limite=limite,
        offset=0,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        categoria_id=categoria_id,
        monto_min=monto_min,
        monto_max=monto_max,
    )

    return respuesta_exito(data=movimientos)


@app.route("/api/movimientos/export/csv", methods=["GET"])
@login_required
def exportar_movimientos_csv(usuario_id):
    """
    Exporta los movimientos del usuario en formato CSV.
    Soporta los mismos filtros que GET /api/movimientos.
    ISO 9001 - Exportación y trazabilidad de datos
    """
    tipo = request.args.get("tipo")
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    categoria_id = request.args.get("categoria_id")
    monto_min = request.args.get("monto_min")
    monto_max = request.args.get("monto_max")

    try:
        categoria_id = int(categoria_id) if categoria_id else None
    except (ValueError, TypeError):
        return respuesta_error("'categoria_id' debe ser un número entero.", codigo=400)

    try:
        monto_min = float(monto_min) if monto_min else None
    except (ValueError, TypeError):
        return respuesta_error("'monto_min' debe ser un número.", codigo=400)

    try:
        monto_max = float(monto_max) if monto_max else None
    except (ValueError, TypeError):
        return respuesta_error("'monto_max' debe ser un número.", codigo=400)

    movimientos = MovimientoRepository.listar_por_usuario(
        usuario_id=usuario_id,
        limite=200,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        categoria_id=categoria_id,
        monto_min=monto_min,
        monto_max=monto_max,
    )

    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Tipo", "Monto", "Categoría", "Descripción", "Fecha"])
    for m in movimientos:
        writer.writerow(
            [
                m.get("id", ""),
                m.get("tipo", ""),
                f"{m.get('monto', 0):.2f}",
                m.get("categoria_nombre", ""),
                m.get("descripcion", ""),
                str(m.get("fecha", ""))[:10],
            ]
        )

    csv_content = output.getvalue()
    fecha_hoy = datetime.now().strftime("%Y%m%d")
    filename = f"controlcash_movimientos_{fecha_hoy}.csv"

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


@app.route("/api/movimientos/<int:movimiento_id>", methods=["PUT"])
@login_required
def editar_movimiento(usuario_id, movimiento_id):
    """
    Edita un movimiento existente del usuario.
    Solo actualiza los campos proporcionados.
    ISO 9001 - Trazabilidad de modificaciones
    """
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    # Validar categoría si se proporciona
    if "categoria_id" in datos:
        categoria = CategoriaRepository.obtener_por_id(
            int(datos["categoria_id"]), usuario_id
        )
        if not categoria:
            return respuesta_error("La categoría no existe.", codigo=404)

    # Validar monto si se proporciona
    if "monto" in datos:
        try:
            monto = float(datos["monto"])
            if monto <= 0 or monto > 999999999.99:
                return respuesta_error("Monto fuera de rango válido.", codigo=422)
        except (ValueError, TypeError):
            return respuesta_error("Monto inválido.", codigo=422)

    # Validar tipo si se proporciona
    if "tipo" in datos and datos["tipo"] not in ("ingreso", "gasto"):
        return respuesta_error("Tipo debe ser 'ingreso' o 'gasto'.", codigo=422)

    actualizado = MovimientoRepository.actualizar(
        movimiento_id=movimiento_id,
        usuario_id=usuario_id,
        categoria_id=datos.get("categoria_id"),
        tipo=datos.get("tipo"),
        monto=datos.get("monto"),
        descripcion=datos.get("descripcion"),
        fecha=datos.get("fecha"),
    )

    if not actualizado:
        return respuesta_error("Movimiento no encontrado.", codigo=404)

    return respuesta_exito(data=actualizado, mensaje="Movimiento actualizado.")


@app.route("/api/movimientos/<int:movimiento_id>", methods=["DELETE"])
@login_required
def eliminar_movimiento(usuario_id, movimiento_id):
    """Elimina un movimiento del usuario."""
    eliminado = MovimientoRepository.eliminar(movimiento_id, usuario_id)
    if not eliminado:
        return respuesta_error("Movimiento no encontrado.", codigo=404)
    return respuesta_exito(mensaje="Movimiento eliminado.")


# ============================================================
#  F4: SOLICITAR BALANCE
#  GET /api/balance
#  ISO/IEC 25000 - Completitud funcional
# ============================================================
@app.route("/api/balance", methods=["GET"])
@login_required
def obtener_balance(usuario_id):
    """Consulta el balance financiero del usuario."""
    balance = MovimientoRepository.obtener_balance(usuario_id)
    return respuesta_exito(data=balance)


# ============================================================
#  F6: NOTIFICACIONES
#  GET  /api/notificaciones       → Listar notificaciones
#  PUT  /api/notificaciones/<id>  → Marcar como leída
#  ISO/IEC 20000 - Gestión de comunicación
# ============================================================
@app.route("/api/notificaciones", methods=["GET"])
@login_required
def listar_notificaciones(usuario_id):
    """Lista las notificaciones del usuario."""
    solo_no_leidas = request.args.get("no_leidas", "").lower() == "true"
    notificaciones = NotificacionRepository.listar_por_usuario(
        usuario_id, solo_no_leidas=solo_no_leidas
    )
    return respuesta_exito(data=notificaciones)


@app.route("/api/notificaciones/<int:notificacion_id>", methods=["PUT"])
@login_required
def marcar_notificacion_leida(usuario_id, notificacion_id):
    """Marca una notificación como leída."""
    exito = NotificacionRepository.marcar_leida(notificacion_id, usuario_id)
    if not exito:
        return respuesta_error("Notificación no encontrada.", codigo=404)
    return respuesta_exito(mensaje="Notificación marcada como leída.")


# ============================================================
#  F7: RESUMEN
#  GET /api/resumen
#  ISO 14598 - Evaluación del producto (reportes)
# ============================================================
@app.route("/api/resumen", methods=["GET"])
@login_required
def obtener_resumen(usuario_id):
    """Genera resumen financiero del usuario."""
    dias = min(int(request.args.get("dias", 30)), 365)
    resumen = MovimientoRepository.obtener_resumen(usuario_id, dias=dias)
    balance = MovimientoRepository.obtener_balance(usuario_id)
    resumen["balance"] = balance
    return respuesta_exito(data=resumen)


# ============================================================
#  REPORTES POR PERIODO
#  GET /api/reportes/resumen?periodo=diario|semanal|mensual
# ============================================================
@app.route("/api/reportes/resumen", methods=["GET"])
@login_required
def obtener_reporte_periodo(usuario_id):
    periodo = (request.args.get("periodo") or "mensual").strip().lower()
    fecha_base = request.args.get("fecha_base")

    try:
        base_dt = (
            datetime.strptime(fecha_base, "%Y-%m-%d") if fecha_base else datetime.now()
        )
    except ValueError:
        return respuesta_error("Formato de 'fecha_base' inválido. Use YYYY-MM-DD.", codigo=400)

    if periodo == "diario":
        inicio = base_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = base_dt.replace(hour=23, minute=59, second=59, microsecond=0)
        prev_inicio = inicio - timedelta(days=1)
        prev_fin = fin - timedelta(days=1)
        periodo_label = "Diario"
    elif periodo == "semanal":
        inicio = base_dt - timedelta(days=base_dt.weekday())
        inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(days=6, hours=23, minutes=59, seconds=59)
        prev_inicio = inicio - timedelta(days=7)
        prev_fin = fin - timedelta(days=7)
        periodo_label = "Semanal"
    elif periodo == "mensual":
        inicio = base_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        dias_mes = calendar.monthrange(inicio.year, inicio.month)[1]
        fin = inicio.replace(day=dias_mes, hour=23, minute=59, second=59)
        prev_ref = inicio - timedelta(days=1)
        prev_inicio = prev_ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_fin = prev_ref.replace(
            day=calendar.monthrange(prev_ref.year, prev_ref.month)[1],
            hour=23,
            minute=59,
            second=59,
        )
        periodo_label = "Mensual"
    else:
        return respuesta_error("Periodo inválido. Use diario, semanal o mensual.", codigo=400)

    inicio_str = inicio.strftime("%Y-%m-%d %H:%M:%S")
    fin_str = fin.strftime("%Y-%m-%d %H:%M:%S")
    prev_inicio_str = prev_inicio.strftime("%Y-%m-%d %H:%M:%S")
    prev_fin_str = prev_fin.strftime("%Y-%m-%d %H:%M:%S")

    actual = MovimientoRepository.obtener_reporte_periodo(
        usuario_id, inicio_str, fin_str
    )
    anterior = MovimientoRepository.obtener_reporte_periodo(
        usuario_id, prev_inicio_str, prev_fin_str
    )

    prev_map = {
        int(c["categoria_id"]): float(c.get("total") or 0)
        for c in (anterior.get("categorias") or [])
    }

    top_categorias = []
    for cat in (actual.get("categorias") or [])[:6]:
        cat_id = int(cat["categoria_id"])
        total_actual = float(cat.get("total") or 0)
        total_prev = float(prev_map.get(cat_id, 0))
        variacion = total_actual - total_prev
        variacion_pct = (
            round((variacion / total_prev) * 100, 1)
            if total_prev > 0
            else (100.0 if total_actual > 0 else 0.0)
        )
        direccion = "up" if variacion > 0 else "down" if variacion < 0 else "flat"

        top_categorias.append(
            {
                "categoria_id": cat_id,
                "nombre": cat.get("nombre"),
                "icono": cat.get("icono"),
                "total": round(total_actual, 2),
                "variacion_monto": round(variacion, 2),
                "variacion_pct": variacion_pct,
                "direccion": direccion,
            }
        )

    payload = {
        "periodo": periodo,
        "periodo_label": periodo_label,
        "rango": {
            "inicio": inicio.strftime("%Y-%m-%d"),
            "fin": fin.strftime("%Y-%m-%d"),
        },
        "totales": actual.get("totales", {}),
        "top_categorias": top_categorias,
    }

    return respuesta_exito(data=payload)


# ============================================================
#  CATEGORÍAS
#  GET /api/categorias
# ============================================================
@app.route("/api/categorias", methods=["GET"])
@login_required
def listar_categorias(usuario_id):
    """Lista las categorías disponibles."""
    tipo = request.args.get("tipo")
    CategoriaRepository.asegurar_para_usuario(usuario_id)
    categorias = CategoriaRepository.listar(usuario_id, tipo=tipo)
    return respuesta_exito(data=categorias)


@app.route("/api/categorias", methods=["POST"])
@login_required
@_rate_limit("20 per minute")
def crear_categoria(usuario_id):
    """Crea una nueva categoría."""
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    valido, errores = validar_categoria(datos)
    if not valido:
        return respuesta_error("Datos inválidos.", errores=errores, codigo=422)

    nombre = datos.get("nombre", "").strip()
    tipo = datos.get("tipo", "").strip().lower()
    icono = str(datos.get("icono") or "").strip()
    descripcion = str(datos.get("descripcion") or "").strip()

    creado = CategoriaRepository.crear(usuario_id, nombre, tipo, icono, descripcion)
    if creado is None:
        return respuesta_error("La categoría ya existe.", codigo=409)
    return respuesta_exito(data=creado, mensaje="Categoría creada.", codigo=201)


@app.route("/api/categorias/<int:categoria_id>", methods=["PUT"])
@login_required
@_rate_limit("30 per minute")
def actualizar_categoria(usuario_id, categoria_id):
    """Actualiza una categoría existente."""
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    valido, errores = validar_categoria(datos, parcial=True)
    if not valido:
        return respuesta_error("Datos inválidos.", errores=errores, codigo=422)

    nombre = datos.get("nombre")
    tipo = datos.get("tipo")
    icono = datos.get("icono")
    descripcion = datos.get("descripcion")

    if nombre is None and tipo is None and icono is None and descripcion is None:
        return respuesta_error("Se requiere al menos un campo a actualizar.", codigo=400)

    actual = CategoriaRepository.obtener_por_id(categoria_id, usuario_id)
    if not actual:
        return respuesta_error("Categoría no encontrada.", codigo=404)

    if nombre is not None:
        nombre = nombre.strip()
    if tipo is not None:
        tipo = tipo.strip().lower()
    if icono is not None:
        icono = str(icono).strip()
    if descripcion is not None:
        descripcion = str(descripcion).strip()

    resultado = CategoriaRepository.actualizar(
        usuario_id,
        categoria_id,
        nombre=nombre,
        tipo=tipo,
        icono=icono,
        descripcion=descripcion,
    )
    if resultado and resultado.get("error") == "duplicate":
        return respuesta_error("La categoría ya existe.", codigo=409)

    actualizada = CategoriaRepository.obtener_por_id(categoria_id, usuario_id)
    return respuesta_exito(data=actualizada, mensaje="Categoría actualizada.")


@app.route("/api/categorias/<int:categoria_id>", methods=["DELETE"])
@login_required
@_rate_limit("20 per minute")
def desactivar_categoria(usuario_id, categoria_id):
    """Borra una categoría para el usuario (soft delete)."""
    exito = CategoriaRepository.desactivar(usuario_id, categoria_id)
    if not exito:
        return respuesta_error("Categoría no encontrada.", codigo=404)
    return respuesta_exito(mensaje="Categoría borrada.")


# ============================================================
#  F4-OCR: ESCANEO DE RECIBOS (NVIDIA NIM)
#  POST /api/ocr/recibo
#  ISO/IEC 25000 - Funcionalidad, Completitud
# ============================================================
@app.route("/api/ocr/recibo", methods=["POST"])
@login_required
def escanear_recibo(usuario_id):
    """Analiza una foto de recibo con OCR y devuelve datos estructurados."""
    datos = request.get_json(silent=True)
    if not datos or "imagen" not in datos:
        return respuesta_error("Se requiere el campo 'imagen' (base64).", codigo=400)

    imagen_b64 = datos["imagen"]

    # Validación de tamaño (máx 10 MB decodificado)
    try:
        imagen_bytes = base64.b64decode(imagen_b64)
        if len(imagen_bytes) > 10 * 1024 * 1024:
            return respuesta_error("Imagen demasiado grande (máx 10 MB).", codigo=413)
    except Exception:
        return respuesta_error("Imagen base64 inválida.", codigo=400)

    # Validación de magic bytes (formatos permitidos)
    MAGIC_BYTES = {
        b"\xff\xd8\xff": "image/jpeg",  # JPEG
        b"\x89PNG\r\n\x1a\n": "image/png",  # PNG
        b"RIFF": "image/webp",  # WebP (primeros 4 bytes)
        b"\x00\x00\x00\x00\x66\x74\x79\x70": "image/heic",  # HEIC (primeros 8 bytes)
    }

    formato_detectado = None
    for magic, mime_type in MAGIC_BYTES.items():
        if imagen_bytes.startswith(magic):
            formato_detectado = mime_type
            break

    # Verificar WebP después de RIFF
    if imagen_bytes[:4] == b"RIFF" and imagen_bytes[8:12] == b"WEBP":
        formato_detectado = "image/webp"

    if not formato_detectado:
        return respuesta_error(
            "Formato de imagen no soportado. Use JPEG, PNG o WebP.", codigo=400
        )

    texto_prueba = None
    if datos.get("texto_prueba") is not None:
        env = os.environ.get("ENVIRONMENT", "development").lower()
        allow_test_text = os.environ.get(
            "OCR_ALLOW_TEST_TEXT", ""
        ).lower() == "true" or env in ("development", "dev", "local", "test")
        if not allow_test_text:
            return respuesta_error(
                "'texto_prueba' solo esta habilitado en entornos de testing.",
                codigo=403,
            )
        texto_prueba = str(datos.get("texto_prueba") or "")[:20000]

    try:
        from ocr import procesar_recibo_base64

        resultado = procesar_recibo_base64(
            imagen_b64,
            mime_type=formato_detectado,
            texto_prueba=texto_prueba,
        )
        resultado["ocr_hibrido"] = True
        resultado["modo_prueba"] = texto_prueba is not None
        return respuesta_exito(data=resultado, mensaje="Recibo analizado.")
    except ValueError as e:
        return respuesta_error(str(e), codigo=503)
    except ImportError as e:
        return respuesta_error(f"Dependencia no disponible: {e}", codigo=503)
    except Exception as e:
        return respuesta_error(f"Error procesando recibo: {e}", codigo=500)


# ============================================================
#  F5-CHAT: ASISTENTE FINANCIERO (NVIDIA NIM LLM)
#  POST /api/chat
#  ISO/IEC 25000 - Funcionalidad, Usabilidad
# ============================================================
@app.route("/api/chat/tools", methods=["GET"])
@login_required
def chat_tools_disponibles(usuario_id):
    """Devuelve el catálogo de herramientas disponibles para el asistente de chat."""
    try:
        from llm import get_chat_tools_catalog

        return respuesta_exito(
            data={"tools": get_chat_tools_catalog()},
            mensaje="Tools del asistente disponibles.",
        )
    except ImportError as e:
        return respuesta_error(f"Dependencia no disponible: {e}", codigo=503)
    except Exception as e:
        return respuesta_error(f"Error obteniendo tools del asistente: {e}", codigo=500)


@app.route("/api/chat", methods=["POST"])
@login_required
def chat_ia(usuario_id):
    """Envía una pregunta al asistente financiero con contexto del usuario."""
    datos = request.get_json(silent=True)
    if not datos or not datos.get("mensaje", "").strip():
        return respuesta_error("Se requiere el campo 'mensaje'.", codigo=400)

    mensaje = datos["mensaje"].strip()
    if len(mensaje) > 2000:
        return respuesta_error(
            "Mensaje demasiado largo (máx 2000 caracteres).", codigo=400
        )

    # Obtener contexto financiero del usuario (robusto por bloques)
    contexto = {}

    try:
        balance = MovimientoRepository.obtener_balance(usuario_id)
        contexto["balance"] = balance
    except Exception:
        contexto["balance"] = {}

    try:
        resumen_30 = MovimientoRepository.obtener_resumen(usuario_id, dias=30)
    except Exception:
        resumen_30 = {}

    try:
        resumen_7 = MovimientoRepository.obtener_resumen(usuario_id, dias=7)
    except Exception:
        resumen_7 = {}

    contexto["resumen"] = resumen_30
    contexto["resumen_30_dias"] = resumen_30
    contexto["resumen_7_dias"] = resumen_7

    try:
        mes_actual = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        contexto["presupuestos_mes_actual"] = PresupuestoRepository.listar_por_usuario(
            usuario_id, mes=mes_actual
        )
    except Exception:
        contexto["presupuestos_mes_actual"] = []

    try:
        contexto["movimientos_recientes"] = MovimientoRepository.listar_por_usuario(
            usuario_id, limite=200
        )
    except Exception:
        contexto["movimientos_recientes"] = []

    try:
        ahora = datetime.now()
        dia_actual = max(1, int(ahora.day))
        dias_del_mes = int(calendar.monthrange(ahora.year, ahora.month)[1])

        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        gastos_mes = MovimientoRepository.listar_por_usuario(
            usuario_id,
            limite=600,
            tipo="gasto",
            fecha_desde=inicio_mes.strftime("%Y-%m-%d %H:%M:%S"),
            fecha_hasta=ahora.strftime("%Y-%m-%d %H:%M:%S"),
        )

        gasto_acumulado = sum(float(m.get("monto", 0) or 0) for m in gastos_mes)
        promedio_diario = gasto_acumulado / dia_actual if dia_actual > 0 else 0
        proyeccion_fin_mes = promedio_diario * dias_del_mes

        contexto["proyeccion_mes_actual"] = {
            "gasto_acumulado": round(gasto_acumulado, 2),
            "dias_transcurridos": dia_actual,
            "dias_del_mes": dias_del_mes,
            "avance_temporal_pct": round((dia_actual / dias_del_mes) * 100, 1)
            if dias_del_mes > 0
            else 0,
            "promedio_diario_mes_actual": round(promedio_diario, 2),
            "proyeccion_gasto_fin_mes": round(proyeccion_fin_mes, 2),
        }
    except Exception:
        contexto["proyeccion_mes_actual"] = {
            "gasto_acumulado": 0.0,
            "dias_transcurridos": 0,
            "dias_del_mes": 0,
            "avance_temporal_pct": 0.0,
            "promedio_diario_mes_actual": 0.0,
            "proyeccion_gasto_fin_mes": 0.0,
        }

    try:
        from llm import chat_financiero

        respuesta = chat_financiero(mensaje, contexto_financiero=contexto)

        if isinstance(respuesta, str):
            payload = {
                "respuesta": respuesta,
                "tools_usadas": [],
            }
        elif isinstance(respuesta, dict):
            payload = {
                "respuesta": str(respuesta.get("respuesta", "")).strip(),
                "tools_usadas": respuesta.get("tools_usadas", []),
            }
        else:
            payload = {
                "respuesta": str(respuesta),
                "tools_usadas": [],
            }

        return respuesta_exito(data=payload, mensaje="Respuesta generada.")
    except ValueError as e:
        return respuesta_error(str(e), codigo=503)
    except ImportError as e:
        return respuesta_error(f"Dependencia no disponible: {e}", codigo=503)
    except Exception as e:
        return respuesta_error(f"Error en asistente IA: {e}", codigo=500)


# ============================================================
#  F5-CHAT LIVE: CONFIGURACIÓN PARA GEMINI LIVE (API KEY)
#  GET /api/chat/live/token
#  GET /api/chat/live/config
#  ISO/IEC 27001 - Seguridad de Información & Control de Acceso
# ============================================================
@app.route("/api/chat/live/token", methods=["GET"])
@app.route("/api/chat/live/config", methods=["GET"])
@login_required
def obtener_config_gemini_live(usuario_id):
    """
    Devuelve la configuración de conexión para Gemini Live al cliente
    autenticado. El cliente usará la API key directamente en el WebSocket
    con ?key=API_KEY (enfoque oficial de Gemini Live).
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key or len(gemini_key) < 10:
        return respuesta_error(
            "GEMINI_API_KEY no configurada en el servidor. Defínela en .env.",
            codigo=501
        )

    return respuesta_exito(
        data={
            "key": gemini_key,
            "model": "models/gemini-3.1-flash-live-preview",
            "ws_url": "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
        },
        mensaje="Configuración de Gemini Live lista."
    )


# ============================================================
#  IA: PERFIL FINANCIERO DEL USUARIO
#  GET  /api/ai/perfil          → Obtener/generar perfil
#  POST /api/ai/daily-insight   → Insight diario tipo Duolingo
#  ISO/IEC 25000 - Funcionalidad avanzada
# ============================================================
@app.route("/api/ai/perfil", methods=["GET"])
@login_required
def obtener_perfil_ia(usuario_id):
    """
    Devuelve el perfil financiero IA del usuario.
    Si existe caché del día, lo devuelve. Si no, lo genera con el LLM.
    """
    force = str(request.args.get("force", "")).strip().lower() in (
        "1",
        "true",
        "yes",
        "si",
    )

    # Verificar caché del día salvo que se haya pedido regenerar.
    if not force:
        perfil_hoy = PerfilIARepository.obtener_hoy(usuario_id)
        if perfil_hoy:
            import json

            # Deserializar listas JSON
            for campo in ("tags", "habitos", "areas_mejora"):
                val = perfil_hoy.get(campo)
                if val and isinstance(val, str):
                    try:
                        perfil_hoy[campo] = json.loads(val)
                    except Exception:
                        perfil_hoy[campo] = []
            if "fecha" in perfil_hoy and hasattr(perfil_hoy["fecha"], "isoformat"):
                perfil_hoy["fecha"] = perfil_hoy["fecha"].isoformat()
            return respuesta_exito(
                data=perfil_hoy, mensaje="Perfil obtenido del caché."
            )

    # Generar nuevo perfil con LLM
    try:
        balance = MovimientoRepository.obtener_balance(usuario_id)
        resumen = MovimientoRepository.obtener_resumen(usuario_id, dias=30)
        contexto = {"balance": balance, "resumen": resumen}

        from llm import generar_perfil_financiero

        perfil = generar_perfil_financiero(contexto)

        # Guardar en caché
        PerfilIARepository.guardar(
            usuario_id=usuario_id,
            tipo_label=perfil.get("tipo_label", "Perfil financiero"),
            score=perfil.get("score", 50),
            tags=perfil.get("tags", []),
            narrativa=perfil.get("narrativa", ""),
            habitos=perfil.get("habitos_positivos", []),
            areas_mejora=perfil.get("areas_mejora", []),
        )

        return respuesta_exito(data=perfil, mensaje="Perfil generado.")

    except ValueError as e:
        return respuesta_error(str(e), codigo=503)
    except ImportError as e:
        return respuesta_error(f"Dependencia no disponible: {e}", codigo=503)
    except Exception as e:
        return respuesta_error(f"Error generando perfil: {e}", codigo=500)


def _generar_insight_diario(usuario_id):
    if InsightDiarioRepository.ya_enviado_hoy(usuario_id):
        return {"ya_existia": True, "insight": None, "fallback_local": False}

    usuario = UsuarioRepository.obtener_por_id(usuario_id)
    nombre = usuario["nombre"].split()[0] if usuario else "Usuario"

    balance = MovimientoRepository.obtener_balance(usuario_id)
    resumen = MovimientoRepository.obtener_resumen(usuario_id, dias=30)
    contexto = {"balance": balance, "resumen": resumen}

    from llm import generar_insight_diario

    fallback_local = False
    try:
        insight_texto = generar_insight_diario(nombre, contexto)
    except ValueError as e:
        err = str(e).lower()
        if (
            "no devolvio contenido" in err
            or "contenido vacio" in err
            or "no devolvio opciones" in err
        ):
            fallback_local = True
            balance_val = float(balance.get("balance", 0) or 0)
            gasto_diario = float(resumen.get("promedio_diario_gasto", 0) or 0)
            variacion = float(resumen.get("variacion_vs_anterior_pct", 0) or 0)
            if variacion > 0:
                tendencia_txt = f"subieron {variacion:.1f}%"
            elif variacion < 0:
                tendencia_txt = f"bajaron {abs(variacion):.1f}%"
            else:
                tendencia_txt = "se mantuvieron estables"

            insight_texto = (
                f"💡 {nombre}, tu balance actual es ${balance_val:,.2f}. "
                f"Tu gasto diario promedio es ${gasto_diario:,.2f} y tus gastos {tendencia_txt} "
                "frente al periodo anterior. Sigue registrando tus movimientos para mejorar tu control financiero."
            )
        else:
            raise

    InsightDiarioRepository.marcar_enviado(usuario_id, insight_texto)

    NotificacionRepository.crear(
        usuario_id=usuario_id,
        titulo="💡 Tu análisis financiero del día",
        mensaje=insight_texto,
        tipo="info",
    )

    try:
        from push import enviar_push

        enviar_push(
            usuario_id=usuario_id,
            titulo="💰 ControlCash — Tu análisis del día",
            mensaje=insight_texto[:100] + ("..." if len(insight_texto) > 100 else ""),
            tag="daily-insight",
        )
    except Exception:
        pass

    return {
        "ya_existia": False,
        "insight": insight_texto,
        "fallback_local": fallback_local,
    }


@app.route("/api/ai/daily-insight", methods=["POST"])
@login_required
def insight_diario(usuario_id):
    """
    Genera el insight financiero diario del usuario (tipo Duolingo).
    Si ya se generó hoy, devuelve el existente sin crear duplicado.
    De lo contrario: genera con LLM, guarda en notificaciones y envía push.
    """
    try:
        data = _generar_insight_diario(usuario_id)
        mensaje = (
            "El insight de hoy ya fue generado."
            if data.get("ya_existia")
            else "Insight diario generado."
        )
        return respuesta_exito(data=data, mensaje=mensaje)
    except ValueError as e:
        return respuesta_error(str(e), codigo=503)
    except ImportError as e:
        return respuesta_error(f"Dependencia no disponible: {e}", codigo=503)
    except Exception as e:
        return respuesta_error(f"Error generando insight: {e}", codigo=500)


def _enviar_resumen_24h(usuario_id):
    resumen = MovimientoRepository.obtener_resumen_24h(usuario_id)
    ingresos = float(resumen.get("total_ingresos", 0) or 0)
    gastos = float(resumen.get("total_gastos", 0) or 0)
    movimientos = int(resumen.get("total_movimientos", 0) or 0)

    if movimientos == 0:
        mensaje = "Resumen 24h: no hubo movimientos registrados en las últimas 24 horas."
    else:
        mensaje = (
            "Resumen 24h: "
            f"Ingresos ${ingresos:,.2f}, "
            f"Gastos ${gastos:,.2f}, "
            f"Movimientos {movimientos}."
        )

    NotificacionRepository.crear(
        usuario_id=usuario_id,
        titulo="🧾 Resumen financiero 24h",
        mensaje=mensaje,
        tipo="info",
    )

    try:
        from push import enviar_push

        enviar_push(
            usuario_id=usuario_id,
            titulo="ControlCash — Resumen 24h",
            mensaje=mensaje[:110] + ("..." if len(mensaje) > 110 else ""),
            tag="resumen-24h",
        )
    except Exception:
        pass


def _ejecutar_job_diario():
    try:
        hoy = datetime.now().strftime("%Y-%m-%d")
        pendientes = RecurrenciaRepository.obtener_pendientes(hoy)
        _procesar_recurrencias_pendientes(pendientes)
    except Exception as e:
        print(f"[JOB] Error en recurrencias diarias: {e}")

    try:
        usuarios = UsuarioRepository.listar_ids_activos()
    except Exception as e:
        print(f"[JOB] Error obteniendo usuarios activos: {e}")
        return

    for usuario_id in usuarios:
        try:
            _generar_insight_diario(usuario_id)
        except Exception as e:
            print(f"[JOB] Insight diario fallo (user {usuario_id}): {e}")

        try:
            _enviar_resumen_24h(usuario_id)
        except Exception as e:
            print(f"[JOB] Resumen 24h fallo (user {usuario_id}): {e}")


_DAILY_JOB_STARTED = False


def _iniciar_job_diario():
    global _DAILY_JOB_STARTED
    if _DAILY_JOB_STARTED:
        return

    habilitado = os.environ.get("DAILY_JOB_ENABLED", "true").lower() in (
        "1",
        "true",
        "yes",
        "si",
    )
    if not habilitado:
        return

    hora = int(os.environ.get("DAILY_JOB_HOUR", "7"))
    minuto = int(os.environ.get("DAILY_JOB_MINUTE", "0"))

    def _loop():
        while True:
            now = datetime.now()
            run_at = now.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            if run_at <= now:
                run_at = run_at + timedelta(days=1)
            wait_seconds = (run_at - now).total_seconds()
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            _ejecutar_job_diario()

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    _DAILY_JOB_STARTED = True


# ============================================================
#  F3-PUSH: WEB PUSH NOTIFICATIONS
#  POST /api/push/subscribe   → Suscribirse
#  POST /api/push/unsubscribe → Desuscribirse
#  GET  /api/push/vapid-key   → Obtener clave pública
#  ISO/IEC 20000 - Gestión de comunicación
# ============================================================
@app.route("/api/push/vapid-key", methods=["GET"])
@login_required
def obtener_vapid_key(usuario_id):
    """Devuelve la clave pública VAPID para suscripción."""
    from push import VAPID_PUBLIC_KEY

    return respuesta_exito(data={"publicKey": VAPID_PUBLIC_KEY})


@app.route("/api/push/subscribe", methods=["POST"])
@login_required
def push_subscribe(usuario_id):
    """Registra una suscripción Web Push."""
    datos = request.get_json(silent=True)
    if not datos or "subscription" not in datos:
        return respuesta_error("Se requiere 'subscription'.", codigo=400)
    from push import guardar_suscripcion

    guardar_suscripcion(usuario_id, datos["subscription"])
    return respuesta_exito(mensaje="Suscripción registrada.")


@app.route("/api/push/unsubscribe", methods=["POST"])
@login_required
def push_unsubscribe(usuario_id):
    """Elimina una suscripción Web Push."""
    datos = request.get_json(silent=True)
    if not datos or "endpoint" not in datos:
        return respuesta_error("Se requiere 'endpoint'.", codigo=400)
    from push import eliminar_suscripcion

    eliminar_suscripcion(usuario_id, datos["endpoint"])
    return respuesta_exito(mensaje="Suscripción eliminada.")


# ============================================================
#  WEBHOOKS
#  POST /api/webhooks           → Registrar webhook
#  ISO/IEC 20000 - Interoperabilidad
# ============================================================
@app.route("/api/webhooks", methods=["POST"])
@login_required
def registrar_webhook_endpoint(usuario_id):
    """Registra una URL de webhook para eventos del usuario."""
    datos = request.get_json(silent=True)
    if not datos or not datos.get("url", "").strip():
        return respuesta_error("Se requiere 'url'.", codigo=400)
    url = datos["url"].strip()
    # Validación básica de URL
    if not url.startswith("https://"):
        return respuesta_error("Solo se permiten URLs HTTPS.", codigo=400)
    from push import registrar_webhook

    registrar_webhook(usuario_id, url)
    return respuesta_exito(mensaje="Webhook registrado.", codigo=201)


# ============================================================
#  PRESUPUESTOS - Metas Financieras
#  ISO/IEC 25000 - Completitud funcional
#  ISO 9001 - Control y mejora continua de procesos
# ============================================================


@app.route("/api/presupuestos", methods=["POST"])
@login_required
@_rate_limit("30 per minute")
def crear_presupuesto(usuario_id):
    """
    Crea o actualiza un presupuesto mensual para una categoría.
    Body JSON: { categoria_id: int|null, monto_limite: float, mes: "YYYY-MM-01" }
    """
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Se requieren datos JSON.", codigo=400)

    monto = datos.get("monto_limite")
    mes = datos.get("mes")
    categoria_id = datos.get("categoria_id")  # None = presupuesto global

    # Validaciones
    if monto is None:
        return respuesta_error("Se requiere 'monto_limite'.", codigo=400)
    try:
        monto = float(monto)
        if monto <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return respuesta_error(
            "'monto_limite' debe ser un número positivo.", codigo=400
        )

    if not mes:
        return respuesta_error("Se requiere 'mes' (formato YYYY-MM-01).", codigo=400)

    # Validar formato de mes
    try:
        from datetime import datetime as dt

        fecha_mes = dt.strptime(mes, "%Y-%m-%d")
        if fecha_mes.day != 1:
            mes = fecha_mes.replace(day=1).strftime("%Y-%m-%d")
    except ValueError:
        return respuesta_error("Formato de 'mes' inválido. Use YYYY-MM-01.", codigo=400)

    # Validar categoría si se proporciona
    if categoria_id is not None:
        cat = CategoriaRepository.obtener_por_id(int(categoria_id), usuario_id)
        if not cat:
            return respuesta_error("Categoría no encontrada.", codigo=404)

    resultado = PresupuestoRepository.crear(usuario_id, categoria_id, monto, mes)
    if resultado:
        return respuesta_exito(
            mensaje="Presupuesto guardado.", data=resultado, codigo=201
        )
    return respuesta_error("Error al guardar presupuesto.", codigo=500)


@app.route("/api/presupuestos", methods=["GET"])
@login_required
def listar_presupuestos(usuario_id):
    """
    Lista presupuestos del usuario con gasto actual vs límite.
    Query params: ?mes=YYYY-MM-01 (opcional)
    """
    mes = request.args.get("mes")
    presupuestos = PresupuestoRepository.listar_por_usuario(usuario_id, mes=mes)
    return respuesta_exito(data=presupuestos)


@app.route("/api/presupuestos/comparativo", methods=["GET"])
@login_required
def comparar_presupuestos_mes(usuario_id):
    """
    Compara gasto del mes actual vs mes anterior.
    Query params: ?mes=YYYY-MM-01 (opcional) & categoria_id (opcional)
    """
    mes = request.args.get("mes")
    categoria_id = request.args.get("categoria_id", type=int)

    if mes:
        try:
            mes_dt = datetime.strptime(mes, "%Y-%m-%d")
            mes_actual_dt = mes_dt.replace(day=1)
        except ValueError:
            return respuesta_error("Formato de 'mes' inválido. Use YYYY-MM-01.", codigo=400)
    else:
        hoy = datetime.now()
        mes_actual_dt = hoy.replace(day=1)

    prev_ref = mes_actual_dt - timedelta(days=1)
    mes_anterior_dt = prev_ref.replace(day=1)

    mes_actual = mes_actual_dt.strftime("%Y-%m-%d")
    mes_anterior = mes_anterior_dt.strftime("%Y-%m-%d")

    data = PresupuestoRepository.comparar_mes(
        usuario_id, mes_actual, mes_anterior, categoria_id
    )
    data.update({
        "mes_actual": mes_actual,
        "mes_anterior": mes_anterior,
        "categoria_id": categoria_id,
    })
    return respuesta_exito(data=data)


@app.route("/api/presupuestos/<int:presupuesto_id>", methods=["DELETE"])
@login_required
def eliminar_presupuesto(usuario_id, presupuesto_id):
    """Desactiva un presupuesto (soft delete)."""
    eliminado = PresupuestoRepository.eliminar(presupuesto_id, usuario_id)
    if eliminado:
        return respuesta_exito(mensaje="Presupuesto eliminado.")
    return respuesta_error("Presupuesto no encontrado.", codigo=404)


@app.route("/api/presupuestos/verificar", methods=["GET"])
@login_required
def verificar_presupuesto(usuario_id):
    """
    Verifica si el usuario ha excedido su presupuesto para una categoría.
    Query params: ?categoria_id=X&mes=YYYY-MM-01
    """
    categoria_id = request.args.get("categoria_id", type=int)
    mes = request.args.get("mes")

    if not categoria_id or not mes:
        return respuesta_error("Se requieren 'categoria_id' y 'mes'.", codigo=400)

    estado = PresupuestoRepository.verificar_exceso(usuario_id, categoria_id, mes)
    if estado is None:
        return respuesta_exito(data={"tiene_presupuesto": False})

    estado["tiene_presupuesto"] = True
    return respuesta_exito(data=estado)


# ============================================================
#  RECURRENCIAS - Movimientos Automáticos
#  ISO/IEC 12207 - Automatización de procesos
#  ISO/IEC 20000 - Gestión de servicios recurrentes
# ============================================================


@app.route("/api/recurrencias", methods=["POST"])
@login_required
@_rate_limit("20 per minute")
def crear_recurrencia(usuario_id):
    """
    Crea un movimiento recurrente (suscripción, salario, renta).
    Body JSON: {
        categoria_id: int,
        tipo: "ingreso"|"gasto",
        monto: float,
        descripcion: string,
        frecuencia: "diario"|"semanal"|"quincenal"|"mensual"|"anual",
        dia_ejecucion: int (1-31),
        proxima_fecha: "YYYY-MM-DD"
    }
    """
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Se requieren datos JSON.", codigo=400)

    # Extraer y validar campos
    categoria_id = datos.get("categoria_id")
    tipo = datos.get("tipo", "").strip().lower()
    monto = datos.get("monto")
    descripcion = datos.get("descripcion", "")
    frecuencia = datos.get("frecuencia", "").strip().lower()
    dia_ejecucion = datos.get("dia_ejecucion")
    proxima_fecha = datos.get("proxima_fecha")

    # Validaciones
    errores = []
    if not categoria_id:
        errores.append("Se requiere 'categoria_id'.")
    if tipo not in ("ingreso", "gasto"):
        errores.append("'tipo' debe ser 'ingreso' o 'gasto'.")
    if frecuencia not in ("diario", "semanal", "quincenal", "mensual", "anual"):
        errores.append("'frecuencia' inválida.")
    if not proxima_fecha:
        errores.append("Se requiere 'proxima_fecha'.")

    try:
        monto = float(monto)
        if monto <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        errores.append("'monto' debe ser un número positivo.")

    if dia_ejecucion is not None:
        try:
            dia_ejecucion = int(dia_ejecucion)
            if not (1 <= dia_ejecucion <= 31):
                raise ValueError()
        except (ValueError, TypeError):
            errores.append("'dia_ejecucion' debe ser entre 1 y 31.")

    if errores:
        return respuesta_error(" ".join(errores), codigo=400)

    # Validar categoría
    cat = CategoriaRepository.obtener_por_id(int(categoria_id), usuario_id)
    if not cat:
        return respuesta_error("Categoría no encontrada.", codigo=404)

    # Validar que el tipo coincida con la categoría
    if cat["tipo"] != tipo:
        return respuesta_error(
            f"La categoría '{cat['nombre']}' es de tipo '{cat['tipo']}', no '{tipo}'.",
            codigo=400,
        )

    resultado = RecurrenciaRepository.crear(
        usuario_id,
        categoria_id,
        tipo,
        monto,
        descripcion,
        frecuencia,
        dia_ejecucion,
        proxima_fecha,
    )
    if resultado:
        return respuesta_exito(
            mensaje="Recurrencia creada.", data=resultado, codigo=201
        )
    return respuesta_error("Error al crear recurrencia.", codigo=500)


@app.route("/api/recurrencias", methods=["GET"])
@login_required
def listar_recurrencias(usuario_id):
    """
    Lista recurrencias del usuario.
    Query params: ?incluir_inactivas=true (opcional)
    """
    incluir_inactivas = request.args.get("incluir_inactivas", "").lower() == "true"
    recurrencias = RecurrenciaRepository.listar_por_usuario(
        usuario_id, solo_activas=not incluir_inactivas
    )
    return respuesta_exito(data=recurrencias)


@app.route("/api/recurrencias/<int:recurrencia_id>", methods=["DELETE"])
@login_required
def desactivar_recurrencia(usuario_id, recurrencia_id):
    """Desactiva una recurrencia (soft delete)."""
    desactivada = RecurrenciaRepository.desactivar(recurrencia_id, usuario_id)
    if desactivada:
        return respuesta_exito(mensaje="Recurrencia desactivada.")
    return respuesta_error("Recurrencia no encontrada.", codigo=404)


@app.route("/api/recurrencias/<int:recurrencia_id>/reactivar", methods=["POST"])
@login_required
def reactivar_recurrencia(usuario_id, recurrencia_id):
    """
    Reactiva una recurrencia con nueva fecha.
    Body JSON: { proxima_fecha: "YYYY-MM-DD" }
    """
    datos = request.get_json(silent=True)
    if not datos or not datos.get("proxima_fecha"):
        return respuesta_error("Se requiere 'proxima_fecha'.", codigo=400)

    reactivada = RecurrenciaRepository.reactivar(
        recurrencia_id, usuario_id, datos["proxima_fecha"]
    )
    if reactivada:
        return respuesta_exito(mensaje="Recurrencia reactivada.")
    return respuesta_error("Recurrencia no encontrada.", codigo=404)


def _procesar_recurrencias_pendientes(pendientes):
    movimientos_creados = []
    for rec in pendientes:
        mov = MovimientoRepository.crear(
            usuario_id=rec["usuario_id"],
            categoria_id=rec["categoria_id"],
            tipo=rec["tipo"],
            monto=rec["monto"],
            descripcion=f"[Auto] {rec['descripcion']}".strip(),
            fecha=rec["proxima_fecha"],
        )
        if mov:
            movimientos_creados.append(mov)

        fecha_actual = datetime.strptime(rec["proxima_fecha"], "%Y-%m-%d")
        if rec["frecuencia"] == "diario":
            nueva_fecha = fecha_actual + timedelta(days=1)
        elif rec["frecuencia"] == "semanal":
            nueva_fecha = fecha_actual + timedelta(weeks=1)
        elif rec["frecuencia"] == "quincenal":
            nueva_fecha = fecha_actual + timedelta(days=15)
        elif rec["frecuencia"] == "mensual":
            mes = fecha_actual.month + 1
            anio = fecha_actual.year
            if mes > 12:
                mes = 1
                anio += 1
            ultimo_dia_mes = calendar.monthrange(anio, mes)[1]
            dia_deseado = rec.get("dia_ejecucion") or fecha_actual.day
            dia = min(int(dia_deseado), ultimo_dia_mes)
            nueva_fecha = fecha_actual.replace(year=anio, month=mes, day=dia)
        elif rec["frecuencia"] == "anual":
            nueva_fecha = fecha_actual.replace(year=fecha_actual.year + 1)
        else:
            nueva_fecha = fecha_actual + timedelta(days=30)

        RecurrenciaRepository.actualizar_proxima_fecha(
            rec["id"], nueva_fecha.strftime("%Y-%m-%d")
        )

    return movimientos_creados


@app.route("/api/recurrencias/ejecutar", methods=["POST"])
@login_required
@_rate_limit("5 per minute")
def ejecutar_recurrencias_pendientes(usuario_id):
    """
    Ejecuta todas las recurrencias pendientes del usuario hasta hoy.
    Crea los movimientos correspondientes y actualiza próximas fechas.
    Útil para sincronización manual o al abrir la app.
    """
    hoy = datetime.now().strftime("%Y-%m-%d")
    pendientes = RecurrenciaRepository.obtener_pendientes(hoy)

    # Filtrar solo las del usuario actual
    pendientes_usuario = [r for r in pendientes if r["usuario_id"] == usuario_id]

    movimientos_creados = _procesar_recurrencias_pendientes(pendientes_usuario)

    return respuesta_exito(
        mensaje=f"{len(movimientos_creados)} movimientos creados.",
        data={
            "movimientos_creados": len(movimientos_creados),
            "movimientos": movimientos_creados,
        },
    )


# ============================================================
#  SEGURIDAD - Estado del Cifrado AES-256
#  ISO/IEC 27001 - Gestión de seguridad de la información
# ============================================================


@app.route("/api/security/status", methods=["GET"])
@login_required
def security_status(usuario_id):
    """
    Retorna el estado de seguridad del sistema.
    ISO/IEC 27001 - Monitoreo de controles de seguridad
    """
    import os

    from db import get_crypto_backend, is_crypto_available

    # Verificar configuración de cifrado
    encrypt_enabled = os.environ.get("ENCRYPT_SENSITIVE_DATA", "").lower() == "true"
    master_key_configured = bool(os.environ.get("AES_MASTER_KEY", ""))

    return respuesta_exito(
        data={
            "cifrado": {
                "disponible": is_crypto_available(),
                "backend": get_crypto_backend(),
                "habilitado": encrypt_enabled,
                "clave_configurada": master_key_configured,
                "algoritmo": "AES-256-GCM" if is_crypto_available() else None,
            },
            "hashing": {
                "algoritmo": "PBKDF2-SHA256",
                "iteraciones": 100000,
                "salt": "único por usuario",
            },
            "sesion": {"timeout_minutos": 15, "csrf_protegido": True},
            "rate_limiting": {
                "activo": LIMITER_AVAILABLE,
                "limite_default": "300/minuto",
            },
            "normas": [
                "ISO/IEC 27001 - Seguridad de la información",
                "OWASP Top 10 - Protección de datos sensibles",
                "NIST SP 800-38D - AES-GCM",
                "NIST SP 800-132 - PBKDF2",
            ],
        }
    )


@app.route("/api/security/encrypt-test", methods=["POST"])
@login_required
@_rate_limit("10 per minute")
def test_encryption(usuario_id):
    """
    Endpoint de prueba para verificar que el cifrado funciona correctamente.
    Solo para debugging/verificación - no usar en producción con datos reales.
    """
    from db import decrypt, encrypt, is_crypto_available

    if not is_crypto_available():
        return respuesta_error(
            "Cifrado no disponible. Instala: pip install cryptography", codigo=503
        )

    datos = request.get_json(silent=True)
    texto = (
        datos.get("texto", "Prueba de cifrado AES-256-GCM")
        if datos
        else "Prueba de cifrado AES-256-GCM"
    )

    try:
        # Cifrar con AAD vinculado al usuario
        cifrado = encrypt(texto, associated_data=str(usuario_id))

        # Descifrar
        descifrado = decrypt(cifrado, associated_data=str(usuario_id))

        return respuesta_exito(
            mensaje="Cifrado verificado correctamente.",
            data={
                "original": texto,
                "cifrado": cifrado[:50] + "..." if len(cifrado) > 50 else cifrado,
                "cifrado_longitud": len(cifrado),
                "descifrado": descifrado,
                "coincide": texto == descifrado,
                "algoritmo": "AES-256-GCM",
                "aad": f"user_{usuario_id}",
            },
        )
    except Exception as e:
        return respuesta_error(f"Error en cifrado: {str(e)}", codigo=500)


# ============================================================
#  ESTADO DEL SERVIDOR — MEJORADO
#  GET /api/health
# ============================================================
@app.route("/api/health", methods=["GET"])
def health():
    """
    Verifica el estado del servicio con métricas detalladas.
    ISO/IEC 20000 - Gestión de disponibilidad del servicio
    """
    uptime_segundos = int(time.time() - _START_TIME)

    # Verificar conectividad de la base de datos (MySQL/MariaDB)
    db_status = "desconectada"
    try:
        from db.config import MYSQL_DATABASE, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER
        import pymysql

        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=int(MYSQL_PORT),
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD or "",
            connect_timeout=3
        )
        conn.close()
        db_status = "conectada"
    except Exception:
        pass

    return respuesta_exito(
        data={
            "servicio": "ControlCash API",
            "version": "2.1.0",
            "uptime_segundos": uptime_segundos,
            "uptime_legible": f"{uptime_segundos // 3600}h {(uptime_segundos % 3600) // 60}m",
            "base_datos": db_status,
            "ia": {"nvidia_configurada": bool(os.environ.get("NVIDIA_API_KEY"))},
            "rate_limiting": "activo" if LIMITER_AVAILABLE else "desactivado",
            "timestamp": datetime.now().isoformat(),
        },
        mensaje="Servicio operativo.",
    )


# ============================================================
#  SERVIR FRONTEND
#  Cualquier ruta que no sea /api/* devuelve index.html
#  Permite que el frontend funcione en el mismo servidor
# ============================================================
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Sirve el frontend desde la carpeta app/."""
    if path and os.path.exists(os.path.join(_APP_DIR, path)):
        return send_from_directory(_APP_DIR, path)
    return send_from_directory(_APP_DIR, "index.html")


# Inicializar job diario (insight + resumen + recurrencias)
_iniciar_job_diario()


# ============================================================
#  PUNTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5000))
    host = os.environ.get("API_HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"[API] Servidor corriendo en: http://{host}:{port}")
    print(f"[API] Abre en el navegador:  http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
