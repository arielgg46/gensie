# Propuesta de pipeline: simple-clean-schema

## Objetivo

Implementar un pipeline intermedio entre el baseline oficial y variantes mas caras: una sola llamada al SLM por tarea, prompting simple pero mas explicito, y Grammar-Constrained Decoding usando siempre el `target_schema` original sin modificar.

La idea es mejorar la calidad semantica del baseline sin aumentar el numero de consultas ni introducir recuperacion, ejemplos dinamicos, self-correction o pasos de validacion con modelo. El coste debe seguir siendo cercano al baseline: una request, un output JSON, y trazas equivalentes.

## Restricciones principales

- Una sola consulta al modelo por `Task`.
- La salida se fuerza con el JSON Schema original, igual que el baseline.
- El schema usado en `response_format` o GCD no se toca.
- El schema que aparece dentro del prompt si se limpia para reducir ruido.
- No se usan ejemplos few-shot en el prompt para evitar coste y posible sobreajuste al dev set.
- El pipeline debe ser zero-shot y agnostico al dominio.

## Nombre sugerido

`simple-clean-schema`

Alternativas:

- `prompted-baseline`
- `cheap-schema-prompt`
- `baseline-plus`

## Diferencia con el baseline

El baseline actual usa:

- System prompt muy corto: `You are a precise data extraction agent.`
- Prompt generado por `Task.get_input_prompt()`: instruction, schema completo y texto.
- `response_format` con `task.target_schema` en modo estricto.

El nuevo pipeline conservaria la parte estructural robusta del baseline, pero cambiaria:

- System prompt mas especifico para GenSIE.
- Prompt de usuario con secciones mas claras.
- Uso separado de la `description` mas externa del schema, especialmente la linea de `Complexity`.
- Version limpia del schema solo para lectura del modelo.
- Reglas explicitas sobre grounding, nulls, enums, listas, formatos y verbatim.

## Observaciones del dataset revisado

Se revisaron ejemplos variados de `data/dev_rev/`: literatura, software, medicamento, contrato, noticias de desastre/judicial/ecologia, astronomia, receta y critica de cine.

Patrones utiles:

- Muchos schemas tienen una `description` externa con descripcion de tarea y `Complexity: Lx (...)`. Esa informacion puede guiar el prompt sin dejarla enterrada dentro del JSON.
- `required` no significa que el valor no pueda ser `null`; la presencia y el tipo real los decide el schema/GCD. En prompt conviene decir que se completen todos los campos del schema y se use `null` cuando el schema lo permita y el texto no aporte evidencia.
- Hay trampas de grounding: fechas exactas, CEO actual, checksums, datos conocidos pero no presentes. El modelo debe ignorar conocimiento externo.
- En campos de enum, el output debe copiar exactamente una de las opciones, con mayusculas y tildes segun aparezcan en el enum.
- En noticias, contratos y software hay campos booleanos inferidos desde evidencia explicita: `has_nda_clause`, `has_liability_limitation`, `is_pediatric`.
- En campos libres como `summary`, `key_verdict`, `pros` y `cons`, conviene sintetizar, pero sin meter hechos externos.
- En listas, el orden no puntua como esencial, pero las listas extra largas penalizan precision. Es preferible extraer items concretos y respaldados.
- En campos numericos, conviene normalizar solo cuando la descripcion lo pide o el tipo lo exige: `50000`, `88.0`, `30420`. Si el campo es string y pide verbatim, conservar la forma textual.
- Hay casos donde la instruction parece mas estrecha que el schema, pero el output esperado completa el schema completo. El prompt debe aclarar que la instruction orienta el objetivo, pero la salida debe llenar todo el schema.
- Algunas anotaciones gold usan inferencia semantica razonable cuando el schema no permite `null` o cuando pide clasificacion: categoria de noticia, tipo de contrato, sentimiento de critica, impacto clinico.

## Limpieza del schema para el prompt

La limpieza se aplica solo al schema serializado dentro del prompt. El schema original permanece intacto para GCD.

Campos a eliminar recursivamente:

- `additionalProperties`
- `title`
- `default`
- `required`

Tratamiento especial:

- Extraer la `description` del objeto raiz antes de limpiar y mostrarla como `Schema task description`.
- Mantener las `description` de propiedades y `$defs`, porque suelen contener instrucciones importantes.
- Mantener `$defs`, `$ref`, `enum`, `type`, `anyOf`, `items`, `properties`, `minimum`, `maximum` y restricciones similares.
- Mantener el orden original de propiedades cuando sea posible.

Razonamiento:

- `additionalProperties: false` y `required` son utiles para validacion, pero aportan poco al razonamiento del modelo y ocupan tokens.
- `title` duplica nombres de campos.
- `default` puede inducir respuestas por defecto, por ejemplo `false`, `null` o listas vacias, aunque el texto contenga evidencia.
- La descripcion externa no debe perderse: suele traer el tipo global de tarea y la complejidad.

## Prompt propuesto

### System

```text
You are a Spanish information extraction engine for GenSIE.
Return only the JSON object required by the provided schema.
Use only evidence from the source text. Do not use outside knowledge.
When a value is absent, return null if the schema allows null; use an empty list for arrays with no supported items.
For enums, output exactly one of the allowed enum strings.
For strings requested as verbatim, preserve the wording from the text as much as possible.
For inferred fields, infer only from explicit textual evidence and schema descriptions.
```

Notas:

- Mantenerlo en ingles puede funcionar bien con modelos instruccionales, pero tambien se puede probar una version espanola. Lo importante es que sea corto y normativo.
- No pedir chain-of-thought. Si se quiere inducir revision interna, usar una frase tipo "Before answering, silently check every field against the text", sin pedir razonamiento visible.

### User

Estructura sugerida:

```text
Task:
Extract the requested structured information from the Spanish source text.
The instruction describes the goal, but the final JSON must cover the full schema.

Instruction:
{task.instruction}

Schema task description:
{root_description_without_complexity_reformatting}

Important extraction rules:
- Ground every non-null value in the text. Do not fill known facts unless the text states them.
- Use null for missing scalar/object values when null is allowed by the schema.
- Use [] for arrays when no supported items are found.
- For enum fields, choose exactly one listed enum value.
- For boolean fields, use true only when there is explicit support; use false when the schema requires a boolean and the evidence is absent or negative.
- For numeric fields, return JSON numbers, not strings. Normalize obvious numbers only when the schema asks for a numeric type.
- For date fields, follow the field description. If it requests a format and the text provides enough information, normalize; otherwise use the verbatim date if allowed by the description.
- Prefer concise, evidence-backed lists. Avoid adding plausible but unstated items.
- Preserve verbatim names, titles, percentages, doses, organizations and quoted labels when the field asks for names or exact values.
- Summaries and verdicts may be concise paraphrases, but must not add external facts.

Readable schema:
{clean_schema_json}

Source text:
{task.input_text}
```

## Manejo de `Complexity`

La linea `Complexity: Lx (...)` aparece en la `description` externa. Propuesta:

- No hacer branching complejo por nivel en la primera implementacion.
- Sacarla a una seccion visible junto a la descripcion.
- Usarla solo para reforzar reglas generales:
  - L2/L4: priorizar extraccion directa y nulls.
  - L5/L8: permitir inferencia semantica respaldada por texto.
  - L9: reforzar "no outside knowledge" y nulls.
  - L10: permitir razonamiento holistico, pero sin inventar ingredientes, tiempos o pasos.

Esto evita crear multiples prompts y mantiene el pipeline simple.

## Implementacion propuesta

### 1. Helper de limpieza de schema

Crear una funcion pura, por ejemplo:

`clean_schema_for_prompt(schema: dict) -> tuple[dict, str | None]`

Responsabilidades:

- Copiar profundamente el schema para no mutar `task.target_schema`.
- Extraer `description` de la raiz.
- Recorrer dicts y listas recursivamente.
- Eliminar las claves de ruido: `additionalProperties`, `title`, `default`, `required`.
- Eliminar `description` solo en la raiz limpia, porque se mostrara fuera del JSON.

No debe resolver `$ref` ni expandir `$defs`: eso aumentaria tokens y podria cambiar la lectura del schema.

### 2. Builder de prompt

Crear un helper independiente:

`build_simple_clean_schema_prompt(task: Task) -> str`

Responsabilidades:

- Llamar al cleaner.
- Serializar el schema limpio con `json.dumps(..., ensure_ascii=False, indent=2)`.
- Construir las secciones `Task`, `Instruction`, `Schema task description`, `Important extraction rules`, `Readable schema`, `Source text`.

Conviene dejarlo testeable sin cliente OpenAI.

### 3. Nuevo agente

Crear una clase similar a `BasicAgent`, por ejemplo:

`SimpleCleanSchemaAgent(GenSIEAgent)`

Responsabilidades:

- Usar el prompt nuevo.
- Usar el system prompt nuevo.
- Mantener `response_format` con `task.target_schema` original.
- Mantener tracing equivalente al baseline.
- Parsear `response.choices[0].message.content` como JSON igual que el baseline.

No debe hacer retry, repair ni segunda llamada.

### 4. Registro del pipeline

En `OfficialParticipant`:

- Registrar `"simple-clean-schema": SimpleCleanSchemaAgent()`.
- Agregar `PipelineInfo` con descripcion corta.

Si el limite de competencia fuera tres pipelines, este ocuparia una plaza junto a `baseline` y una variante mas fuerte.

### 5. Tests recomendados

Sin implementar aun, los tests minimos serian:

- El cleaner no muta el schema original.
- El cleaner elimina claves recursivamente.
- El cleaner conserva `$defs`, `$ref`, `enum`, `anyOf`, `items`, `properties`, `minimum`, `maximum`.
- El prompt contiene instruction, descripcion externa, schema limpio y source text.
- El prompt no contiene `additionalProperties`, `default`, `required` ni `title` dentro del schema limpio.
- El agente manda el schema original en `response_format`.

### 6. Evaluacion local

Comparar contra baseline en:

- `data/starter/`
- `data/dev_rev/`
- Opcionalmente `data/dev/` completo, sabiendo que no todo esta curated igual que `dev_rev`.

Metricas a mirar:

- Micro-F1.
- Validez estructural.
- Tokens de entrada.
- Casos con null hallucination.
- Campos enum rigid exact match.
- Precision en listas.

El exito esperado no es superar pipelines complejos, sino mejorar el baseline manteniendo coste similar.

## Riesgos y mitigaciones

- Riesgo: quitar `required` del prompt hace que el modelo crea que hay campos opcionales.
  Mitigacion: el prompt dice explicitamente que la salida debe cubrir el schema completo, y GCD usa el schema original.

- Riesgo: reglas genericas demasiado largas comen tokens.
  Mitigacion: mantener una lista fija de reglas cortas y medir tokens frente al baseline.

- Riesgo: `default: false` eliminado puede quitar pistas para booleanos.
  Mitigacion: una regla general para booleanos cubre el caso sin inducir defaults ciegos.

- Riesgo: nulls excesivos en campos inferibles.
  Mitigacion: distinguir "missing" de "inferred fields": inferir cuando el schema lo pide y hay evidencia textual.

- Riesgo: normalizacion incorrecta de fechas.
  Mitigacion: regla especifica: seguir la descripcion del campo; si no hay informacion suficiente, usar verbatim si procede o `null`.

## Decision recomendada

Implementar este pipeline como una variante barata y estable del baseline. La mayor ganancia probable viene de tres cambios de bajo riesgo:

1. System prompt orientado a GenSIE y grounding.
2. Schema limpio en el prompt, manteniendo el schema original para GCD.
3. Reglas explicitas sobre nulls, enums, listas, verbatim y normalizacion.

Es una mejora compatible con el espiritu del benchmark: zero-shot, una sola llamada, sin entrenamiento, sin dependencia externa y con coste controlado.
