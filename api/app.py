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

import os
import sys
import csv
import io
import time
import secrets
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory, Response
from flask_cors import CORS

# Cargar variables de entorno desde .env (si existe)
_PROJECT_DIR_EARLY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_PROJECT_DIR_EARLY, '.env'))
except ImportError:
    pass

# Rutas base del proyecto
_API_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_API_DIR)
_APP_DIR     = os.path.join(_PROJECT_DIR, 'app')

# Agregar directorios al path
sys.path.insert(0, _API_DIR)      # para importar validators
sys.path.insert(0, _PROJECT_DIR)  # para importar db

from db import (
    init_database,
    UsuarioRepository,
    CategoriaRepository,
    MovimientoRepository,
    NotificacionRepository,
    PerfilIARepository,
    InsightDiarioRepository,
)
from validators import validar_registro, validar_login, validar_movimiento

# ============================================================
#  CONFIGURACIÓN DE LA APLICACIÓN
#  ISO/IEC 20000 - Gestión de configuración del servicio
# ============================================================
app = Flask(__name__, static_folder=_APP_DIR, static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app, supports_credentials=True,
     origins=["http://localhost:5000", "http://127.0.0.1:5000"])

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
except ImportError:
    LIMITER_AVAILABLE = False
    limiter = None
    print("[WARN] flask-limiter no instalado. Rate limiting desactivado.")


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
# ============================================================
def login_required(f):
    """Decorador que verifica que el usuario esté autenticado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({"error": "Sesión no válida. Inicie sesión."}), 401
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


# ============================================================
#  F1: REGISTRARSE
#  POST /api/auth/registro
#  IEEE 730 - Trazabilidad del proceso de registro
# ============================================================
@app.route('/api/auth/registro', methods=['POST'])
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

    usuario = UsuarioRepository.crear(
        nombre=datos['nombre'],
        email=datos['email'],
        password=datos['password']
    )

    if usuario is None:
        return respuesta_error("El email ya está registrado.", codigo=409)

    # F6: Notificación - Bienvenida
    NotificacionRepository.crear(
        usuario_id=usuario['id'],
        titulo="¡Bienvenido!",
        mensaje=f"Hola {usuario['nombre']}, tu cuenta ha sido creada exitosamente. "
                "Comienza a registrar tus movimientos financieros.",
        tipo="exito"
    )

    return respuesta_exito(
        data={"id": usuario['id'], "nombre": usuario['nombre'], "email": usuario['email']},
        mensaje="Registro exitoso.",
        codigo=201
    )


# ============================================================
#  F2: INICIAR SESIÓN
#  POST /api/auth/login
#  ISO 9126 - Seguridad: Autenticación
# ============================================================
@app.route('/api/auth/login', methods=['POST'])
@_rate_limit("5 per minute")
def login():
    """Permite al usuario autenticarse en el sistema."""
    datos = request.get_json(silent=True)
    if not datos:
        return respuesta_error("Datos no proporcionados.", codigo=400)

    valido, errores = validar_login(datos)
    if not valido:
        return respuesta_error("Datos inválidos.", errores=errores, codigo=422)

    usuario = UsuarioRepository.autenticar(
        email=datos['email'],
        password=datos['password']
    )

    if usuario is None:
        return respuesta_error("Credenciales incorrectas.", codigo=401)

    session['usuario_id'] = usuario['id']
    session['usuario_nombre'] = usuario['nombre']

    no_leidas = NotificacionRepository.contar_no_leidas(usuario['id'])

    return respuesta_exito(
        data={
            "id": usuario['id'],
            "nombre": usuario['nombre'],
            "email": usuario['email'],
            "notificaciones_no_leidas": no_leidas
        },
        mensaje="Inicio de sesión exitoso."
    )


# ============================================================
#  CERRAR SESIÓN
#  POST /api/auth/logout
# ============================================================
@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout(usuario_id):
    """Cierra la sesión del usuario."""
    session.clear()
    return respuesta_exito(mensaje="Sesión cerrada correctamente.")


# ============================================================
#  F3: GESTIONAR MOVIMIENTO
#  POST   /api/movimientos          → Crear movimiento
#  GET    /api/movimientos          → Listar movimientos
#  PUT    /api/movimientos/<id>     → Editar movimiento  ← NUEVO
#  DELETE /api/movimientos/<id>     → Eliminar movimiento
#  GET    /api/movimientos/export/csv → Exportar CSV     ← NUEVO
#  ISO 9001 - Trazabilidad de registros financieros
# ============================================================
@app.route('/api/movimientos', methods=['POST'])
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
    categoria = CategoriaRepository.obtener_por_id(int(datos['categoria_id']))
    if not categoria:
        return respuesta_error("La categoría no existe.", codigo=404)

    movimiento = MovimientoRepository.crear(
        usuario_id=usuario_id,
        categoria_id=int(datos['categoria_id']),
        tipo=datos['tipo'],
        monto=float(datos['monto']),
        descripcion=datos.get('descripcion', ''),
        fecha=datos.get('fecha')
    )

    # F6: Notificación al registrar gasto grande
    if datos['tipo'] == 'gasto' and float(datos['monto']) >= 1000:
        NotificacionRepository.crear(
            usuario_id=usuario_id,
            titulo="Gasto importante registrado",
            mensaje=f"Has registrado un gasto de ${float(datos['monto']):,.2f} "
                    f"en {categoria['nombre']}. Revisa tu balance.",
            tipo="alerta"
        )

    return respuesta_exito(data=movimiento, mensaje="Movimiento registrado.", codigo=201)


@app.route('/api/movimientos', methods=['GET'])
@login_required
def listar_movimientos(usuario_id):
    """Lista los movimientos del usuario con filtros opcionales."""
    tipo = request.args.get('tipo')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    limite = min(int(request.args.get('limite', 50)), 200)
    # Filtros adicionales por categoría y monto
    categoria_id = request.args.get('categoria_id')
    monto_min = request.args.get('monto_min')
    monto_max = request.args.get('monto_max')

    movimientos = MovimientoRepository.listar_por_usuario(
        usuario_id=usuario_id,
        limite=limite,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

    # Filtros adicionales en memoria (categoría y monto)
    if categoria_id:
        movimientos = [m for m in movimientos if str(m.get('categoria_id', '')) == str(categoria_id)]
    if monto_min:
        movimientos = [m for m in movimientos if float(m.get('monto', 0)) >= float(monto_min)]
    if monto_max:
        movimientos = [m for m in movimientos if float(m.get('monto', 0)) <= float(monto_max)]

    return respuesta_exito(data=movimientos)


@app.route('/api/movimientos/export/csv', methods=['GET'])
@login_required
def exportar_movimientos_csv(usuario_id):
    """
    Exporta los movimientos del usuario en formato CSV.
    Soporta los mismos filtros que GET /api/movimientos.
    ISO 9001 - Exportación y trazabilidad de datos
    """
    tipo = request.args.get('tipo')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    movimientos = MovimientoRepository.listar_por_usuario(
        usuario_id=usuario_id,
        limite=200,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Tipo', 'Monto', 'Categoría', 'Descripción', 'Fecha'])
    for m in movimientos:
        writer.writerow([
            m.get('id', ''),
            m.get('tipo', ''),
            f"{m.get('monto', 0):.2f}",
            m.get('categoria_nombre', ''),
            m.get('descripcion', ''),
            str(m.get('fecha', ''))[:10],
        ])

    csv_content = output.getvalue()
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    filename = f"controlcash_movimientos_{fecha_hoy}.csv"

    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv; charset=utf-8',
        }
    )


@app.route('/api/movimientos/<int:movimiento_id>', methods=['PUT'])
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
    if 'categoria_id' in datos:
        categoria = CategoriaRepository.obtener_por_id(int(datos['categoria_id']))
        if not categoria:
            return respuesta_error("La categoría no existe.", codigo=404)

    # Validar monto si se proporciona
    if 'monto' in datos:
        try:
            monto = float(datos['monto'])
            if monto <= 0 or monto > 999999999.99:
                return respuesta_error("Monto fuera de rango válido.", codigo=422)
        except (ValueError, TypeError):
            return respuesta_error("Monto inválido.", codigo=422)

    # Validar tipo si se proporciona
    if 'tipo' in datos and datos['tipo'] not in ('ingreso', 'gasto'):
        return respuesta_error("Tipo debe ser 'ingreso' o 'gasto'.", codigo=422)

    actualizado = MovimientoRepository.actualizar(
        movimiento_id=movimiento_id,
        usuario_id=usuario_id,
        categoria_id=datos.get('categoria_id'),
        tipo=datos.get('tipo'),
        monto=datos.get('monto'),
        descripcion=datos.get('descripcion'),
        fecha=datos.get('fecha'),
    )

    if not actualizado:
        return respuesta_error("Movimiento no encontrado.", codigo=404)

    return respuesta_exito(data=actualizado, mensaje="Movimiento actualizado.")


@app.route('/api/movimientos/<int:movimiento_id>', methods=['DELETE'])
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
@app.route('/api/balance', methods=['GET'])
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
@app.route('/api/notificaciones', methods=['GET'])
@login_required
def listar_notificaciones(usuario_id):
    """Lista las notificaciones del usuario."""
    solo_no_leidas = request.args.get('no_leidas', '').lower() == 'true'
    notificaciones = NotificacionRepository.listar_por_usuario(
        usuario_id, solo_no_leidas=solo_no_leidas
    )
    return respuesta_exito(data=notificaciones)


@app.route('/api/notificaciones/<int:notificacion_id>', methods=['PUT'])
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
@app.route('/api/resumen', methods=['GET'])
@login_required
def obtener_resumen(usuario_id):
    """Genera resumen financiero del usuario."""
    dias = min(int(request.args.get('dias', 30)), 365)
    resumen = MovimientoRepository.obtener_resumen(usuario_id, dias=dias)
    balance = MovimientoRepository.obtener_balance(usuario_id)
    resumen['balance'] = balance
    return respuesta_exito(data=resumen)


# ============================================================
#  CATEGORÍAS
#  GET /api/categorias
# ============================================================
@app.route('/api/categorias', methods=['GET'])
@login_required
def listar_categorias(usuario_id):
    """Lista las categorías disponibles."""
    tipo = request.args.get('tipo')
    categorias = CategoriaRepository.listar(tipo=tipo)
    return respuesta_exito(data=categorias)


# ============================================================
#  F4-OCR: ESCANEO DE RECIBOS (NVIDIA NIM)
#  POST /api/ocr/recibo
#  ISO/IEC 25000 - Funcionalidad, Completitud
# ============================================================
@app.route('/api/ocr/recibo', methods=['POST'])
@login_required
def escanear_recibo(usuario_id):
    """Analiza una foto de recibo con OCR y devuelve datos estructurados."""
    datos = request.get_json(silent=True)
    if not datos or 'imagen' not in datos:
        return respuesta_error("Se requiere el campo 'imagen' (base64).", codigo=400)

    imagen_b64 = datos['imagen']
    # Validar que es base64 razonable (máx 10 MB codificado)
    if len(imagen_b64) > 10 * 1024 * 1024 * 4 // 3:
        return respuesta_error("Imagen demasiado grande (máx 10 MB).", codigo=413)

    try:
        from ocr import procesar_recibo_base64
        resultado = procesar_recibo_base64(imagen_b64)
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
@app.route('/api/chat', methods=['POST'])
@login_required
def chat_ia(usuario_id):
    """Envía una pregunta al asistente financiero con contexto del usuario."""
    datos = request.get_json(silent=True)
    if not datos or not datos.get('mensaje', '').strip():
        return respuesta_error("Se requiere el campo 'mensaje'.", codigo=400)

    mensaje = datos['mensaje'].strip()
    if len(mensaje) > 2000:
        return respuesta_error("Mensaje demasiado largo (máx 2000 caracteres).", codigo=400)

    # Obtener contexto financiero del usuario
    try:
        balance = MovimientoRepository.obtener_balance(usuario_id)
        resumen = MovimientoRepository.obtener_resumen(usuario_id, dias=30)
        contexto = {"balance": balance, "resumen": resumen}
    except Exception:
        contexto = None

    try:
        from llm import chat_financiero
        respuesta = chat_financiero(mensaje, contexto_financiero=contexto)
        return respuesta_exito(
            data={"respuesta": respuesta},
            mensaje="Respuesta generada."
        )
    except ValueError as e:
        return respuesta_error(str(e), codigo=503)
    except ImportError as e:
        return respuesta_error(f"Dependencia no disponible: {e}", codigo=503)
    except Exception as e:
        return respuesta_error(f"Error en asistente IA: {e}", codigo=500)


# ============================================================
#  IA: PERFIL FINANCIERO DEL USUARIO
#  GET  /api/ai/perfil          → Obtener/generar perfil
#  POST /api/ai/daily-insight   → Insight diario tipo Duolingo
#  ISO/IEC 25000 - Funcionalidad avanzada
# ============================================================
@app.route('/api/ai/perfil', methods=['GET'])
@login_required
def obtener_perfil_ia(usuario_id):
    """
    Devuelve el perfil financiero IA del usuario.
    Si existe caché del día, lo devuelve. Si no, lo genera con el LLM.
    """
    # Verificar caché del día
    perfil_hoy = PerfilIARepository.obtener_hoy(usuario_id)
    if perfil_hoy:
        import json
        # Deserializar listas JSON
        for campo in ('tags', 'habitos', 'areas_mejora'):
            val = perfil_hoy.get(campo)
            if val and isinstance(val, str):
                try:
                    perfil_hoy[campo] = json.loads(val)
                except Exception:
                    perfil_hoy[campo] = []
        if 'fecha' in perfil_hoy and hasattr(perfil_hoy['fecha'], 'isoformat'):
            perfil_hoy['fecha'] = perfil_hoy['fecha'].isoformat()
        return respuesta_exito(data=perfil_hoy, mensaje="Perfil obtenido del caché.")

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


@app.route('/api/ai/daily-insight', methods=['POST'])
@login_required
def insight_diario(usuario_id):
    """
    Genera el insight financiero diario del usuario (tipo Duolingo).
    Si ya se generó hoy, devuelve el existente sin crear duplicado.
    De lo contrario: genera con LLM, guarda en notificaciones y envía push.
    """
    # Verificar si ya se envió hoy
    if InsightDiarioRepository.ya_enviado_hoy(usuario_id):
        return respuesta_exito(
            data={"ya_existia": True, "insight": None},
            mensaje="El insight de hoy ya fue generado."
        )

    try:
        # Obtener datos del usuario
        usuario = UsuarioRepository.obtener_por_id(usuario_id)
        nombre = usuario['nombre'].split()[0] if usuario else "Usuario"

        balance = MovimientoRepository.obtener_balance(usuario_id)
        resumen = MovimientoRepository.obtener_resumen(usuario_id, dias=30)
        contexto = {"balance": balance, "resumen": resumen}

        from llm import generar_insight_diario
        insight_texto = generar_insight_diario(nombre, contexto)

        # Guardar en DB como insight del día
        InsightDiarioRepository.marcar_enviado(usuario_id, insight_texto)

        # Crear notificación en el panel
        NotificacionRepository.crear(
            usuario_id=usuario_id,
            titulo="💡 Tu análisis financiero del día",
            mensaje=insight_texto,
            tipo="info"
        )

        # Enviar push notification al dispositivo
        try:
            from push import enviar_push
            enviar_push(
                usuario_id=usuario_id,
                titulo="💰 ControlCash — Tu análisis del día",
                mensaje=insight_texto[:100] + ("..." if len(insight_texto) > 100 else ""),
                tag="daily-insight"
            )
        except Exception:
            pass  # Push es opcional, no bloquea la respuesta

        return respuesta_exito(
            data={"ya_existia": False, "insight": insight_texto},
            mensaje="Insight diario generado."
        )

    except ValueError as e:
        return respuesta_error(str(e), codigo=503)
    except ImportError as e:
        return respuesta_error(f"Dependencia no disponible: {e}", codigo=503)
    except Exception as e:
        return respuesta_error(f"Error generando insight: {e}", codigo=500)


# ============================================================
#  F3-PUSH: WEB PUSH NOTIFICATIONS
#  POST /api/push/subscribe   → Suscribirse
#  POST /api/push/unsubscribe → Desuscribirse
#  GET  /api/push/vapid-key   → Obtener clave pública
#  ISO/IEC 20000 - Gestión de comunicación
# ============================================================
@app.route('/api/push/vapid-key', methods=['GET'])
@login_required
def obtener_vapid_key(usuario_id):
    """Devuelve la clave pública VAPID para suscripción."""
    from push import VAPID_PUBLIC_KEY
    return respuesta_exito(data={"publicKey": VAPID_PUBLIC_KEY})


@app.route('/api/push/subscribe', methods=['POST'])
@login_required
def push_subscribe(usuario_id):
    """Registra una suscripción Web Push."""
    datos = request.get_json(silent=True)
    if not datos or 'subscription' not in datos:
        return respuesta_error("Se requiere 'subscription'.", codigo=400)
    from push import guardar_suscripcion
    guardar_suscripcion(usuario_id, datos['subscription'])
    return respuesta_exito(mensaje="Suscripción registrada.")


@app.route('/api/push/unsubscribe', methods=['POST'])
@login_required
def push_unsubscribe(usuario_id):
    """Elimina una suscripción Web Push."""
    datos = request.get_json(silent=True)
    if not datos or 'endpoint' not in datos:
        return respuesta_error("Se requiere 'endpoint'.", codigo=400)
    from push import eliminar_suscripcion
    eliminar_suscripcion(usuario_id, datos['endpoint'])
    return respuesta_exito(mensaje="Suscripción eliminada.")


# ============================================================
#  WEBHOOKS
#  POST /api/webhooks           → Registrar webhook
#  ISO/IEC 20000 - Interoperabilidad
# ============================================================
@app.route('/api/webhooks', methods=['POST'])
@login_required
def registrar_webhook_endpoint(usuario_id):
    """Registra una URL de webhook para eventos del usuario."""
    datos = request.get_json(silent=True)
    if not datos or not datos.get('url', '').strip():
        return respuesta_error("Se requiere 'url'.", codigo=400)
    url = datos['url'].strip()
    # Validación básica de URL
    if not url.startswith('https://'):
        return respuesta_error("Solo se permiten URLs HTTPS.", codigo=400)
    from push import registrar_webhook
    registrar_webhook(usuario_id, url)
    return respuesta_exito(mensaje="Webhook registrado.", codigo=201)


# ============================================================
#  ESTADO DEL SERVIDOR — MEJORADO
#  GET /api/health
# ============================================================
@app.route('/api/health', methods=['GET'])
def health():
    """
    Verifica el estado del servicio con métricas detalladas.
    ISO/IEC 20000 - Gestión de disponibilidad del servicio
    """
    uptime_segundos = int(time.time() - _START_TIME)

    # Verificar conectividad de la base de datos
    db_status = "desconectada"
    try:
        from db.config import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
        import pg8000
        conn = pg8000.connect(
            host=PG_HOST, port=int(PG_PORT), database=PG_DATABASE,
            user=PG_USER, password=PG_PASSWORD or ""
        )
        conn.close()
        db_status = "conectada"
    except Exception:
        pass

    return respuesta_exito(data={
        "servicio": "ControlCash API",
        "version": "2.1.0",
        "uptime_segundos": uptime_segundos,
        "uptime_legible": f"{uptime_segundos // 3600}h {(uptime_segundos % 3600) // 60}m",
        "base_datos": db_status,
        "rate_limiting": "activo" if LIMITER_AVAILABLE else "desactivado",
        "timestamp": datetime.now().isoformat(),
    }, mensaje="Servicio operativo.")


# ============================================================
#  SERVIR FRONTEND
#  Cualquier ruta que no sea /api/* devuelve index.html
#  Permite que el frontend funcione en el mismo servidor
# ============================================================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Sirve el frontend desde la carpeta app/."""
    if path and os.path.exists(os.path.join(_APP_DIR, path)):
        return send_from_directory(_APP_DIR, path)
    return send_from_directory(_APP_DIR, 'index.html')


# ============================================================
#  PUNTO DE ENTRADA
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"[API] Servidor corriendo en: http://127.0.0.1:{port}")
    print(f"[API] Abre en el navegador:  http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=debug)

