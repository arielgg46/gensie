# Analisis retrieval-only preliminar

Este documento resume una corrida de retrieval-only sobre `data/test`, sin
llamadas a modelos generativos. No esta escrito en tono de paper; es una nota
tecnica para decidir que tablas y cruces implementar despues.

## Artefactos generados

La corrida dejo estos archivos:

- `analysis/retrieval_only/retrieval_summary.json`
- `analysis/retrieval_only/retrieval_summary.md`
- `analysis/retrieval_only/test_retrieval_by_task.csv`
- `analysis/retrieval_only/test_retrieval_trace.json`
- `analysis/retrieval_only/retrieval_trace_check.md`

El archivo mas facil de auditar manualmente es
`analysis/retrieval_only/retrieval_trace_check.md`. El CSV es el punto de union
natural con `results/final_results*.json`.

## Metodo

El script `scripts/analyze_retrieval_only.py` usa la misma funcion principal del
sistema:

- `rank_fsp_cases_by_field_embeddings`
- `top_k=2`
- umbral same-schema `0.6`
- corpus FSP de `default_extraction_fsp_cases()`
- modelo de embeddings `BAAI/bge-small-en-v1.5`

Para que la corrida fuera rapida y reproducible, el script usa un wrapper de
cache sobre `FieldEmbedder`. La corrida completa proceso las 145 tasks en unos
22 segundos y cacheo 255 textos de embedding.

Para los casos sin ruta same-schema, el script calcula tambien una variante
diagnostica:

- retrieval oficial: par complementario;
- comparador: top-2 independiente por `field_score`, sin complementariedad.

Esto no corre ningun pipeline nuevo; solo compara dos decisiones de seleccion
de ejemplos sobre los mismos embeddings.

## Resumen global

| grupo | tasks | porcentaje |
| --- | ---: | ---: |
| total test | 145 | 100.0% |
| ruta same-schema oficial | 36 | 24.8% |
| ruta no-same-schema total | 109 | 75.2% |
| field-embedding fallback con diagnosticos de par | 99 | 68.3% |
| retrieval fallido tras fallback | 10 | 6.9% |

Los 36 casos con mismo schema estructural en el corpus FSP entran todos por la
ruta same-schema. No hubo casos con schema estructural compartido que cayeran al
fallback de campos por no superar el umbral.

## Ruta same-schema

La ruta same-schema cubre 36 tasks. Las similitudes son altas:

| estadistico | selected min similarity |
| --- | ---: |
| min | 0.861286 |
| p25 | 0.952150 |
| mean | 0.958284 |
| median | 0.971718 |
| p75 | 0.980835 |
| max | 0.992740 |

Por schema title, los casos same-schema se distribuyen asi:

| schema | tasks |
| --- | ---: |
| NewsArticle | 7 |
| DiseaseProfile | 6 |
| LiteraryWork | 5 |
| CelestialObjectProperties | 5 |
| MediaReview | 3 |
| ContractSummary | 3 |
| TextAnswer | 2 |
| MonumentBIC | 2 |
| SoftwareDescription | 2 |
| NamedEntities | 1 |

Hay dos patrones de disponibilidad:

- 26 tasks tienen exactamente 2 candidatos same-schema en el corpus.
- 10 tasks tienen 8 candidatos same-schema. Esto ocurre en schemas genericos
  compartidos por varios dominios, como `TextAnswer` y `NamedEntities`.

Lectura preliminar: cuando el schema esta cubierto por el corpus, el mecanismo
same-schema parece estable. La seleccion no depende solo del fingerprint; usa
similitud de instruccion/texto global para ordenar candidatos dentro del mismo
schema.

## Ruta field-RAG en casos sin same-schema

De los 109 casos sin ruta same-schema, 99 producen diagnosticos completos de
field embeddings. En esos 99:

- el par complementario oficial difiere del top-2 independiente en 99/99 casos;
- el pair score del par oficial es mayor en 99/99 casos;
- el top-2 independiente conserva mayor suma de field scores en 99/99 casos;
- la cobertura de campos mejora en 48/99 casos y queda igual en 51/99.

Distribuciones clave:

| metrica | min | p25 | mean | median | p75 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pair-score gain vs top-2 independiente | 0.513803 | 0.660404 | 0.785784 | 0.707351 | 0.920162 | 1.103806 |
| perdida de suma de field score vs top-2 independiente | 0.034685 | 0.138033 | 0.245730 | 0.246109 | 0.349033 | 0.527373 |
| ganancia de cobertura de campos | 0.000000 | 0.000000 | 0.066366 | 0.000000 | 0.111111 | 0.250000 |

Lectura preliminar: el retrieval complementario esta haciendo exactamente el
trade-off previsto. Sacrifica similitud individual agregada para escoger dos
ejemplos mas diversos/complementarios. La ganancia de cobertura no aparece en
todos los casos, pero cuando aparece puede llegar a 25 puntos porcentuales de
cobertura relativa de campos.

## Casos con fallo de retrieval

Hay 10 tasks con `retrieval_failed_after_error`:

- `test_stem_biology_001` a `test_stem_biology_010`
- schema title: `TaxonomicClassification`
- dominio: `stem_biology`
- error principal: `maximum recursion depth exceeded`

Estos schemas son recursivos o efectivamente recursivos para el parser de
campos (`task_field_specs`). El fallback lexico tambien falla para ellos, de
modo que el script los conserva con seleccion vacia.

Esto es importante para el paper porque separa dos cosas:

- hay 109 tasks sin same-schema;
- pero solo 99 tienen diagnosticos field-RAG completos;
- los 10 restantes revelan una limitacion estructural del analizador de campos,
  no del modelo generativo.

Tambien es una pista para explicar parte de los `calls=0` ya observados en los
resultados finales, aunque no todos los `calls=0` se explican por esto: los
`medical_trials` no fallan en retrieval-only y aun asi aparecian entre los casos
problematicos de ejecucion.

## Sesgo de seleccion de ejemplos FSP

El retrieval field-RAG selecciona repetidamente algunos casos del corpus. En la
ruta field embeddings, los mas frecuentes son:

| caso FSP | selecciones |
| --- | ---: |
| `medical_diseases_faringitis_estreptococica` | 40 |
| `medical_drug_ibuprofeno_lumen` | 31 |
| `legal_contracts_compraventa_maquinaria_agricola` | 21 |
| `cultural_media_mixed_series` | 20 |
| `environmental_ecology_derrame_rio_san_juan` | 20 |
| `cultural_literature_ciudad_espejos` | 15 |
| `stem_astronomy_detailed_marte` | 15 |
| `legal_legislation_patios_verdes_valenciana` | 13 |
| `cultural_monuments_abrigos_solana` | 13 |
| `lifestyle_recipes_berenjenas_tahini` | 10 |

Esto merece revision: puede ser una virtud si esos ejemplos cubren tipos de
campo frecuentes, pero tambien puede indicar que el corpus FSP es pequeno y que
ciertos schemas funcionan como hubs genericos. Para el analisis con resultados
finales conviene cruzar performance por:

- caso FSP seleccionado;
- dominio del caso FSP seleccionado;
- si los dos ejemplos seleccionados vienen del mismo dominio o de dominios
  distintos;
- cobertura de campos del par.

## Distribucion por dominio test

Dominios completamente cubiertos por same-schema:

- `general_disasters`
- `medical_diseases`
- `cultural_literature`
- `cultural_media`
- `legal_contracts`
- `stem_astronomy_detailed`
- `cultural_extraction`
- `cultural_monuments`
- `stem_astronomy`
- `technical_software`
- `cultural_entities`

Dominios completamente por field-RAG:

- `cultural_album_review`
- `cultural_people`
- `cultural_theater`
- `environmental_assessments`
- `legal_case_timeline`
- `legal_judicial`
- `legal_legislation`
- `medical_discharge`
- `medical_trials`
- `research_paper_argument`
- `stem_observations`
- `technical_security_incident`

Dominio con fallo estructural completo:

- `stem_biology` (`TaxonomicClassification`): 10/10 fallan en retrieval.

## Trazabilidad manual

`retrieval_trace_check.md` muestra ejemplos compactos. Algunos casos utiles
para revisar:

- `test_cultural_extraction_002`: ruta same-schema con 8 candidatos y
  similitudes relativamente bajas dentro del grupo same-schema.
- `test_technical_software_002`: ruta same-schema con exactamente 2 candidatos.
- `cultural_album_review_001`: ruta field-RAG donde el par complementario cubre
  100% de campos frente a 75% del top-2 independiente.
- `test_stem_biology_001`: caso fallido por recursividad, visible en el CSV.

## Implicaciones para los siguientes cruces

El siguiente script deberia unir `test_retrieval_by_task.csv` con
`results/final_results*.json`. Las agrupaciones mas importantes serian:

- same-schema vs field-RAG vs retrieval-failed;
- bins de similitud same-schema;
- bins de pair-score gain;
- bins de cobertura de campos;
- si el par complementario mejora cobertura o no;
- caso FSP seleccionado;
- dominio del FSP seleccionado;
- dominio test.

Metricas por grupo:

- F1, precision, recall usando `tps`, `gold_keys`, `system_keys`;
- tokens promedio;
- tiempo promedio;
- `calls=0`;
- `system_keys - gold_keys`.

Esto permitiria convertir el retrieval-only en evidencia experimental indirecta
sin correr nuevos pipelines.
