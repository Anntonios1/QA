"""
============================================================
  MÓDULO OCR - Escaneo de Recibos con NVIDIA NIM
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Implementación modular
    - ISO/IEC 25000: Funcionalidad - Completitud
    - CMMI Nivel 3: Integración de servicios externos
============================================================
  Usa el modelo nemotron-page-elements-v3 de NVIDIA NIM
  para extraer datos estructurados de fotos de recibos.
============================================================
"""

import os
import re
import json
import base64
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def _get_client():
    """Crea un cliente OpenAI apuntando a NVIDIA NIM."""
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY no configurada. Establece la variable de entorno.")
    if not OPENAI_AVAILABLE:
        raise ImportError("openai no instalado. Ejecuta: pip install openai")
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )


def procesar_recibo_base64(image_base64: str) -> dict:
    """
    Envía una imagen en base64 al modelo nemotron-page-elements-v3
    para OCR y extrae datos del recibo.

    Retorna dict con: total, fecha, descripcion, items[]
    """
    client = _get_client()

    response = client.chat.completions.create(
        model="nvidia/nemotron-page-elements-v3",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Analiza este recibo/ticket de compra. "
                            "Extrae y devuelve ÚNICAMENTE un JSON con esta estructura: "
                            '{"total": número, "fecha": "YYYY-MM-DD", '
                            '"descripcion": "nombre del comercio o resumen", '
                            '"items": [{"nombre": "...", "precio": número}]}. '
                            "Si no puedes leer algún campo, usa null. "
                            "Responde SOLO con el JSON, sin texto adicional."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    },
                ],
            }
        ],
        max_tokens=1024,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()
    return _parse_ocr_response(raw)


def _parse_ocr_response(raw_text: str) -> dict:
    """Parsea la respuesta del modelo OCR a un dict estructurado."""
    # Intentar extraer JSON del texto
    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return {
                "total": _safe_float(data.get("total")),
                "fecha": _safe_date(data.get("fecha")),
                "descripcion": data.get("descripcion", "Recibo escaneado"),
                "items": data.get("items", []),
                "raw": raw_text,
            }
        except json.JSONDecodeError:
            pass

    # Fallback: retornar texto sin parsear
    return {
        "total": None,
        "fecha": None,
        "descripcion": "No se pudo interpretar el recibo",
        "items": [],
        "raw": raw_text,
    }


def _safe_float(value) -> float:
    """Convierte a float de forma segura."""
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return None


def _safe_date(value) -> str:
    """Valida y normaliza una fecha."""
    if not value:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        datetime.strptime(str(value)[:10], "%Y-%m-%d")
        return str(value)[:10]
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d")
