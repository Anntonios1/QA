"""
============================================================
  MÓDULO JWT - Autenticación Stateless
============================================================
  Normas aplicadas:
    - ISO/IEC 27001: Gestión de acceso e identidad
    - OWASP: Autenticación segura con tokens
    - RFC 7519: JSON Web Tokens
    - ISO/IEC 25000: Seguridad - Autenticidad
============================================================
  Implementación de JWT con Access + Refresh tokens.
  
  Características:
    - Access Token: 15 minutos (corta vida, en memoria)
    - Refresh Token: 7 días (larga vida, en DB)
    - Algoritmo: HS256 (HMAC-SHA256)
    - Claims: user_id, nombre, tipo, exp, iat, jti
============================================================
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from functools import wraps

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from flask import request, jsonify


# ============================================================
#  CONFIGURACIÓN
# ============================================================

# Entorno de ejecución
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development').lower()
IS_PRODUCTION = ENVIRONMENT in ('production', 'prod', 'staging')

# Valor por defecto para desarrollo (NUNCA usar en producción)
_DEFAULT_JWT_SECRET = 'ControlCash_JWT_Secret_CHANGE_IN_PRODUCTION_2026'

# Clave secreta para firmar tokens (DEBE estar en .env en producción)
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', '')

# Validar que la clave esté configurada en producción
if IS_PRODUCTION:
    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY no está configurada. "
            "Establece la variable de entorno JWT_SECRET_KEY con un valor seguro en producción. "
            "Puedes generar una con: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    if JWT_SECRET_KEY == _DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET_KEY está usando el valor por defecto inseguro. "
            "Genera una nueva clave con: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
else:
    # En desarrollo, usar valor por defecto si no está configurado
    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = _DEFAULT_JWT_SECRET
        print("[WARN] JWT_SECRET_KEY no configurada. Usando valor de desarrollo. "
              "NO usar en producción.")

# Tiempos de expiración
ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRES = timedelta(days=7)

# Algoritmo de firma
JWT_ALGORITHM = 'HS256'


# ============================================================
#  GENERACIÓN DE TOKENS
# ============================================================

# [NORMA: ISO/IEC 27001 - Control A.9.4.2] Cierre automático de sesión y expiración por inactividad mediante token temporal
# [NORMA: OWASP Mobile Top 10 - M4] Autenticación insegura prevenida mediante tokens de corta duración
def generate_access_token(user_id: int, nombre: str, email: str) -> str:
    """
    Genera un Access Token JWT de corta duración.
    
    Args:
        user_id: ID del usuario
        nombre: Nombre del usuario
        email: Email del usuario
    
    Returns:
        Token JWT como string
    """
    if not JWT_AVAILABLE:
        raise RuntimeError("PyJWT no instalado. Ejecuta: pip install PyJWT")
    
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),  # Subject - string por RFC 7519
        'user_id': user_id,   # ID numérico para conveniencia
        'nombre': nombre,
        'email': email,
        'tipo': 'access',
        'iat': now,  # Issued at
        'exp': now + ACCESS_TOKEN_EXPIRES,  # Expiration
        'jti': secrets.token_hex(16),  # JWT ID único
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def generate_refresh_token(user_id: int) -> tuple:
    """
    Genera un Refresh Token de larga duración.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Tupla (token_string, token_hash, expires_at)
        - token_string: Token para enviar al cliente
        - token_hash: Hash para almacenar en DB
        - expires_at: Fecha de expiración
    """
    if not JWT_AVAILABLE:
        raise RuntimeError("PyJWT no instalado. Ejecuta: pip install PyJWT")
    
    now = datetime.now(timezone.utc)
    expires_at = now + REFRESH_TOKEN_EXPIRES
    jti = secrets.token_hex(32)  # ID único del token
    
    payload = {
        'sub': str(user_id),  # Subject - string por RFC 7519
        'user_id': user_id,   # ID numérico para conveniencia
        'tipo': 'refresh',
        'iat': now,
        'exp': expires_at,
        'jti': jti,
    }
    
    token_string = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    # Hash del token para almacenar en DB (no guardamos el token en claro)
    token_hash = hashlib.sha256(token_string.encode()).hexdigest()
    
    return token_string, token_hash, expires_at


def verify_token(token: str, expected_type: str = 'access') -> dict:
    """
    Verifica y decodifica un token JWT.
    
    Args:
        token: Token JWT a verificar
        expected_type: Tipo esperado ('access' o 'refresh')
    
    Returns:
        Payload decodificado si es válido
    
    Raises:
        jwt.ExpiredSignatureError: Token expirado
        jwt.InvalidTokenError: Token inválido
        ValueError: Tipo de token incorrecto
    """
    if not JWT_AVAILABLE:
        raise RuntimeError("PyJWT no instalado. Ejecuta: pip install PyJWT")
    
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    
    if payload.get('tipo') != expected_type:
        raise ValueError(f"Tipo de token incorrecto. Esperado: {expected_type}")
    
    return payload


def get_token_hash(token: str) -> str:
    """Genera el hash SHA-256 de un token para búsqueda en DB."""
    return hashlib.sha256(token.encode()).hexdigest()


# ============================================================
#  DECORADOR PARA ENDPOINTS PROTEGIDOS
# ============================================================

# [NORMA: ISO/IEC 27001 - Control A.9.4.2] Verificación de identidad mediante token para endpoints protegidos
# [NORMA: OWASP Mobile Top 10 - M4] Control de acceso robusto stateless
def jwt_required(f):
    """
    Decorador que requiere un Access Token JWT válido.
    Extrae el token del header Authorization: Bearer <token>
    
    Pasa usuario_id como primer argumento a la función decorada.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Obtener token del header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'ok': False,
                'error': 'Token no proporcionado',
                'codigo': 'NO_TOKEN'
            }), 401
        
        token = auth_header[7:]  # Quitar "Bearer "
        
        try:
            payload = verify_token(token, expected_type='access')
            usuario_id = payload['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({
                'ok': False,
                'error': 'Token expirado',
                'codigo': 'TOKEN_EXPIRED'
            }), 401
        except jwt.InvalidTokenError as e:
            return jsonify({
                'ok': False,
                'error': f'Token inválido: {str(e)}',
                'codigo': 'INVALID_TOKEN'
            }), 401
        except ValueError as e:
            return jsonify({
                'ok': False,
                'error': str(e),
                'codigo': 'WRONG_TOKEN_TYPE'
            }), 401
        
        return f(usuario_id, *args, **kwargs)
    
    return decorated


# ============================================================
#  FUNCIONES DE UTILIDAD
# ============================================================

def is_jwt_available() -> bool:
    """Verifica si PyJWT está disponible."""
    return JWT_AVAILABLE


def generate_jwt_secret() -> str:
    """Genera una nueva clave secreta segura para JWT."""
    return secrets.token_hex(32)


def decode_token_unsafe(token: str) -> dict:
    """
    Decodifica un token SIN verificar la firma.
    Útil solo para debugging o inspección.
    """
    if not JWT_AVAILABLE:
        return {}
    return jwt.decode(token, options={"verify_signature": False})


# ============================================================
#  TEST
# ============================================================

if __name__ == "__main__":
    print(f"[JWT] PyJWT disponible: {is_jwt_available()}")
    
    if is_jwt_available():
        # Test de generación
        access = generate_access_token(1, "Test User", "test@example.com")
        print(f"\n[Test] Access Token: {access[:50]}...")
        
        refresh, refresh_hash, expires = generate_refresh_token(1)
        print(f"[Test] Refresh Token: {refresh[:50]}...")
        print(f"[Test] Refresh Hash: {refresh_hash[:30]}...")
        print(f"[Test] Expira: {expires}")
        
        # Verificar
        payload = verify_token(access, 'access')
        print(f"\n[Test] Payload: {payload}")
        
        # Generar clave para producción
        print(f"\n[Info] Nueva clave JWT para producción:")
        print(f"JWT_SECRET_KEY={generate_jwt_secret()}")
