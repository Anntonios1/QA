"""
============================================================
  MÓDULO WEB PUSH + WEBHOOKS
============================================================
  Normas aplicadas:
    - ISO/IEC 20000: Gestión de comunicación
    - ISO/IEC 12207: Implementación modular
    - ISO/IEC 25000: Usabilidad, Funcionalidad
============================================================
  Gestión de suscripciones Web Push y disparo de
  notificaciones al navegador. Incluye soporte para
  webhooks salientes a servicios externos.
============================================================
"""

import os
import json
import time
from datetime import datetime, timedelta

try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False

# Claves VAPID para Web Push (generar con: openssl ecparam ...)
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {"sub": os.environ.get("VAPID_CONTACT", "mailto:admin@controlcash.app")}

# Configuración de límites
MAX_SUBSCRIPTIONS_PER_USER = 5  # Máximo de dispositivos por usuario
SUBSCRIPTION_TTL_DAYS = 90      # Días antes de que una suscripción expire

# Almacenamiento en memoria de suscripciones (en producción usar DB)
# Formato: {usuario_id: [{"endpoint": "...", "keys": {...}, "created_at": timestamp, "last_used": timestamp}, ...]}
_subscriptions = {}


def guardar_suscripcion(usuario_id: int, subscription_info: dict):
    """
    Guarda una suscripción Web Push para un usuario.

    Limita a MAX_SUBSCRIPTIONS_PER_USER dispositivos por usuario,
    eliminando la más antigua si se excede el límite.
    """
    if usuario_id not in _subscriptions:
        _subscriptions[usuario_id] = []

    endpoint = subscription_info.get("endpoint")
    if not endpoint:
        return False

    # Eliminar suscripción existente con el mismo endpoint (actualizar)
    _subscriptions[usuario_id] = [
        s for s in _subscriptions[usuario_id]
        if s.get("endpoint") != endpoint
    ]

    # Agregar timestamp a la suscripción
    subscription_with_meta = {
        **subscription_info,
        "created_at": time.time(),
        "last_used": time.time()
    }

    # Agregar nueva suscripción
    _subscriptions[usuario_id].append(subscription_with_meta)

    # Si excede el límite, eliminar la más antigua (por created_at)
    if len(_subscriptions[usuario_id]) > MAX_SUBSCRIPTIONS_PER_USER:
        _subscriptions[usuario_id].sort(key=lambda s: s.get("created_at", 0), reverse=True)
        _subscriptions[usuario_id] = _subscriptions[usuario_id][:MAX_SUBSCRIPTIONS_PER_USER]

    return True


def eliminar_suscripcion(usuario_id: int, endpoint: str):
    """Elimina una suscripción por endpoint."""
    if usuario_id in _subscriptions:
        _subscriptions[usuario_id] = [
            s for s in _subscriptions[usuario_id]
            if s.get("endpoint") != endpoint
        ]


def limpiar_suscripciones_expiradas():
    """
    Elimina suscripciones que han expirado (más de SUBSCRIPTION_TTL_DAYS días sin usarse).
    Debe llamarse periódicamente desde un scheduler o al iniciar la app.
    """
    cutoff_time = time.time() - (SUBSCRIPTION_TTL_DAYS * 24 * 60 * 60)
    total_eliminadas = 0

    for usuario_id in list(_subscriptions.keys()):
        subs_antes = len(_subscriptions[usuario_id])
        _subscriptions[usuario_id] = [
            s for s in _subscriptions[usuario_id]
            if s.get("last_used", s.get("created_at", 0)) > cutoff_time
        ]
        total_eliminadas += subs_antes - len(_subscriptions[usuario_id])

        # Eliminar entrada vacía
        if not _subscriptions[usuario_id]:
            del _subscriptions[usuario_id]

    return total_eliminadas


def obtener_estadisticas_suscripciones():
    """Retorna estadísticas del almacenamiento de suscripciones."""
    total_usuarios = len(_subscriptions)
    total_subs = sum(len(subs) for subs in _subscriptions.values())
    return {
        "total_usuarios_con_suscripciones": total_usuarios,
        "total_suscripciones": total_subs,
        "promedio_por_usuario": round(total_subs / max(total_usuarios, 1), 1)
    }


# [NORMA: ISO/IEC 20000 - Gestión de Servicios TI] Gestión de comunicación mediante disparo de notificaciones push
# [NORMA: ISO/IEC 25000] Característica de usabilidad: notificaciones en tiempo real al usuario
def enviar_push(usuario_id: int, titulo: str, mensaje: str, tag: str = "default"):
    """Envía notificación push a todas las suscripciones de un usuario."""
    if not WEBPUSH_AVAILABLE:
        return {"enviadas": 0, "error": "pywebpush no instalado"}
    if not VAPID_PRIVATE_KEY:
        return {"enviadas": 0, "error": "VAPID keys no configuradas"}

    subs = _subscriptions.get(usuario_id, [])
    if not subs:
        return {"enviadas": 0, "error": "Sin suscripciones"}

    payload = json.dumps({
        "titulo": titulo,
        "mensaje": mensaje,
        "tag": tag,
        "data": {"url": "/"}
    })

    enviadas = 0
    for sub in subs[:]:  # copia para poder modificar durante iteración
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
            enviadas += 1
            # Actualizar timestamp de último uso
            sub["last_used"] = time.time()
        except WebPushException as e:
            # Si la suscripción expiró, eliminarla
            if hasattr(e, 'response') and e.response and e.response.status_code in (404, 410):
                _subscriptions[usuario_id].remove(sub)

    return {"enviadas": enviadas}


# ============================================================
#  WEBHOOKS SALIENTES
# ============================================================

import urllib.request

_webhook_urls = {}  # {usuario_id: [url, ...]}


def registrar_webhook(usuario_id: int, url: str):
    """Registra una URL de webhook para un usuario."""
    if usuario_id not in _webhook_urls:
        _webhook_urls[usuario_id] = []
    if url not in _webhook_urls[usuario_id] and len(_webhook_urls[usuario_id]) < 5:
        _webhook_urls[usuario_id].append(url)


def disparar_webhooks(usuario_id: int, evento: str, datos: dict):
    """Envía evento a todos los webhooks registrados del usuario."""
    urls = _webhook_urls.get(usuario_id, [])
    payload = json.dumps({
        "evento": evento,
        "datos": datos,
        "usuario_id": usuario_id,
    }).encode("utf-8")

    resultados = []
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resultados.append({"url": url, "status": resp.status})
        except Exception as e:
            resultados.append({"url": url, "error": str(e)})

    return resultados
