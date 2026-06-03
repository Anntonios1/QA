"""
============================================================
  MÓDULO LLM - Asistente Financiero con NVIDIA NIM
============================================================
  Normas aplicadas:
    - ISO/IEC 12207: Implementación modular
    - ISO/IEC 25000: Funcionalidad, Usabilidad
    - CMMI Nivel 3: Integración de servicios externos
============================================================
  Usa el modelo openai/gpt-oss-120b vía NVIDIA NIM
  para responder preguntas financieras y dar consejos
  basados en los datos del usuario.
============================================================
"""

import os
import json
import copy
import re
import unicodedata

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


SYSTEM_PROMPT = (
    "Eres un asistente financiero inteligente integrado en una app de control de gastos "
    "llamada ControlCash. Tu rol es ayudar al usuario con:\n"
    "- Análisis de sus hábitos de gasto\n"
    "- Consejos de ahorro personalizados\n"
    "- Explicaciones sobre presupuesto y finanzas personales\n"
    "- Interpretación de su balance y movimientos\n\n"
    "Responde siempre en español, de forma concisa y amigable. "
    "Si te dan contexto de su balance o resumen, úsalo para personalizar la respuesta. "
    "Limita respuestas a 3 párrafos máximo."
)


CHAT_TOOL_DEFINITIONS = [
    {
        "name": "obtener_balance_actual",
        "description": "Devuelve el balance financiero actual del usuario (ingresos, gastos y balance neto).",
        "data_access": ["balance.total_ingresos", "balance.total_gastos", "balance.balance", "balance.total_movimientos"],
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "obtener_resumen_30_dias",
        "description": "Devuelve métricas de los últimos 30 días: promedio diario, variación y proyección.",
        "data_access": [
            "resumen_30_dias.promedio_diario_gasto",
            "resumen_30_dias.variacion_vs_anterior_pct",
            "resumen_30_dias.proyeccion_30_dias",
            "resumen_30_dias.total_movimientos",
        ],
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "obtener_resumen_7_dias",
        "description": "Devuelve métricas de la última semana para detectar cambios recientes.",
        "data_access": [
            "resumen_7_dias.total_gastos",
            "resumen_7_dias.promedio_diario_gasto",
            "resumen_7_dias.variacion_vs_anterior_pct",
            "resumen_7_dias.total_movimientos",
        ],
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "obtener_top_categorias",
        "description": "Devuelve categorías más relevantes por monto en el período actual.",
        "data_access": ["resumen_30_dias.por_categoria"],
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": ["gasto", "ingreso", "todos"],
                    "description": "Filtra por tipo de categoría.",
                },
                "limite": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Cantidad máxima de categorías a devolver.",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "obtener_presupuestos_estado",
        "description": "Devuelve estado de presupuestos mensuales, con alertas de uso y excedidos.",
        "data_access": ["presupuestos_mes_actual"],
        "parameters": {
            "type": "object",
            "properties": {
                "solo_alertas": {
                    "type": "boolean",
                    "description": "Si true, devuelve solo presupuestos cerca del limite o excedidos.",
                },
                "umbral_alerta": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Porcentaje desde el cual se considera alerta (por defecto 80).",
                },
                "limite": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Cantidad maxima de presupuestos a devolver.",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "obtener_movimientos_recientes",
        "description": "Devuelve los movimientos mas recientes con filtros basicos para analisis rapido.",
        "data_access": ["movimientos_recientes"],
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": ["gasto", "ingreso", "todos"],
                    "description": "Filtra por tipo de movimiento.",
                },
                "limite": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Cantidad maxima de movimientos a devolver.",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "obtener_comparativo_periodos",
        "description": "Compara resumen de 7 dias y 30 dias para detectar tendencia de corto y mediano plazo.",
        "data_access": ["resumen_7_dias", "resumen_30_dias"],
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "obtener_proyeccion_fin_de_mes",
        "description": "Devuelve proyeccion de gasto al cierre del mes y porcentaje de avance temporal.",
        "data_access": ["proyeccion_mes_actual"],
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
]


def get_chat_tools_catalog() -> list:
    """Catálogo público de tools disponibles para el chat financiero."""
    return copy.deepcopy(CHAT_TOOL_DEFINITIONS)


def _responses_create(client, **kwargs):
    """Ejecuta Responses API y valida disponibilidad del SDK."""
    responses_api = getattr(client, "responses", None)
    if responses_api is None or not hasattr(responses_api, "create"):
        raise ValueError("El SDK OpenAI no soporta Responses API. Actualiza openai a una versión reciente.")
    return responses_api.create(**kwargs)


def _extract_responses_text(response) -> str:
    """Extrae texto de una respuesta de Responses API de forma robusta."""
    direct_text = getattr(response, "output_text", None)
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    output_items = getattr(response, "output", None) or []
    chunks = []

    for item in output_items:
        item_type = getattr(item, "type", None)

        if item_type in ("output_text", "text"):
            text = getattr(item, "text", None)
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
            continue

        if item_type == "message":
            for part in (getattr(item, "content", None) or []):
                part_type = getattr(part, "type", None)
                if part_type in ("output_text", "text"):
                    part_text = getattr(part, "text", None)
                    if isinstance(part_text, str) and part_text.strip():
                        chunks.append(part_text.strip())

    merged = "\n".join(chunks).strip()
    if not merged:
        raise ValueError("El proveedor IA no devolvio contenido de texto.")
    return merged


def _extract_responses_function_calls(response) -> list:
    """Extrae function calls de una respuesta de Responses API."""
    output_items = getattr(response, "output", None) or []
    calls = []

    for item in output_items:
        item_type = getattr(item, "type", None)
        if item_type != "function_call":
            continue

        call_id = getattr(item, "call_id", None) or getattr(item, "id", None) or ""
        name = getattr(item, "name", None) or ""
        arguments = getattr(item, "arguments", None)

        if not isinstance(arguments, str):
            try:
                arguments = json.dumps(arguments or {}, ensure_ascii=False)
            except Exception:
                arguments = "{}"

        calls.append({
            "call_id": call_id,
            "name": name,
            "arguments": arguments,
        })

    return calls


def _tool_name_from_user_shortcut(mensaje_usuario: str) -> str | None:
    """Detecta atajos explícitos del usuario para ejecutar una tool concreta."""
    texto = str(mensaje_usuario or "").lower().strip()
    if not texto:
        return None

    # Soporta comandos del estilo: "usa la 1", "herramienta 3", "usa 8".
    match = re.search(r"\b(?:usa(?:r)?|herramienta)\s+(?:la\s+)?([1-8])\b", texto)
    if match:
        idx = int(match.group(1)) - 1
        if 0 <= idx < len(CHAT_TOOL_DEFINITIONS):
            return CHAT_TOOL_DEFINITIONS[idx]["name"]

    for t in CHAT_TOOL_DEFINITIONS:
        if t["name"].lower() in texto:
            return t["name"]

    return None


def _normalize_text(texto: str) -> str:
    """Normaliza texto español a minúsculas ASCII simples para heurísticas robustas."""
    base = unicodedata.normalize("NFKD", str(texto or "").lower())
    sin_tildes = "".join(ch for ch in base if not unicodedata.combining(ch))
    limpio = re.sub(r"[^a-z0-9\s]", " ", sin_tildes)
    return re.sub(r"\s+", " ", limpio).strip()


def _mensaje_requiere_balance(mensaje_usuario: str) -> bool:
    """Heurística para preguntas de saldo/balance cuando el modelo no invoca tools."""
    texto = _normalize_text(mensaje_usuario)
    claves = (
        "saldo",
        "balance",
        "disponible",
        "cuanto dinero tengo",
        "dinero tengo",
        "cuánto dinero tengo",
    )
    return any(k in texto for k in claves)


def _mensaje_requiere_detalle_gastos(mensaje_usuario: str) -> bool:
    """Detecta preguntas sobre en qué se gastó el dinero y detalle de compras/pagos."""
    texto = _normalize_text(mensaje_usuario)
    if re.search(r"\ben que\b.*\bgast", texto):
        return True
    if re.search(r"\bdonde\b.*\bgast", texto):
        return True
    if "en que se fue el dinero" in texto:
        return True

    claves = (
        "detalle de gastos",
        "que compre",
        "mis gastos",
        "gastos recientes",
        "en que me lo gaste",
    )
    return any(k in texto for k in claves)


def _extract_movimiento_ref(mensaje_usuario: str) -> int | None:
    """Extrae referencia numérica de movimiento (soporta typo 'movimiendo')."""
    texto = _normalize_text(mensaje_usuario)
    # Ejemplos: movimiento 2, movimiendo 2, mov no 3, movimiento numero 5
    m = re.search(r"\bmov(?:imiento|imiendo|)\s*(?:n(?:umero|o)\s*)?(\d+)\b", texto)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def _format_balance_response(balance_data: dict) -> str:
    """Construye una respuesta directa de saldo usando datos verificados."""
    ingresos = _safe_float((balance_data or {}).get("total_ingresos", 0), 0.0)
    gastos = _safe_float((balance_data or {}).get("total_gastos", 0), 0.0)
    balance = _safe_float((balance_data or {}).get("balance", ingresos - gastos), ingresos - gastos)
    movimientos = _safe_int((balance_data or {}).get("total_movimientos", 0), 0)

    estado = "positivo" if balance > 0 else ("en equilibrio" if balance == 0 else "negativo")
    return (
        f"Tu saldo disponible actual es **${balance:,.2f}**. "
        f"Ingresos acumulados: **${ingresos:,.2f}**; gastos acumulados: **${gastos:,.2f}** "
        f"en **{movimientos}** movimientos. Tu balance está {estado}."
    )


def _format_gastos_detallados_response(top_data: dict, movs_data: dict) -> str:
    """Construye respuesta de gastos con desglose por categoría y movimientos recientes."""
    categorias = list((top_data or {}).get("categorias") or [])
    movimientos = list((movs_data or {}).get("movimientos") or [])

    if not categorias and not movimientos:
        return "No encontré gastos registrados en el periodo actual."

    lineas = ["Esto es en lo que has gastado tu dinero:"]

    if categorias:
        lineas.append("\n**Top categorías de gasto:**")
        for c in categorias[:5]:
            nombre = str(c.get("nombre", "N/A"))
            total = _safe_float(c.get("total", 0), 0.0)
            pct = _safe_float(c.get("porcentaje", 0), 0.0)
            lineas.append(f"- {nombre}: ${total:,.2f} ({pct:.1f}%)")

    if movimientos:
        lineas.append("\n**Movimientos de gasto recientes:**")
        for m in movimientos[:8]:
            monto = _safe_float(m.get("monto", 0), 0.0)
            categoria = str(m.get("categoria", "N/A"))
            descripcion = str(m.get("descripcion", "") or "Sin descripción")
            fecha = str(m.get("fecha", "") or "")
            fecha_short = fecha[:10] if len(fecha) >= 10 else fecha
            sufijo_fecha = f" ({fecha_short})" if fecha_short else ""
            lineas.append(f"- ${monto:,.2f} en {categoria}: {descripcion}{sufijo_fecha}")

    return "\n".join(lineas)


def _format_movimiento_detalle_response(movs_data: dict, ref_num: int) -> str:
    """Devuelve detalle de un movimiento por id o por posición (1-based)."""
    movimientos = list((movs_data or {}).get("movimientos") or [])
    if not movimientos:
        return "No encontré movimientos registrados para revisar ese detalle."

    seleccionado = None
    metodo = "id"

    for m in movimientos:
        if _safe_int(m.get("id"), -1) == ref_num:
            seleccionado = m
            break

    if seleccionado is None and 1 <= ref_num <= len(movimientos):
        seleccionado = movimientos[ref_num - 1]
        metodo = "posición"

    if seleccionado is None:
        ids = [str(_safe_int(m.get("id"), 0)) for m in movimientos[:8]]
        return (
            f"No encontré un movimiento {ref_num} en los recientes. "
            f"IDs visibles ahora: {', '.join(ids)}."
        )

    mov_id = _safe_int(seleccionado.get("id"), 0)
    tipo = str(seleccionado.get("tipo", "N/A") or "N/A")
    monto = _safe_float(seleccionado.get("monto", 0), 0.0)
    categoria = str(seleccionado.get("categoria", "N/A") or "N/A")
    descripcion = str(seleccionado.get("descripcion", "") or "Sin descripción")
    fecha = str(seleccionado.get("fecha", "") or "")
    fecha_short = fecha[:10] if len(fecha) >= 10 else fecha

    return (
        f"El movimiento {ref_num} ({metodo}) corresponde a ID {mov_id}: "
        f"tipo {tipo}, monto ${monto:,.2f}, categoría {categoria}, "
        f"descripción '{descripcion}'" + (f", fecha {fecha_short}." if fecha_short else ".")
    )


def _extract_text_content(response) -> str:
    """Obtiene texto del primer choice de forma segura.

    Algunos proveedores/modelos pueden devolver `message.content = None` en ciertos casos
    (p. ej., respuestas vacias o formatos no textuales). Esta funcion evita errores
    de atributo y estandariza un fallo controlado.
    """
    if not response or not getattr(response, "choices", None):
        raise ValueError("El proveedor IA no devolvio opciones de respuesta.")

    first = response.choices[0]
    message = getattr(first, "message", None)
    content = getattr(message, "content", None)

    if content is None:
        raise ValueError("El proveedor IA no devolvio contenido de texto.")

    if not isinstance(content, str):
        content = str(content)

    content = content.strip()
    if not content:
        raise ValueError("El proveedor IA devolvio contenido vacio.")

    return content


def _get_client():
    """Crea un cliente OpenAI apuntando a NVIDIA NIM."""
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY no configurada.")
    if not OPENAI_AVAILABLE:
        raise ImportError("openai no instalado. Ejecuta: pip install openai")
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )


def _build_contexto_resumido(contexto_financiero: dict) -> str:
    """Crea una versión compacta del contexto para el prompt del chat."""
    if not contexto_financiero:
        return "Sin datos financieros disponibles para este usuario."

    ctx_parts = []
    if "balance" in contexto_financiero:
        b = contexto_financiero["balance"]
        ctx_parts.append(
            f"Balance actual: Ingresos ${b.get('total_ingresos', 0):,.2f}, "
            f"Gastos ${b.get('total_gastos', 0):,.2f}, "
            f"Balance ${b.get('balance', 0):,.2f}"
        )

    if "resumen" in contexto_financiero:
        r = contexto_financiero["resumen"]
        ctx_parts.append(
            f"Promedio diario de gasto: ${r.get('promedio_diario_gasto', 0):,.2f}"
        )
        if r.get("por_categoria"):
            cats = ", ".join(
                f"{c.get('nombre', 'N/A')}(${float(c.get('total', 0) or 0):,.2f})"
                for c in r["por_categoria"][:5]
            )
            ctx_parts.append(f"Categorías principales: {cats}")

    if not ctx_parts:
        return "Sin datos financieros disponibles para este usuario."
    return "\n".join(ctx_parts)


def _chat_financiero_legacy(client, mensaje_usuario: str, contexto_financiero: dict = None) -> str:
    """Flujo sin tools usando Responses API para fallback robusto."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if contexto_financiero:
        messages.append({
            "role": "system",
            "content": "Contexto financiero del usuario:\n" + _build_contexto_resumido(contexto_financiero),
        })
    messages.append({"role": "user", "content": mensaje_usuario})

    try:
        response = _responses_create(
            client,
            model="openai/gpt-oss-120b",
            input=messages,
            max_output_tokens=512,
            temperature=0.7,
            top_p=1,
        )
        return _extract_responses_text(response)
    except Exception:
        # Compatibilidad defensiva para entornos con SDK antiguo.
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        return _extract_text_content(response)


def _safe_int(value, default_value: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default_value


def _safe_float(value, default_value: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default_value)


def _safe_bool(value, default_value: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        val = value.strip().lower()
        if val in ("1", "true", "yes", "si", "on"):
            return True
        if val in ("0", "false", "no", "off"):
            return False
    return default_value


def _execute_chat_tool(tool_name: str, args: dict, contexto_financiero: dict) -> dict:
    """Ejecuta una tool de chat sobre el contexto financiero actual."""
    contexto = contexto_financiero or {}
    balance = contexto.get("balance") or {}
    resumen = contexto.get("resumen") or {}
    resumen_7 = contexto.get("resumen_7_dias") or {}
    resumen_30 = contexto.get("resumen_30_dias") or resumen
    presupuestos = list(contexto.get("presupuestos_mes_actual") or [])
    movimientos = list(contexto.get("movimientos_recientes") or [])
    proyeccion_mes = contexto.get("proyeccion_mes_actual") or {}

    if tool_name == "obtener_balance_actual":
        return {
            "total_ingresos": float(balance.get("total_ingresos", 0) or 0),
            "total_gastos": float(balance.get("total_gastos", 0) or 0),
            "balance": float(balance.get("balance", 0) or 0),
            "total_movimientos": int(balance.get("total_movimientos", 0) or 0),
        }

    if tool_name == "obtener_resumen_30_dias":
        return {
            "periodo_dias": 30,
            "total_ingresos": _safe_float(resumen_30.get("total_ingresos", 0)),
            "total_gastos": _safe_float(resumen_30.get("total_gastos", 0)),
            "promedio_diario_gasto": _safe_float(resumen_30.get("promedio_diario_gasto", 0)),
            "variacion_vs_anterior_pct": _safe_float(resumen_30.get("variacion_vs_anterior_pct", 0)),
            "proyeccion_30_dias": _safe_float(resumen_30.get("proyeccion_30_dias", 0)),
            "total_movimientos": _safe_int(resumen_30.get("total_movimientos", 0), 0),
        }

    if tool_name == "obtener_resumen_7_dias":
        return {
            "periodo_dias": 7,
            "total_ingresos": _safe_float(resumen_7.get("total_ingresos", 0)),
            "total_gastos": _safe_float(resumen_7.get("total_gastos", 0)),
            "promedio_diario_gasto": _safe_float(resumen_7.get("promedio_diario_gasto", 0)),
            "variacion_vs_anterior_pct": _safe_float(resumen_7.get("variacion_vs_anterior_pct", 0)),
            "proyeccion_30_dias": _safe_float(resumen_7.get("proyeccion_30_dias", 0)),
            "total_movimientos": _safe_int(resumen_7.get("total_movimientos", 0), 0),
        }

    if tool_name == "obtener_top_categorias":
        categorias = list(resumen_30.get("por_categoria") or resumen.get("por_categoria") or [])
        tipo = str((args or {}).get("tipo", "todos") or "todos").lower().strip()
        if tipo in ("gasto", "ingreso"):
            categorias = [c for c in categorias if str(c.get("tipo", "")).lower() == tipo]

        limite = max(1, min(10, _safe_int((args or {}).get("limite"), 5)))
        salida = []
        for c in categorias[:limite]:
            salida.append({
                "nombre": c.get("nombre", "N/A"),
                "tipo": c.get("tipo", "N/A"),
                "total": float(c.get("total", 0) or 0),
                "porcentaje": float(c.get("porcentaje", 0) or 0),
            })
        return {"categorias": salida, "count": len(salida)}

    if tool_name == "obtener_presupuestos_estado":
        solo_alertas = _safe_bool((args or {}).get("solo_alertas"), False)
        umbral = max(1.0, min(100.0, _safe_float((args or {}).get("umbral_alerta"), 80.0)))
        limite = max(1, min(50, _safe_int((args or {}).get("limite"), 20)))

        items = []
        alertas = 0
        excedidos = 0
        for p in presupuestos:
            porcentaje = _safe_float(p.get("porcentaje_usado", 0))
            excedido = bool(p.get("excedido", False))
            alerta = excedido or porcentaje >= umbral
            if alerta:
                alertas += 1
            if excedido:
                excedidos += 1

            if solo_alertas and not alerta:
                continue

            items.append({
                "categoria": p.get("categoria_nombre") or "Global",
                "monto_limite": _safe_float(p.get("monto_limite", 0)),
                "gasto_actual": _safe_float(p.get("gasto_actual", 0)),
                "porcentaje_usado": round(porcentaje, 1),
                "excedido": excedido,
                "alerta": alerta,
            })

        return {
            "umbral_alerta": umbral,
            "total_presupuestos": len(presupuestos),
            "total_alertas": alertas,
            "total_excedidos": excedidos,
            "presupuestos": items[:limite],
        }

    if tool_name == "obtener_movimientos_recientes":
        tipo = str((args or {}).get("tipo", "todos") or "todos").lower().strip()
        limite = max(1, min(50, _safe_int((args or {}).get("limite"), 10)))

        rows = movimientos
        if tipo in ("gasto", "ingreso"):
            rows = [m for m in rows if str(m.get("tipo", "")).lower() == tipo]

        salida = []
        for m in rows[:limite]:
            fecha = m.get("fecha")
            if hasattr(fecha, "isoformat"):
                fecha = fecha.isoformat()
            salida.append({
                "id": _safe_int(m.get("id"), 0),
                "tipo": m.get("tipo", "N/A"),
                "monto": _safe_float(m.get("monto", 0)),
                "categoria": m.get("categoria_nombre", "N/A"),
                "descripcion": str(m.get("descripcion", "") or "")[:200],
                "fecha": fecha,
            })

        return {
            "count": len(salida),
            "movimientos": salida,
        }

    if tool_name == "obtener_comparativo_periodos":
        g7 = _safe_float(resumen_7.get("total_gastos", 0))
        g30 = _safe_float(resumen_30.get("total_gastos", 0))
        prom7 = _safe_float(resumen_7.get("promedio_diario_gasto", 0))
        prom30 = _safe_float(resumen_30.get("promedio_diario_gasto", 0))
        diff_prom = round(prom7 - prom30, 2)

        return {
            "periodo_7_dias": {
                "total_gastos": g7,
                "total_ingresos": _safe_float(resumen_7.get("total_ingresos", 0)),
                "promedio_diario_gasto": prom7,
                "variacion_vs_anterior_pct": _safe_float(resumen_7.get("variacion_vs_anterior_pct", 0)),
                "total_movimientos": _safe_int(resumen_7.get("total_movimientos", 0), 0),
            },
            "periodo_30_dias": {
                "total_gastos": g30,
                "total_ingresos": _safe_float(resumen_30.get("total_ingresos", 0)),
                "promedio_diario_gasto": prom30,
                "variacion_vs_anterior_pct": _safe_float(resumen_30.get("variacion_vs_anterior_pct", 0)),
                "total_movimientos": _safe_int(resumen_30.get("total_movimientos", 0), 0),
            },
            "diferencia_promedio_diario": diff_prom,
            "tendencia_corto_plazo": "alza" if diff_prom > 0 else ("baja" if diff_prom < 0 else "estable"),
        }

    if tool_name == "obtener_proyeccion_fin_de_mes":
        return {
            "gasto_acumulado": _safe_float(proyeccion_mes.get("gasto_acumulado", 0)),
            "dias_transcurridos": _safe_int(proyeccion_mes.get("dias_transcurridos", 0), 0),
            "dias_del_mes": _safe_int(proyeccion_mes.get("dias_del_mes", 0), 0),
            "avance_temporal_pct": _safe_float(proyeccion_mes.get("avance_temporal_pct", 0)),
            "proyeccion_gasto_fin_mes": _safe_float(proyeccion_mes.get("proyeccion_gasto_fin_mes", 0)),
            "promedio_diario_mes_actual": _safe_float(proyeccion_mes.get("promedio_diario_mes_actual", 0)),
        }

    raise ValueError(f"Tool no soportada: {tool_name}")


# [NORMA: ISO/IEC 12207 - Proceso de Operación] Endpoint principal de negocio: Asistente financiero inteligente con IA
# [NORMA: ISO/IEC 25000 - Característica de Usabilidad] Asistencia personalizada al usuario mediante LLM y NVIDIA NIM
def chat_financiero(mensaje_usuario: str, contexto_financiero: dict = None) -> dict:
    """Envía un mensaje al LLM con Responses API + tool-calling financiero."""
    client = _get_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                "Si necesitas datos financieros numéricos del usuario, usa tools antes de responder. "
                "No inventes cifras: consulta herramientas cuando aplique."
            ),
        },
        {
            "role": "system",
            "content": "Contexto financiero de partida:\n" + _build_contexto_resumido(contexto_financiero),
        },
        {"role": "user", "content": mensaje_usuario},
    ]

    tools = [
        {
            "type": "function",
            "name": t["name"],
            "description": t["description"],
            "parameters": t["parameters"],
        }
        for t in CHAT_TOOL_DEFINITIONS
    ]

    tools_usadas = []

    try:
        first_response = _responses_create(
            client,
            model="openai/gpt-oss-120b",
            input=messages,
            tools=tools,
            tool_choice="auto",
            max_output_tokens=640,
            temperature=0.7,
            top_p=1,
        )
        tool_calls = _extract_responses_function_calls(first_response)
        shortcut_tool = _tool_name_from_user_shortcut(mensaje_usuario)
        requiere_balance = _mensaje_requiere_balance(mensaje_usuario)
        requiere_detalle_gastos = _mensaje_requiere_detalle_gastos(mensaje_usuario)
        movimiento_ref = _extract_movimiento_ref(mensaje_usuario)

        # Fallback determinístico: si el usuario usa atajo explícito o pide saldo,
        # ejecutamos tool local aunque el proveedor no emita function_call.
        if not tool_calls:
            forced_tool = shortcut_tool
            if forced_tool:
                tool_calls = [{"name": forced_tool, "arguments": "{}", "call_id": "forced-call"}]
            elif movimiento_ref is not None:
                tool_calls = [
                    {"name": "obtener_movimientos_recientes", "arguments": json.dumps({"tipo": "todos", "limite": 50}), "call_id": "forced-movs-ref"},
                ]
            elif requiere_detalle_gastos:
                tool_calls = [
                    {"name": "obtener_top_categorias", "arguments": json.dumps({"tipo": "gasto", "limite": 5}), "call_id": "forced-top-gastos"},
                    {"name": "obtener_movimientos_recientes", "arguments": json.dumps({"tipo": "gasto", "limite": 12}), "call_id": "forced-movs-gastos"},
                ]
            elif requiere_balance:
                tool_calls = [{"name": "obtener_balance_actual", "arguments": "{}", "call_id": "forced-balance"}]

        if not tool_calls:
            return {
                "respuesta": _extract_responses_text(first_response),
                "tools_usadas": tools_usadas,
            }

        for tc in tool_calls[:4]:
            fn_name = str(tc.get("name") or "")
            raw_args = tc.get("arguments", "{}")

            args = {}
            if isinstance(raw_args, str) and raw_args.strip():
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}

            tool_output = _execute_chat_tool(fn_name, args, contexto_financiero)
            tools_usadas.append(
                {
                    "tool": fn_name,
                    "args": args,
                    "output": tool_output,
                }
            )

        # Si el usuario pide detalle de gastos, aseguramos ambas fuentes aunque el modelo
        # solo haya pedido una tool.
        if requiere_detalle_gastos:
            names = {str(t.get("tool") or "") for t in tools_usadas}
            if "obtener_top_categorias" not in names:
                top_output = _execute_chat_tool(
                    "obtener_top_categorias",
                    {"tipo": "gasto", "limite": 5},
                    contexto_financiero,
                )
                tools_usadas.append(
                    {
                        "tool": "obtener_top_categorias",
                        "args": {"tipo": "gasto", "limite": 5},
                        "output": top_output,
                    }
                )
            if "obtener_movimientos_recientes" not in names:
                movs_output = _execute_chat_tool(
                    "obtener_movimientos_recientes",
                    {"tipo": "gasto", "limite": 12},
                    contexto_financiero,
                )
                tools_usadas.append(
                    {
                        "tool": "obtener_movimientos_recientes",
                        "args": {"tipo": "gasto", "limite": 12},
                        "output": movs_output,
                    }
                )

        # Respuesta determinística para saldo/balance (evita pedir datos ya disponibles).
        if len(tools_usadas) == 1 and tools_usadas[0].get("tool") == "obtener_balance_actual":
            if requiere_balance or shortcut_tool == "obtener_balance_actual":
                return {
                    "respuesta": _format_balance_response(tools_usadas[0].get("output") or {}),
                    "tools_usadas": tools_usadas,
                }

        if movimiento_ref is not None:
            movs_data = {}
            for t in tools_usadas:
                if t.get("tool") == "obtener_movimientos_recientes":
                    movs_data = t.get("output") or {}
                    break

            if not movs_data:
                movs_data = _execute_chat_tool(
                    "obtener_movimientos_recientes",
                    {"tipo": "todos", "limite": 50},
                    contexto_financiero,
                )
                tools_usadas.append(
                    {
                        "tool": "obtener_movimientos_recientes",
                        "args": {"tipo": "todos", "limite": 50},
                        "output": movs_data,
                    }
                )

            return {
                "respuesta": _format_movimiento_detalle_response(movs_data, movimiento_ref),
                "tools_usadas": tools_usadas,
            }

        if requiere_detalle_gastos:
            top_data = {}
            movs_data = {}
            for t in tools_usadas:
                if t.get("tool") == "obtener_top_categorias" and not top_data:
                    top_data = t.get("output") or {}
                if t.get("tool") == "obtener_movimientos_recientes" and not movs_data:
                    movs_data = t.get("output") or {}

            return {
                "respuesta": _format_gastos_detallados_response(top_data, movs_data),
                "tools_usadas": tools_usadas,
            }

        # NVIDIA Responses no soporta encadenar function_call_output con previous_response_id
        # en este endpoint. En su lugar, inyectamos los resultados como contexto verificado.
        resultados_tools = json.dumps(tools_usadas, ensure_ascii=False)
        synthesis_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": (
                    "Usa exclusivamente los resultados de tools ya ejecutadas como fuente de verdad. "
                    "No pidas al usuario datos que ya estén en esos resultados."
                ),
            },
            {"role": "system", "content": "Resultados de tools ejecutadas:\n" + resultados_tools},
            {"role": "user", "content": mensaje_usuario},
        ]

        final_response = _responses_create(
            client,
            model="openai/gpt-oss-120b",
            input=synthesis_messages,
            max_output_tokens=640,
            temperature=0.5,
            top_p=1,
        )

        return {
            "respuesta": _extract_responses_text(final_response),
            "tools_usadas": tools_usadas,
        }

    except ValueError:
        raise
    except Exception:
        # Fallback robusto en modo sin tools usando Responses API.
        respuesta_legacy = _chat_financiero_legacy(client, mensaje_usuario, contexto_financiero=contexto_financiero)
        return {
            "respuesta": respuesta_legacy,
            "tools_usadas": [],
        }


def _perfil_por_metricas(contexto_financiero: dict) -> dict:
    """Construye un perfil consistente usando reglas determinísticas del contexto."""
    balance = (contexto_financiero or {}).get("balance") or {}
    resumen = (contexto_financiero or {}).get("resumen") or {}

    ingresos = _safe_float(balance.get("total_ingresos", resumen.get("total_ingresos", 0)), 0.0)
    gastos = _safe_float(balance.get("total_gastos", resumen.get("total_gastos", 0)), 0.0)
    balance_neto = _safe_float(balance.get("balance", ingresos - gastos), ingresos - gastos)
    movimientos = _safe_int(balance.get("total_movimientos", resumen.get("total_movimientos", 0)), 0)
    variacion = _safe_float(resumen.get("variacion_vs_anterior_pct", 0), 0.0)

    hay_actividad = movimientos > 0 or ingresos > 0 or gastos > 0

    if not hay_actividad:
        return {
            "tipo_label": "El Inactivo Financiero",
            "score": 5,
            "tags": ["🛒 Básicos", "⚠️ Sin actividad", "💤 Inactivo", "📉 Riesgo bajo"],
            "narrativa": (
                "Actualmente no se registran ingresos ni gastos, lo que indica una ausencia de actividad financiera. "
                "Es importante iniciar un seguimiento activo para comprender mejor tu situación y planificar futuros objetivos."
            ),
            "habitos_positivos": [
                "Mantienes un registro sin deudas",
                "No hay gastos impulsivos",
            ],
            "areas_mejora": [
                "Generar ingresos sostenibles",
                "Establecer un presupuesto básico",
            ],
        }

    score = 35
    if ingresos > 0:
        score += 15
    if gastos > 0:
        score += 10
    if balance_neto > 0:
        score += 20
    if movimientos >= 5:
        score += 5
    if variacion <= 0:
        score += 5
    score = max(0, min(100, int(score)))

    tipo_label = "El Organizador en Progreso"
    if score >= 75:
        tipo_label = "El Ahorrador Inteligente"
    elif score >= 55:
        tipo_label = "El Equilibrado"

    tags = []
    if ingresos > 0:
        tags.append("💰 Con ingresos")
    if gastos > 0:
        tags.append("🧾 En seguimiento")
    if balance_neto > 0:
        tags.append("✅ Balance positivo")
    else:
        tags.append("⚠️ Ajustar gastos")
    tags.append("📊 Activo")

    narrativa = (
        f"Registras actividad financiera con {movimientos} movimientos, ingresos por ${ingresos:,.2f} y "
        f"gastos por ${gastos:,.2f}. Tu balance actual es ${balance_neto:,.2f}. "
        "Vas en buen camino; mantén la constancia para que el análisis sea cada vez más preciso."
    )

    habitos = []
    if ingresos > 0:
        habitos.append("Estás registrando ingresos de forma explícita")
    if gastos >= 0:
        habitos.append("Llevas trazabilidad de tus movimientos")
    if balance_neto > 0:
        habitos.append("Mantienes saldo neto positivo")

    mejoras = []
    if gastos == 0:
        mejoras.append("Registrar también gastos para obtener un diagnóstico más completo")
    if ingresos > 0 and balance_neto <= 0:
        mejoras.append("Reducir gastos para recuperar balance positivo")
    if movimientos < 5:
        mejoras.append("Aumentar la frecuencia de registro para mejorar recomendaciones")
    if not mejoras:
        mejoras.append("Definir metas de ahorro mensuales para acelerar progreso")

    return {
        "tipo_label": tipo_label,
        "score": score,
        "tags": tags[:4],
        "narrativa": narrativa,
        "habitos_positivos": habitos[:3],
        "areas_mejora": mejoras[:3],
    }


def _perfil_inconsistente_con_contexto(perfil: dict, contexto_financiero: dict) -> bool:
    """Detecta si el texto del perfil contradice la actividad real del usuario."""
    balance = (contexto_financiero or {}).get("balance") or {}
    resumen = (contexto_financiero or {}).get("resumen") or {}

    ingresos = _safe_float(balance.get("total_ingresos", resumen.get("total_ingresos", 0)), 0.0)
    gastos = _safe_float(balance.get("total_gastos", resumen.get("total_gastos", 0)), 0.0)
    movimientos = _safe_int(balance.get("total_movimientos", resumen.get("total_movimientos", 0)), 0)

    hay_actividad = movimientos > 0 or ingresos > 0 or gastos > 0
    if not hay_actividad:
        return False

    tipo_label = str((perfil or {}).get("tipo_label", "")).lower()
    narrativa = str((perfil or {}).get("narrativa", "")).lower()
    tags = " ".join(str(t).lower() for t in ((perfil or {}).get("tags") or []))
    texto = f"{tipo_label} {narrativa} {tags}"

    marcadores_inactivos = (
        "sin actividad",
        "inactivo",
        "inactiva",
        "no se registran ingresos ni gastos",
        "ausencia de actividad",
    )

    return any(m in texto for m in marcadores_inactivos)


def generar_perfil_financiero(contexto_financiero: dict) -> dict:
    """
    Genera un perfil psicológico-financiero del usuario basado en sus datos.

    El perfil incluye:
    - tipo_label: Arquetipo del usuario (ej. "El Ahorrador Cauteloso")
    - score: Puntuación de salud financiera 0-100
    - tags: Lista de etiquetas de comportamiento
    - narrativa: Párrafo descriptivo personalizado
    - habitos_positivos: Lista de hábitos detectados buenos
    - areas_mejora: Lista de áreas donde mejorar

    Args:
        contexto_financiero: Dict con balance y resumen 30 días

    Returns:
        Dict estructurado con el perfil financiero
    """
    client = _get_client()

    perfil_fallback = _perfil_por_metricas(contexto_financiero)

    # Construir contexto
    ctx_lines = []
    if "balance" in contexto_financiero:
        b = contexto_financiero["balance"]
        ctx_lines.append(f"- Ingresos totales: ${_safe_float(b.get('total_ingresos', 0)):,.2f}")
        ctx_lines.append(f"- Gastos totales: ${_safe_float(b.get('total_gastos', 0)):,.2f}")
        ctx_lines.append(f"- Balance neto: ${_safe_float(b.get('balance', 0)):,.2f}")
        ctx_lines.append(f"- Total movimientos: {_safe_int(b.get('total_movimientos', 0), 0)}")

    if "resumen" in contexto_financiero:
        r = contexto_financiero["resumen"]
        ctx_lines.append(f"- Promedio gasto diario (30d): ${r.get('promedio_diario_gasto', 0):,.2f}")
        ctx_lines.append(f"- Variación vs período anterior: {r.get('variacion_vs_anterior_pct', 0):.1f}%")
        ctx_lines.append(f"- Proyección 30 días: ${r.get('proyeccion_30_dias', 0):,.2f}")
        if r.get("por_categoria"):
            cats = [(c["nombre"], c["tipo"], c["total"], c.get("porcentaje", 0))
                    for c in r["por_categoria"][:8]]
            cats_str = ", ".join(
                f"{n}({'gasto' if t == 'gasto' else 'ingreso'}: ${v:,.2f} = {p:.0f}%)"
                for n, t, v, p in cats
            )
            ctx_lines.append(f"- Distribución por categoría: {cats_str}")
        if r.get("top_gastos"):
            top = r["top_gastos"]
            top_str = ", ".join(
                f"${g['monto']:,.2f} en {g.get('categoria', 'N/A')}"
                for g in top[:3]
            )
            ctx_lines.append(f"- Top gastos: {top_str}")

    ctx_text = "\n".join(ctx_lines) if ctx_lines else "Sin datos financieros disponibles."

    prompt = (
        f"Analiza los siguientes datos financieros del usuario y genera un perfil detallado.\n\n"
        f"DATOS FINANCIEROS:\n{ctx_text}\n\n"
        "REGLAS ESTRICTAS DE CONSISTENCIA:\n"
        "- Si Total movimientos > 0 o hay ingresos/gastos > 0, NUNCA afirmes 'sin actividad' o 'inactivo'.\n"
        "- Si hay ingresos registrados, debes reflejar actividad financiera en tipo_label, tags y narrativa.\n"
        "- El análisis debe ser coherente con los montos numéricos entregados.\n\n"
        "Responde ÚNICAMENTE con un JSON válido (sin markdown, sin texto extra) con esta estructura exacta:\n"
        "{\n"
        '  "tipo_label": "Nombre del arquetipo financiero (ej: El Ahorrador Inteligente, El Gastador Impulsivo, El Equilibrado)",\n'
        '  "score": <número entero entre 0 y 100 que representa la salud financiera>,\n'
        '  "tags": ["etiqueta1 con emoji", "etiqueta2 con emoji", "etiqueta3 con emoji", "etiqueta4 con emoji"],\n'
        '  "narrativa": "2-3 oraciones describiendo el perfil financiero del usuario de forma empática y personalizada",\n'
        '  "habitos_positivos": ["hábito positivo 1", "hábito positivo 2"],\n'
        '  "areas_mejora": ["área de mejora 1", "área de mejora 2"]\n'
        "}\n\n"
        "El score debe calcularse considerando: ahorro (diferencia ingreso-gasto), diversificación de categorías, "
        "consistencia de gastos, y tendencia vs período anterior. "
        "Los tags deben incluir emojis descriptivos como '🛒 Básicos', '🎓 Educación', '⚠️ Ocio excesivo', '💰 Buen ahorrador'."
    )

    response = _responses_create(
        client,
        model="openai/gpt-oss-120b",
        input=[
            {"role": "system", "content": "Eres un analista financiero experto. Respondes SIEMPRE con JSON puro válido, sin markdown, sin explicaciones adicionales."},
            {"role": "user", "content": prompt}
        ],
        max_output_tokens=800,
        temperature=0.5,
        top_p=1,
    )

    raw = _extract_responses_text(response)

    # Limpiar si tiene bloques markdown
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        perfil = json.loads(raw)
        # Asegurar tipos correctos
        perfil["score"] = max(0, min(100, int(perfil.get("score", 50))))
        if not isinstance(perfil.get("tags"), list):
            perfil["tags"] = []
        if not isinstance(perfil.get("habitos_positivos"), list):
            perfil["habitos_positivos"] = []
        if not isinstance(perfil.get("areas_mejora"), list):
            perfil["areas_mejora"] = []

        # Guardrail: evita perfiles incoherentes con actividad real.
        if _perfil_inconsistente_con_contexto(perfil, contexto_financiero):
            return perfil_fallback

        return perfil
    except (json.JSONDecodeError, ValueError):
        # Fallback robusto si el JSON falla.
        return perfil_fallback


def generar_insight_diario(nombre: str, contexto_financiero: dict) -> str:
    """
    Genera un mensaje motivador diario personalizado tipo Duolingo.

    El mensaje es corto (2-3 oraciones), usa emojis, es positivo/motivador
    y menciona datos concretos del usuario del día/semana anterior.

    Args:
        nombre: Nombre del usuario
        contexto_financiero: Dict con balance y resumen

    Returns:
        Mensaje string motivador personalizado
    """
    client = _get_client()

    ctx_lines = [f"Nombre del usuario: {nombre}"]
    if "balance" in contexto_financiero:
        b = contexto_financiero["balance"]
        ctx_lines.append(f"Balance actual: ${b.get('balance', 0):,.2f}")
        ctx_lines.append(f"Gastos totales registrados: ${b.get('total_gastos', 0):,.2f}")
        ctx_lines.append(f"Ingresos totales: ${b.get('total_ingresos', 0):,.2f}")

    if "resumen" in contexto_financiero:
        r = contexto_financiero["resumen"]
        ctx_lines.append(f"Gasto promedio diario (30d): ${r.get('promedio_diario_gasto', 0):,.2f}")
        ctx_lines.append(f"Variación vs período anterior: {r.get('variacion_vs_anterior_pct', 0):.1f}%")
        ctx_lines.append(f"Total movimientos período: {r.get('total_movimientos', 0)}")
        if r.get("por_categoria"):
            top_cat = r["por_categoria"][0]
            ctx_lines.append(f"Categoría principal de gasto: {top_cat['nombre']} (${top_cat['total']:,.2f})")

    ctx_text = "\n".join(ctx_lines)

    prompt = (
        f"Genera un mensaje motivador diario corto (máximo 2-3 oraciones) para el usuario de una app de finanzas.\n\n"
        f"DATOS:\n{ctx_text}\n\n"
        "El mensaje debe:\n"
        "- Empezar con un emoji relevante y el nombre del usuario\n"
        "- Mencionar 1-2 datos financieros concretos (monto, categoría, tendencia)\n"
        "- Ser motivador, positivo y de apoyo (como Duolingo)\n"
        "- Terminar con una llamada a la acción o aliento\n"
        "- Estar en español, ser informal y amigable\n"
        "- Tener máximo 150 palabras\n\n"
        "Responde SOLO con el mensaje, sin comillas, sin explicaciones."
    )

    response = _responses_create(
        client,
        model="openai/gpt-oss-120b",
        input=[
            {"role": "system", "content": "Eres un coach financiero motivador y amigable. Escribes mensajes cortos, cálidos y con datos concretos."},
            {"role": "user", "content": prompt}
        ],
        max_output_tokens=200,
        temperature=0.85,
        top_p=1,
    )

    return _extract_responses_text(response)
