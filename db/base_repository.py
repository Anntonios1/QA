"""
============================================================
  INTERFACES ABSTRACTAS - Patrón Repository
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Separación de responsabilidades
    - ISO 9001: Estandarización de procesos
    - CMMI Nivel 3: Definición de procesos estándar
    - IEEE 730: Trazabilidad de interfaces
    - ISO/IEC 25000: Mantenibilidad - Modificabilidad
============================================================
  Define las interfaces que toda implementación de
  repositorio debe cumplir. La capa API consume
  estas interfaces sin acoplarse a PostgreSQL.
============================================================
"""

from abc import ABC, abstractmethod
import hashlib
import secrets


# ============================================================
#  UTILIDADES COMUNES (compartidas entre implementaciones)
# ============================================================

class PasswordMixin:
    """Funciones de hashing de contraseña reutilizables."""

    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """Genera hash seguro con PBKDF2-SHA256 + salt (ISO 9126 - Seguridad)."""
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000
        )
        return f"{salt}${hashed.hex()}", salt

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verifica contraseña contra hash almacenado."""
        salt, _ = stored_hash.split('$', 1)
        new_hash, _ = PasswordMixin.hash_password(password, salt)
        return secrets.compare_digest(new_hash, stored_hash)


# ============================================================
#  INTERFAZ: Repositorio de Usuarios
# ============================================================

class BaseUsuarioRepository(ABC):

    @abstractmethod
    def crear(self, nombre: str, email: str, password: str) -> dict:
        """Registra un nuevo usuario. Retorna dict o None si email duplicado."""
        ...

    @abstractmethod
    def autenticar(self, email: str, password: str) -> dict:
        """Autentica un usuario. Retorna dict o None."""
        ...

    @abstractmethod
    def obtener_por_id(self, usuario_id: int) -> dict:
        """Obtiene un usuario por ID. Retorna dict o None."""
        ...


# ============================================================
#  INTERFAZ: Repositorio de Categorías
# ============================================================

class BaseCategoriaRepository(ABC):

    @abstractmethod
    def listar(self, tipo: str = None) -> list:
        """Lista categorías activas, opcionalmente filtradas por tipo."""
        ...

    @abstractmethod
    def obtener_por_id(self, categoria_id: int) -> dict:
        """Obtiene una categoría por ID."""
        ...


# ============================================================
#  INTERFAZ: Repositorio de Movimientos
# ============================================================

class BaseMovimientoRepository(ABC):

    @abstractmethod
    def crear(self, usuario_id: int, categoria_id: int, tipo: str,
              monto: float, descripcion: str = "", fecha: str = None) -> dict:
        """Registra un nuevo movimiento financiero."""
        ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int, limite: int = 50,
                           tipo: str = None, fecha_desde: str = None,
                           fecha_hasta: str = None) -> list:
        """Lista movimientos de un usuario con filtros opcionales."""
        ...

    @abstractmethod
    def eliminar(self, movimiento_id: int, usuario_id: int) -> bool:
        """Elimina un movimiento verificando que pertenezca al usuario."""
        ...

    @abstractmethod
    def obtener_balance(self, usuario_id: int) -> dict:
        """Calcula el balance financiero del usuario."""
        ...

    @abstractmethod
    def obtener_resumen(self, usuario_id: int, dias: int = 30) -> dict:
        """Genera resumen financiero por categoría."""
        ...


# ============================================================
#  INTERFAZ: Repositorio de Notificaciones
# ============================================================

class BaseNotificacionRepository(ABC):

    @abstractmethod
    def crear(self, usuario_id: int, titulo: str, mensaje: str,
              tipo: str = "info") -> dict:
        """Crea una nueva notificación."""
        ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int,
                           solo_no_leidas: bool = False) -> list:
        """Lista notificaciones del usuario."""
        ...

    @abstractmethod
    def marcar_leida(self, notificacion_id: int, usuario_id: int) -> bool:
        """Marca notificación como leída."""
        ...

    @abstractmethod
    def contar_no_leidas(self, usuario_id: int) -> int:
        """Cuenta notificaciones no leídas."""
        ...
