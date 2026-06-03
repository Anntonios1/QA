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
import math
from datetime import datetime
from copy import deepcopy

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


MAX_TOTAL_OCR = 999999999.99
DEFAULT_DESC = "Recibo escaneado"
OCR_MAX_ROUNDS = 3
OCR_TARGET_PRECISION = 0.86
OCR_PARSE_MODEL = os.environ.get("OCR_PARSE_MODEL", "nvidia/nemotron-parse")
OCR_PARSE_TOOLS = [
    t.strip()
    for t in os.environ.get("OCR_PARSE_TOOLS", "markdown_bbox,markdown_no_bbox,detection_only").split(",")
    if t.strip()
]
PAGE_ELEMENTS_URL = os.environ.get(
    "NVIDIA_PAGE_ELEMENTS_URL",
    "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-page-elements-v3",
)
OCR_LLM_MODEL = os.environ.get("OCR_LLM_MODEL", "openai/gpt-oss-120b")
OCR_LLM_FALLBACK_MODELS = os.environ.get("OCR_LLM_FALLBACK_MODELS", "").strip()
NVIDIA_CHAT_COMPLETIONS_URL = os.environ.get(
    "NVIDIA_CHAT_COMPLETIONS_URL",
    "https://integrate.api.nvidia.com/v1/chat/completions",
)

MONTHS_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


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


def _get_api_key() -> str:
    """Obtiene API key NVIDIA de entorno."""
    api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not api_key:
        raise ValueError("NVIDIA_API_KEY no configurada. Establece la variable de entorno.")
    return api_key


def _get_llm_models() -> list:
    """Lista ordenada de modelos LLM para rondas OCR (principal + fallback)."""
    models = [OCR_LLM_MODEL]
    if OCR_LLM_FALLBACK_MODELS:
        models.extend([m.strip() for m in OCR_LLM_FALLBACK_MODELS.split(",") if m.strip()])

    unique = []
    seen = set()
    for m in models:
        if m in seen:
            continue
        seen.add(m)
        unique.append(m)
    return unique


def _get_parse_tools() -> list:
    """Lista de tools para Nemotron Parse, en orden de intento."""
    return OCR_PARSE_TOOLS or ["markdown_bbox"]


def _run_nemotron_parse(image_base64: str, mime_type: str, parse_tool: str) -> dict:
    """Ejecuta nvidia/nemotron-parse forzando una tool de salida estructurada."""
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests no instalado. Ejecuta: pip install requests")

    api_key = _get_api_key()
    media_tag = f'<img src="data:{mime_type};base64,{image_base64}" />'
    payload = {
        "model": OCR_PARSE_MODEL,
        "messages": [{"role": "user", "content": media_tag}],
        "tools": [{"type": "function", "function": {"name": parse_tool}}],
        "tool_choice": {"type": "function", "function": {"name": parse_tool}},
        "max_tokens": 8192,
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    resp = requests.post(NVIDIA_CHAT_COMPLETIONS_URL, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        excerpt = (resp.text or "")[:320]
        raise ValueError(f"Nemotron Parse {parse_tool} fallo: {resp.status_code} {excerpt}")
    return resp.json()


def _extract_parse_blocks(parse_json: dict) -> list:
    """Extrae bloques de texto del output de Nemotron Parse (tool_calls o content)."""
    blocks = []
    try:
        choices = parse_json.get("choices") or []
        message = (choices[0] or {}).get("message") if choices else {}
        tool_calls = (message or {}).get("tool_calls") or []

        for call in tool_calls:
            fn = (call or {}).get("function") or {}
            args_raw = fn.get("arguments") or ""
            if not isinstance(args_raw, str) or not args_raw.strip():
                continue

            try:
                parsed = json.loads(args_raw)
            except Exception:
                continue

            candidates = []
            if isinstance(parsed, list):
                # markdown_bbox suele devolver lista de paginas [[...]].
                if parsed and isinstance(parsed[0], list):
                    for page in parsed:
                        if isinstance(page, list):
                            candidates.extend(page)
                else:
                    candidates.extend(parsed)

            for item in candidates:
                if not isinstance(item, dict):
                    continue
                text = str(item.get("text") or "").strip()
                block = {
                    "text": text,
                    "type": str(item.get("type") or ""),
                    "bbox": item.get("bbox") if isinstance(item.get("bbox"), dict) else None,
                }
                blocks.append(block)

        # Fallback cuando el modelo responde en content sin tool_calls.
        content = (message or {}).get("content")
        if not blocks and isinstance(content, str) and content.strip():
            for line in content.splitlines():
                clean = line.strip()
                if clean:
                    blocks.append({"text": clean, "type": "Text", "bbox": None})

    except Exception:
        return []

    return blocks


def _blocks_to_text(parse_blocks: list) -> str:
    """Convierte bloques parseados a texto lineal para normalizacion LLM y heuristicas."""
    lines = []
    for b in parse_blocks or []:
        if not isinstance(b, dict):
            continue
        text = str(b.get("text") or "").strip()
        if not text:
            continue
        lines.append(text)
    return "\n".join(lines)


def _dedupe_parse_blocks(parse_blocks: list) -> list:
    """Elimina bloques duplicados preservando orden."""
    out = []
    seen = set()
    for b in parse_blocks or []:
        if not isinstance(b, dict):
            continue
        text = str(b.get("text") or "").strip()
        block_type = str(b.get("type") or "").strip()
        if not text:
            continue
        key = (text.lower(), block_type.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append({"text": text, "type": block_type, "bbox": b.get("bbox")})
    return out


def _infer_tipo_movimiento(raw_text: str) -> tuple:
    """Sugiere tipo de movimiento (ingreso/gasto/desconocido) basado en lenguaje del comprobante."""
    txt = (raw_text or "").lower()
    if not txt:
        return "desconocido", 0.0

    salida_terms = [
        "envio realizado",
        "envio realzado",
        "transferencia enviada",
        "pagaste",
        "salio",
        "débito",
        "debito",
        "pago",
        "compra",
    ]
    ingreso_terms = [
        "dinero recibido",
        "envio recibido",
        "te enviaron",
        "abono",
        "abonado",
        "consignacion",
        "consignación",
        "ingreso",
        "deposito",
        "depósito",
    ]

    salida_hits = sum(1 for t in salida_terms if t in txt)
    ingreso_hits = sum(1 for t in ingreso_terms if t in txt)

    if salida_hits > ingreso_hits and salida_hits > 0:
        return "gasto", min(1.0, 0.65 + 0.08 * salida_hits)
    if ingreso_hits > salida_hits and ingreso_hits > 0:
        return "ingreso", min(1.0, 0.65 + 0.08 * ingreso_hits)
    return "desconocido", 0.35 if (salida_hits or ingreso_hits) else 0.0


def _run_parse_normalizer_llm(parse_blocks: list, raw_text: str) -> tuple:
    """Usa GPT para convertir bloques OCR de Nemotron Parse a JSON de negocio."""
    client = _get_client()

    compact_blocks = []
    for b in (parse_blocks or [])[:120]:
        if not isinstance(b, dict):
            continue
        text = str(b.get("text") or "").strip()
        if not text:
            continue
        compact_blocks.append({
            "text": text[:220],
            "type": str(b.get("type") or "")[:60],
        })

    prompt = (
        "Extrae datos de un comprobante de pago usando SOLO evidencia textual detectada por OCR. "
        "No inventes valores. Si no hay evidencia, usa null. "
        "Si aparece 'Envio Realizado' o equivalente, tipo_sugerido debe ser 'gasto'. "
        "Responde SOLO JSON con schema: "
        '{"total": numero|null, "fecha": "YYYY-MM-DD"|null, "descripcion": "texto", '
        '"items": [{"nombre": "...", "precio": numero|null}], '
        '"confidence": numero_0_a_1, "tipo_sugerido": "ingreso|gasto|desconocido", '
        '"hallazgos": ["..."]}.\n\n'
        f"OCR_TEXT:\n{(raw_text or '')[:7000]}\n\n"
        f"OCR_BLOCKS:\n{json.dumps(compact_blocks, ensure_ascii=False)}"
    )

    errors = []
    for model_name in _get_llm_models():
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.0,
            )
            return _extract_text_content(response), model_name
        except Exception as exc:
            errors.append(f"{model_name}: {exc}")

    raise ValueError("No se pudo normalizar OCR con LLM: " + " | ".join(errors[:3]))


def _run_page_elements_fast(image_base64: str, mime_type: str = "image/jpeg") -> dict:
    """Llama al endpoint CV de NVIDIA Page Elements para detectar zonas del documento."""
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests no instalado. Ejecuta: pip install requests")

    api_key = _get_api_key()
    payload = {
        "input": [
            {
                "type": "image_url",
                "url": f"data:{mime_type};base64,{image_base64}",
            }
        ]
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    resp = requests.post(PAGE_ELEMENTS_URL, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        excerpt = (resp.text or "")[:280]
        raise ValueError(f"{resp.status_code} {excerpt}")

    return resp.json()


def _summarize_page_elements(page_json: dict) -> dict:
    """Resume resultados de page-elements para consumo de rondas LLM."""
    summary = {
        "total_boxes": 0,
        "labels": {},
    }

    data = page_json.get("data") or []
    for entry in data:
        boxes = (entry or {}).get("bounding_boxes") or {}
        for label, arr in boxes.items():
            arr = arr or []
            confidences = [float(x.get("confidence", 0) or 0) for x in arr if isinstance(x, dict)]
            count = len(arr)
            summary["labels"][label] = {
                "count": count,
                "max_confidence": round(max(confidences), 4) if confidences else 0.0,
            }
            summary["total_boxes"] += count

    summary["labels_count"] = len(summary["labels"])
    return summary


def _confirm_page_elements(previous_summary: dict, current_summary: dict) -> dict:
    """Compara dos lecturas de page-elements para medir consistencia entre rondas."""
    if not previous_summary:
        return {
            "consistente": None,
            "overlap_labels": 0.0,
            "delta_total_boxes": 0,
        }

    prev_labels = set((previous_summary.get("labels") or {}).keys())
    cur_labels = set((current_summary.get("labels") or {}).keys())
    union = prev_labels | cur_labels
    inter = prev_labels & cur_labels
    overlap = (len(inter) / len(union)) if union else 1.0

    prev_total = int(previous_summary.get("total_boxes") or 0)
    cur_total = int(current_summary.get("total_boxes") or 0)
    delta = abs(cur_total - prev_total)
    tolerated = max(1, int(prev_total * 0.30))

    consistente = (overlap >= 0.45) and (delta <= tolerated)
    return {
        "consistente": consistente,
        "overlap_labels": round(overlap, 3),
        "delta_total_boxes": delta,
    }


def _extract_text_content(response) -> str:
    """Extrae texto del proveedor de forma segura."""
    if not response or not getattr(response, "choices", None):
        raise ValueError("El proveedor OCR no devolvio opciones de respuesta.")

    first = response.choices[0]
    message = getattr(first, "message", None)
    content = getattr(message, "content", None)

    if content is None:
        raise ValueError("El proveedor OCR no devolvio contenido de texto.")

    if not isinstance(content, str):
        content = str(content)

    content = content.strip()
    if not content:
        raise ValueError("El proveedor OCR devolvio contenido vacio.")

    return content


def _run_nvidia_ocr(image_base64: str, mime_type: str = "image/jpeg") -> tuple:
    """Ejecuta extracción visual en modo básico usando el LLM principal/fallback."""
    client = _get_client()
    errors = []
    for model_name in _get_llm_models():
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Analiza este comprobante de pago. "
                                    "Extrae y devuelve SOLO JSON: "
                                    '{"total": numero|null, "fecha": "YYYY-MM-DD"|null, '
                                    '"descripcion": "texto", "items": [{"nombre": "...", "precio": numero|null}], '
                                    '"confidence": numero_0_a_1}. '
                                    "Si no puedes leer algun campo, usa null."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1024,
                temperature=0.1,
            )
            return _extract_text_content(response), model_name
        except Exception as exc:
            errors.append(f"{model_name}: {exc}")

    raise ValueError("No se pudo invocar LLM en modo basico: " + " | ".join(errors[:3]))


def _build_round_prompt(round_num: int, context: dict = None) -> str:
    """Genera instrucciones por ronda para OCR avanzado de comprobantes."""
    context = context or {}

    base_schema = (
        '{"total": numero|null, "fecha": "YYYY-MM-DD"|null, '
        '"descripcion": "texto", "items": [{"nombre": "...", "precio": numero|null}], '
        '"confidence": numero_0_a_1, "hallazgos": ["..."]}'
    )

    page_summary = context.get("page_elements_summary") or {}
    page_confirm = context.get("page_confirmacion") or {}
    texto_base = context.get("texto_base") or ""

    page_ctx_txt = (
        f"Deteccion page-elements actual: {json.dumps(page_summary, ensure_ascii=False)}. "
        f"Confirmacion vs ronda previa: {json.dumps(page_confirm, ensure_ascii=False)}."
    )
    text_ctx = f"Texto OCR/base disponible: {texto_base}." if texto_base else "No hay texto OCR previo confiable."

    if round_num == 1:
        return (
            "Eres un auditor OCR de comprobantes de pago. "
            "Ronda 1/3: extrae estructura base del comprobante con enfoque en total, fecha y comercio. "
            "Usa SOLO texto visible en la imagen; no inventes ni infieras datos por contexto o fecha actual. "
            f"{page_ctx_txt} "
            f"{text_ctx} "
            "Si hay ambiguedad, agrega en hallazgos. "
            "Si no hay lectura confiable, devuelve total=null y fecha=null. "
            f"Devuelve SOLO JSON con schema {base_schema}."
        )

    if round_num == 2:
        prev = context.get("prev_resumen", "")
        return (
            "Eres un verificador OCR de alta precision. "
            "Ronda 2/3: re-lee el comprobante y corrige posibles errores de la ronda anterior. "
            "Prioriza detectar correctamente TOTAL A PAGAR/TOTAL/PAGADO y FECHA. "
            "No reutilices valores previos si no hay evidencia visual clara en esta ronda. "
            f"Contexto previo: {prev}. "
            f"{page_ctx_txt} "
            f"{text_ctx} "
            "Si no hay lectura confiable, devuelve total=null y fecha=null. "
            f"Devuelve SOLO JSON con schema {base_schema}."
        )

    prev = context.get("prev_resumen", "")
    return (
        "Eres un reconciliador OCR final. "
        "Ronda 3/3: entrega la mejor lectura posible, resolviendo conflictos numericos y de fecha. "
        "Si no hay certeza visual, usa null en lugar de inferir por contexto. "
        f"Contexto previo: {prev}. "
        f"{page_ctx_txt} "
        f"{text_ctx} "
        f"Devuelve SOLO JSON con schema {base_schema}."
    )


def _run_nvidia_ocr_round(
    image_base64: str,
    mime_type: str,
    round_num: int,
    context: dict = None,
) -> tuple:
    """Ejecuta una ronda OCR avanzada con instrucciones especificas."""
    client = _get_client()
    prompt = _build_round_prompt(round_num, context=context)
    errors = []
    for model_name in _get_llm_models():
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1200,
                temperature=0.1,
            )
            return _extract_text_content(response), model_name
        except Exception as exc:
            errors.append(f"{model_name} (vision): {exc}")

    raise ValueError("No se pudo invocar LLM en ronda OCR: " + " | ".join(errors[:3]))


def _summarize_for_next_round(candidate: dict) -> str:
    """Compacta un candidato para contexto de rondas siguientes."""
    has_total = _safe_float(candidate.get("total")) is not None
    has_date = _safe_date_or_none(candidate.get("fecha")) is not None
    desc = (candidate.get("descripcion") or "").strip().lower()
    has_desc = bool(desc and desc not in ("no se pudo interpretar el recibo", DEFAULT_DESC.lower()))
    return (
        f"campos_detectados(total={has_total}, fecha={has_date}, descripcion={has_desc}), "
        f"precision={candidate.get('precision_score')}"
    )


def _tool_extract_numeric_candidates(raw_text: str) -> dict:
    """Tool call interno: extrae candidatos monetarios del texto OCR."""
    totals = []
    amount_lines = []
    match_total_lines = re.findall(
        r'(?im)\btotal(?:\s*(?:a\s*pagar|pagado)?)?\b[^\d\n\r-]*(-?[\d][\d\.,]*)',
        raw_text or "",
    )
    for m in match_total_lines:
        v = _safe_float(m)
        if v is not None:
            totals.append(v)

    match_amount_lines = re.findall(
        r'(?im)\b(?:cuanto|monto|valor|pagaste|importe)\b[^\d\n\r-]*(-?[\d][\d\.,]*)',
        raw_text or "",
    )
    for m in match_amount_lines:
        v = _safe_float(m)
        if v is not None:
            amount_lines.append(v)

    decimal_candidates = re.findall(r'(-?[\d][\d\.,]*[\.,]\d{2})', raw_text or "")
    all_decimals = []
    for c in decimal_candidates:
        v = _safe_float(c)
        if v is not None:
            all_decimals.append(v)

    return {
        "total_lines": sorted(set(totals)),
        "amount_lines": sorted(set(amount_lines)),
        "decimal_candidates": sorted(set(all_decimals)),
    }


def _tool_extract_date_candidates(raw_text: str) -> list:
    """Tool call interno: extrae fechas candidatas del comprobante."""
    candidates = []

    for m in re.findall(r'\b(\d{4}-\d{2}-\d{2})\b', raw_text or ""):
        d = _safe_date_or_none(m)
        if d:
            candidates.append(d)

    for dd, mm, yyyy in re.findall(r'\b(\d{2})[/-](\d{2})[/-](\d{4})\b', raw_text or ""):
        d = _safe_date_or_none(f"{yyyy}-{mm}-{dd}")
        if d:
            candidates.append(d)

    for d in _extract_spanish_dates(raw_text):
        valid = _safe_date_or_none(d)
        if valid:
            candidates.append(valid)

    return sorted(set(candidates))


def _tool_extract_merchant_candidates(raw_text: str) -> list:
    """Tool call interno: propone nombres de comercio desde lineas del OCR."""
    merchants = []
    for line in (raw_text or "").splitlines()[:12]:
        clean = line.strip()
        if len(clean) < 3:
            continue
        if re.search(r'^(total|fecha|subtotal|iva|ruc|nit|folio|ticket)\b', clean, flags=re.IGNORECASE):
            continue
        if re.fullmatch(r'[\d\s\.,\-/:$#]+', clean):
            continue
        merchants.append(clean[:200])

    # Quitar duplicados preservando orden
    seen = set()
    unique = []
    for m in merchants:
        key = m.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(m)
    return unique


def _tool_refine_candidate(candidate: dict, tool_data: dict) -> dict:
    """Tool call interno: corrige candidato usando senales locales."""
    refined = deepcopy(candidate)

    total_lines = tool_data.get("numeric", {}).get("total_lines", [])
    amount_lines = tool_data.get("numeric", {}).get("amount_lines", [])
    decimals = tool_data.get("numeric", {}).get("decimal_candidates", [])
    date_candidates = tool_data.get("dates", [])
    merchant_candidates = tool_data.get("merchants", [])

    total = _safe_float(refined.get("total"))
    combined_candidates = sorted(set(total_lines + amount_lines + decimals))
    strong_candidates = [v for v in (total_lines + amount_lines) if v is not None]

    if total is None:
        if strong_candidates:
            refined["total"] = max(strong_candidates)
        elif combined_candidates:
            refined["total"] = max(combined_candidates)
    else:
        # Corrige lecturas implausibles (ej: 0.60) cuando hay un candidato fuerte mucho mayor.
        if strong_candidates:
            strongest = max(strong_candidates)
            if total <= 1 and strongest >= 100:
                refined["total"] = strongest
            elif strongest >= (total * 10) and strongest >= 100:
                refined["total"] = strongest
        elif combined_candidates:
            strongest = max(combined_candidates)
            if total <= 1 and strongest >= 100:
                refined["total"] = strongest

    if not _safe_date_or_none(refined.get("fecha")):
        if date_candidates:
            refined["fecha"] = date_candidates[0]

    desc = _safe_desc(refined.get("descripcion"))
    if (not desc) or (desc.lower() in ("no se pudo interpretar el recibo", DEFAULT_DESC.lower())):
        if merchant_candidates:
            refined["descripcion"] = merchant_candidates[0]
    else:
        refined["descripcion"] = desc

    # Si la descripcion parece un fragmento JSON o ruido numerico, usar mejor candidato textual.
    desc_norm = (refined.get("descripcion") or "").strip().lower()
    if (
        '"total"' in desc_norm
        or '{' in desc_norm
        or '}' in desc_norm
        or re.fullmatch(r'[\d\s\.,\-/:$#]+', desc_norm or '')
    ):
        if merchant_candidates:
            refined["descripcion"] = merchant_candidates[0]
        else:
            refined["descripcion"] = DEFAULT_DESC

    return refined


def _tool_score_precision(candidate: dict, tool_data: dict) -> float:
    """Tool call interno: calcula score de precision del candidato OCR."""
    score = 0.0

    total = _safe_float(candidate.get("total"))
    fecha = _safe_date_or_none(candidate.get("fecha"))
    desc = (candidate.get("descripcion") or "").strip()
    items = candidate.get("items") or []

    if total is not None:
        score += 0.35
    if fecha:
        score += 0.20
    if desc and desc.lower() not in ("no se pudo interpretar el recibo", DEFAULT_DESC.lower()):
        score += 0.15
    if items:
        score += 0.10

    if candidate.get("contexto_inferido"):
        score -= 0.35

    total_lines = tool_data.get("numeric", {}).get("total_lines", [])
    amount_lines = tool_data.get("numeric", {}).get("amount_lines", [])
    decimals = tool_data.get("numeric", {}).get("decimal_candidates", [])
    if total is not None and (total in total_lines or total in amount_lines):
        score += 0.15
    elif total is not None and (total in decimals):
        score += 0.10

    # Penaliza montos extremadamente bajos cuando hay candidatos monetarios mucho mayores.
    if total is not None and total <= 1:
        strongest = 0
        if total_lines or amount_lines or decimals:
            strongest = max((total_lines + amount_lines + decimals) or [0])
        if strongest >= 100:
            score -= 0.25

    date_candidates = tool_data.get("dates", [])
    if fecha and fecha in date_candidates:
        score += 0.05

    model_conf = _extract_confidence_from_raw(candidate.get("raw", ""))
    if model_conf is not None:
        score += min(max(model_conf, 0.0), 1.0) * 0.10

    score = min(max(score, 0.0), 1.0)
    return round(score, 3)


def _run_tool_calls(raw_text: str, candidate: dict) -> dict:
    """Ejecuta un loop de tool calls internos para mejorar precision OCR."""
    trace = []
    context_inferido = _raw_indicates_context_inference(raw_text)

    tool_data = {
        "numeric": _tool_extract_numeric_candidates(raw_text),
        "dates": _tool_extract_date_candidates(raw_text),
        "merchants": _tool_extract_merchant_candidates(raw_text),
    }

    trace.append({
        "tool": "extract_numeric_candidates",
        "output": {
            "total_lines": len(tool_data["numeric"].get("total_lines", [])),
            "amount_lines": len(tool_data["numeric"].get("amount_lines", [])),
            "decimal_candidates": len(tool_data["numeric"].get("decimal_candidates", [])),
        },
    })
    trace.append({
        "tool": "extract_date_candidates",
        "output": {"count": len(tool_data.get("dates", []))},
    })
    trace.append({
        "tool": "extract_merchant_candidates",
        "output": {"count": len(tool_data.get("merchants", []))},
    })

    refined = _tool_refine_candidate(candidate, tool_data)
    trace.append({
        "tool": "refine_candidate",
        "output": {
            "total": refined.get("total"),
            "fecha": refined.get("fecha"),
            "descripcion": refined.get("descripcion"),
        },
    })

    precision = _tool_score_precision(refined, tool_data)
    trace.append({
        "tool": "score_precision",
        "output": {"precision_score": precision},
    })

    refined["precision_score"] = precision
    refined["contexto_inferido"] = context_inferido
    refined["tool_calls"] = trace
    return refined


def _choose_best_candidate(candidates: list) -> dict:
    """Selecciona el mejor candidato OCR por precision y completitud."""
    if not candidates:
        return None

    def key_fn(c):
        precision = c.get("precision_score", 0.0)
        has_total = 1 if _safe_float(c.get("total")) is not None else 0
        has_date = 1 if _safe_date_or_none(c.get("fecha")) else 0
        has_items = 1 if c.get("items") else 0
        return (precision, has_total, has_date, has_items)

    return sorted(candidates, key=key_fn, reverse=True)[0]


def _extract_confidence_from_raw(raw_text: str):
    """Intenta leer confidence de JSON OCR crudo si existe."""
    if not raw_text:
        return None

    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if not json_match:
        return None

    try:
        data = json.loads(json_match.group())
    except Exception:
        return None

    conf = data.get("confidence")
    try:
        conf = float(conf)
    except Exception:
        return None

    if not math.isfinite(conf):
        return None
    return min(max(conf, 0.0), 1.0)


def _raw_indicates_context_inference(raw_text: str) -> bool:
    """Detecta respuestas OCR donde el modelo admite inferencia sin lectura visual suficiente."""
    txt = (raw_text or "").lower()
    if not txt:
        return False

    markers = [
        "contexto previo",
        "datos externos",
        "sin ocr",
        "ausencia de texto ocr",
        "no hay texto ocr",
        "sin texto ocr confiable",
    ]
    return any(m in txt for m in markers)


# [NORMA: ISO/IEC 12207 - Proceso de Operación del Software] Proceso de negocio: Procesamiento de recibos por OCR
# [NORMA: ISO 9001:2000 - Enfoque basado en procesos] Proceso estandarizado para extracción de datos estructurados de comprobantes
def procesar_recibo_base64(image_base64: str, mime_type: str = "image/jpeg", texto_prueba: str = None) -> dict:
    """
    Procesa recibos con arquitectura OCR hibrida:
    1) OCR remoto (NVIDIA NIM) cuando esta disponible.
    2) Parser heuristico local para interpretar texto libre (testing/fallback).

    Retorna dict con: total, fecha, descripcion, items[], fuente.
    """
    errores = []
    candidatos = []

    if texto_prueba is not None:
        raw = str(texto_prueba)
        parsed = _parse_ocr_response(raw)
        parsed["fuente"] = "test_texto"
        parsed = _run_tool_calls(raw, parsed)
        tipo_sugerido, tipo_conf = _infer_tipo_movimiento(raw)
        parsed["tipo_sugerido"] = tipo_sugerido
        parsed["tipo_confianza"] = round(float(tipo_conf), 3)
        parsed["parse_summary"] = {
            "motor": "test_texto",
            "blocks": 0,
            "lineas": len([ln for ln in raw.splitlines() if ln.strip()]),
        }
        parsed["parse_tool"] = None
        parsed["rondas_ocr"] = 1
        parsed["modelo_llm"] = None
        parsed["page_elements_summary"] = {}
        parsed["page_elements_confirmacion"] = {"consistente": None}
        parsed["page_elements_trace"] = []
        candidatos.append(parsed)
    else:
        parse_payload = None
        parse_blocks = []
        parse_blocks_merged = []
        parse_tool_used = None

        for parse_tool in _get_parse_tools():
            try:
                parse_payload_current = _run_nemotron_parse(image_base64, mime_type, parse_tool)
                blocks_current = _extract_parse_blocks(parse_payload_current)
                if blocks_current:
                    parse_blocks_merged.extend(blocks_current)
                    if parse_tool_used is None:
                        parse_tool_used = parse_tool
                        parse_payload = parse_payload_current
            except Exception as exc:
                errores.append(f"NemotronParse {parse_tool}: {exc}")

        parse_blocks = _dedupe_parse_blocks(parse_blocks_merged)

        raw_parse_text = _blocks_to_text(parse_blocks)

        if raw_parse_text:
            llm_model_used = None
            normalized_raw = raw_parse_text
            try:
                normalized_raw, llm_model_used = _run_parse_normalizer_llm(parse_blocks, raw_parse_text)
            except Exception as exc:
                errores.append(f"Normalizador GPT: {exc}")

            parsed = _parse_ocr_response(normalized_raw)
            parsed["fuente"] = "nemotron_parse_gpt"
            parsed["raw"] = raw_parse_text
            parsed = _run_tool_calls(raw_parse_text, parsed)
            parsed["rondas_ocr"] = 1
            parsed["modelo_llm"] = llm_model_used
            parsed["page_elements_summary"] = {}
            parsed["page_elements_confirmacion"] = {"consistente": None}
            parsed["page_elements_trace"] = []

            tipo_sugerido, tipo_conf = _infer_tipo_movimiento(raw_parse_text)
            parsed["tipo_sugerido"] = tipo_sugerido
            parsed["tipo_confianza"] = round(float(tipo_conf), 3)
            parsed["parse_tool"] = parse_tool_used
            parsed["parse_summary"] = {
                "motor": OCR_PARSE_MODEL,
                "tool": parse_tool_used,
                "blocks": len(parse_blocks),
                "lineas": len([ln for ln in raw_parse_text.splitlines() if ln.strip()]),
                "tools_configuradas": _get_parse_tools(),
            }

            candidatos.append(parsed)

        # Fallback de compatibilidad si Nemotron Parse no entrega texto util.
        if not candidatos:
            try:
                raw_basic, llm_model_basic = _run_nvidia_ocr(image_base64, mime_type=mime_type)
                parsed_basic = _parse_ocr_response(raw_basic)
                parsed_basic["fuente"] = "nvidia_nim_basic"
                parsed_basic = _run_tool_calls(raw_basic, parsed_basic)
                tipo_sugerido, tipo_conf = _infer_tipo_movimiento(raw_basic)
                parsed_basic["tipo_sugerido"] = tipo_sugerido
                parsed_basic["tipo_confianza"] = round(float(tipo_conf), 3)
                parsed_basic["parse_tool"] = None
                parsed_basic["parse_summary"] = {
                    "motor": "fallback_basic",
                    "tool": None,
                    "blocks": 0,
                    "lineas": len([ln for ln in (raw_basic or "").splitlines() if ln.strip()]),
                    "tools_configuradas": _get_parse_tools(),
                }
                parsed_basic["rondas_ocr"] = 1
                parsed_basic["modelo_llm"] = llm_model_basic
                parsed_basic["page_elements_summary"] = {}
                parsed_basic["page_elements_confirmacion"] = {"consistente": None}
                parsed_basic["page_elements_trace"] = []
                candidatos.append(parsed_basic)
            except Exception as exc:
                errores.append(f"Fallback basico: {exc}")

        # Ultimo fallback: si hubo respuesta parse pero sin texto legible.
        if not candidatos and parse_payload:
            parsed_parse_only = {
                "total": None,
                "fecha": None,
                "descripcion": "Comprobante detectado por Nemotron Parse (sin texto legible)",
                "items": [],
                "raw": json.dumps(parse_payload, ensure_ascii=False),
                "fuente": "nemotron_parse_only",
                "rondas_ocr": 1,
                "modelo_llm": None,
                "page_elements_summary": {},
                "page_elements_confirmacion": {"consistente": None},
                "page_elements_trace": [],
                "precision_score": 0.2,
                "tool_calls": [],
                "tipo_sugerido": "desconocido",
                "tipo_confianza": 0.0,
                "parse_tool": parse_tool_used,
                "parse_summary": {
                    "motor": OCR_PARSE_MODEL,
                    "tool": parse_tool_used,
                    "blocks": len(parse_blocks),
                    "lineas": 0,
                    "tools_configuradas": _get_parse_tools(),
                },
            }
            candidatos.append(parsed_parse_only)

    best = _choose_best_candidate(candidatos)
    if best:
        if errores:
            best["errores"] = errores
        if _is_meaningful_result(best):
            return _normalize_result(best)

    if errores and texto_prueba is None:
        raise ValueError(f"OCR no disponible: {errores[0]}")

    return _normalize_result({
        "total": None,
        "fecha": None,
        "descripcion": "No se pudo interpretar el recibo",
        "items": [],
        "raw": (candidatos[0].get("raw", "") if candidatos else ""),
        "fuente": "fallback_local",
        "errores": errores,
        "precision_score": 0.0,
        "tool_calls": [],
        "rondas_ocr": 0,
        "modelo_llm": None,
        "page_elements_summary": {},
        "page_elements_confirmacion": {"consistente": None},
        "page_elements_trace": [],
    })


def _parse_ocr_response(raw_text: str) -> dict:
    """Parsea la respuesta OCR a un dict estructurado (JSON + heuristicas)."""
    raw_text = raw_text or ""
    # Algunos clientes envian saltos de linea escapados como texto literal (\\n).
    raw_text = raw_text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\r")

    # Intentar extraer JSON del texto.
    json_match = re.search(r'\{[\s\S]*\}', raw_text)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return {
                "total": _safe_float(data.get("total")),
                "fecha": _safe_date(data.get("fecha")),
                "descripcion": _safe_desc(data.get("descripcion")),
                "items": _safe_items(data.get("items")),
                "raw": raw_text,
            }
        except json.JSONDecodeError:
            pass

    # Fallback heuristico cuando no hay JSON valido.
    return {
        "total": _extract_total_from_text(raw_text),
        "fecha": _extract_date_from_text(raw_text),
        "descripcion": _extract_desc_from_text(raw_text),
        "items": [],
        "raw": raw_text,
    }


def _normalize_result(result: dict) -> dict:
    """Normaliza salida para evitar valores fuera de contrato."""
    normalized = {
        "total": _safe_float(result.get("total")),
        "fecha": _safe_date(result.get("fecha")),
        "descripcion": _safe_desc(result.get("descripcion")),
        "items": _safe_items(result.get("items")),
        "raw": result.get("raw", ""),
        "fuente": result.get("fuente", "fallback_local"),
        "errores": result.get("errores", []),
    }
    if "precision_score" in result:
        try:
            normalized["precision_score"] = round(float(result.get("precision_score") or 0.0), 3)
        except Exception:
            normalized["precision_score"] = 0.0
    if "tool_calls" in result:
        normalized["tool_calls"] = result.get("tool_calls", [])
    if "rondas_ocr" in result:
        try:
            normalized["rondas_ocr"] = int(result.get("rondas_ocr") or 0)
        except Exception:
            normalized["rondas_ocr"] = 0
    if "modelo_llm" in result:
        normalized["modelo_llm"] = result.get("modelo_llm")
    if "page_elements_summary" in result:
        normalized["page_elements_summary"] = result.get("page_elements_summary", {})
    if "page_elements_confirmacion" in result:
        normalized["page_elements_confirmacion"] = result.get("page_elements_confirmacion", {})
    if "page_elements_trace" in result:
        normalized["page_elements_trace"] = result.get("page_elements_trace", [])
    if "contexto_inferido" in result:
        normalized["contexto_inferido"] = bool(result.get("contexto_inferido"))
    tipo = str(result.get("tipo_sugerido") or "desconocido").lower().strip()
    if tipo not in ("ingreso", "gasto", "desconocido"):
        tipo = "desconocido"
    normalized["tipo_sugerido"] = tipo
    try:
        normalized["tipo_confianza"] = round(float(result.get("tipo_confianza") or 0.0), 3)
    except Exception:
        normalized["tipo_confianza"] = 0.0
    normalized["parse_tool"] = result.get("parse_tool")
    normalized["parse_summary"] = result.get("parse_summary", {})
    return normalized


def _is_meaningful_result(result: dict) -> bool:
    """Indica si el parse obtuvo informacion util del recibo."""
    if result.get("contexto_inferido"):
        total_present = _safe_float(result.get("total")) is not None
        date_present = _safe_date_or_none(result.get("fecha")) is not None

        total_lines = 0
        amount_lines = 0
        date_count = 0
        for call in (result.get("tool_calls") or []):
            if call.get("tool") == "extract_numeric_candidates":
                out = call.get("output") or {}
                total_lines = int(out.get("total_lines") or 0)
                amount_lines = int(out.get("amount_lines") or 0)
            elif call.get("tool") == "extract_date_candidates":
                out = call.get("output") or {}
                date_count = int(out.get("count") or 0)

        if total_present and (total_lines + amount_lines == 0):
            return False
        if date_present and date_count == 0:
            return False

    if result.get("total") is not None:
        return True
    if _safe_date_or_none(result.get("fecha")):
        return True
    if result.get("items"):
        return True
    desc = (result.get("descripcion") or "").strip().lower()
    if desc and "no se pudo" not in desc:
        return True
    return False


def _safe_items(items):
    """Normaliza lista de items y sus precios."""
    if not isinstance(items, list):
        return []

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        nombre = str(item.get("nombre", "")).strip()[:120]
        precio = _safe_float(item.get("precio"))
        if not nombre and precio is None:
            continue
        normalized.append({"nombre": nombre or "Item", "precio": precio})
    return normalized


def _safe_desc(value) -> str:
    """Normaliza descripcion del comercio."""
    desc = str(value or "").strip()
    if not desc:
        return DEFAULT_DESC
    # Evita descripciones contaminadas con JSON u objetos serializados.
    if '"total"' in desc.lower() or ('{' in desc and '}' in desc):
        return DEFAULT_DESC
    if re.fullmatch(r'[\d\s\.,\-/:$#]+', desc):
        return DEFAULT_DESC
    return desc[:200]


def _extract_total_from_text(raw_text: str):
    """Extrae monto total desde texto OCR libre."""
    if not raw_text:
        return None

    # Preferencia 1: linea con palabra TOTAL.
    match_total = re.search(
        r'(?im)\btotal(?:\s*(?:a\s*pagar|pagado)?)?\b[^\d\n\r-]*(-?[\d][\d\.,]*)',
        raw_text,
    )
    if match_total:
        parsed = _safe_float(match_total.group(1))
        if parsed is not None:
            return parsed

    # Preferencia 1.5: linea de monto/cuanto (comun en comprobantes Nequi).
    match_amount = re.search(
        r'(?im)\b(?:cuanto|monto|valor|pagaste|importe)\b[^\d\n\r-]*(-?[\d][\d\.,]*)',
        raw_text,
    )
    if match_amount:
        parsed = _safe_float(match_amount.group(1))
        if parsed is not None:
            return parsed

    # Preferencia 2: tomar monto con formato monetario decimal (ej: 123.45).
    decimal_candidates = re.findall(r'(-?[\d][\d\.,]*[\.,]\d{2})', raw_text)
    decimal_values = [v for v in (_safe_float(c) for c in decimal_candidates) if v is not None]
    if decimal_values:
        return max(decimal_values)

    # Preferencia 3: tomar el mayor monto detectado evitando anos de fecha comunes.
    candidates = re.findall(r'(-?[\d][\d\.,]*)', raw_text)
    values = []
    for c in candidates:
        v = _safe_float(c)
        if v is None:
            continue
        if v.is_integer() and 1900 <= int(v) <= 2100:
            continue
        values.append(v)
    if values:
        return max(values)
    return None


def _extract_date_from_text(raw_text: str):
    """Extrae fecha desde texto OCR libre en formatos comunes."""
    if not raw_text:
        return None

    iso_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', raw_text)
    if iso_match:
        return _safe_date(iso_match.group(1))

    latam_match = re.search(r'\b(\d{2})[/-](\d{2})[/-](\d{4})\b', raw_text)
    if latam_match:
        dd, mm, yyyy = latam_match.groups()
        return _safe_date(f"{yyyy}-{mm}-{dd}")

    spanish_dates = _extract_spanish_dates(raw_text)
    if spanish_dates:
        return _safe_date(spanish_dates[0])

    return None


def _extract_desc_from_text(raw_text: str):
    """Extrae descripcion heuristica del comercio desde primeras lineas."""
    if not raw_text:
        return "No se pudo interpretar el recibo"

    for line in raw_text.splitlines()[:8]:
        clean = line.strip()
        if len(clean) < 3:
            continue
        if re.search(r'^(total|fecha|subtotal|iva)\b', clean, flags=re.IGNORECASE):
            continue
        if re.fullmatch(r'[\d\s\.,\-/:$]+', clean):
            continue
        return clean[:200]

    return "No se pudo interpretar el recibo"


def _safe_float(value) -> float:
    """Convierte a float de forma segura."""
    if value is None:
        return None

    try:
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            cleaned = re.sub(r'[^\d,\.\-]', '', cleaned)
            if cleaned.count(',') > 0 and cleaned.count('.') > 0:
                # Si hay ambos separadores, el ultimo es el decimal.
                if cleaned.rfind(',') > cleaned.rfind('.'):
                    cleaned = cleaned.replace('.', '')
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            elif cleaned.count(',') > 0:
                cleaned = cleaned.replace('.', '')
                cleaned = cleaned.replace(',', '.')
            value = cleaned

        parsed = float(value)
        if not math.isfinite(parsed):
            return None
        if parsed < 0 or parsed > MAX_TOTAL_OCR:
            return None
        return round(parsed, 2)
    except (ValueError, TypeError):
        return None


def _safe_date(value) -> str:
    """Valida y normaliza una fecha."""
    if not value:
        return None
    try:
        datetime.strptime(str(value)[:10], "%Y-%m-%d")
        return str(value)[:10]
    except ValueError:
        return None


def _safe_date_or_none(value):
    """Valida una fecha sin autocompletar con fecha actual."""
    if not value:
        return None
    try:
        dt = datetime.strptime(str(value)[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _extract_spanish_dates(raw_text: str) -> list:
    """Extrae fechas en formato 'dd de mes de yyyy' (espanol)."""
    out = []
    if not raw_text:
        return out

    pattern = re.compile(
        r'\b(\d{1,2})\s+de\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)\s+de\s+(\d{4})\b',
        flags=re.IGNORECASE,
    )

    for dd_s, month_s, yyyy_s in pattern.findall(raw_text):
        month_key = (
            month_s.lower()
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )
        mm = MONTHS_ES.get(month_key)
        if not mm:
            continue
        try:
            dd = int(dd_s)
            yyyy = int(yyyy_s)
            candidate = f"{yyyy:04d}-{mm:02d}-{dd:02d}"
            if _safe_date_or_none(candidate):
                out.append(candidate)
        except Exception:
            continue

    # Quitar duplicados preservando orden.
    seen = set()
    uniq = []
    for d in out:
        if d in seen:
            continue
        seen.add(d)
        uniq.append(d)
    return uniq
