# Analisis Mixed-SC vs single-call

Este documento compara las corridas existentes de self-consistency con los extractores single-call disponibles. No corre nuevos pipelines ni usa details internos.

Salidas principales:

- `analysis/mixed_sc_vs_single/mixed_sc_vs_single_overview.csv`
- `analysis/mixed_sc_vs_single/mixed_sc_vs_single_summary.csv`
- `analysis/mixed_sc_vs_single/mixed_sc_vs_single_task_deltas.csv`

## Resumen oficial

| short_model | reference_pipeline | task_count | official_reference_f1 | official_mixed_f1 | official_delta_f1 | improved_tasks | regressed_tasks | delta_tokens_avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | enriched-schema-rag | 145 | 0.748218 | 0.743363 | -0.004855 | 54 | 58 | 8766.476 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | 145 | 0.74445 | 0.743363 | -0.001087 | 48 | 55 | 5533.469 |
| qwen3-14b | enriched-schema-rag | 145 | 0.734163 | 0.747459 | 0.013296 | 63 | 55 | 7641.497 |

## Sin tasks con calls=0 en ambos lados

| short_model | reference_pipeline | both_calls_nonzero_task_count | nonzero_reference_f1 | nonzero_mixed_f1 | nonzero_delta_f1 |
| --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | enriched-schema-rag | 125 | 0.814046 | 0.818157 | 0.004111 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | 125 | 0.811025 | 0.818157 | 0.007132 |
| qwen3-14b | enriched-schema-rag | 125 | 0.807654 | 0.813804 | 0.00615 |

## Rutas de retrieval

| short_model | reference_pipeline | group | task_count | reference_f1 | mixed_f1 | delta_f1 | reference_tokens_avg | mixed_tokens_avg | reference_calls_zero | mixed_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | enriched-schema-rag | field_embeddings | 99 | 0.791127 | 0.777888 | -0.013239 | 6233.657 | 14691.949 | 8 | 9 |
| gemma-4-e4b-it | enriched-schema-rag | retrieval_failed | 10 | 0 | 0 | 0 | 0 | 0 | 10 | 10 |
| gemma-4-e4b-it | enriched-schema-rag | same_schema | 36 | 0.750586 | 0.770202 | 0.019616 | 2608.139 | 14657.25 | 0 | 1 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | field_embeddings | 99 | 0.77277 | 0.777888 | 0.005118 | 9939.596 | 14691.949 | 8 | 9 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | retrieval_failed | 10 | 0 | 0 | 0 | 0 | 0 | 10 | 10 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | same_schema | 36 | 0.78921 | 0.770202 | -0.019008 | 5438.639 | 14657.25 | 0 | 1 |
| qwen3-14b | enriched-schema-rag | field_embeddings | 99 | 0.782215 | 0.779993 | -0.002222 | 6354.818 | 13233.818 | 9 | 8 |
| qwen3-14b | enriched-schema-rag | retrieval_failed | 10 | 0 | 0 | 0 | 0 | 0 | 10 | 10 |
| qwen3-14b | enriched-schema-rag | same_schema | 36 | 0.719987 | 0.779138 | 0.059151 | 2851.611 | 14712.611 | 1 | 0 |

## Rutas de retrieval, calls>0 en ambos lados

| short_model | reference_pipeline | group | task_count | reference_f1 | mixed_f1 | delta_f1 | reference_tokens_avg | mixed_tokens_avg | reference_calls_zero | mixed_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | enriched-schema-rag | field_embeddings | 90 | 0.839894 | 0.829891 | -0.010003 | 6747.8 | 16161.144 | 0 | 0 |
| gemma-4-e4b-it | enriched-schema-rag | same_schema | 35 | 0.74155 | 0.785245 | 0.043695 | 2618.6 | 15076.029 | 0 | 0 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | field_embeddings | 90 | 0.820875 | 0.829891 | 0.009016 | 10792.578 | 16161.144 | 0 | 0 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | same_schema | 35 | 0.783687 | 0.785245 | 0.001558 | 5430.486 | 15076.029 | 0 | 0 |
| qwen3-14b | enriched-schema-rag | field_embeddings | 90 | 0.834508 | 0.827234 | -0.007274 | 6990.3 | 14403.533 | 0 | 0 |
| qwen3-14b | enriched-schema-rag | same_schema | 35 | 0.73378 | 0.776859 | 0.043079 | 2933.086 | 14702.429 | 0 | 0 |

## Seen vs unseen

| short_model | reference_pipeline | group | task_count | reference_f1 | mixed_f1 | delta_f1 | reference_tokens_avg | mixed_tokens_avg | reference_calls_zero | mixed_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | enriched-schema-rag | seen_schema | 36 | 0.750586 | 0.770202 | 0.019616 | 2608.139 | 14657.25 | 0 | 1 |
| gemma-4-e4b-it | enriched-schema-rag | unseen_schema | 109 | 0.747445 | 0.734725 | -0.01272 | 5661.761 | 13344.064 | 18 | 19 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | seen_schema | 36 | 0.78921 | 0.770202 | -0.019008 | 5438.639 | 14657.25 | 0 | 1 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | unseen_schema | 109 | 0.729706 | 0.734725 | 0.005019 | 9027.706 | 13344.064 | 18 | 19 |
| qwen3-14b | enriched-schema-rag | seen_schema | 36 | 0.719987 | 0.779138 | 0.059151 | 2851.611 | 14712.611 | 1 | 0 |
| qwen3-14b | enriched-schema-rag | unseen_schema | 109 | 0.738812 | 0.736926 | -0.001886 | 5771.807 | 12019.706 | 19 | 18 |

## Cobertura del par complementario

| short_model | reference_pipeline | group | task_count | reference_f1 | mixed_f1 | delta_f1 | reference_tokens_avg | mixed_tokens_avg | reference_calls_zero | mixed_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | enriched-schema-rag | coverage_gain_positive | 48 | 0.800189 | 0.794615 | -0.005574 | 5255.833 | 13691.917 | 8 | 8 |
| gemma-4-e4b-it | enriched-schema-rag | coverage_gain_zero | 51 | 0.781124 | 0.759219 | -0.021905 | 7153.961 | 15633.157 | 0 | 1 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | coverage_gain_positive | 48 | 0.770353 | 0.794615 | 0.024262 | 9373.479 | 13691.917 | 8 | 8 |
| gemma-4-e4b-it | enriched-inline-reasoning-rag | coverage_gain_zero | 51 | 0.775389 | 0.759219 | -0.01617 | 10472.412 | 15633.157 | 0 | 1 |
| qwen3-14b | enriched-schema-rag | coverage_gain_positive | 48 | 0.80266 | 0.8076 | 0.00494 | 5418.104 | 11145.417 | 8 | 8 |
| qwen3-14b | enriched-schema-rag | coverage_gain_zero | 51 | 0.759398 | 0.74952 | -0.009878 | 7236.431 | 15199.373 | 1 | 0 |

## Top mejoras y regresiones por task

### gemma-4-e4b-it: Mixed-SC vs enriched-inline-reasoning-rag

Mejoras:

| task_id | schema_title | route_group | seen_group | reference_f1 | mixed_f1 | delta_f1 | reference_system_minus_gold | mixed_system_minus_gold | reference_calls | mixed_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cultural_album_review_003 | AlbumReview | field_embeddings | unseen_schema | 0 | 0.92671 | 0.92671 | -7 | 0 | 1 | 2 |
| stem_observations_009 | ObservationLog | field_embeddings | unseen_schema | 0 | 0.879051 | 0.879051 | -8 | 0 | 1 | 1 |
| research_paper_argument_005 | PaperArgument | field_embeddings | unseen_schema | 0.627942 | 0.756762 | 0.128819 | 0 | 0 | 1 | 2 |
| test_general_disasters_005 | NewsArticle | same_schema | seen_schema | 0.626668 | 0.740516 | 0.113848 | 0 | 0 | 1 | 4 |
| test_legal_contracts_008 | ContractSummary | same_schema | seen_schema | 0.877234 | 0.988345 | 0.111111 | 0 | 0 | 1 | 3 |
| test_stem_astronomy_detailed_004 | CelestialObjectProperties | same_schema | seen_schema | 0.888889 | 1 | 0.111111 | 0 | 0 | 1 | 4 |
| medical_discharge_005 | DischargeSummary | field_embeddings | unseen_schema | 0.690155 | 0.79371 | 0.103555 | 0 | 0 | 1 | 2 |
| test_legal_judicial_004 | SentencingLogic | field_embeddings | unseen_schema | 0.641881 | 0.737167 | 0.095286 | 0 | 0 | 1 | 3 |

Regresiones:

| task_id | schema_title | route_group | seen_group | reference_f1 | mixed_f1 | delta_f1 | reference_system_minus_gold | mixed_system_minus_gold | reference_calls | mixed_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_general_disasters_006 | NewsArticle | same_schema | seen_schema | 0.9306 | 0 | -0.9306 | 0 | -10 | 1 | 0 |
| research_paper_argument_001 | PaperArgument | field_embeddings | unseen_schema | 0.750688 | 0 | -0.750688 | 0 | -8 | 1 | 0 |
| test_medical_diseases_006 | DiseaseProfile | same_schema | seen_schema | 0.402084 | 0.256586 | -0.145498 | 0 | 0 | 1 | 4 |
| test_technical_software_002 | SoftwareDescription | same_schema | seen_schema | 0.917056 | 0.787427 | -0.12963 | 0 | 0 | 1 | 4 |
| test_cultural_people_005 | ArtistProfile | field_embeddings | unseen_schema | 1 | 0.888889 | -0.111111 | 0 | 0 | 1 | 3 |
| test_environmental_assessments_005 | EnvironmentalRuling | field_embeddings | unseen_schema | 0.632138 | 0.521733 | -0.110404 | 0 | 0 | 1 | 1 |
| research_paper_argument_002 | PaperArgument | field_embeddings | unseen_schema | 0.758716 | 0.650255 | -0.108462 | 0 | 0 | 1 | 1 |
| test_general_disasters_007 | NewsArticle | same_schema | seen_schema | 0.876048 | 0.777808 | -0.098241 | 0 | 0 | 1 | 3 |

### gemma-4-e4b-it: Mixed-SC vs enriched-schema-rag

Mejoras:

| task_id | schema_title | route_group | seen_group | reference_f1 | mixed_f1 | delta_f1 | reference_system_minus_gold | mixed_system_minus_gold | reference_calls | mixed_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_general_disasters_003 | NewsArticle | same_schema | seen_schema | 0.53064 | 0.735228 | 0.204588 | 0 | 0 | 1 | 4 |
| test_cultural_entities_001 | NamedEntities | same_schema | seen_schema | 0.8 | 1 | 0.2 | 0 | 0 | 1 | 4 |
| test_legal_judicial_003 | SentencingLogic | field_embeddings | unseen_schema | 0.6 | 0.8 | 0.2 | 0 | 0 | 1 | 3 |
| test_cultural_literature_001 | LiteraryWork | same_schema | seen_schema | 0.754788 | 0.919682 | 0.164895 | 0 | 0 | 1 | 4 |
| test_cultural_media_002 | MediaReview | same_schema | seen_schema | 0.728492 | 0.88657 | 0.158079 | 0 | 0 | 1 | 3 |
| test_medical_diseases_005 | DiseaseProfile | same_schema | seen_schema | 0.519743 | 0.675656 | 0.155913 | 0 | 0 | 1 | 4 |
| test_medical_diseases_004 | DiseaseProfile | same_schema | seen_schema | 0.489928 | 0.631562 | 0.141634 | 0 | 0 | 1 | 3 |
| test_cultural_media_003 | MediaReview | same_schema | seen_schema | 0.733812 | 0.865923 | 0.132111 | 0 | 0 | 1 | 3 |

Regresiones:

| task_id | schema_title | route_group | seen_group | reference_f1 | mixed_f1 | delta_f1 | reference_system_minus_gold | mixed_system_minus_gold | reference_calls | mixed_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_general_disasters_006 | NewsArticle | same_schema | seen_schema | 0.981883 | 0 | -0.981883 | 0 | -10 | 1 | 0 |
| research_paper_argument_001 | PaperArgument | field_embeddings | unseen_schema | 0.765409 | 0 | -0.765409 | 0 | -8 | 1 | 0 |
| test_environmental_assessments_005 | EnvironmentalRuling | field_embeddings | unseen_schema | 0.755809 | 0.521733 | -0.234076 | 0 | 0 | 1 | 1 |
| test_technical_software_001 | SoftwareDescription | same_schema | seen_schema | 0.902564 | 0.737779 | -0.164785 | 0 | 0 | 1 | 3 |
| medical_discharge_006 | DischargeSummary | field_embeddings | unseen_schema | 0.877512 | 0.758204 | -0.119308 | 0 | 0 | 1 | 2 |
| test_cultural_people_004 | ArtistProfile | field_embeddings | unseen_schema | 1 | 0.888889 | -0.111111 | 0 | 0 | 1 | 3 |
| test_cultural_people_005 | ArtistProfile | field_embeddings | unseen_schema | 1 | 0.888889 | -0.111111 | 0 | 0 | 1 | 3 |
| test_legal_contracts_005 | ContractSummary | same_schema | seen_schema | 1 | 0.888889 | -0.111111 | 0 | 0 | 1 | 3 |

### qwen3-14b: Mixed-SC vs enriched-schema-rag

Mejoras:

| task_id | schema_title | route_group | seen_group | reference_f1 | mixed_f1 | delta_f1 | reference_system_minus_gold | mixed_system_minus_gold | reference_calls | mixed_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_general_disasters_006 | NewsArticle | same_schema | seen_schema | 0 | 0.838619 | 0.838619 | -10 | 0 | 0 | 3 |
| technical_security_incident_008 | SecurityIncident | field_embeddings | unseen_schema | 0 | 0.830052 | 0.830052 | -8 | 0 | 0 | 1 |
| test_legal_judicial_004 | SentencingLogic | field_embeddings | unseen_schema | 0.241608 | 0.635345 | 0.393738 | 0 | 0 | 1 | 3 |
| test_cultural_monuments_002 | MonumentBIC | same_schema | seen_schema | 0.56544 | 0.833333 | 0.267893 | 0 | 0 | 1 | 2 |
| test_stem_astronomy_detailed_004 | CelestialObjectProperties | same_schema | seen_schema | 0.666667 | 0.888889 | 0.222222 | 0 | 0 | 1 | 4 |
| test_cultural_monuments_003 | MonumentBIC | same_schema | seen_schema | 0.833333 | 1 | 0.166667 | 0 | 0 | 1 | 3 |
| test_medical_diseases_006 | DiseaseProfile | same_schema | seen_schema | 0.272917 | 0.437032 | 0.164115 | 0 | 0 | 1 | 4 |
| test_medical_diseases_005 | DiseaseProfile | same_schema | seen_schema | 0.380854 | 0.530329 | 0.149476 | 0 | 0 | 1 | 2 |

Regresiones:

| task_id | schema_title | route_group | seen_group | reference_f1 | mixed_f1 | delta_f1 | reference_system_minus_gold | mixed_system_minus_gold | reference_calls | mixed_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_legal_legislation_002 | LegalInquiry | field_embeddings | unseen_schema | 0.763579 | 0.064164 | -0.699415 | 0 | 0 | 1 | 4 |
| test_cultural_extraction_001 | TextAnswer | same_schema | seen_schema | 1 | 0.510601 | -0.489399 | 0 | 0 | 1 | 4 |
| test_environmental_assessments_006 | EnvironmentalRuling | field_embeddings | unseen_schema | 0.82573 | 0.574499 | -0.25123 | 0 | 0 | 1 | 2 |
| medical_discharge_009 | DischargeSummary | field_embeddings | unseen_schema | 0.86269 | 0.64886 | -0.21383 | 0 | 0 | 1 | 2 |
| test_legal_judicial_003 | SentencingLogic | field_embeddings | unseen_schema | 0.8 | 0.6 | -0.2 | 0 | 0 | 1 | 3 |
| research_paper_argument_008 | PaperArgument | field_embeddings | unseen_schema | 0.770983 | 0.571042 | -0.199941 | 0 | 0 | 1 | 1 |
| research_paper_argument_009 | PaperArgument | field_embeddings | unseen_schema | 0.664475 | 0.514265 | -0.150211 | 0 | 0 | 1 | 1 |
| test_environmental_assessments_007 | EnvironmentalRuling | field_embeddings | unseen_schema | 0.726641 | 0.589527 | -0.137115 | 0 | 0 | 1 | 2 |

## Lectura preliminar

- Mixed-SC se debe leer como trade-off de robustez contra costo: las tablas reportan delta F1 junto con delta de tokens y tiempo.
- La comparacion mas limpia por modelo es contra `enriched-schema-rag`; en Gemma tambien existe la comparacion contra `enriched-inline-reasoning-rag`.
- Las rutas same-schema y field-RAG se reportan separadas porque self-consistency no tiene el mismo comportamiento en ambos cortes.
