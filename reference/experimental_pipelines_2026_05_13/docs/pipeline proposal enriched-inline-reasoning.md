# Propuesta de pipeline: enriched-inline-reasoning

## Objetivo

Crear un pipeline nuevo que combine las dos ideas que mejor parecen atacar el problema:

- de `inline-reasoning`: razonamiento estructurado por campo, citas textuales estrictas, `value` final separado, postprocesamiento para devolver solo valores, y ejemplo few-shot;
- de `enriched-schema`: representar el schema como clases tipo Pydantic, porque suele ser mas legible para el SLM que JSON Schema crudo.

La salida generada por el modelo sigue estando instrumentada con wrappers `{reasoning, value}`. Despues de la llamada, el agente reconstruye el output oficial extrayendo solo `value`.

Nombre sugerido:

`enriched-inline-reasoning`

## Hipotesis

`inline-reasoning` obliga al modelo a razonar, pero si el schema del prompt se muestra como JSON wrapper, el SLM puede seguir sin entender bien la semantica de cada campo, especialmente con `$defs`, arrays de objetos, enums y nullables.

`enriched-schema` ayuda a entender estructura y tipos mediante una representacion tipo Pydantic, pero no obliga a justificar respuestas ni a citar evidencia.

El pipeline hibrido busca juntar ambas cosas:

1. Mostrar un schema enriquecido tipo Pydantic que ya incluya los wrappers `reasoning` y `value`.
2. Mantener GCD con schema wrapper real para forzar estructura.
3. Usar FSP con el mismo formato Pydantic enriquecido para ensenar reasonings buenos, completos y con citas.

## Restricciones

- Una sola llamada al SLM por tarea.
- Sin repair, retry semantico ni segunda consulta.
- El schema de generacion se modifica como en `inline-reasoning`: cada campo top-level se envuelve con `{reasoning, value}`.
- El output final se reconstruye como JSON oficial usando solo `value`.
- El schema mostrado en prompt no debe ser JSON Schema crudo, sino una vista tipo Pydantic ajustada al wrapper.
- El FSP debe usar tambien la vista Pydantic ajustada, no el JSON Schema modificado.
- El pipeline debe poder activar/desactivar el FSP mediante constante.

## Diferencias con pipelines existentes

### Frente a `enriched-schema`

- `enriched-schema` devuelve directamente el JSON final.
- Este pipeline genera primero un JSON instrumentado `{reasoning, value}` y luego lo desenvuelve.
- `enriched-schema` muestra Pydantic del schema original.
- Este pipeline muestra Pydantic del schema wrapper.
- `enriched-schema` no tiene FSP ni razonamiento por campo.
- Este pipeline si lo tiene.

### Frente a `inline-reasoning`

- `inline-reasoning` muestra un JSON Schema modificado o el schema final limpio.
- Este pipeline muestra clases tipo Pydantic con el wrapper incluido.
- `inline-reasoning` ya tiene FSP, pero el schema del ejemplo es JSON modificado.
- Este pipeline debe mostrar el FSP con schema Pydantic enriquecido.

## Schema de generacion

El schema de generacion/GCD puede reutilizar la logica de `inline-reasoning`:

```json
{
  "type": "object",
  "properties": {
    "field": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "reasoning": {
          "type": "string",
          "description": "..."
        },
        "value": ORIGINAL_FIELD_SCHEMA
      },
      "required": ["reasoning", "value"]
    }
  },
  "required": ["field"],
  "additionalProperties": false
}
```

Reglas:

- Solo envolver campos de primer nivel.
- No envolver recursivamente objetos ni items de arrays de objetos.
- Conservar `$defs` para que `$ref` dentro de `value` sigan resolviendo.
- El schema original del campo queda dentro de `value`.

## Schema Pydantic mostrado en prompt

El prompt debe mostrar una representacion tipo Pydantic del schema ya instrumentado, pero sin imports ni ruido.

### Problema actual en `enriched-schema`

`render_pydantic_code` mete siempre:

```python
from __future__ import annotations

from typing import Any, List, Optional, Literal
from pydantic import BaseModel, Field
```

Para prompting esto es ruido. El modelo no necesita imports, y esas lineas no aportan semantica de extraccion. La nueva vista debe omitir imports y empezar directamente por alias/enums/clases.

### Formato deseado

La primera idea era crear una clase wrapper por campo (`ReasonedTitle`, `ReasonedAuthor`, etc.). Eso funciona, pero infla mucho el prompt y pierde una de las fortalezas de `enriched-schema`: ser compacto y escaneable.

La forma preferida es usar dos pseudo-tipos definidos una sola vez en el prompt:

- `Reasoned[T]`: significa un objeto con exactamente `reasoning: str` y `value: T`.
- `Nullable[T]`: significa que `value` puede ser `null`, pero el campo `Reasoned[...]` no se puede omitir.

Ejemplo aproximado:

```python
SoftwareType = Literal["ARCHIVER", "WEB_BROWSER", "OFFICE_SUITE", "IDE_EDITOR", "GRAPHICS_EDITOR", "MEDIA_PLAYER", "SYSTEM_TOOL", "OTHER"]

class Reasoned[T](BaseModel):
    reasoning: str
    value: T

Nullable[T] = T | null

class Extraction(BaseModel):
    official_name: Reasoned[str] = Field(description="The full official name of the software")
    exact_release_date: Reasoned[Nullable[str]] = Field(description="The EXACT date (DD/MM/YYYY) of the first release. RETURN NULL IF ONLY THE YEAR IS MENTIONED.")
```

No hace falta que sea Python ejecutable perfecto. Es una representacion para el modelo. Debe ser compacta, legible y consistente.

Regla semantica importante:

```text
En un campo Reasoned[T], la description del Field describe el value, no el reasoning.
Cada campo Reasoned[T] debe generarse como {"reasoning": "...", "value": ...}.
```

## Nullables: reemplazar `Optional`

`Optional[T]` puede sugerir que el campo es opcional, cuando en este pipeline queremos exactamente lo contrario:

- todos los campos top-level deben existir;
- todos deben tener `reasoning`;
- todos deben tener `value`;
- si la informacion no esta en el texto y el schema permite null, entonces `value` debe ser `null`;
- el reasoning debe explicar explicitamente por que corresponde `null`.

Por eso conviene no renderizar `Optional[T]`.

Opciones mejores:

### Opcion recomendada: `Nullable[T]`

Usar una pseudo-notacion:

```python
value: Nullable[str]
```

Y explicar en el prompt:

```text
Nullable[T] significa que value puede ser null, pero el campo no se puede omitir. Si usas null, reasoning debe justificar que no hay evidencia suficiente en el texto.
```

Ventaja:

- Evita la ambiguedad de `Optional`.
- Refuerza que el campo existe siempre.
- Es compacto.

### Alternativa: `str | null`

```python
value: str | null
```

Es claro, pero menos estilo Pydantic/Python y puede mezclarse peor con `List[...]` o `Literal[...]`.

### Alternativa: comentario inline

```python
value: str  # nullable: use null if unsupported by text
```

Mas verboso y menos estructural.

Decision recomendada: usar `Nullable[T]` y definirlo en texto, sin importarlo.

## Wrappers Pydantic

Cada campo top-level debe renderizarse como `Reasoned[T]`, no como una clase wrapper nueva por campo.

```python
class Reasoned[T](BaseModel):
    reasoning: str
    value: T
```

La `description` original del campo debe ir en el `Field(description=...)` del campo top-level:

```python
class LiteraryWork(BaseModel):
    title: Reasoned[str] = Field(description="The official title of the literary work")
    publication_year: Reasoned[Nullable[int]] = Field(description="The year the work was first published")
```

Aunque la description este en el campo `Reasoned[...]`, el prompt debe explicar que esa description describe el `value`. Esto evita repetir `Field(description=...)` dentro de cada wrapper y mantiene el schema compacto.

`reasoning` no necesita `Field(description=...)` en la vista Pydantic: el prompt global ya explica que debe contener citas, analisis y justificacion. Repetirlo por campo seria ruido.

Para arrays de objetos y objetos:

```python
class SideEffect(BaseModel):
    reaction: str = Field(description="Name of the adverse effect in Spanish")
    system_organ_class: Nullable[str] = Field(description="Affected body system")
    probability: FrequencyLevel = Field(description="Frequency based on text")
    impact: ImpactLevel = Field(description="Inferred clinical severity")

class DrugDescription(BaseModel):
    side_effects: Reasoned[List[SideEffect]] = Field(description="Structured list of all adverse reactions found")
```

No envolver internamente `SideEffect.reaction`, `SideEffect.impact`, etc. El reasoning es global para todo el campo top-level.

Este formato preserva las dos fortalezas buscadas:

- compacto como `enriched-schema`, porque el modelo raiz sigue siendo una lista clara de campos;
- explicito como `inline-reasoning`, porque `Reasoned[T]` marca estructuralmente que cada campo requiere `reasoning` y `value`.

## Prompt propuesto

El prompt debe cambiar de orden. En `inline-reasoning` actualmente puede empezar directamente con el FSP. Eso es mala ergonomia para el modelo: ve un ejemplo antes de saber claramente su rol y la tarea general.

Orden recomendado:

```text
TAREA:
Eres un extractor de informacion estructurada. Debes usar solo evidencia del TEXTO FUENTE.
La salida debe seguir el schema de generacion: cada campo de primer nivel contiene reasoning y value.

FORMATO DE RAZONAMIENTO:
- Completa todos los campos del schema.
- En cada campo, escribe primero reasoning y despues value.
- reasoning debe citar texto exacto del TEXTO FUENTE cuando exista evidencia.
- Si no hay evidencia suficiente y value permite null, usa null y explica por que.
- value contiene solo la respuesta final, sin explicaciones.
- Reasoned[T] significa que el campo se genera como {"reasoning": str, "value": T}.
- La description de un campo Reasoned[T] describe su value.
- Nullable[T] significa que value puede ser null, pero el campo no se puede omitir.
- En objetos, arrays de objetos y arrays de simples, haz un unico reasoning para todo el campo y luego rellena value completo.

EJEMPLO FEW-SHOT:
...
FIN DEL EJEMPLO FEW-SHOT.

INSTRUCCION:
{task.instruction}
{schema_description}

SCHEMA PYDANTIC:
{reasoned_pydantic_schema}

TEXTO FUENTE:
{task.input_text}
```

Puntos importantes:

- El rol/proposito y las reglas van antes del ejemplo.
- El ejemplo demuestra el comportamiento, no introduce la tarea real.
- La tarea real queda despues del FSP, cerca del schema y del texto real.

## Few-shot prompting

El FSP debe seguir usando `data/dev_rev/cultural_literature_001.json`, pero con schema Pydantic enriquecido.

Bloque del ejemplo:

```text
EJEMPLO FEW-SHOT:

INSTRUCCION DEL EJEMPLO:
Extrae los metadatos bibliograficos y temas principales de la obra literaria descrita.
Extracts basic bibliographic metadata and key themes from a book description or encyclopedia entry.
Complexity: L2 (Explicit Information Retrieval).

SCHEMA PYDANTIC DEL EJEMPLO:
class Reasoned[T](BaseModel):
    reasoning: str
    value: T

Nullable[T] = T | null

class LiteraryWork(BaseModel):
    title: Reasoned[str] = Field(description="The official title of the literary work")
    author: Reasoned[str] = Field(description="The primary author or creator of the work")
    publication_year: Reasoned[Nullable[int]] = Field(description="The year the work was first published")

...

INPUT TEXT DEL EJEMPLO:
...

OUTPUT DEL EJEMPLO:
{
  "title": {
    "reasoning": "... cita ... justificacion ...",
    "value": "Don Quijote de la Mancha"
  },
  ...
}

FIN DEL EJEMPLO FEW-SHOT.
```

El output del ejemplo debe mantenerse completo, con reasonings que:

- expliquen que pide el campo;
- citen texto literal;
- justifiquen la respuesta final;
- expliquen nulls;
- no metan explicaciones dentro de `value`.

## Implementacion propuesta

### 1. Reutilizar schema wrapper de inline

Reusar:

- `build_inline_reasoning_schema`
- `unwrap_inline_reasoning_output`

Esto evita duplicar la parte delicada del GCD y el postproceso.

### 2. Crear renderer Pydantic para schema reasoned

Helper sugerido:

`render_reasoned_pydantic_schema(schema: dict) -> str`

Responsabilidades:

- Renderizar `$defs` como aliases `Literal[...]` o clases.
- Renderizar el modelo raiz con campos reasoned.
- Definir una sola vez el pseudo-wrapper generico:
  - `class Reasoned[T](BaseModel):`
  - `reasoning: str`
  - `value: T`
- Renderizar cada campo top-level como `field_name: Reasoned[T]`.
- Usar `Nullable[T]` para nullables, no `Optional[T]`.
- No incluir imports.
- No incluir `from __future__`.
- Mantener descriptions en `Field(description=...)` del campo `Reasoned[T]`, aclarando en el prompt que describen el `value`.
- No envolver recursivamente campos internos.

Podria apoyarse en partes de `schema_enrichment.py`, pero probablemente conviene crear funciones nuevas o parametrizar el renderer actual para no romper `enriched-schema`.

### 3. Crear builder de FSP enriquecido

Helper sugerido:

`build_enriched_inline_few_shot_example() -> str`

Responsabilidades:

- Usar el input de `cultural_literature_001`.
- Usar instruction + schema description.
- Usar `render_reasoned_pydantic_schema` para el schema del ejemplo.
- Usar el output razonado existente de inline-reasoning.

### 4. Crear builder de prompt

Helper sugerido:

`build_enriched_inline_reasoning_prompt(task: Task) -> str`

Responsabilidades:

- Poner primero tarea/reglas.
- Insertar FSP si `INCLUDE_ENRICHED_INLINE_FEW_SHOT` es `True`.
- Incluir instruction real y schema description.
- Incluir schema Pydantic reasoned real.
- Incluir texto fuente real.

### 5. Crear agente

Clase sugerida:

`EnrichedInlineReasoningAgent(GenSIEAgent)`

Responsabilidades:

- Construir `reasoning_schema = build_inline_reasoning_schema(task.target_schema)`.
- Construir prompt enriquecido.
- Enviar `response_format` con `reasoning_schema`.
- Parsear output instrumentado.
- Devolver `unwrap_inline_reasoning_output(...)`.
- Guardar en tracing:
  - prompt;
  - schema wrapper enviado;
  - output crudo con reasoning;
  - output final desenvuelto.

### 6. Registro

Registrar como:

`"enriched-inline-reasoning"`

Puede convivir con `inline-reasoning` para comparar JSON-schema prompt vs Pydantic-schema prompt.

## Tests recomendados

- El renderer Pydantic no incluye imports.
- El renderer usa `Nullable[T]`, no `Optional[T]`.
- El renderer define `Reasoned[T]` una sola vez.
- El renderer no genera una clase por cada campo top-level.
- Cada campo top-level se renderiza como `Reasoned[T]`.
- `reasoning` aparece como `str` dentro de la definicion generica, sin `Field(description=...)`.
- La `description` original queda en `Field(description=...)` del campo `Reasoned[T]`.
- Arrays de objetos no se envuelven internamente.
- `$defs` con enums se renderizan como `Literal[...]`.
- El FSP incluye instruction, schema description, schema Pydantic, input text y output.
- El prompt pone reglas antes del FSP.
- El agente envia schema wrapper por `response_format`.
- El agente devuelve solo `value`.

## Evaluacion

Comparar contra:

- `baseline`
- `enriched-schema`
- `simple-clean-schema`
- `inline-reasoning`

Ablations:

- FSP on/off.
- Pydantic reasoned vs JSON wrapper visible.
- `Nullable[T]` vs `Optional[T]` si se quiere confirmar la intuicion.

Metricas:

- Micro-F1.
- Tokens de entrada y salida.
- Tasa de errores de parseo/postproceso.
- Null traps.
- Enums exactos.
- Listas largas (`medical_drug` especialmente).

## Riesgos

- El Pydantic reasoned puede ser mas largo que JSON Schema limpio, aunque `Reasoned[T]` generico reduce mucho el crecimiento.
- El FSP suma tokens y puede sesgar estilo.
- `Nullable[T]` es una pseudo-notacion; hay que explicarla claramente.
- `Reasoned[T]` tambien es una pseudo-notacion; hay que explicarla antes del schema y mantenerla consistente en FSP y tarea real.
- Si el renderer simplifica demasiado, puede ocultar restricciones del JSON Schema.
- Si el modelo copia el ejemplo demasiado literalmente, puede contaminar dominios no literarios.

## Decision recomendada

Implementar este pipeline como una variante nueva, no como reemplazo inmediato de `inline-reasoning`.

La version inicial deberia:

1. Reutilizar GCD y unwrap de `inline-reasoning`.
2. Crear un renderer Pydantic reasoned sin imports y con `Reasoned[T]` genérico.
3. Usar `Nullable[T]`.
4. Poner reglas antes del FSP.
5. Usar el FSP de Don Quijote con schema Pydantic reasoned.

Si funciona, probablemente sea la variante mas fuerte de las baratas de una llamada: conserva estructura estricta, fuerza grounding por campo y le da al modelo una vista del schema mas cercana a codigo legible.
