# Propuesta: ejemplos FSP para RAG

## Objetivo

Construir una colección de ejemplos FSP reutilizables por RAG para varios tipos
de prompt:

- extracción sin reasoning;
- extracción con inline reasoning top-level;
- juez de agregación con salida `{reasoning, value}`;
- juez de agregación con veredictos por candidato.

La idea central es que cada ejemplo FSP tenga una base común, con la misma forma
que una instancia de GenSIE:

- texto fuente;
- instrucción;
- schema original de extracción.

Lo único que cambia entre extracción y agregación es la vista de salida que se
renderiza para ese mismo caso. Esto evita duplicar ejemplos casi iguales y
permite que un mismo ejemplo recuperado por RAG enseñe distintos contratos de
prompt según el pipeline activo.

La decisión principal es no guardar los ejemplos como strings de prompt ya
cerrados. El prompt debe ser una vista renderizada de datos estructurados:
texto fuente, instrucción, schema, campos, valores, candidatos, evidencias y
razonamientos.

## Contexto actual

GenSIE es una tarea zero-shot de extracción estructurada grounded: cada salida
debe obedecer el schema, usar solo el texto fuente y devolver `null` o `[]`
cuando el schema y la evidencia lo pidan.

La modularización actual ya separa varias piezas útiles para esta propuesta:

- `ExtractionSpec` contiene `reasoning`, `schema_prompt`, `few_shot`, fases y
  opciones.
- `FewShotMode` ya declara `RAG`, aunque no hay provider RAG implementado.
- `src/gensie/fsp/*` contiene providers FSP fijos y un contrato base.
- `src/gensie/prompts/reference.py` conserva los prompts de referencia y hoy
  inyecta FSP fijos pre-renderizados.
- `src/gensie/aggregation/judge_prompt.py` implementa el juez
  `reasoned_output`.
- `src/gensie/aggregation/verdict_prompt.py` implementa el juez
  `candidate_verdicts`.
- `src/gensie/aggregation/judge_scope.py` ya calcula campos estables,
  disputados y schema reducido. La lógica de recortar schemas por campos
  podría moverse luego a un helper común para que FSP no dependa de
  `aggregation`.

El RAG de ejemplos debe entrar como provider, no como lógica dentro del prompt
principal.

## Base Común

No conviene modelar los ejemplos como dos recursos independientes
`extraction`/`judge` con texto y schema repetidos. Conviene modelarlos como
casos FSP de base común:

```json
{
  "id": "cultural_literature_quijote",
  "domain": "cultural_literature",
  "language": "es",
  "tags": [
    "direct_string",
    "numeric_normalization",
    "simple_array",
    "grounded_null",
    "long_verbatim_evidence"
  ],
  "source_text": "# Don Quijote de la Mancha\n\n...",
  "instruction": "Extrae los metadatos bibliográficos y temas principales de la obra literaria descrita.",
  "schema": {},
  "field_examples": {},
  "outputs": {
    "extraction": {},
    "judge": {}
  }
}
```

Reglas:

- `source_text`, `instruction` y `schema` son únicos para el ejemplo.
- `schema` siempre es el schema original de extracción, sin wrappers de
  reasoning ni wrappers del juez.
- `field_examples` contiene información reusable por campo: valor final,
  etiquetas de subtarea y razonamiento/evidencia editable.
- `outputs.extraction` contiene las vistas de salida para pipelines de
  extracción.
- `outputs.judge` contiene candidatos y salidas esperadas para variantes del
  juez.

Esta estructura permite que el mismo caso se renderice como FSP de extracción o
como FSP de agregación sin desincronizar texto, instrucción ni schema.

## Extracción: Alcance Inicial

Para extracción propongo soportar desde el inicio:

- `ReasoningMode.NONE`;
- `ReasoningMode.TOP_LEVEL`.

`ReasoningMode.NONE` no debe quedar fuera, porque hay pipelines sin reasoning
que a veces son útiles y pueden beneficiarse de FSPs dedicados. En ese modo, el
ejemplo enseña directamente el JSON final sin `{reasoning, value}`.

`ReasoningMode.TOP_LEVEL` usa los mismos valores finales, pero renderiza cada
campo de primer nivel como `Reasoned[T]`.

Queda fuera inicialmente:

- `ReasoningMode.DEEP`, porque los resultados no han sido buenos y el formato
  de ejemplo requiere razonamientos recursivos.

Las variantes que afectan el render de un ejemplo de extracción son:

- `reasoning=none`: la salida del ejemplo es el JSON final directo.
- `reasoning=top_level`: la salida del ejemplo usa `{reasoning, value}` en cada
  campo de primer nivel.
- `schema_prompt=json_schema` o `clean_json_schema`: el ejemplo puede mostrar
  schema JSON.
- `schema_prompt=pydantic`: el ejemplo puede mostrar schema Pydantic plano.
- `schema_prompt=inline_reasoning_wrapper`: el ejemplo debe mostrar schema JSON
  con wrappers `{reasoning, value}`.
- `schema_prompt=reasoned_pydantic`: el ejemplo debe mostrar schema Pydantic
  con `Reasoned[T]`.
- `few_shot=rag`: activa el provider RAG.

No hay variables de entorno actuales que cambien el FSP de extracción. Las
variables relevantes al multi-trial o budget no deberían modificar cómo se
renderiza un ejemplo.

## Razonamiento de Extracción

La estructura usada en el ejemplo fijo del Quijote debe conservarse. En vez de
guardar un string libre sin estructura, cada campo puede tener partes editables:

```json
{
  "field": "publication_year",
  "tags": ["date_normalization", "numeric_normalization"],
  "value": 1605,
  "reasoning": {
    "field_asks": "el año de la primera publicación de la obra (null si no hay suficiente evidencia en el texto)",
    "relevant_fragments": "\"Publicada su primera parte [...] a comienzos de 1605\" y \"En 1615 apareció su continuación\"",
    "final_value": "es el año de publicación de la primera parte: 1605."
  }
}
```

`relevant_fragments` no debería ser un array de strings. Es más flexible como
string editable, porque a veces la evidencia necesita:

- una cita compuesta;
- explicación de ausencia de evidencia;
- contraste entre dos fragmentos;
- una frase completa ya redactada;
- elipsis internas como `[...]`;
- texto que no se comporta bien como lista de fragmentos independientes.

El renderer convierte esas partes al formato configurado:

```text
EL CAMPO PIDE: el año de la primera publicación de la obra (null si no hay suficiente evidencia en el texto).
FRAGMENTOS RELEVANTES: "Publicada su primera parte [...] a comienzos de 1605" y "En 1615 apareció su continuación".
VALOR FINAL: es el año de publicación de la primera parte: 1605.
```

Los títulos de sección no deben quedar hardcodeados en muchos lugares. Deben
vivir en una configuración de renderer, no en variables de entorno:

```python
@dataclass(frozen=True)
class ReasoningSectionLabels:
    field_asks: str = "EL CAMPO PIDE"
    relevant_fragments: str = "FRAGMENTOS RELEVANTES"
    final_value: str = "VALOR FINAL"
```

Así, si luego queremos cambiar `FRAGMENTOS RELEVANTES` por otro rótulo, se
cambia una sola configuración del renderer.

Cuando se migren los ejemplos fijos actuales del Quijote, el contenido textual
debe quedar exactamente igual al actual. Si se descompone un reasoning existente
en `field_asks`, `relevant_fragments` y `final_value`, el renderer debe
reconstruir el mismo texto. Si eso no se puede garantizar para un campo, se debe
guardar también un `reasoning_text` exacto y usarlo como fuente de verdad hasta
que la migración pueda hacerse sin cambios de contenido.

## Formato Común de Ejemplo

La fuente de verdad debería ser un recurso estructurado, no un string Python con
todo el prompt. Para evitar dependencias nuevas, JSON es suficiente. Si se
vuelve incómodo para textos largos, se puede cambiar a TOML usando `tomllib`,
pero empezaría con JSON por simplicidad y compatibilidad.

Formato recomendado:

```json
{
  "id": "cultural_literature_quijote",
  "domain": "cultural_literature",
  "language": "es",
  "tags": [
    "direct_string",
    "numeric_normalization",
    "simple_array",
    "grounded_null",
    "long_verbatim_evidence"
  ],
  "source_text": "# Don Quijote de la Mancha\n\nDon Quijote de la Mancha es una novela escrita por el español Miguel de Cervantes Saavedra...",
  "instruction": "Extrae los metadatos bibliográficos y temas principales de la obra literaria descrita.",
  "schema": {},
  "field_examples": {
    "title": {
      "value": "Don Quijote de la Mancha",
      "tags": ["direct_string"],
      "reasoning": {
        "field_asks": "el título oficial de la obra literaria",
        "relevant_fragments": "el texto abre con \"# Don Quijote de la Mancha\" y luego repite \"Don Quijote de la Mancha es una novela\"",
        "final_value": "el título principal usado para la obra completa es Don Quijote de la Mancha."
      }
    }
  },
  "outputs": {
    "extraction": {
      "none": {
        "title": "Don Quijote de la Mancha"
      },
      "top_level": {
        "title": {
          "reasoning": "EL CAMPO PIDE: ...\nFRAGMENTOS RELEVANTES: ...\nVALOR FINAL: ...",
          "value": "Don Quijote de la Mancha"
        }
      }
    },
    "judge": {
      "total_trials": 4,
      "stable_fields": {
        "author": "Miguel de Cervantes Saavedra"
      },
      "fields": {}
    }
  }
}
```

Reglas:

- `field_examples` se indexa por campo de primer nivel.
- cada campo tiene `value`, `tags` y, si aplica, `reasoning`.
- `outputs.extraction.none` puede generarse desde `field_examples[*].value`.
- `outputs.extraction.top_level` puede generarse desde `field_examples` y el
  renderer de reasoning.
- `outputs.judge` contiene `total_trials`, campos estables y candidatos
  hipotéticos para ese mismo schema.
- si el ejemplo se proyecta a un subconjunto de campos, se recortan
  `schema.properties`, `schema.required`, `field_examples` y las salidas
  renderizadas.

## Render de Extracción

El renderer de extracción debe producir un bloque equivalente al FSP actual,
pero con salida dependiente del modo:

```text
EJEMPLO:
...

INSTRUCCIÓN DEL EJEMPLO:
...

SCHEMA DEL EJEMPLO:
...

TEXTO FUENTE DEL EJEMPLO:
...

SALIDA DEL EJEMPLO:
...

FIN DEL EJEMPLO.
```

Para `ReasoningMode.NONE`, `SALIDA DEL EJEMPLO` es directa:

```json
{
  "title": "Don Quijote de la Mancha",
  "publication_year": 1605
}
```

Para `ReasoningMode.TOP_LEVEL`, el mismo ejemplo se renderiza como:

```json
{
  "title": {
    "reasoning": "EL CAMPO PIDE: ...\nFRAGMENTOS RELEVANTES: ...\nVALOR FINAL: ...",
    "value": "Don Quijote de la Mancha"
  },
  "publication_year": {
    "reasoning": "EL CAMPO PIDE: ...\nFRAGMENTOS RELEVANTES: ...\nVALOR FINAL: ...",
    "value": 1605
  }
}
```

No se debería escribir ese JSON a mano salvo cuando sea necesario para preservar
exactamente un FSP fijo ya validado. En la migración del Quijote, la prioridad
es equivalencia textual exacta.

## Tipos de Tarea para Retrieval

La recuperación de ejemplos debería usar etiquetas por forma de razonamiento,
no solo por dominio. La referencia experimental del super-FSP ya tenía una
taxonomía útil:

- `verbatim_answer`
- `direct_string`
- `summary_string`
- `long_verbatim_evidence`
- `enum_classification`
- `date_normalization`
- `numeric_normalization`
- `boolean_inference`
- `nullable_boolean`
- `grounded_null`
- `simple_array`
- `empty_array`
- `entity_array`
- `complex_object_array`
- `nested_numeric_object_array`
- `enum_array`
- `bounded_score`
- `sentinel_pattern`

El selector RAG puede construir la query del task real inspeccionando el schema:
tipos, `enum`, `anyOf` nullable, arrays, objetos, nombres de campo,
descriptions, patrones y min/max. La recuperación ideal mezcla:

- ejemplos con tags similares;
- ejemplos del mismo dominio si existen;
- ejemplos con schema igual o muy parecido;
- ejemplos que cubran los campos más riesgosos: nullable traps, enums,
  verbatim largo, arrays de objetos y fechas exactas.

## Juez: Variantes Soportadas

El RAG del juez debe ser variante-específico, pero debe partir del mismo caso
FSP base usado por extracción.

### Variante `reasoned_output`

Esta es la ruta de `JudgeAggregator` y `judge_prompt.py`.

El juez recibe campos disputados y devuelve un objeto con los campos reducidos,
cada uno como:

```json
{
  "reasoning": "compara candidatos, soporte y evidencia textual",
  "value": "valor final"
}
```

El FSP debe enseñar:

- candidatos por campo;
- soportes opcionales;
- campos estables opcionales;
- razonamiento comparativo;
- salida etiquetada como `SALIDA`;
- solo campos disputados en el schema de salida.

### Variante `candidate_verdicts`

Esta es la ruta de `VerdictJudgeAggregator`, `verdict_prompt.py` y
`verdict_schema.py`.

El juez no devuelve directamente el valor final de arrays. Devuelve veredictos
por candidato:

```python
class SingleVerdict[T](BaseModel):
    field: str
    candidates: list[SingleCandidate[T]]
    value: T

class ArrayVerdict[T](BaseModel):
    field: str
    candidates: list[ArrayCandidate[T]]
```

El FSP debe enseñar:

- `field` como explicación de lo que pide el campo, no como decisión;
- `candidate_value` copiado literalmente;
- `evidence` como micro-veredicto grounded de cada candidato;
- `include` solo en arrays;
- `value` solo en campos simples;
- reconstrucción posterior fuera del modelo.

Por tanto, el caso FSP base puede ser único, pero `outputs.judge` debe poder
renderizarse con `variant="reasoned_output"` o `variant="candidate_verdicts"`.

## Variables que Afectan al FSP del Juez

Estas variables deben ser parte explícita del render del ejemplo:

- `GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS`
  - `0` por defecto: no se muestran campos estables.
  - `1`: se muestra `CAMPOS YA CONSENSUADOS` y se agrega la instrucción de no
    devolverlos.

- `GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS`
  - `1` por defecto: se muestra `Trials válidos: N` y soportes como `2/3`.
  - `0`: se ocultan conteos y prefijos de soporte.

`GENSIE_SC_JUDGE_INCLUDE_SCALAR_REASONINGS` y
`GENSIE_SC_JUDGE_INCLUDE_ARRAY_REASONINGS` sí afectan al prompt real del juez,
porque hacen que el resumen de votos incluya razonamientos de los trials. Para
que un FSP RAG los enseñe bien habría que guardar razonamientos de trials en el
ejemplo y renderizarlos de forma condicional.

Sin embargo, no parece prometedor incluir esos razonamientos inicialmente. Por
eso quedan fuera del alcance de la primera versión del FSP RAG del juez. La
primera versión debe asumir que esos knobs están desactivados o, si están
activados en una corrida real, dejar que el resumen de votos real los incluya
sin intentar que el FSP recuperado modele también esa sección.

Otros knobs existen, pero no cambian el contenido del ejemplo:

- `GENSIE_SC_JUDGE_TEMPERATURE`, `GENSIE_SC_JUDGE_TOP_P`,
  `GENSIE_SC_JUDGE_MAX_TOKENS` y `GENSIE_SC_JUDGE_TOP_K` afectan generación.
- `GENSIE_SC_VERDICT_JUDGE_ENFORCE_VALIDATION` y
  `GENSIE_SC_VERDICT_JUDGE_REPORT_VALIDATION` afectan reconstrucción/validación
  de `candidate_verdicts`.

## Estructura Común del Juez

Un ejemplo de juez debe guardar candidatos por campo, no un prompt cerrado.
`total_trials` debe ser global para el ejemplo, no repetirse dentro de cada
candidato.

```json
{
  "outputs": {
    "judge": {
      "total_trials": 4,
      "stable_fields": {
        "author": "Miguel de Cervantes Saavedra"
      },
      "fields": {
        "title": {
          "kind": "single",
          "tags": ["direct_string"],
          "candidates": [
            {
              "value": "Don Quijote de la Mancha",
              "support": 3,
              "evidence": "El encabezado y la oración principal presentan este literal como título de la obra completa, por lo que debe ser el valor final."
            },
            {
              "value": "El ingenioso hidalgo don Quijote de la Mancha",
              "support": 1,
              "evidence": "Aparece como título de la primera parte publicada en 1605, no como título general de la obra completa, por lo que no debe elegirse."
            }
          ],
          "value": "Don Quijote de la Mancha",
          "reasoned_output": {
            "reasoning": "El candidato con mayor soporte también coincide con el encabezado y la oración principal. El segundo candidato corresponde solo a una parte de la obra. Por tanto el valor final es Don Quijote de la Mancha.",
            "value": "Don Quijote de la Mancha"
          }
        }
      }
    }
  }
}
```

No hace falta un campo `verdict` con valores como `aceptar` o `rechazar`.
La decisión vive en `evidence`: un string que mezcla evidencia explícita,
ausencia de evidencia cuando aplique y la conclusión sobre si ese candidato
debe ser el valor final, o uno de los valores si el campo es un array.

Para `candidate_verdicts`, el mismo campo puede renderizarse como:

```json
{
  "title": {
    "field": "El campo pide el título principal de la obra literaria descrita.",
    "candidates": [
      {
        "candidate_value": "Don Quijote de la Mancha",
        "evidence": "Fragmentos: \"# Don Quijote de la Mancha\" y \"Don Quijote de la Mancha es una novela\". El literal identifica la obra completa y debe ser el valor final."
      },
      {
        "candidate_value": "El ingenioso hidalgo don Quijote de la Mancha",
        "evidence": "Fragmento: \"Publicada su primera parte [...] con el título de El ingenioso hidalgo don Quijote de la Mancha\". El literal corresponde a la primera parte, no al título general."
      }
    ],
    "value": "Don Quijote de la Mancha"
  }
}
```

Para arrays, cada candidato tiene `include` al renderizar
`candidate_verdicts`, pero el recurso base puede guardar esa decisión como
`include: true | false` dentro del candidato:

```json
{
  "value": "novela moderna",
  "support": 3,
  "include": true,
  "evidence": "El texto dice \"Representa la primera novela moderna\", así que este candidato está explícitamente respaldado y debe incluirse."
}
```

Además, los campos top-level de tipo array deben guardar cuántos trials dieron
lista vacía. Ese dato no debe modelarse como un candidato más, porque `[]` no es
un item del array; es una observación sobre el campo completo.

Ejemplo:

```json
{
  "kind": "array",
  "empty_trial_count": 2,
  "candidates": [
    {
      "value": "novela",
      "support": 3,
      "include": true,
      "evidence": "El texto dice \"Don Quijote de la Mancha es una novela\", así que este item debe incluirse."
    }
  ]
}
```

Cuando `GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS=1`, el renderer debe poder
mostrar esa señal junto a los elementos candidatos:

```text
CAMPO `genres` (lista)
Elementos candidatos:
- 3/4: "novela"
- Lista vacía en 2/4 trials.
```

Cuando `GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS=0`, se puede ocultar el conteo:

```text
CAMPO `genres` (lista)
Elementos candidatos:
- "novela"
- Lista vacía.
```

Si más adelante queremos modelar también `null` o valores no-lista inválidos en
campos array, pueden añadirse como metadatos hermanos, por ejemplo
`null_trial_count` e `invalid_value_count`, siguiendo la forma que ya usa el
resumen actual del juez.

## Orden de Candidatos

El orden en que aparecen los candidatos en el prompt debe ser configurable.
No conviene fijarlo dentro del modelo de datos.

Configuración propuesta:

```python
class CandidateOrder(StrEnum):
    RESOURCE = "resource"
    SUPPORT_DESC = "support_desc"
    SUPPORT_ASC = "support_asc"
    FIRST_SEEN = "first_seen"
    CANONICAL_JSON = "canonical_json"
```

Default recomendado:

- para ejemplos fijos migrados: `RESOURCE`, para preservar exactamente el orden
  textual actual;
- para candidatos construidos desde trials reales: `SUPPORT_DESC`, con empate
  por primer trial observado y luego JSON canónico, que coincide con la lógica
  actual de summaries.

Esta configuración debe vivir en el renderer o en opciones del provider, no
como transformación manual dentro de cada ejemplo.

## Proyección a Campos Disputados

La parte más importante para RAG del juez es que un ejemplo recuperado pueda
proyectarse a un subconjunto de campos de primer nivel.

Caso esperado:

1. El task real genera varios trials.
2. `JudgeScope` calcula `disputed_fields`.
3. El provider RAG recupera un caso FSP base.
4. Si el ejemplo tiene el mismo schema o uno compatible, el renderer incluye
   solo los campos de `disputed_fields`.
5. Los campos estables solo aparecen si
   `GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS=1`.

La proyección debe aplicar la misma idea al schema, al prompt y a la salida:

- `schema.properties`: solo campos disputados.
- `schema.required`: intersección con campos disputados.
- `field_examples`: solo campos disputados disponibles en el ejemplo.
- `outputs.judge.fields`: solo campos disputados disponibles en el ejemplo.
- `stable_fields`: solo si el knob está activo.
- `VALORES CANDIDATOS POR CAMPO`: solo campos disputados.
- `SALIDA`: solo campos disputados.

Si el ejemplo no tiene todos los campos disputados del task real, hay dos
opciones razonables:

- incluir solo los campos que cubre, si aún enseña un tipo de razonamiento útil;
- descartarlo si se pidió modo `same_schema_only`.

Para la primera versión recomiendo:

- si `schema_fingerprint` coincide, proyectar exactamente a
  `disputed_fields`;
- si no coincide, seleccionar campos del ejemplo por tags y límite de tokens,
  pero nunca fingir que sus nombres corresponden al schema real.

## Fingerprints y Compatibilidad de Schema

Para detectar "mismo schema" no hace falta depender del `title`. Conviene crear
dos fingerprints:

- `schema_fingerprint`: JSON canónico del schema limpio, incluyendo
  propiedades, required, tipos, enums, anyOf, items, `$defs`, min/max y
  patterns.
- `field_fingerprints`: firma por campo de primer nivel, útil para comparar
  schemas parecidos.

Las descriptions deben participar en ranking, pero no necesariamente en el hash
estricto. Si dos schemas son estructuralmente iguales pero tienen descriptions
ligeramente distintas, puede ser útil tratarlos como compatibles, no como
idénticos.

## Módulos Propuestos

Organización sugerida:

```text
src/gensie/fsp/
  base.py
  providers.py
  examples.py          # dataclasses estructuradas y validación ligera
  resources.py         # carga de recursos JSON
  render_extraction.py # render none y top-level Reasoned[T]
  render_judge.py      # render reasoned_output y candidate_verdicts
  rag.py               # retrieval local y providers RAG
  resources/
    cases/
      cultural_literature_quijote.json
      atlas_ie_super.json

src/gensie/aggregation/
  judge_fsp.py         # mantiene FixedJudgeFspProvider y agrega RagJudgeFspProvider
  verdict_fsp.py       # mantiene FixedVerdictJudgeFspProvider y agrega RagVerdictJudgeFspProvider
```

`examples.py` debería contener modelos como:

```python
@dataclass(frozen=True)
class StructuredFspCase:
    id: str
    domain: str
    language: str
    tags: tuple[str, ...]
    source_text: str
    instruction: str
    schema: JsonDict
    field_examples: Mapping[str, FieldExample]
    judge: JudgeExample | None = None

@dataclass(frozen=True)
class FieldReasoning:
    field_asks: str
    relevant_fragments: str
    final_value: str
    exact_text: str | None = None

@dataclass(frozen=True)
class ReasoningSectionLabels:
    field_asks: str = "EL CAMPO PIDE"
    relevant_fragments: str = "FRAGMENTOS RELEVANTES"
    final_value: str = "VALOR FINAL"

@dataclass(frozen=True)
class JudgeExample:
    total_trials: int
    stable_fields: Mapping[str, Any]
    fields: Mapping[str, JudgeFieldExample]

@dataclass(frozen=True)
class JudgeCandidateExample:
    value: Any
    support: int
    evidence: str
    include: bool | None = None
    first_seen: int | None = None

@dataclass(frozen=True)
class JudgeFieldExample:
    kind: Literal["single", "array"]
    candidates: tuple[JudgeCandidateExample, ...]
    value: Any | None = None
    reasoned_output: Mapping[str, Any] | None = None
    empty_trial_count: int = 0
    null_trial_count: int = 0
    invalid_value_count: int = 0
```

Los renderers no deberían leer archivos ni hacer retrieval; solo reciben un
modelo ya cargado/proyectado y devuelven texto.

## Integración con Specs

Para extracción sin reasoning:

```python
ExtractionSpec(
    name="baseline-rag-fsp",
    reasoning=ReasoningMode.NONE,
    schema_prompt=SchemaPromptMode.JSON_SCHEMA,
    few_shot=FewShotMode.RAG,
)
```

Para extracción top-level:

```python
ExtractionSpec(
    name="enriched-inline-reasoning-rag-fsp",
    reasoning=ReasoningMode.TOP_LEVEL,
    schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
    few_shot=FewShotMode.RAG,
)
```

`default_fsp_provider_for` debería devolver `RagExtractionFspProvider` cuando
`few_shot is FewShotMode.RAG`.

Para juez:

```python
AggregationSpec(
    mode=AggregationMode.JUDGE,
    options={
        "variant": "candidate_verdicts",
        "judge_fsp": "rag"
    },
)
```

La factory del agregador debería elegir:

- `RagJudgeFspProvider` para `variant=reasoned_output`;
- `RagVerdictJudgeFspProvider` para `variant=candidate_verdicts`.

Si `judge_fsp` no se especifica, se conserva el FSP fijo actual.

## Retrieval Inicial

No hace falta empezar con embeddings. Para una primera versión reproducible y
sin dependencias nuevas, el retrieval puede ser lexical y por tags:

1. inspeccionar schema real y construir tags de subtarea;
2. sumar coincidencias de tags entre task y ejemplo;
3. bonificar mismo dominio si se puede inferir;
4. bonificar schema o field fingerprint compatible;
5. penalizar ejemplos demasiado largos;
6. devolver `top_k` ejemplos renderizados.

Después se puede reemplazar el ranker por SQLite/FTS, BM25 o embeddings locales
sin tocar los renderers ni los prompts principales.

Variables futuras razonables, si hacen falta:

- `GENSIE_FSP_RAG_TOP_K`
- `GENSIE_FSP_RAG_MAX_PROMPT_CHARS`
- `GENSIE_FSP_RAG_SAME_SCHEMA_ONLY`
- `GENSIE_FSP_RAG_DEBUG`

Conviene introducirlas solo cuando el provider RAG exista, para evitar knobs
muertos.

## Plan de Implementación

1. Crear modelos estructurados de caso FSP y renderers.
2. Migrar el FSP fijo del Quijote a un recurso de base común, preservando
   exactamente el contenido textual actual.
3. Renderizar extracción `none` y `top_level` desde ese mismo recurso.
4. Crear salidas de juez `reasoned_output` y `candidate_verdicts` dentro del
   mismo recurso base.
5. Implementar proyección por campos de primer nivel en un helper común, por
   ejemplo `gensie.schemas.projection.build_reduced_schema`.
6. Conectar `FewShotMode.RAG` para extracción sin reasoning y extracción
   top-level.
7. Conectar `judge_fsp="rag"` para ambas variantes del juez.
8. Agregar configuración de `ReasoningSectionLabels`.
9. Agregar configuración de orden de candidatos.
10. Agregar retrieval simple por tags/fingerprint.
11. Agregar tracing/metadata que indique qué ejemplo se recuperó, score, campos
    renderizados, modo de reasoning y variante de juez.

## Tests Necesarios

Tests de extracción:

- un recurso estructurado renderiza `SALIDA DEL EJEMPLO` directa para
  `ReasoningMode.NONE`;
- el mismo recurso renderiza `{reasoning, value}` para
  `ReasoningMode.TOP_LEVEL`;
- cada reasoning top-level contiene los rótulos configurados;
- cambiar `ReasoningSectionLabels` cambia los rótulos desde un solo lugar;
- el FSP migrado del Quijote conserva exactamente el contenido textual actual;
- `ReasoningMode.DEEP` no usa el provider RAG inicial;
- `SchemaPromptMode.JSON_SCHEMA`, `PYDANTIC`, `INLINE_REASONING_WRAPPER` y
  `REASONED_PYDANTIC` renderizan vistas de schema compatibles desde el mismo
  ejemplo;
- la proyección recorta schema, required, field_examples y output.

Tests de juez:

- `reasoned_output` renderiza schema reducido con `Reasoned[T]`;
- `candidate_verdicts` renderiza `SingleVerdict` y `ArrayVerdict`;
- `total_trials` se guarda una sola vez y se renderiza como soporte `N/total`;
- no existe campo `verdict`; la decisión vive en `evidence`;
- campos array guardan `empty_trial_count` a nivel de campo y el renderer lo
  muestra como observación del campo, no como candidato;
- `GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS=1` incluye campos estables en prompt y
  FSP;
- `GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS=0` los oculta;
- `GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS=1` muestra `Trials válidos` y
  soportes;
- `GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS=0` los oculta;
- el orden de candidatos cambia según configuración;
- si el schema coincide, el ejemplo se proyecta solo a `disputed_fields`;
- si no hay campos compatibles, el provider no devuelve ejemplo o usa fallback.

Tests de retrieval:

- tags de schema seleccionan ejemplos esperados;
- mismo schema gana a schema parecido;
- ejemplos largos se limitan por presupuesto;
- metadata reporta ids, campos usados, modo de reasoning, variante de juez y
  orden de candidatos.

## Riesgos

- Si se guarda demasiado en strings pre-renderizados, el RAG no podrá proyectar
  por campo sin parsing frágil.
- Si se modelan extracción y juez como recursos separados, el texto fuente y el
  schema pueden desincronizarse.
- Si los ejemplos no tienen tags por campo, el retrieval tenderá a seleccionar
  por dominio y no por razonamiento necesario.
- Si se incluyen campos estables por defecto, el juez puede redecidir campos que
  ya estaban resueltos. El default actual debe mantenerse: no incluirlos.
- Si se soporta deep reasoning demasiado pronto, se duplica el trabajo de
  render y validación con poco beneficio observado.
- Si se migra el Quijote cambiando una palabra, se pierde fidelidad con los
  prompts de referencia ya probados.

## Decisión Recomendada

Implementar primero una librería estructurada de casos FSP con base común:
texto fuente, instrucción y schema original de extracción.

Cada caso debe poder renderizar salidas de extracción para
`ReasoningMode.NONE` y `ReasoningMode.TOP_LEVEL`. En top-level, las razones se
componen desde `field_asks`, `relevant_fragments` y `final_value`, usando
rótulos configurables por renderer. En la migración de ejemplos fijos actuales,
la equivalencia textual exacta tiene prioridad sobre la normalización elegante.

Para el juez, mantener renderers/providers separados por variante:
`reasoned_output` y `candidate_verdicts`. Ambos deben partir del mismo caso FSP
base, usar `total_trials` global, renderizar solo los campos de primer nivel
disputados cuando el schema coincida y respetar
`GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS`,
`GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS` y la configuración de orden de
candidatos.

Con esto los ejemplos quedan editables como datos, los prompts siguen siendo
consistentes y RAG puede seleccionar/proyectar ejemplos sin tocar la lógica de
extracción ni la lógica de agregación.
