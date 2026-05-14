# Plan de modularización de pipelines GenSIE

## Objetivo

Modularizar las variantes experimentales de extracción para que los pipelines se construyan seleccionando un subconjunto de módulos y variantes, en lugar de crear una clase nueva por cada combinación.

La meta es que una configuración de pipeline pueda expresar decisiones como:

- tipo de extracción estructurada inline;
- representación del schema en el prompt;
- estrategia de few-shot prompting;
- fases previas de extracción;
- número de trials;
- estrategia de agregación;
- fases futuras como self-refine o sub-extracción.

El resultado deseado es una arquitectura declarativa y combinable, manteniendo compatibilidad con el servidor/evaluador oficial de GenSIE.

## Estado git recomendado

La rama actual de trabajo contiene las variantes experimentales en `dev_set_curation`.

El `origin/main` local no contiene las actualizaciones del 12 de mayo. El main actualizado del repositorio base original está en:

`https://github.com/gia-uh/gensie.git`

Se trajo como referencia local:

`upstream/main`

Punta observada:

`5f112d0 docs: no-streaming rule, X-GenSIE-Token-Usage header, token_usage reporting`

Commits relevantes incorporados en `upstream/main`:

- `02aed48`: actualización de documentación del 12 de mayo.
- `13f5d9b`: alineación de métricas con la especificación, comando `gensie rank` y timing por instancia.
- `3b455f5`: módulo `gensie.usage`, lectura de usage logs, parsing de headers y `UsageTracker`.
- `21e00cc`: resumen de token usage con presupuesto blando medio de 32K.
- `d57cffe`: `gensie eval` registra tokens por instancia usando log o header.
- `284bf7d`: el agente de referencia emite `X-GenSIE-Token-Usage` vía `UsageTracker`.
- `5f112d0`: documenta regla de no streaming, header de token usage y reporte `token_usage`.

La modularización debe partir de `upstream/main`, no de `origin/main`.

## Estrategia de rama

Crear una rama nueva desde `upstream/main`:

```bash
git switch -c refactor/modular-pipeline-composition upstream/main
```

En esa rama, conservar la implementación experimental actual solo como referencia en una carpeta no importable, por ejemplo:

`reference/experimental_pipelines_2026_05_13/`

Archivos relevantes a copiar desde `dev_set_curation` o el commit experimental actual:

- `src/gensie/baseline.py`
- `src/gensie/inline_reasoning.py`
- `src/gensie/enriched_inline_reasoning.py`
- `src/gensie/prompting.py`
- `src/gensie/schema_enrichment.py`
- `src/gensie/self_consistency.py`
- `src/gensie/self_consistency_judge.py`
- `src/gensie/super_fsp.py`
- `src/gensie/verbatim_entities.py`
- `src/gensie/tracing.py`
- `tests/test_inline_reasoning_pipeline.py`
- `tests/test_enriched_inline_reasoning_pipeline.py`
- `tests/test_self_consistency.py`
- `tests/test_self_consistency_judge.py`
- `tests/test_super_fsp.py`
- `tests/test_verbatim_entities.py`
- `docs/pipeline proposal *.md`
- `docs/super-fsp-extraction-types.md`

Esta carpeta debe servir para consulta humana durante la refactorización, no como código ejecutable del paquete.

## Estado de fase 1

Estado aplicado en esta rama:

- Rama activa: `refactor/modular-pipeline-composition`.
- Base: `upstream/main` en `5f112d0`.
- Referencia experimental: `reference/experimental_pipelines_2026_05_13/`.
- Commit de procedencia de la referencia: `dev_set_curation` en `8a1930e`.
- La referencia no debe importarse desde `src/gensie`; solo se consulta durante la migración.
- Se ignoran artefactos locales de ejecución/evaluación: `local-results/`, `test-artifacts/` y `pytest-cache-files-*/`.

Verificación inicial:

- Pasan los tests que no dependen del evaluador semántico ni de descargas externas:
  `tests/test_core.py`, `tests/test_server.py`, `tests/test_timing.py`, `tests/test_token_usage.py`.
- La suite completa de `upstream/main` queda bloqueada en este entorno por permisos en directorios temporales y por carga/descarga de `fastembed`/HuggingFace, no por cambios de la modularización.

## Estado de fase 2

Estado aplicado:

- Se creó el paquete `gensie.pipeline` con especificaciones declarativas,
  registros de resultados, contexto de ejecución, registry y adaptador
  `ComposablePipelineAgent`.
- Se creó `gensie.sampling` con resolución determinista de planes de trials,
  incluyendo grupos heterogéneos por `count` o `ratio`.
- Se creó `gensie.aggregation` con el contrato de agregador y un agregador
  `PassthroughAggregator` para el caso de un único resultado válido o fallback.
- Se crearon contratos livianos para `gensie.runtime`, `gensie.prompts`,
  `gensie.fsp` y `gensie.phases`.
- No se migró aún la lógica experimental desde `reference/`; esta fase solo
  fija las fronteras de módulos y tipos compartidos.

Verificación de fase 2:

```bash
.venv\Scripts\python.exe -m pytest tests\test_pipeline_composition.py tests\test_core.py tests\test_server.py tests\test_timing.py tests\test_token_usage.py -p no:cacheprovider
```

Resultado observado: `16 passed`.

## Estado de fase 3

Estado aplicado:

- Se crearon módulos puros de `gensie.schemas` para:
  - inspección de JSON Schema y refs locales;
  - limpieza de schemas para prompt;
  - parsing de campos y field cards;
  - render Pydantic final, `Reasoned[T]` top-level y `Reasoned[T]` profundo;
  - transformación y unwrap de schemas `{reasoning, value}` top-level y deep.
- Se crearon módulos de `gensie.prompts` para:
  - system prompts por modo de reasoning;
  - vistas de schema raw JSON, clean JSON, Pydantic y reasoned Pydantic;
  - builder de prompt de extracción que recibe un provider FSP separado.
- Se creó `gensie.fsp.providers` con providers FSP sin ejemplo, estático y de texto pre-renderizado.
- Se extendió `SchemaPromptMode` con `CLEAN_JSON_SCHEMA`.
- No se conectó aún ningún agente real a estos builders; eso queda para fase 4.

Verificación de fase 3:

```bash
.venv\Scripts\python.exe -m pytest tests\test_schema_prompt_modules.py tests\test_pipeline_composition.py tests\test_core.py tests\test_server.py tests\test_timing.py tests\test_token_usage.py -p no:cacheprovider
```

Resultado observado: `26 passed`.

## Estado de fase 4

Estado aplicado:

- Se agregó `OpenAIChatClient` como adaptador único de chat completions sin streaming.
- Se agregó `build_json_schema_response_format` para construir el response format
  usando el schema original o el schema transformado por reasoning.
- Se agregó `SingleExtractionRunner` para pipelines single-call:
  - construye prompt mediante `ExtractionPromptBuilder`;
  - llama al runtime común;
  - registra usage en `UsageTracker`;
  - parsea JSON;
  - normaliza outputs `{reasoning, value}` a valores finales.
- Se agregaron specs por defecto para:
  - `baseline`;
  - `inline-reasoning`;
  - `enriched-inline-reasoning`;
  - `enriched-inline-reasoning-deep`;
  - `enriched-inline-reasoning-super-fsp`.
- Se agregaron providers FSP fijos y super-estático en módulos separados.
- `baseline.py` quedó como facade/compatibilidad: clases finas, registry y
  `OfficialParticipant`; no contiene prompts largos, transforms de schema ni
  lógica de ejecución.
- Corrección de fidelidad: los pipelines oficiales single-call usan ahora un
  builder de referencia que conserva los prompts en español de la implementación
  experimental y los FSP originales:
  - Don Quijote para inline/enriched/deep;
  - Atlas-IE para super FSP.
  El builder genérico queda disponible para variantes futuras, pero no sustituye
  el comportamiento experimental ya validado.

Verificación de fase 4:

```bash
.venv\Scripts\python.exe -m pytest tests\test_single_extraction_pipeline.py tests\test_schema_prompt_modules.py tests\test_pipeline_composition.py tests\test_core.py tests\test_server.py tests\test_timing.py tests\test_token_usage.py -p no:cacheprovider
```

Resultado observado después de la corrección de fidelidad: `34 passed`, con
asserts explícitos sobre prompts/FSP de referencia.

## Inventario de módulos actuales

### Orquestación

Actualmente la mayor parte de la orquestación vive en `src/gensie/baseline.py`.

Responsabilidades mezcladas:

- construcción del cliente OpenAI;
- control de delay entre requests;
- lectura de variables de entorno;
- construcción de prompts;
- construcción de schemas de respuesta;
- llamada al modelo;
- parsing y unwrap;
- tracing;
- planificación de trials;
- agregación local;
- llamada al juez;
- registro de pipelines en `OfficialParticipant`.

Esta concentración hace difícil combinar módulos sin duplicar clases.

### Extraccion estructurada inline

Módulo actual:

`src/gensie/inline_reasoning.py`

Variante:

- `{reasoning, value}` solo en campos de primer nivel.

Funciones principales:

- `build_inline_reasoning_schema`
- `build_inline_reasoning_prompt_schema`
- `build_inline_reasoning_prompt`
- `unwrap_inline_reasoning_output`

Sistema:

- `INLINE_REASONING_SYSTEM_PROMPT`

Knobs actuales:

- `INLINE_PROMPT_SCHEMA_VIEW`
- `INCLUDE_INLINE_REASONING_FEW_SHOT`

### Extraccion inline profunda

Módulo actual:

`src/gensie/enriched_inline_reasoning.py`

Variante:

- `{reasoning, value}` en todos los campos, subcampos y elementos de arrays.

Funciones principales:

- `build_deep_inline_reasoning_schema`
- `unwrap_deep_inline_reasoning_output`
- `render_deep_reasoned_pydantic_schema`
- `build_enriched_deep_inline_reasoning_prompt`

Sistema:

- `DEEP_INLINE_REASONING_SYSTEM_PROMPT`

### Schema Pydantic en prompt

Módulos actuales:

- `src/gensie/schema_enrichment.py`
- `src/gensie/enriched_inline_reasoning.py`

Variantes:

- schema limpio JSON;
- schema Pydantic final;
- schema Pydantic con `Reasoned[T]` top-level;
- schema Pydantic con `Reasoned[T]` profundo.

Funciones principales:

- `clean_schema_for_prompt`
- `parse_schema_fields`
- `render_field_cards`
- `render_pydantic_code`
- `render_reasoned_pydantic_schema`
- `render_deep_reasoned_pydantic_schema`

Dependencia importante:

La representación Pydantic con `Reasoned[T]` depende de la estrategia de extracción inline seleccionada. No debe ser un módulo totalmente independiente: debe recibir el modo de reasoning o una abstracción de schema transform.

### Few-shot prompting y FSP

Módulo actual:

`src/gensie/super_fsp.py`

Variantes actuales:

- FSP fijo de Quijote/cultural en `inline_reasoning.py` y `enriched_inline_reasoning.py`.
- Super FSP fijo basado en Atlas-IE.
- Super FSP dinámico task-schema-dependant: ya existen funciones para seleccionar subtareas por schema, pero no están conectadas a los pipelines actuales.
- RAG: no implementado.

Funciones principales:

- `build_super_fsp_example`
- `build_super_fsp_example_for_schema`
- `select_super_fsp_subtasks_for_schema`
- `explain_super_fsp_subtask_selection`
- `build_super_fsp_schema`
- `build_super_fsp_reasoned_output`

Subtareas FSP actuales:

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

### Varios trials

Módulo actual:

`src/gensie/self_consistency.py`

Responsabilidades:

- estimación de presupuesto de trials;
- sampling multi-trial;
- similitud de strings;
- comparación schema-aware de valores;
- clustering;
- agregación de arrays;
- diagnósticos de agregación.

Clases principales:

- `TrialBudgetConfig`
- `TrialBudgetPlanner`
- `SelfConsistencyConfig`
- `SchemaAwareSelfConsistencyAggregator`
- `SchemaValueSimilarity`
- `ItemClusterer`
- `ArrayCandidateBuilder`
- `ArrayCandidateSelector`
- `HeuristicIdentityFieldSelector`

Knobs actuales:

- `GENSIE_SC_TRIALS`
- `GENSIE_SC_MAX_TRIALS`
- `GENSIE_SC_MIN_TRIALS`
- `GENSIE_SC_DYNAMIC_TRIALS`
- `GENSIE_SC_TOKEN_BUDGET`
- `GENSIE_SC_TOKEN_BUDGET_RATIO`
- `GENSIE_SC_TIME_BUDGET_S`
- `GENSIE_SC_TIME_BUDGET_RATIO`
- `GENSIE_SC_COMPLETION_TOKEN_SAFETY_FACTOR`
- `GENSIE_SC_TIME_SAFETY_FACTOR`
- `GENSIE_SC_CHARS_PER_TOKEN`
- `GENSIE_SC_TEMPERATURE`
- `GENSIE_SC_FIRST_TEMPERATURE`
- `GENSIE_SC_TOP_P`
- `GENSIE_SC_TOP_K`
- `GENSIE_SC_MAX_TOKENS`
- `GENSIE_SC_STRING_SIMILARITY`
- `GENSIE_SC_EMBEDDING_MODEL`
- `GENSIE_SC_EMBEDDING_WEIGHT`
- `GENSIE_SC_SCALAR_STRING_THRESHOLD`
- `GENSIE_SC_ARRAY_STRING_THRESHOLD`
- `GENSIE_SC_OBJECT_ITEM_THRESHOLD`
- `GENSIE_SC_SIMPLE_ITEM_SUPPORT_FLOOR`
- `GENSIE_SC_OBJECT_ITEM_SUPPORT_FLOOR`
- `GENSIE_SC_OPTIONAL_PROPERTY_SUPPORT_RATIO`
- `GENSIE_SC_INTRA_TRIAL_DEDUPE_THRESHOLD`
- `GENSIE_SC_INCLUDE_GREEDY_ARRAY_CANDIDATE`
- `GENSIE_SC_INCLUDE_THRESHOLD_ARRAY_CANDIDATES`
- `GENSIE_SC_INCLUDE_ORIGINAL_ARRAY_CANDIDATES`
- `GENSIE_SC_USE_IDENTITY_CLUSTERING`
- `GENSIE_SC_IDENTITY_MIN_SCORE`
- `GENSIE_SC_IDENTITY_MIN_MARGIN`
- `GENSIE_SC_IDENTITY_STRING_THRESHOLD`
- `GENSIE_SC_ARRAY_SELECTOR`
- `GENSIE_SC_RECALL_MBR_TOLERANCE`
- `GENSIE_SC_NULL_WINS_TIES`

### Agregación heurística self-consistency

Implementación actual:

`SchemaAwareSelfConsistencyAggregator`

Entrada:

- lista de candidatos finales ya desenvueltos;
- schema original de salida.

Salida:

- objeto final;
- diagnósticos opcionales.

Observación:

Como opera sobre candidatos finales, puede reutilizarse con extracción top-level o profunda si antes se aplica el unwrap adecuado.

### Agregación con juez SLM

Módulo actual:

`src/gensie/self_consistency_judge.py`

Responsabilidades:

- resumir votos por campo;
- agrupar valores escalares;
- agrupar items de arrays item-by-item;
- construir prompt del juez;
- renderizar resumen compacto para el prompt.

Funciones principales:

- `build_self_consistency_judge_prompt`
- `build_judge_vote_summary`
- `render_judge_vote_summary`

Knobs actuales:

- `GENSIE_SC_JUDGE_INCLUDE_SCALAR_REASONINGS`
- `GENSIE_SC_JUDGE_INCLUDE_ARRAY_REASONINGS`
- `GENSIE_SC_JUDGE_TEMPERATURE`
- `GENSIE_SC_JUDGE_TOP_P`
- `GENSIE_SC_JUDGE_TOP_K`
- `GENSIE_SC_JUDGE_MAX_TOKENS`

Fallbacks implementados:

- si solo hay un trial válido, no se llama al juez;
- si falla el juez, se usa el primer trial válido;
- si no hay ningún trial válido, se devuelve error.

Limitación actual:

El juez asume trials con razonamiento top-level. Para soportar razonamiento profundo haría falta normalizar los trials a una estructura común.

### Fase de extracción de entidades

Módulo actual:

`src/gensie/verbatim_entities.py`

Responsabilidades:

- extracción previa de entidades verbatim en un schema fijo;
- normalización;
- flatten a lista;
- evaluación auxiliar.

Funciones principales:

- `build_verbatim_entity_schema`
- `build_verbatim_entity_prompt`
- `build_verbatim_entity_response_format`
- `parse_verbatim_entity_response`
- `normalize_verbatim_entities`
- `flatten_verbatim_entities`
- `extract_verbatim_entities`

Uso actual:

Solo existe una variante concreta:

`VerbatimEntitiesEnrichedInlineReasoningAgent`

En la modularización debe convertirse en una fase previa opcional que enriquece el contexto del prompt.

### Módulos futuros no implementados

Self-Refine:

- debe modelarse como fase posterior a una extracción inicial;
- podría recibir output candidato, schema, texto fuente y razonamientos;
- podría devolver un output corregido o un objeto inline reasoned corregido.

Sub-extracción:

- debe modelarse como un subpipeline por campo, grupo de campos o item de array;
- podría compartir los mismos módulos de extraction, FSP y aggregation;
- probablemente necesita un contrato de composición jerárquico.

RAG para FSP:

- debe modelarse como proveedor de ejemplos;
- no debe acoplarse al prompt renderer principal.

## Cambios de upstream que afectan la arquitectura

`upstream/main` introduce `gensie.usage.UsageTracker` y el header:

`X-GenSIE-Token-Usage`

El servidor lee `agent.usage.header_value()` si el agente expone un tracker.

Por tanto, la nueva arquitectura debe:

- resetear usage al inicio de cada `run`;
- registrar cada llamada al modelo con `usage.add(response.usage)`;
- mantener el contrato de no streaming;
- permitir que el evaluador mida tokens vía header o usage log;
- evitar que cada modulo implemente su propio conteo incompatible.

El tracing experimental puede conservarse como diagnostico opcional, pero no debe sustituir el contrato oficial de usage.

## Diseno objetivo

### Capas propuestas

`runtime`

- cliente OpenAI;
- request pacing;
- llamada a chat completions;
- parseo comun de respuesta;
- usage tracking;
- tracing opcional.

`schemas`

- schema final original;
- schema transformado para top-level reasoning;
- schema transformado para deep reasoning;
- unwrap de cada estrategia;
- validaciones comunes.

`prompts`

- composición de prompt;
- render de schema limpio;
- render de schema Pydantic;
- render de `Reasoned[T]`;
- inclusion de FSP;
- inclusión de contexto de fases previas.

`fsp`

- proveedor sin ejemplos;
- proveedor FSP fijo;
- proveedor Super FSP fijo;
- proveedor Super FSP dinámico por schema;
- proveedor RAG futuro.

`phases`

- fase previa de entidades verbatim;
- fases futuras de sub-extracción;
- fases futuras de self-refine.

`sampling`

- single call;
- multi-trial;
- planificación dinámica de trials.

`aggregation`

- passthrough para single call;
- agregación heurística self-consistency;
- agregación con juez;
- futuras agregaciones híbridas.

`registry`

- registro de pipelines declarativos;
- metadata de `ParticipantInfo`;
- construcción de `GenSIEAgent` a partir de specs.

### Organización física de la implementación

La implementación no debe volver a concentrarse en archivos `.py` masivos. La regla de diseño es:

- cada archivo debe tener una responsabilidad dominante;
- los runners orquestan, pero no contienen prompts largos, transformaciones de schema ni algoritmos de agregación completos;
- los prompts largos y ejemplos FSP viven en módulos de `prompts` o `fsp`;
- las dataclasses/configs viven cerca del módulo que configuran;
- los `__init__.py` solo exportan una API pequeña y estable;
- las dependencias deben ir de capas bajas a altas: `schemas` y `prompts` no importan `pipeline`, `registry` ni `agents`.

No hay que atomizar en exceso. Un archivo puede contener varias funciones privadas si todas sirven a una única responsabilidad. Lo que se debe evitar es repetir el patrón actual de un archivo como `baseline.py` que contiene clientes, prompts, schemas, sampling, agregación, trazas y registro a la vez.

Estructura propuesta:

```text
src/gensie/
  baseline.py                  # OfficialParticipant y compatibilidad mínima
  agent.py
  task.py
  eval.py
  usage.py                     # upstream
  ranking.py                   # upstream
  server.py
  cli.py

  pipeline/
    __init__.py
    specs.py                   # PipelineSpec, ExtractionSpec, SamplingSpec, AggregationSpec
    agent.py                   # ConfigurablePipelineAgent
    registry.py                # build_official_registry, PipelineRegistry
    context.py                 # PipelineContext, PhaseContext, PromptContext
    records.py                 # ModelCallRecord, TrialRecord, PipelineRunResult

  runtime/
    __init__.py
    client.py                  # OpenAI client factory
    chat.py                    # chat completion wrapper, no streaming, usage tracking
    env.py                     # typed env helpers
    tracing.py                 # optional trace integration, if preserved
    options.py                 # generation options dataclasses/factories

  schemas/
    __init__.py
    inspect.py                 # deref, nullable unwrap, schema type, field walking
    clean.py                   # clean_schema_for_prompt
    pydantic_render.py         # final-value Pydantic-like rendering
    reasoning.py               # top-level/deep reasoning schema transforms and unwrap
    fields.py                  # FieldInfo and schema field parsing

  prompts/
    __init__.py
    base.py                    # prompt assembly contracts
    extraction.py              # extraction prompt builder
    schema_views.py            # raw/clean/pydantic/reasoned schema prompt views
    system.py                  # system prompts
    context_blocks.py          # entities block, extra evidence blocks

  fsp/
    __init__.py
    providers.py               # FspProvider interface and provider registry
    fixed.py                   # small fixed examples
    super.py                   # Super FSP subtasks and renderers
    selector.py                # dynamic schema-dependent subtask selection
    rag.py                     # placeholder/provider interface for future RAG

  phases/
    __init__.py
    base.py                    # PrePhase/PostPhase interfaces
    verbatim_entities.py       # entity pre-extraction phase
    self_refine.py             # future placeholder or interface
    subextraction.py           # future placeholder or interface

  sampling/
    __init__.py
    single.py                  # single extraction call
    multi.py                   # multi-trial runner
    budget.py                  # TrialBudgetConfig/Planner
    plans.py                   # homogeneous and heterogeneous trial plans

  aggregation/
    __init__.py
    base.py                    # Aggregator interface
    passthrough.py             # single output aggregator
    self_consistency.py        # schema-aware heuristic aggregator facade
    similarity.py              # string/value similarity
    clustering.py              # item clustering and identity selection
    arrays.py                  # array candidate builders/selectors
    judge.py                   # SLM judge aggregator
    judge_prompt.py            # vote summary and judge prompt rendering
```

Notas sobre esta estructura:

- `baseline.py` debe volver a ser pequeño. Su responsabilidad ideal es construir y exponer `OfficialParticipant`, no implementar cada pipeline.
- `pipeline/agent.py` debe ser el único adaptador principal a `GenSIEAgent`.
- `runtime/chat.py` debe ser el único camino normal para llamar al modelo, así se conserva `UsageTracker`.
- `aggregation/self_consistency.py` puede exponer una fachada, pero los detalles largos de similitud, clustering y arrays deben vivir en archivos separados.
- `fsp/super.py` puede ser grande por contener datos de ejemplo, pero no debe mezclar ejecución de pipelines ni llamadas al modelo.
- Si un archivo crece porque acumula dos responsabilidades, se separa por responsabilidad, no por tamaño arbitrario.

### Diseño de multi-trials heterogéneos

Los multi-trials no deben asumir que todos los trials usan el mismo extractor. Desde el inicio, el sampling debe aceptar un plan de trials con grupos heterogéneos.

Caso objetivo:

- algunos trials usan `baseline`;
- otros usan `enriched-inline-reasoning`;
- otros usan `deep-inline-reasoning`;
- otros usan un FSP distinto;
- todos producen `TrialRecord` normalizados;
- la agregación opera sobre esos records normalizados.

Para esto, `SamplingSpec` debe poder expresar un plan:

```python
SamplingSpec(
    mode="multi_trial",
    trial_plan=[
        TrialGroupSpec(
            name="baseline",
            count=1,
            extraction=ExtractionSpec(
                reasoning="none",
                schema_prompt="raw_json",
                fsp="none",
            ),
            generation_options={"temperature": 0.0},
        ),
        TrialGroupSpec(
            name="enriched",
            ratio=0.60,
            extraction=ExtractionSpec(
                reasoning="top_level",
                schema_prompt="reasoned_pydantic",
                fsp="fixed",
            ),
            generation_options={"temperature": 0.5},
        ),
        TrialGroupSpec(
            name="deep",
            ratio=0.40,
            extraction=ExtractionSpec(
                reasoning="deep",
                schema_prompt="deep_reasoned_pydantic",
                fsp="dynamic_super",
            ),
            generation_options={"temperature": 0.5},
        ),
    ],
    budget={...},
)
```

Reglas para planes heterogéneos:

- cada grupo define su propio `ExtractionSpec`;
- cada grupo puede definir sus propios generation options;
- `count` tiene prioridad sobre `ratio`;
- `ratio` se resuelve contra el número de trials permitido por el presupuesto;
- el planner debe garantizar al menos los grupos con `min_count` antes de repartir ratios;
- el orden de ejecución debe ser configurable: secuencial por grupos o intercalado;
- cada `TrialRecord` conserva `group_name`, `pipeline_variant`, `extraction_spec` y `generation_options`;
- los errores se registran por trial sin abortar todo el plan si quedan candidatos válidos.

Contrato propuesto:

```python
TrialGroupSpec(
    name="enriched",
    extraction=ExtractionSpec(...),
    count=None,
    ratio=0.6,
    min_count=1,
    max_count=None,
    generation_options={...},
)
```

`TrialRecord` debe incluir metadatos de grupo:

```python
TrialRecord(
    trial_index=2,
    group_name="deep",
    extraction_name="deep_reasoned_pydantic_dynamic_super",
    raw_response={...},
    structured_output={...},
    final_candidate={...},
    reasoning_view={...},
    usage={...},
    error=None,
)
```

La agregación heurística puede empezar usando solo `final_candidate`, pero debe recibir también los metadatos para diagnósticos y futuras estrategias ponderadas.

El juez debe recibir un resumen que pueda indicar el origen de los candidatos:

- conteos globales por valor;
- conteos por grupo cuando sea útil;
- índices de trial;
- reasoning normalizado;
- advertencia cuando un valor solo aparece en un grupo especifico.

Esto permite que el juez compare no solo "cuántos trials votan por X", sino también "qué familia de extractor produjo X".

### Normalización entre variantes de extracción

Para que trials heterogéneos sean agregables, todos deben pasar por un adaptador común:

```python
ExtractionResult(
    structured_output={...},      # output bruto compatible con response_format
    final_candidate={...},        # JSON final GenSIE
    reasoning_view={...},         # razonamientos normalizados por campo/path
    schema_mode="none | top_level | deep",
)
```

Ejemplos:

- baseline sin reasoning: `reasoning_view` vacío o con entradas `None`;
- top-level inline: `reasoning_view["field"] = reasoning`;
- deep inline: `reasoning_view["field.subfield"] = reasoning` y también un resumen top-level opcional;
- futuras sub-extracciones: `reasoning_view` puede incluir `source_phase` o `subtask_id`.

Esta normalización debe vivir en `schemas/reasoning.py` o en un módulo pequeño de `pipeline/records.py`, no dentro del agregador.

### Política de tamaño y responsabilidades

No se fija un límite numérico rígido, pero si un archivo supera aproximadamente 400-500 líneas debe revisarse si contiene más de una responsabilidad. Excepciones razonables:

- archivos con datos declarativos extensos, como `fsp/super.py`;
- tests que cubren una matriz amplia de casos relacionados;
- documentos generados o reportes, si se versionan.

Señales de que un archivo debe dividirse:

- importa OpenAI y también renderiza prompts largos;
- contiene dataclasses de configuración y también algoritmos extensos;
- contiene varias clases `Agent` concretas;
- contiene muchas variables de entorno de dominios distintos;
- requiere tocarlo para agregar una variante que conceptualmente pertenece a otra capa.

### Contratos propuestos

La unidad de composición principal debe ser un `PipelineSpec`:

```python
PipelineSpec(
    name="enriched-inline-reasoning-self-consistency-judge",
    description="Multi-trial enriched inline reasoning with an SLM judge.",
    pre_phases=[],
    extraction=ExtractionSpec(
        reasoning="top_level",
        schema_prompt="reasoned_pydantic",
        fsp="fixed_super",
    ),
    sampling=SamplingSpec(
        mode="multi_trial",
        trial_plan=[
            TrialGroupSpec(
                name="default",
                extraction="$pipeline.extraction",
                ratio=1.0,
            )
        ],
    ),
    aggregation=AggregationSpec(mode="judge"),
)
```

`ExtractionSpec`:

```python
ExtractionSpec(
    reasoning="none | top_level | deep",
    schema_prompt="raw_json | clean_json | pydantic | reasoned_pydantic | deep_reasoned_pydantic",
    fsp="none | fixed | fixed_super | dynamic_super | rag",
    system_prompt="...",
)
```

`SamplingSpec`:

```python
SamplingSpec(
    mode="single | multi_trial",
    trial_plan=[TrialGroupSpec(...)] | None,
    generation_options={...},
    budget={...},
    execution_order="grouped | interleaved",
)
```

`TrialGroupSpec`:

```python
TrialGroupSpec(
    name="enriched",
    extraction=ExtractionSpec(...) | "$pipeline.extraction",
    count=None,
    ratio=1.0,
    min_count=0,
    max_count=None,
    generation_options={...},
)
```

`AggregationSpec`:

```python
AggregationSpec(
    mode="none | heuristic_self_consistency | judge",
    options={...},
)
```

`TrialRecord`:

```python
TrialRecord(
    trial_index=0,
    group_name="default",
    extraction_name="top_level_reasoned_pydantic_fixed_super",
    extraction_spec=ExtractionSpec(...),
    generation_options={...},
    raw_response={...},
    structured_output={...},
    final_candidate={...},
    reasoning_view={...},
    usage={...},
    error=None,
)
```

La clave es que `reasoning_view` abstraiga si el reasoning es top-level o profundo, para que el juez y futuros refiners no dependan del formato exacto del output del modelo.

## Matriz de módulos y dependencias

| Módulo | Depende de | Produce | Combinable con |
| --- | --- | --- | --- |
| Inline top-level | schema original | reasoned schema top-level, unwrap top-level | single, multi-trial, heurística, juez |
| Inline deep | schema original | deep reasoned schema, unwrap deep | single, multi-trial, heurística |
| Pydantic prompt | schema parser | texto de schema | FSP, entidades, single/multi |
| FSP fijo | prompt renderer | bloque de ejemplo | top-level, deep si se adapta el ejemplo |
| Super FSP dinámico | schema parser | bloque de ejemplo seleccionado | top-level primero; deep requiere output deep |
| Entidades verbatim | texto fuente, modelo | contexto auxiliar | extraction prompt |
| Multi-trial homogéneo | extraction callable | lista de TrialRecord de un grupo | heurística, juez |
| Multi-trial heterogéneo | plan de TrialGroupSpec | lista de TrialRecord normalizados por grupo | heurística, juez, futuras agregaciones ponderadas |
| Agregación heurística | candidatos finales y metadatos de trials | output final | top-level, deep, trials heterogéneos |
| Juez | TrialRecord con reasoning normalizado | output final | top-level, deep si hay reasoning_view normalizado |
| Self-refine futuro | output inicial | output revisado | single/multi/agregado |
| Sub-extracción futura | schema segmentado | outputs parciales | cualquier extraction spec |

## Pipelines actuales expresados como specs

`baseline`

```python
PipelineSpec(
    name="baseline",
    extraction=ExtractionSpec(reasoning="none", schema_prompt="raw_task_prompt", fsp="none"),
    sampling=SamplingSpec(mode="single"),
    aggregation=AggregationSpec(mode="none"),
)
```

`inline-reasoning`

```python
PipelineSpec(
    name="inline-reasoning",
    extraction=ExtractionSpec(reasoning="top_level", schema_prompt="reasoning_wrapper_json", fsp="fixed"),
    sampling=SamplingSpec(mode="single"),
    aggregation=AggregationSpec(mode="none"),
)
```

`enriched-inline-reasoning`

```python
PipelineSpec(
    name="enriched-inline-reasoning",
    extraction=ExtractionSpec(reasoning="top_level", schema_prompt="reasoned_pydantic", fsp="fixed"),
    sampling=SamplingSpec(mode="single"),
    aggregation=AggregationSpec(mode="none"),
)
```

`enriched-inline-reasoning-deep`

```python
PipelineSpec(
    name="enriched-inline-reasoning-deep",
    extraction=ExtractionSpec(reasoning="deep", schema_prompt="deep_reasoned_pydantic", fsp="fixed_deep"),
    sampling=SamplingSpec(mode="single"),
    aggregation=AggregationSpec(mode="none"),
)
```

`enriched-inline-reasoning-super-fsp`

```python
PipelineSpec(
    name="enriched-inline-reasoning-super-fsp",
    extraction=ExtractionSpec(reasoning="top_level", schema_prompt="reasoned_pydantic", fsp="fixed_super"),
    sampling=SamplingSpec(mode="single"),
    aggregation=AggregationSpec(mode="none"),
)
```

`verbatim-entities-enriched-inline-reasoning`

```python
PipelineSpec(
    name="verbatim-entities-enriched-inline-reasoning",
    pre_phases=[PrePhaseSpec(name="verbatim_entities")],
    extraction=ExtractionSpec(reasoning="top_level", schema_prompt="reasoned_pydantic", fsp="fixed"),
    sampling=SamplingSpec(mode="single"),
    aggregation=AggregationSpec(mode="none"),
)
```

`enriched-inline-reasoning-self-consistency`

```python
PipelineSpec(
    name="enriched-inline-reasoning-self-consistency",
    extraction=ExtractionSpec(reasoning="top_level", schema_prompt="reasoned_pydantic", fsp="fixed"),
    sampling=SamplingSpec(mode="multi_trial"),
    aggregation=AggregationSpec(mode="heuristic_self_consistency"),
)
```

`enriched-inline-reasoning-super-fsp-self-consistency`

```python
PipelineSpec(
    name="enriched-inline-reasoning-super-fsp-self-consistency",
    extraction=ExtractionSpec(reasoning="top_level", schema_prompt="reasoned_pydantic", fsp="fixed_super"),
    sampling=SamplingSpec(mode="multi_trial"),
    aggregation=AggregationSpec(mode="heuristic_self_consistency"),
)
```

`enriched-inline-reasoning-self-consistency-judge`

```python
PipelineSpec(
    name="enriched-inline-reasoning-self-consistency-judge",
    extraction=ExtractionSpec(reasoning="top_level", schema_prompt="reasoned_pydantic", fsp="fixed"),
    sampling=SamplingSpec(mode="multi_trial"),
    aggregation=AggregationSpec(mode="judge"),
)
```

## Plan de migración recomendado

### Fase 1: base limpia y carpeta de referencia

1. Crear rama desde `upstream/main`.
2. Copiar la implementación experimental a `reference/experimental_pipelines_2026_05_13/`.
3. Confirmar que el baseline upstream sigue pasando tests.
4. No importar nada desde `reference/`.

### Fase 2: runtime común

1. Crear un runtime de llamadas al modelo que use `UsageTracker`.
2. Centralizar timeout, base URL, API key y request pacing.
3. Garantizar que cada llamada registre usage.
4. Mantener no streaming.

### Fase 3: schemas y prompts

1. Migrar transformaciones de schema a módulos puros.
2. Migrar renderers de prompt.
3. Separar FSP providers del prompt builder.
4. Cubrir con tests unitarios sin llamadas al modelo.

### Fase 4: extracción single-call

1. Implementar un `ExtractionRunner`.
2. Recrear `baseline`, `inline-reasoning`, `enriched-inline-reasoning`, `deep` y `super-fsp` como specs.
3. Mantener `OfficialParticipant` como registry de specs.

### Fase 5: fases previas

1. Convertir entidades verbatim en `PreExtractionPhase`.
2. Hacer que el prompt builder reciba contexto enriquecido por fases.
3. Reproducir `verbatim-entities-enriched-inline-reasoning`.

### Fase 6: multi-trial y agregación

1. Implementar `TrialGroupSpec` y resolución de planes homogéneos/heterogéneos.
2. Implementar `SamplingRunner` que produce `TrialRecord` normalizados con metadatos de grupo.
3. Conectar `TrialBudgetPlanner` para calcular el número total de trials permitidos.
4. Implementar reparto de trials por `count`, `min_count`, `max_count` y `ratio`.
5. Soportar ejecución agrupada e intercalada.
6. Conectar agregación heurística usando primero `final_candidate`, pero preservando metadatos.
7. Conectar juez con fallbacks y resumen opcional por grupo.
8. Agregar tests de compatibilidad para outputs equivalentes.
9. Agregar tests específicos para planes heterogéneos: baseline + enriched + deep.

### Fase 7: FSP dinámico y futuros módulos

1. Conectar `build_super_fsp_example_for_schema`.
2. Definir interfaz RAG como proveedor de ejemplos.
3. Definir interfaz self-refine.
4. Definir interfaz sub-extracción.

## Riesgos principales

### Riesgo: romper el contrato de usage de upstream

Mitigación:

- toda llamada al modelo debe pasar por runtime común;
- runtime registra `UsageTracker`;
- tests de servidor deben comprobar header.

### Riesgo: mezclar reasoning top-level y deep

Mitigación:

- definir `ReasoningMode`;
- cada modo proporciona schema transform, unwrap y reasoning view;
- el juez trabaja sobre `TrialRecord`, no sobre el JSON bruto.

### Riesgo: explosión de combinaciones

Mitigación:

- specs declarativos;
- registry de pipelines públicos;
- tests unitarios de módulos;
- pocos tests end-to-end de combinaciones importantes.

### Riesgo: recrear archivos monoliticos

Mitigación:

- revisar responsabilidades antes de agregar código nuevo;
- si una clase necesita prompts, schemas, runtime y agregación a la vez, convertirla en orquestador que delega;
- mantener `baseline.py` como facade/registry pequeño;
- mover algoritmos largos a submódulos dedicados;
- evitar clases `Agent` por combinación de pipeline.

### Riesgo: trials heterogéneos no comparables

Mitigación:

- toda variante de extracción debe producir `ExtractionResult`;
- todo trial debe producir `TrialRecord`;
- `reasoning_view` debe normalizar top-level, deep, baseline y futuras sub-extracciones;
- los agregadores no deben depender del JSON bruto de una variante concreta;
- el juez debe poder ver conteos por grupo cuando existan trials heterogéneos.

### Riesgo: FSP acoplado a un modo de reasoning

Mitigación:

- `FspProvider` debe declarar que reasoning modes soporta;
- FSP top-level y FSP deep deben renderizar outputs distintos si es necesario.

### Riesgo: dependencia de variables de entorno dispersas

Mitigación:

- mover lectura env a factories de config;
- las clases internas reciben dataclasses ya construidas;
- documentar defaults en un solo lugar.

## Preguntas abiertas

- El juez debe soportar también reasoning profundo o solo top-level en la primera versión modular?
- El Super FSP dinámico debe reemplazar al Super FSP fijo o convivir como variante?
- La fase de entidades debe usar siempre temperatura `0.0` o debe tener config propia?
- La carpeta `reference/` debe versionarse completa o solo incluir archivos fuente y docs, excluyendo resultados grandes?
- Conviene mantener `trace_step` como módulo experimental o adaptarlo al nuevo formato de reportes de upstream?
- Los porcentajes de trials heterogéneos deben configurarse por variables de entorno, por archivo de config, o solo por specs Python?
- La agregación heurística debe ponderar todos los grupos igual o permitir pesos por grupo?

## Resultado esperado

Al final de la refactorización, agregar un pipeline nuevo debería ser principalmente declarar una combinación de módulos:

```python
register_pipeline(
    PipelineSpec(
        name="dynamic-super-fsp-sc-judge",
        pre_phases=[PrePhaseSpec(name="verbatim_entities")],
        extraction=ExtractionSpec(
            reasoning="top_level",
            schema_prompt="reasoned_pydantic",
            fsp="dynamic_super",
        ),
        sampling=SamplingSpec(mode="multi_trial"),
        aggregation=AggregationSpec(mode="judge"),
    )
)
```

Un pipeline heterogeneo deberia declararse asi:

```python
register_pipeline(
    PipelineSpec(
        name="mixed-baseline-enriched-deep-sc-judge",
        sampling=SamplingSpec(
            mode="multi_trial",
            trial_plan=[
                TrialGroupSpec(
                    name="baseline",
                    extraction=ExtractionSpec(
                        reasoning="none",
                        schema_prompt="raw_json",
                        fsp="none",
                    ),
                    count=1,
                    generation_options={"temperature": 0.0},
                ),
                TrialGroupSpec(
                    name="enriched",
                    extraction=ExtractionSpec(
                        reasoning="top_level",
                        schema_prompt="reasoned_pydantic",
                        fsp="fixed",
                    ),
                    ratio=0.5,
                ),
                TrialGroupSpec(
                    name="deep_dynamic_super",
                    extraction=ExtractionSpec(
                        reasoning="deep",
                        schema_prompt="deep_reasoned_pydantic",
                        fsp="dynamic_super",
                    ),
                    ratio=0.5,
                ),
            ],
        ),
        aggregation=AggregationSpec(mode="judge"),
    )
)
```

Y no crear otra subclase de `GenSIEAgent` con logica duplicada.
