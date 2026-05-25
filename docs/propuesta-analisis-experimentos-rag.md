# Propuesta breve: análisis de experimentos RAG

## Objetivo

Consolidar las corridas completas de `qwen/qwen3-14b` para comparar
`enriched-schema-rag` y `enriched-inline-reasoning-rag` sobre las tasks de
`data/golden_cover`, usando tanto sus corridas directas como las extracciones
individuales disponibles dentro de `mixed-extractors-self-consistency-rag`.

## Entradas

- `data/golden_cover`: lista canónica de tasks a analizar.
- `data/dev`: superconjunto usado solo para recuperar la corrida directa de dev
  correspondiente a cada task de `golden_cover`.
- Corridas directas:
  - `local-results/enriched-schema-rag/20260522-171113`
  - `local-results/enriched-schema-rag/20260522-171628`
  - `local-results/enriched-inline-reasoning-rag/20260522-173426`
  - `local-results/enriched-inline-reasoning-rag/20260522-174255`
- Corrida mixta:
  - `local-results/mixed-extractors-self-consistency-rag/20260522-183416`

## Salidas Propuestas

Crear una carpeta de análisis, por ejemplo:

`analysis/qwen3-14b-rag-golden-cover/`

Dentro:

- `run_counts.json`: por cada task de `golden_cover`, número efectivo de
  corridas de cada extractor base.
- `predictions/enriched-schema-rag/<task_id>/<run_id>.json`
- `predictions/enriched-inline-reasoning-rag/<task_id>/<run_id>.json`
- `metrics/by_schema.json`
- `metrics/by_prefix.json`
- `metrics/by_field_tag.json`
- `summary.md`: resumen legible de hallazgos.

## Conteo y Extracción de Predicciones

Para cada task de `data/golden_cover`:

1. Tomar la predicción directa de la corrida sobre `golden_cover`, si existe.
2. Tomar la predicción directa de la corrida sobre `data/dev`, si existe para el
   mismo `task_id`.
3. Recorrer los steps `self_consistency_trial_*` de la corrida mixta.
4. Leer `summary.json` y usar `request_metadata.extraction` para asignar cada
   trial a `enriched-schema-rag` o `enriched-inline-reasoning-rag`.
5. Contar solo trials con `summary.error == null` y `response.json.final_output`
   disponible.
6. Guardar cada `final_output` como un JSON separado con un `run_id` estable,
   por ejemplo `golden_direct`, `dev_direct`, `mixed_trial_01`.

## Métricas

Usar `Evaluator.score_instance` y las funciones existentes de evaluación para
calcular precision, recall y F1 agregadas.

Agrupaciones:

- Por `description/schema`: agrupar por descripción del `target_schema` y, si
  hace falta desambiguar, por fingerprint normalizado del schema.
- Por prefijo: derivar desde `task_id`, removiendo el sufijo numérico final
  (`medical_diseases_001` -> `medical_diseases`).
- Por field tag: para cada campo de primer nivel, obtener tags con
  `src/gensie/fsp/retrieval.py::_field_tags`; evaluar el campo aislado contra
  su gold y promediar el score por tag (`nullable`, `enum_classification`,
  `numeric_normalization`, `boolean_inference`, `date_normalization`,
  `long_verbatim_evidence`, `simple_array`, `complex_object_array`,
  `entity_array`, etc.).

## Criterios

- `data/golden_cover` manda: no analizar tasks que no estén ahí.
- Las corridas directas y los trials mixtos se tratan como muestras separadas
  del extractor base que las produjo.
- El output usado para scoring siempre debe ser `final_output`, no
  `parsed_output` ni el `content` crudo.
- La corrida mixta no se evalúa como agregador aquí; se usa para rescatar sus
  extracciones base individuales.
