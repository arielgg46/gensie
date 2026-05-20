# Implementación FSP RAG

## Estado actual

Se implementó la primera capa estructurada para ejemplos FSP RAG en
`src/gensie/fsp/`, sin cambiar los pipelines oficiales existentes.

Archivos principales:

- `examples.py`: modelos comunes (`StructuredFspCase`, `FieldExample`,
  `FieldReasoning`, `JudgeExample`, `JudgeFieldExample`,
  `JudgeCandidateExample`, `ReasoningSectionLabels`, `CandidateOrder`).
- `resources/cases/cultural_literature_quijote.json`: caso Quijote cultural
  puro editable, con texto fuente, instrucción, schema original, ejemplos de
  campos y datos iniciales del juez. No incluye `literary_impact_evidence`.
- `resources.py`: carga y validación ligera de casos FSP desde JSON.
- `cases.py`: acceso a casos conocidos; actualmente carga el Quijote cultural
  desde `resources/cases/*.json`.
- `render_extraction.py`: render de extracción para `ReasoningMode.NONE` y
  `ReasoningMode.TOP_LEVEL`.
- `render_judge.py`: render inicial del resumen de candidatos del juez,
  incluyendo `empty_trial_count` como observación de campos array.
- `retrieval.py`: ranker local inicial para casos FSP, con perfil de schema,
  tags derivados, fingerprints y metadata de recuperación.
- `rag.py`: `RagExtractionFspProvider`, provider inicial para `FewShotMode.RAG`,
  usando el ranker local en vez de devolver el primer recurso.
- `schemas/projection.py`: helper común `build_reduced_schema()` para recortar
  schemas por campos de primer nivel.
- `fsp/projection.py`: `project_structured_fsp_case()` para proyectar un caso
  FSP completo.

También se exportaron las piezas nuevas desde `fsp/__init__.py` y
`default_fsp_provider_for()` ya devuelve `RagExtractionFspProvider()` cuando el
spec usa `few_shot=FewShotMode.RAG`.

El pipeline público `enriched-inline-reasoning-rag` ya está registrado. Usa
`ReasoningMode.TOP_LEVEL`, `SchemaPromptMode.REASONED_PYDANTIC` y
`FewShotMode.RAG`. La ruta de prompts de referencia delega al builder genérico
cuando detecta `few_shot=RAG`, de modo que el pipeline puede ejecutarse desde
el `OfficialParticipant` y el CLI normal.

## Garantías cubiertas

- El caso Quijote cultural renderiza exactamente el mismo FSP inline puro que
  `build_inline_reasoning_few_shot_example()`.
- El caso Quijote cultural no incluye el campo enriched
  `literary_impact_evidence`.
- El mismo caso base puede renderizar salida directa (`none`) o
  `{reasoning, value}` top-level.
- Los rótulos de reasoning (`EL CAMPO PIDE`, `FRAGMENTOS RELEVANTES`,
  `VALOR FINAL`) son configuración del renderer mediante
  `ReasoningSectionLabels`.
- `ReasoningMode.DEEP` queda fuera del provider RAG inicial.
- El provider RAG de extracción prioriza schema exacto, campos compatibles,
  tags derivados del schema, términos compartidos y dominio; si se define
  `max_prompt_chars`, omite ejemplos renderizados que excedan ese presupuesto
  y prueba el siguiente candidato rankeado.
- Cada ejemplo RAG renderizado incluye metadata de recuperación: score, rank,
  tags/términos coincidentes, match de schema y campos compatibles.
- `enriched-inline-reasoning-rag` usa el recurso editable puro del Quijote, sin
  `literary_impact_evidence`, dentro del bloque `EJEMPLOS FEW-SHOT`.
- Los labels hardcodeados del builder genérico de extracción están en español
  (`TAREA`, `INSTRUCCIÓN`, `REGLAS`, `TEXTO FUENTE`, `SALIDA`), para que la ruta
  RAG no mezcle instrucciones inglesas con prompts españoles.
- En campos array del juez, `empty_trial_count` se renderiza como observación
  del campo, no como candidato.
- Los `evidence` de candidatos array deben mencionar fragmentos verbatim
  concretos del texto fuente, con `[...]` si hace falta abreviar; no deben ser
  conclusiones genéricas del estilo "el texto respalda explícitamente...".
- La proyección recorta schema, `field_examples` y campos del juez, preservando
  `total_trials` y permitiendo incluir u ocultar `stable_fields`.
- `JudgeScope` usa ahora el helper común de schema projection, evitando duplicar
  esa lógica en `aggregation`.

## Verificación

Última corrida relevante:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_fsp_rag_examples.py tests\test_schema_prompt_modules.py tests\test_single_extraction_pipeline.py tests\test_multi_trial_runner.py tests\test_judge_aggregation.py -p no:cacheprovider
```

Resultado más reciente: `58 passed` en la suite amplia tocada; `14 passed` en
`tests/test_fsp_rag_examples.py`.

## Pendiente

### Retrieval inicial

- Afinar pesos del ranking cuando haya más recursos reales.
- Separar, si hace falta, los tags derivados automáticamente de tags curados por
  recurso/campo para poder auditar por qué se recuperó un ejemplo.
- Añadir modo `same_schema_only` si los experimentos muestran que ejemplos de
  schemas distintos distraen al modelo.
- Definir si `max_prompt_chars` debe venir de opciones del spec o de una futura
  variable dedicada; por ahora es parámetro del provider.

### Recursos editables

- Migrar próximos casos a `src/gensie/fsp/resources/cases/*.json`.
- Mantener equivalencia textual exacta cuando un recurso sustituya un FSP fijo
  validado.
- Completar validación de recursos si aparecen formas más complejas:
  referencias a `$defs`, campos requeridos ausentes de `field_examples`, arrays
  de objetos y variantes de juez más grandes.

### Extracción RAG

- Registrar un pipeline público sin reasoning, por ejemplo `baseline-rag`.
- Añadir más tests de prompt completo para `ReasoningMode.NONE`.
- Evaluar si el prompt genérico RAG debe acercarse más al estilo de referencia
  español para comparar mejor contra `enriched-inline-reasoning`.

### Juez RAG

- Implementar `RagJudgeFspProvider` para `reasoned_output`.
- Implementar `RagVerdictJudgeFspProvider` para `candidate_verdicts`.
- Conectar `AggregationSpec.options["judge_fsp"] == "rag"` en la factory del
  agregador.
- Usar `project_structured_fsp_case()` para renderizar solo los campos
  disputados cuando el caso recuperado tenga el mismo schema.
- Renderizar el FSP completo del juez, no solo `VALORES CANDIDATOS POR CAMPO`:
  instrucción, schema reducido, texto fuente, campos estables opcionales,
  candidatos y `SALIDA`.
- Respetar `GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS` y
  `GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS`.
- Dejar fuera inicialmente los reasonings de trials aunque
  `GENSIE_SC_JUDGE_INCLUDE_SCALAR_REASONINGS` y
  `GENSIE_SC_JUDGE_INCLUDE_ARRAY_REASONINGS` afecten el prompt real.

### Orden de candidatos

- Exponer `CandidateOrder` en providers/renderers del juez.
- Mantener `RESOURCE` para ejemplos fijos migrados.
- Usar `SUPPORT_DESC` para candidatos derivados de trials reales, con empates
  por `first_seen` y JSON canónico.
- Cubrir con tests que el orden cambia sin modificar el recurso.

### Metadata y tracing

- Guardar en metadata qué caso FSP se recuperó, score, tags, campos usados,
  modo de reasoning, variante de juez y orden de candidatos.
- Si tracing está activo, incluir esa metadata en el request/summary del step
  correspondiente.
- Evitar guardar textos grandes duplicados si ya están en el prompt trazado.
