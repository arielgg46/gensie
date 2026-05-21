STRICT_ANCHORING_RULE = (
    "REGLA DE ANCLAJE ESTRICTO:\n"
    "\n"
    "Cada value debe provenir del TEXTO FUENTE: copia textual, selección de enum "
    "justificada por el texto, o normalización directa de un dato explícito. No "
    "completes información ausente con conocimiento externo, no transformes "
    "pistas débiles en hechos exactos y no cambies una categoría semántica por "
    "otra.\n"
    "\n"
    "Si el schema obliga un valor y la evidencia es limitada, dilo en el "
    "reasoning y elige la opción menos especulativa compatible con el schema."
)

EXTRACTION_RULES_HEADER = "REGLAS DE EXTRACCIÓN, OBLIGATORIAS, NO NEGOCIABLES:"

EXTRACTION_RULES = (
    "- Devuelve solo el JSON requerido y completa todos los campos del schema. No agregues campos, notas ni texto fuera del JSON.",
    '- `value` contiene solo la respuesta final: nunca explicaciones, dudas, frases de ausencia ni el string "null". Si corresponde ausencia y el schema permite null, usa JSON null.',
    "- Decide cada campo por su nombre, tipo, enum y description. No sustituyas el tipo pedido por uno parecido: persona no es organización, país no es organización, lugar no es evento, rol/descripción no es nombre propio.",
    "- Todo `value` no nulo debe apoyarse en el TEXTO FUENTE. Los ejemplos few-shot enseñan formato y criterio; nunca son evidencia para el task actual.",
    "- El `reasoning` debe citar solo los fragmentos mínimos que deciden el valor. Cada fragmento citado debe aportar identidad, tipo, fecha, cantidad, condición, negación o contexto necesario.",
    "- Si el campo pide string extraído o lista de strings y no pide normalización, prefiere fragmentos verbatim o casi verbatim. No parafrasees una formulación clara del texto.",
    "- En arrays, incluye todos los elementos explícitamente respaldados del tipo pedido y excluye elementos de otro tipo aunque aparezcan cerca. Usa [] solo si no hay ningún elemento válido.",
    "- En enums, `value` debe ser exactamente una opción permitida y el `reasoning` debe conectar el texto con esa opción; no elijas por conocimiento externo.",
    "- Para fechas, cantidades, unidades y formatos, normaliza solo datos presentes en el texto. Puedes combinar fragmentos conectados, pero no completar partes ausentes.",
    "- Si el texto da una pista parcial, aproximada, relativa, comparativa o cualitativa y el schema pide un valor exacto, usa null cuando esté permitido.",
)

BASE_EXTRACTION_SYSTEM_PROMPT = (
    "Eres un agente preciso de extracción de información. "
    "Devuelve solo el objeto JSON requerido por el schema. "
    "Usa solo evidencia del texto fuente."
)

ENRICHED_SCHEMA_SYSTEM_PROMPT = (
    "Eres un motor experto de extracción de información en español.\n"
    "Devuelve solo el objeto JSON requerido por el schema.\n"
    "Usa solo evidencia del texto fuente.\n"
    "No incluyas explicaciones, reasoning ni campos adicionales."
)

INLINE_REASONING_SYSTEM_PROMPT = (
    "Eres un motor experto de extracción de información en español.\n"
    "Devuelve solo el objeto JSON requerido por el schema.\n"
    "Usa solo evidencia del texto fuente.\n"
    "Para cada campo de primer nivel, escribe tu razonamiento antes del valor final.\n"
    "En cada reasoning, cita texto exacto cuando exista evidencia, o indica que no hay evidencia textual.\n"
    f"{STRICT_ANCHORING_RULE}"
)

ENRICHED_INLINE_REASONING_SYSTEM_PROMPT = (
    "Eres un motor experto de extracción de información en español.\n"
    "Devuelve solo el objeto JSON requerido por el schema.\n"
    "Usa solo evidencia del texto fuente.\n"
    "Cada campo de primer nivel debe incluir reasoning y value.\n"
    "En cada reasoning, cita texto exacto cuando exista evidencia, o indica que no hay evidencia textual.\n"
    f"{STRICT_ANCHORING_RULE}"
)

DEEP_INLINE_REASONING_SYSTEM_PROMPT = (
    "Eres un motor experto de extracción de información en español.\n"
    "Devuelve solo el objeto JSON requerido por el schema.\n"
    "Usa solo evidencia del texto fuente.\n"
    "Cada campo, subcampo y elemento de array debe incluir reasoning y value.\n"
    "En cada reasoning, cita texto exacto cuando exista evidencia, o indica que no hay evidencia textual.\n"
    f"{STRICT_ANCHORING_RULE}"
)
