# Propuesta: prompting compacto para FSP RAG con mismo schema

## Problema

El pipeline `enriched-inline-reasoning-rag` ya puede recuperar cases FSP desde
`resources/cases`, pero cuando los ejemplos recuperados tienen el mismo schema
que el task real el prompt todavía los trata como ejemplos autosuficientes. Eso
repite por cada ejemplo la instrucción, la descripción del schema y el schema
Pydantic, y después vuelve a repetir esos mismos bloques para el task final.

Esa repetición tiene dos costes: consume tokens y diluye la señal más útil del
RAG, que no es "este es un ejemplo parecido", sino "estas son instancias
resueltas de exactamente esta misma tarea".

## Hipótesis

Cuando todos los FSP recuperados para extracción tienen `schema_match=True`, el
prompt debería cambiar a un layout de mismo schema:

- El `system` define el rol, las reglas de extracción, la regla de anclaje
  estricta una sola vez, y el contrato común de la tarea: instrucción,
  descripción del schema y schema Pydantic.
- El `user` contiene solo los ejemplos FSP compactos y el caso nuevo a resolver:
  input del ejemplo, output del ejemplo, y luego el `input_text` del task real.

Esto debería hacer que el modelo vea los FSP como demostraciones directas del
mismo formulario de extracción, no como tareas separadas con schemas repetidos.

## Cuándo Aplicar

Usar el layout compacto solo si se cumplen todas estas condiciones:

- `extraction.few_shot == RAG`.
- El modo de reasoning es compatible con los FSP renderizados, inicialmente
  `TOP_LEVEL`.
- Hay al menos un ejemplo seleccionado.
- Todos los ejemplos seleccionados tienen metadata de retrieval con
  `schema_match == true`.
- El `schema_prompt` del task es el mismo modo que se usará para describir el
  contrato común, inicialmente `REASONED_PYDANTIC`.

Si algún ejemplo no tiene schema exacto, se conserva el layout actual, donde
cada FSP incluye su propia instrucción, descripción y schema. En esos casos el
FSP es una analogía, no una instancia del mismo formulario, y quitarle el schema
podría confundir.

## Layout Propuesto

### System Prompt

El `system` debería contener:

```text
Eres un extractor de información estructurada...

REGLAS:
- Para cada campo de primer nivel, escribe reasoning antes de value.
- reasoning debe citar evidencia exacta o explicar por qué no hay evidencia suficiente.
- value contiene solo la respuesta final.
- Fundamenta cada value no nulo en el texto fuente.
- Usa null solo cuando el schema lo permita y no haya evidencia suficiente.
- Usa [] para arrays cuando no encuentres elementos respaldados por el texto.
- No añadas hechos externos.
- [REGLA DE ANCLAJE ESTRICTO, una sola vez]

En esta llamada resolverás tareas de este tipo:

INSTRUCCIÓN:
...

DESCRIPCIÓN DEL SCHEMA:
...

SCHEMA PYDANTIC:
...

Los ejemplos del mensaje de usuario usan este mismo schema. Úsalos para
aprender cómo interpretar los campos, tratar nulls/listas/enums y escribir el
reasoning, pero no copies sus valores al nuevo task.
```

La regla de anclaje no debe repetirse en el user prompt. Si se repite, el prompt
vuelve a tener ruido instructivo duplicado.

### User Prompt

El `user` debería quedar más cercano a un cuaderno de ejemplos:

```text
EJEMPLOS FEW-SHOT:

Ejemplo 1: technical_software_quantapack_pro
TEXTO FUENTE DEL EJEMPLO:
...

SALIDA DEL EJEMPLO:
{
  ...
}

Ejemplo 2: technical_software_lince_editor
TEXTO FUENTE DEL EJEMPLO:
...

SALIDA DEL EJEMPLO:
{
  ...
}

TEXTO FUENTE:
...
```

Si hay contexto de fases previas, por ejemplo entidades verbatim, debería seguir
en el `user`, cerca del task real, porque es material específico de esa
instancia y no una regla general.

## Diseño Modular

No conviene resolver esto metiendo condicionales sueltos dentro de
`ExtractionPromptBuilder`. El diseño debe respetar la separación planteada en
`docs/modularizacion-pipelines.md`: `fsp` selecciona/renderiza ejemplos,
`prompts` ensambla prompts, y los runners solo orquestan.

La recomendación es hacer un refactor local, no un refactor grande de pipelines:

1. Separar selección de FSP y render de FSP.
   - Hoy `RagExtractionFspProvider.examples()` recupera y devuelve
     `FSPExample.prompt` ya renderizado.
   - Para el layout compacto, el prompt builder necesita saber si los ejemplos
     son mismo-schema antes de decidir qué va al `system` y qué va al `user`.
   - Por tanto, el RAG debería exponer una selección estructurada además del
     string renderizado.

2. Crear un objeto de selección explícito en `fsp`, por ejemplo:

```python
@dataclass(frozen=True)
class SelectedFspCase:
    case: StructuredFspCase
    metadata: Mapping[str, Any]

@dataclass(frozen=True)
class FspSelection:
    cases: tuple[SelectedFspCase, ...]

    @property
    def all_schema_match(self) -> bool: ...
```

3. Añadir renderers de extracción con intención clara en
   `src/gensie/fsp/render_extraction.py`:

- `render_full_extraction_fsp_example(...)`: el comportamiento actual, con
  instrucción, schema, texto y salida.
- `render_same_schema_extraction_fsp_example(...)`: solo texto fuente del
  ejemplo y salida.

4. Añadir una capa pequeña de layout en `prompts`, por ejemplo
   `src/gensie/prompts/extraction_layouts.py`:

- `DefaultExtractionLayout`: layout actual.
- `SameSchemaRagExtractionLayout`: system con contrato común y user compacto.
- Una función `choose_extraction_layout(selection, extraction, schema_view)`.

5. Mantener `ExtractionPromptBuilder` como orquestador del prompt:

- obtiene `schema_view`;
- obtiene selección FSP;
- elige layout;
- devuelve `PromptBundle(system, user, metadata)`.

Así el builder no acumula reglas largas de cada variante, y `RagExtractionFspProvider`
no se convierte en compositor de system/user prompts.

## Refactor Recomendado

No hace falta un refactor grande de todo el sistema. Sí hace falta un refactor
pequeño pero real alrededor de FSP de extracción, porque el contrato actual
"provider devuelve strings ya renderizados" limita la composición por roles.

Un parche rápido que haga que `RagExtractionFspProvider` renderice distinto
según `schema_match` sería más corto, pero peor organizado: acoplaría retrieval,
rendering y decisión system/user en el provider. Eso va contra la regla de
modularización de no acoplar RAG al prompt renderer principal.

El cambio ideal es incremental:

- conservar `FSPExample` para providers fijos y compatibilidad;
- añadir una ruta estructurada para providers RAG;
- adaptar solo `ExtractionPromptBuilder` para usar la ruta estructurada cuando
  exista;
- dejar el layout actual como fallback.

## Riesgos

- Poner demasiado contenido en `system` puede hacerlo largo y menos legible. El
  contrato común debe ser estructurado y directo.
- Algunos modelos atienden mucho al final del `user`; por eso el `user` debe
  terminar con `TEXTO FUENTE` del task real, no con metainstrucciones.
- Si un ejemplo tiene schema parecido pero no idéntico, el layout compacto puede
  enseñar campos incorrectos. Por eso la condición debe ser fingerprint exacto,
  no solo prefijo o dominio.
- Si los FSP recuperados están mal curados, el layout compacto puede reforzar el
  error más que el layout actual. Esto aumenta la importancia de revisar
  dualidades y reasonings.

## Tests Sugeridos

- Con un task `technical_software_*` y dos FSP del mismo schema, el `system`
  contiene instrucción, descripción y schema Pydantic una sola vez.
- En ese mismo caso, el `user` contiene dos ejemplos compactos sin
  `SCHEMA PYDANTIC DEL EJEMPLO`.
- Si uno de los ejemplos recuperados no tiene `schema_match`, se usa el layout
  actual con schema por ejemplo.
- `STRICT_ANCHORING_RULE` aparece una sola vez en el prompt completo.
- `request.metadata` y `summary.json` registran `layout:
  same_schema_rag_compact` o `layout: default`.
- El response format sigue usando el schema del task real; el cambio solo afecta
  al texto del prompt.

## Evaluación

La comparación útil no es solo token count. Hay que medir:

- tokens de entrada por task;
- F1 por prefijo;
- errores de null/no null;
- errores de arrays vacíos vs poblados;
- errores de enum;
- contaminación por copiar valores del FSP.

La expectativa razonable es que mejore más en prefijos donde tenemos dos FSP
complementarios del mismo schema y donde el task actual comparte estructura de
input con los ejemplos. Si el prefijo todavía no tiene cases revisados, el
layout compacto no debería activarse.

## Estado De Implementación

Implementado como refactor local: `RagExtractionFspProvider` expone ahora una
selección estructurada (`FspSelection`) además de mantener `examples()` como
compatibilidad; `fsp/render_extraction.py` separa el render completo del render
compacto de mismo schema; y `prompts/extraction_layouts.py` decide entre layout
default y `same_schema_rag_compact`. El cambio no modifica el scoring de
`retrieval.py`.

El layout compacto se activa solo para `few_shot=RAG`,
`reasoning=TOP_LEVEL`, `schema_prompt=REASONED_PYDANTIC` y todos los ejemplos
seleccionados con `schema_match=true`. En ese caso el `system` contiene la
instrucción, la descripción del schema, el schema Pydantic y la regla de
anclaje una sola vez; el `user` conserva ejemplos compactos y el `TEXTO FUENTE`
del task real. La metadata del request registra `layout` y `prompt_layout`.
