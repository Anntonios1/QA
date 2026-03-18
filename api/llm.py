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


def chat_financiero(mensaje_usuario: str, contexto_financiero: dict = None) -> str:
    """
    Envía un mensaje al LLM con contexto financiero opcional.

    Args:
        mensaje_usuario: Pregunta o mensaje del usuario
        contexto_financiero: Dict con balance, resumen, etc.

    Returns:
        Respuesta del LLM como string
    """
    client = _get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Agregar contexto financiero si existe
    if contexto_financiero:
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
                    f"{c['nombre']}(${c['total']:,.2f})"
                    for c in r["por_categoria"][:5]
                )
                ctx_parts.append(f"Categorías principales: {cats}")

        if ctx_parts:
            messages.append({
                "role": "system",
                "content": "Contexto financiero del usuario:\n" + "\n".join(ctx_parts)
            })

    messages.append({"role": "user", "content": mensaje_usuario})

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        max_tokens=512,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


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

    # Construir contexto
    ctx_lines = []
    if "balance" in contexto_financiero:
        b = contexto_financiero["balance"]
        ctx_lines.append(f"- Ingresos totales: ${b.get('total_ingresos', 0):,.2f}")
        ctx_lines.append(f"- Gastos totales: ${b.get('total_gastos', 0):,.2f}")
        ctx_lines.append(f"- Balance neto: ${b.get('balance', 0):,.2f}")
        ctx_lines.append(f"- Total movimientos: {b.get('total_movimientos', 0)}")

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

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "Eres un analista financiero experto. Respondes SIEMPRE con JSON puro válido, sin markdown, sin explicaciones adicionales."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.5,
    )

    raw = response.choices[0].message.content.strip()

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
        return perfil
    except (json.JSONDecodeError, ValueError):
        # Fallback si el JSON falla
        return {
            "tipo_label": "Perfil en análisis",
            "score": 50,
            "tags": ["📊 Analizando datos"],
            "narrativa": raw[:300] if raw else "No se pudo generar el análisis.",
            "habitos_positivos": [],
            "areas_mejora": []
        }


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

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "Eres un coach financiero motivador y amigable. Escribes mensajes cortos, cálidos y con datos concretos."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.85,
    )

    return response.choices[0].message.content.strip()
