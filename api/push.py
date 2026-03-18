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

try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False

# Claves VAPID para Web Push (generar con: openssl ecparam ...)
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {"sub": os.environ.get("VAPID_CONTACT", "mailto:admin@controlcash.app")}

# Almacenamiento en memoria de suscripciones (en producción usar DB)
_subscriptions = {}  # {usuario_id: [subscription_info, ...]}


def guardar_suscripcion(usuario_id: int, subscription_info: dict):
    """Guarda una suscripción Web Push para un usuario."""
    if usuario_id not in _subscriptions:
        _subscriptions[usuario_id] = []
    # Evitar duplicados por endpoint
    endpoints = [s.get("endpoint") for s in _subscriptions[usuario_id]]
    if subscription_info.get("endpoint") not in endpoints:
        _subscriptions[usuario_id].append(subscription_info)


def eliminar_suscripcion(usuario_id: int, endpoint: str):
    """Elimina una suscripción por endpoint."""
    if usuario_id in _subscriptions:
        _subscriptions[usuario_id] = [
            s for s in _subscriptions[usuario_id]
            if s.get("endpoint") != endpoint
        ]


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
        except WebPushException as e:
            # Si la suscripción expiró, eliminarla
            if hasattr(e, 'response') and e.response and e.response.status_code in (404, 410):
                subs.remove(sub)

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
