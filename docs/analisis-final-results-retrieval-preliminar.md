# Analisis final_results cruzado con retrieval

Este documento resume el cruce entre:

- `analysis/retrieval_only/test_retrieval_by_task.csv`
- `results/final_results*.json`

No usa details por task ni vuelve a correr modelos. Las metricas se recomputan
micro-agregando `tps`, `gold_keys` y `system_keys` desde los `final_results`.

## Artefactos generados

El script usado fue:

- `scripts/analyze_final_results_with_retrieval.py`

Salidas:

- `analysis/final_results_retrieval/joined_task_metrics.csv`
- `analysis/final_results_retrieval/run_summary.csv`
- `analysis/final_results_retrieval/run_summary_calls_nonzero.csv`
- `analysis/final_results_retrieval/retrieval_group_metrics.csv`
- `analysis/final_results_retrieval/retrieval_group_metrics_calls_nonzero.csv`
- `analysis/final_results_retrieval/retrieval_group_metrics.json`
- `analysis/final_results_retrieval/retrieval_group_metrics.md`
- `analysis/final_results_retrieval/selected_case_metrics.csv`

El join cubrio 7 corridas y 1015 filas task-run, sin warnings de `task_id`
faltantes.

## Lectura global

Metricas oficiales sobre las 145 tasks:

| run | F1 | precision | recall | avg tokens | calls=0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemma baseline | 0.669154 | 0.702199 | 0.639080 | 3690.779 | 18 |
| Gemma enriched-schema-rag | 0.748218 | 0.804799 | 0.699069 | 4903.621 | 18 |
| Gemma enriched-inline-reasoning-rag | 0.744450 | 0.807240 | 0.690724 | 8136.628 | 18 |
| Gemma Mixed-SC RAG | 0.743363 | 0.807381 | 0.688751 | 13670.097 | 20 |
| Qwen baseline | 0.640133 | 0.699489 | 0.590062 | 3670.579 | 18 |
| Qwen enriched-schema-rag | 0.734163 | 0.793073 | 0.683400 | 5046.793 | 20 |
| Qwen Mixed-SC RAG | 0.747459 | 0.799745 | 0.701591 | 12688.290 | 18 |

Lectura preliminar:

- RAG mejora claramente a baseline en ambos modelos.
- En Gemma, `enriched-schema-rag` es el mejor single-call y supera levemente al
  extractor con reasoning.
- En Qwen, Mixed-SC mejora a `enriched-schema-rag` en el agregado, pero con
  mucho mas costo.
- Los `calls=0` pesan mucho en el F1 oficial; por eso tambien se generaron
  tablas `calls>0`.

## Rutas de retrieval

Metricas oficiales por ruta:

| run | same-schema F1 | field-RAG F1 | retrieval-failed F1 |
| --- | ---: | ---: | ---: |
| Gemma baseline | 0.652812 | 0.708866 | 0.000000 |
| Gemma enriched-schema-rag | 0.750586 | 0.791127 | 0.000000 |
| Gemma enriched-inline-reasoning-rag | 0.789210 | 0.772770 | 0.000000 |
| Gemma Mixed-SC RAG | 0.770202 | 0.777888 | 0.000000 |
| Qwen baseline | 0.587996 | 0.690821 | 0.000000 |
| Qwen enriched-schema-rag | 0.719987 | 0.782215 | 0.000000 |
| Qwen Mixed-SC RAG | 0.779138 | 0.779993 | 0.000000 |

Los 10 `retrieval_failed` son los `stem_biology` con schema
`TaxonomicClassification`; en todas las corridas tienen `calls=0`, por eso el
grupo tiene F1 0. Este grupo debe tratarse como fallo estructural de ejecucion o
preprocesamiento, no como evidencia contra RAG.

En las rutas con respuesta (`calls>0`), el panorama queda:

| run | same-schema F1 | field-RAG F1 |
| --- | ---: | ---: |
| Gemma baseline | 0.652812 | 0.746773 |
| Gemma enriched-schema-rag | 0.750586 | 0.839074 |
| Gemma enriched-inline-reasoning-rag | 0.789210 | 0.820094 |
| Gemma Mixed-SC RAG | 0.785245 | 0.829891 |
| Qwen baseline | 0.587996 | 0.728700 |
| Qwen enriched-schema-rag | 0.733780 | 0.834508 |
| Qwen Mixed-SC RAG | 0.779138 | 0.827265 |

Lectura preliminar:

- RAG mejora tanto en same-schema como en field-RAG.
- La ruta field-RAG tiene F1 mayor que same-schema en casi todas las corridas,
  pero esto esta influido por composicion de schemas: same-schema y non-same no
  contienen los mismos tipos de tareas.
- En `calls>0`, `enriched-schema-rag` es muy fuerte en field-RAG para ambos
  modelos.

## Delta de RAG sobre baseline

Delta F1 de `enriched-schema-rag` sobre baseline:

| modelo | all | same-schema | field-RAG |
| --- | ---: | ---: | ---: |
| Gemma | +0.079064 | +0.097774 | +0.082261 |
| Qwen | +0.094030 | +0.131991 | +0.091394 |

En `calls>0`, el delta field-RAG aumenta:

| modelo | field-RAG calls>0 |
| --- | ---: |
| Gemma | +0.092301 |
| Qwen | +0.105808 |

Lectura preliminar: RAG no esta ganando solo por los schemas vistos/same-schema.
Tambien mejora claramente en schemas sin same-schema cuando el retrieval por
campos produce ejemplos.

## Reasoning en Gemma

Comparacion Gemma `enriched-inline-reasoning-rag` vs
`enriched-schema-rag`:

| subset | delta F1 |
| --- | ---: |
| all | -0.003768 |
| same-schema | +0.038624 |
| field-RAG | -0.018357 |

En `calls>0`, la lectura se mantiene: reasoning ayuda en same-schema, pero
queda por debajo del schema RAG directo en field-RAG.

Hipotesis preliminar: el reasoning top-level puede ayudar cuando el ejemplo FSP
comparte exactamente el contrato estructural, pero puede introducir costo y
friccion cuando los ejemplos son complementarios y no homologos. Esto todavia
no es causal; es una lectura por subset con resultados existentes.

## Mixed-SC

Delta F1 de Mixed-SC RAG respecto a `enriched-schema-rag`:

| modelo | all | same-schema | field-RAG |
| --- | ---: | ---: | ---: |
| Gemma | -0.004855 | +0.019616 | -0.013239 |
| Qwen | +0.013296 | +0.059151 | -0.002222 |

Lectura preliminar:

- Mixed-SC parece aportar mas en same-schema que en field-RAG.
- En field-RAG no mejora al single-call `enriched-schema-rag` en estas corridas.
- El costo es alto: ~13K tokens promedio por task frente a ~5K del RAG
  single-call.
- En Qwen, el agregado global mejora porque same-schema gana bastante y el
  field-RAG cae muy poco.
- En Gemma, el costo extra no se traduce en mejora global.

## Complementariedad y cobertura

El retrieval-only habia mostrado que, en los 99 casos field-RAG con diagnosticos
completos:

- el par complementario difiere del top-2 independiente en 99/99;
- aumenta pair-score en 99/99;
- mejora cobertura de campos en 48/99;
- mantiene cobertura en 51/99.

Al cruzar con resultados:

| run | coverage gain zero F1 | coverage gain positive F1 |
| --- | ---: | ---: |
| Gemma enriched-schema-rag | 0.781124 | 0.800189 |
| Qwen enriched-schema-rag | 0.759398 | 0.802660 |

Pero este corte incluye `calls=0` en `ClinicalTrialRecord`, que pertenece al
grupo con ganancia de cobertura. En `calls>0`:

| run | coverage gain zero F1 | coverage gain positive F1 |
| --- | ---: | ---: |
| Gemma enriched-schema-rag | 0.781124 | 0.897989 |
| Qwen enriched-schema-rag | 0.767883 | 0.900763 |

Lectura preliminar: cuando la ejecucion no falla, los casos donde el par
complementario aumenta cobertura son muy fuertes para el RAG single-call. Aun
asi, esto esta fuertemente determinado por schemas concretos:

- cobertura positiva: `AlbumReview`, `TheaterPlaybill`, `DischargeSummary`,
  `ObservationLog`, `ClinicalTrialRecord`;
- cobertura cero: `CourtCaseTimeline`, `SecurityIncident`, `PaperArgument`,
  `EnvironmentalRuling`, `LegalInquiry`, `ArtistProfile`, `SentencingLogic`.

No conviene presentar esto como prueba causal de la cobertura sin controlar por
schema.

## Pair-gain tertiles

Los bins de pair-score gain muestran un grupo medio muy bajo, pero esta lectura
esta confunde retrieval y fallos:

- el tercil medio incluye los 8 `ClinicalTrialRecord` con `calls=0`;
- despues de excluir `calls=0`, el tercil medio queda con `EnvironmentalRuling`
  y `SentencingLogic`, que tambien son schemas relativamente dificiles.

Por tanto, los tertiles de pair-gain son utiles para diagnostico, pero no deben
leerse solos como "mas complementariedad implica mejor F1".

## Fallos calls=0

Patron principal:

- 18 `calls=0` comunes: 10 `TaxonomicClassification` y 8
  `ClinicalTrialRecord`.
- Los 10 `TaxonomicClassification` coinciden con `retrieval_failed_after_error`
  en retrieval-only.
- Los 8 `ClinicalTrialRecord` no fallan en retrieval-only; son fallos de
  ejecucion/pipeline posteriores.

Fallos extra:

- Gemma Mixed-SC: +2 (`test_general_disasters_006`,
  `research_paper_argument_001`).
- Qwen enriched-schema-rag: +2 (`technical_security_incident_008`,
  `test_general_disasters_006`).

Esto sugiere que conviene reportar metricas oficiales y tambien una vista sin
`calls=0`, porque los fallos de ejecucion dominan ciertos cortes de retrieval.

## Hubs FSP y performance

El CSV `selected_case_metrics.csv` permite ver performance de tasks que
seleccionaron cada ejemplo FSP. Los casos mas frecuentes en field-RAG aparecen
en muchos subsets y no son mutuamente excluyentes.

Ejemplos de hubs:

- `medical_diseases_faringitis_estreptococica`
- `medical_drug_ibuprofeno_lumen`
- `legal_contracts_compraventa_maquinaria_agricola`
- `cultural_media_mixed_series`
- `environmental_ecology_derrame_rio_san_juan`
- `stem_astronomy_detailed_marte`

Lectura preliminar: algunos ejemplos funcionan como "prototipos" estructurales
para muchos schemas sin same-schema. Para el paper conviene reportar esta
concentracion como propiedad del retrieval, pero no necesariamente como problema
si los resultados en esos grupos son altos.

## Conclusiones de trabajo

1. RAG mejora baseline tanto en same-schema como en field-RAG.
2. Same-schema no explica toda la ganancia; field-RAG tambien aporta.
3. Reasoning en Gemma parece beneficiar same-schema, pero no field-RAG.
4. Mixed-SC ayuda sobre todo en same-schema; no supera claramente al single-call
   en field-RAG.
5. Los fallos `calls=0` son una capa separada que debe aislarse en analisis.
6. Los bins de cobertura/pair-gain son prometedores, pero estan confudidos con
   schema type y fallos de ejecucion.

Siguiente paso recomendado: preparar tablas mas limpias para RAG vs baseline y
Mixed-SC vs single-call por rutas de retrieval, con columnas oficiales y
`calls>0`.
