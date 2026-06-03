"""
============================================================
  MÓDULO DE CIFRADO - AES-256-GCM
============================================================
  Normas aplicadas:
    - ISO/IEC 27001: Seguridad de la información
    - ISO/IEC 25000: Confidencialidad de datos
    - OWASP: Protección de datos sensibles en reposo
    - NIST SP 800-38D: Galois/Counter Mode (GCM)
============================================================
  Implementación de cifrado simétrico AES-256-GCM para
  proteger datos sensibles almacenados en la base de datos.
  
  Características:
    - AES-256: Cifrado de 256 bits (máxima seguridad)
    - GCM: Modo autenticado (integridad + confidencialidad)
    - IV único: 12 bytes aleatorios por cada cifrado
    - PBKDF2: Derivación de clave desde master key
============================================================
"""

import os
import base64
import hashlib
import secrets

# Intentar importar cryptography (preferido)
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
    CRYPTO_BACKEND = "cryptography"
except ImportError:
    CRYPTO_AVAILABLE = False
    CRYPTO_BACKEND = None

# Fallback a pycryptodome si cryptography no está disponible
if not CRYPTO_AVAILABLE:
    try:
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
        CRYPTO_AVAILABLE = True
        CRYPTO_BACKEND = "pycryptodome"
    except ImportError:
        pass


# ============================================================
#  CONFIGURACIÓN
# ============================================================

# Salt fijo para derivación de clave (puede moverse a .env)
_KEY_SALT = os.environ.get(
    'AES_KEY_SALT',
    'ControlCash_AES256_Salt_v1_2026'
).encode('utf-8')

# Iteraciones PBKDF2 para derivar la clave AES
_KDF_ITERATIONS = 100000

# Tamaño del IV para AES-GCM (12 bytes recomendado por NIST)
_IV_SIZE = 12

# Tamaño del tag de autenticación GCM (16 bytes = 128 bits)
_TAG_SIZE = 16


def _get_master_key() -> bytes:
    """
    Obtiene la clave maestra desde variables de entorno.
    ISO/IEC 27001: Las claves no deben estar hardcodeadas.
    """
    master_key = os.environ.get('AES_MASTER_KEY', '')
    if not master_key:
        # Generar una clave por defecto (solo para desarrollo)
        # En producción DEBE configurarse AES_MASTER_KEY en .env
        master_key = 'ControlCash_Dev_Key_CHANGE_IN_PRODUCTION_2026'
    return master_key.encode('utf-8')


def _derive_key(master_key: bytes, salt: bytes = None) -> bytes:
    """
    Deriva una clave AES-256 desde la clave maestra usando PBKDF2.
    NIST SP 800-132: Recomendación para derivación de claves.
    
    Args:
        master_key: Clave maestra en bytes
        salt: Salt para derivación (usa default si no se proporciona)
    
    Returns:
        Clave de 32 bytes (256 bits) para AES-256
    """
    if salt is None:
        salt = _KEY_SALT
    
    if CRYPTO_BACKEND == "cryptography":
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=_KDF_ITERATIONS,
        )
        return kdf.derive(master_key)
    else:
        # Fallback usando hashlib
        return hashlib.pbkdf2_hmac(
            'sha256',
            master_key,
            salt,
            _KDF_ITERATIONS,
            dklen=32
        )


# ============================================================
#  FUNCIONES PRINCIPALES DE CIFRADO
# ============================================================

# [NORMA: ISO/IEC 27001 - Control A.10.1.1] Uso de algoritmo de cifrado robusto para protección de credenciales y datos sensibles en reposo
# [NORMA: OWASP Mobile Top 10 - M4] Autenticación insegura y almacenamiento inseguro prevenidos mediante cifrado simétrico
def encrypt(plaintext: str, associated_data: str = None) -> str:
    """
    Cifra un texto usando AES-256-GCM.
    
    Args:
        plaintext: Texto a cifrar
        associated_data: Datos adicionales autenticados (opcional)
                        Útil para vincular el cifrado a un contexto (ej: usuario_id)
    
    Returns:
        String base64 con formato: iv(12) + tag(16) + ciphertext
    
    Raises:
        RuntimeError: Si no hay biblioteca de cifrado disponible
    
    Ejemplo:
        >>> encrypted = encrypt("Pago de Netflix $15.99")
        >>> encrypted = encrypt("Datos sensibles", associated_data="user_123")
    """
    if not CRYPTO_AVAILABLE:
        raise RuntimeError(
            "No hay biblioteca de cifrado disponible. "
            "Instala: pip install cryptography"
        )
    
    if not plaintext:
        return ""
    
    # Derivar clave AES-256
    key = _derive_key(_get_master_key())
    
    # Generar IV único (12 bytes para GCM)
    iv = secrets.token_bytes(_IV_SIZE)
    
    # Preparar datos
    plaintext_bytes = plaintext.encode('utf-8')
    aad = associated_data.encode('utf-8') if associated_data else None
    
    if CRYPTO_BACKEND == "cryptography":
        # Usar cryptography (preferido)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plaintext_bytes, aad)
        # ciphertext ya incluye el tag al final
        result = iv + ciphertext
    else:
        # Usar pycryptodome
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        if aad:
            cipher.update(aad)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext_bytes)
        result = iv + tag + ciphertext
    
    # Retornar como base64 para almacenamiento seguro
    return base64.b64encode(result).decode('ascii')


# [NORMA: ISO/IEC 27001 - Control A.10.1.1] Uso de algoritmo de cifrado robusto para protección de credenciales y datos sensibles en reposo
# [NORMA: OWASP Mobile Top 10 - M4] Autenticación insegura y almacenamiento inseguro prevenidos mediante cifrado simétrico
def decrypt(encrypted: str, associated_data: str = None) -> str:
    """
    Descifra un texto cifrado con AES-256-GCM.
    
    Args:
        encrypted: String base64 con datos cifrados
        associated_data: Datos adicionales autenticados (debe coincidir con encrypt)
    
    Returns:
        Texto original descifrado
    
    Raises:
        RuntimeError: Si no hay biblioteca de cifrado
        ValueError: Si los datos están corruptos o el tag no coincide
    
    Ejemplo:
        >>> plaintext = decrypt(encrypted_data)
        >>> plaintext = decrypt(encrypted_data, associated_data="user_123")
    """
    if not CRYPTO_AVAILABLE:
        raise RuntimeError(
            "No hay biblioteca de cifrado disponible. "
            "Instala: pip install cryptography"
        )
    
    if not encrypted:
        return ""
    
    # Derivar clave AES-256
    key = _derive_key(_get_master_key())
    
    # Decodificar base64
    try:
        data = base64.b64decode(encrypted)
    except Exception:
        raise ValueError("Datos cifrados inválidos (no es base64 válido)")
    
    # Preparar AAD
    aad = associated_data.encode('utf-8') if associated_data else None
    
    if CRYPTO_BACKEND == "cryptography":
        # Extraer IV (primeros 12 bytes)
        if len(data) < _IV_SIZE + _TAG_SIZE:
            raise ValueError("Datos cifrados demasiado cortos")
        
        iv = data[:_IV_SIZE]
        ciphertext_with_tag = data[_IV_SIZE:]
        
        aesgcm = AESGCM(key)
        try:
            plaintext_bytes = aesgcm.decrypt(iv, ciphertext_with_tag, aad)
        except Exception as e:
            raise ValueError(f"Error al descifrar: datos corruptos o clave incorrecta. {e}")
    else:
        # Usar pycryptodome
        if len(data) < _IV_SIZE + _TAG_SIZE:
            raise ValueError("Datos cifrados demasiado cortos")
        
        iv = data[:_IV_SIZE]
        tag = data[_IV_SIZE:_IV_SIZE + _TAG_SIZE]
        ciphertext = data[_IV_SIZE + _TAG_SIZE:]
        
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        if aad:
            cipher.update(aad)
        try:
            plaintext_bytes = cipher.decrypt_and_verify(ciphertext, tag)
        except Exception as e:
            raise ValueError(f"Error al descifrar: datos corruptos o clave incorrecta. {e}")
    
    return plaintext_bytes.decode('utf-8')


def encrypt_if_enabled(plaintext: str, associated_data: str = None) -> str:
    """
    Cifra solo si el cifrado está habilitado en el entorno.
    Útil para migración gradual o ambientes de desarrollo.
    
    Returns:
        Texto cifrado si ENCRYPT_SENSITIVE_DATA=true, sino el texto original
    """
    if os.environ.get('ENCRYPT_SENSITIVE_DATA', '').lower() == 'true':
        if CRYPTO_AVAILABLE:
            return encrypt(plaintext, associated_data)
    return plaintext


def decrypt_if_encrypted(data: str, associated_data: str = None) -> str:
    """
    Descifra solo si los datos parecen estar cifrados (base64 válido con estructura correcta).
    Útil para migración gradual de datos existentes.
    
    Returns:
        Texto descifrado si estaba cifrado, sino el texto original
    """
    if not data:
        return data
    
    # Verificar si parece ser base64 cifrado (heurística)
    try:
        decoded = base64.b64decode(data)
        # Debe tener al menos IV + TAG + 1 byte de datos
        if len(decoded) >= _IV_SIZE + _TAG_SIZE + 1:
            if CRYPTO_AVAILABLE:
                return decrypt(data, associated_data)
    except Exception:
        pass
    
    # No está cifrado o no se puede descifrar, retornar original
    return data


# ============================================================
#  FUNCIONES DE UTILIDAD
# ============================================================

def generate_master_key() -> str:
    """
    Genera una nueva clave maestra segura para AES-256.
    Usar para configurar AES_MASTER_KEY en producción.
    
    Returns:
        String de 64 caracteres hexadecimales (256 bits)
    
    Ejemplo:
        >>> key = generate_master_key()
        >>> print(f"AES_MASTER_KEY={key}")
    """
    return secrets.token_hex(32)


def is_crypto_available() -> bool:
    """Verifica si el cifrado está disponible."""
    return CRYPTO_AVAILABLE


def get_crypto_backend() -> str:
    """Retorna el nombre del backend de cifrado en uso."""
    return CRYPTO_BACKEND or "none"


def encrypt_dict_fields(data: dict, fields: list, user_id: int = None) -> dict:
    """
    Cifra campos específicos de un diccionario.
    
    Args:
        data: Diccionario con datos
        fields: Lista de campos a cifrar
        user_id: ID de usuario para AAD (opcional)
    
    Returns:
        Nuevo diccionario con campos cifrados
    
    Ejemplo:
        >>> mov = {"monto": 100.00, "descripcion": "Pago secreto"}
        >>> mov_cifrado = encrypt_dict_fields(mov, ["descripcion"], user_id=1)
    """
    result = data.copy()
    aad = str(user_id) if user_id else None
    
    for field in fields:
        if field in result and result[field]:
            value = result[field]
            if isinstance(value, (int, float)):
                value = str(value)
            result[field] = encrypt(value, associated_data=aad)
    
    return result


def decrypt_dict_fields(data: dict, fields: list, user_id: int = None) -> dict:
    """
    Descifra campos específicos de un diccionario.
    
    Args:
        data: Diccionario con datos cifrados
        fields: Lista de campos a descifrar
        user_id: ID de usuario para AAD (debe coincidir con el usado al cifrar)
    
    Returns:
        Nuevo diccionario con campos descifrados
    """
    result = data.copy()
    aad = str(user_id) if user_id else None
    
    for field in fields:
        if field in result and result[field]:
            try:
                result[field] = decrypt_if_encrypted(result[field], associated_data=aad)
            except ValueError:
                # Si falla el descifrado, mantener el valor original
                pass
    
    return result


# ============================================================
#  VERIFICACIÓN AL IMPORTAR
# ============================================================

if __name__ == "__main__":
    print(f"[Crypto] Backend disponible: {get_crypto_backend()}")
    print(f"[Crypto] Cifrado disponible: {is_crypto_available()}")
    
    if is_crypto_available():
        # Test básico
        original = "Información confidencial: Salario $5,000 MXN"
        print(f"\n[Test] Original: {original}")
        
        encrypted = encrypt(original, associated_data="test_user")
        print(f"[Test] Cifrado: {encrypted[:50]}...")
        
        decrypted = decrypt(encrypted, associated_data="test_user")
        print(f"[Test] Descifrado: {decrypted}")
        
        assert original == decrypted, "Error: el descifrado no coincide"
        print("\n[OK] Test de cifrado/descifrado exitoso")
        
        # Generar clave para producción
        print(f"\n[Info] Nueva clave maestra para producción:")
        print(f"AES_MASTER_KEY={generate_master_key()}")
