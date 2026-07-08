# Analisis RAG vs baseline

Este documento cruza resultados ya existentes. No corre pipelines nuevos ni usa details por campo.

Entradas:

- `analysis/final_results_retrieval/joined_task_metrics.csv`
- `analysis/test_schema_subsets/schema_overlap.json`

Salidas principales:

- `analysis/rag_vs_baseline/rag_vs_baseline_overview.csv`
- `analysis/rag_vs_baseline/rag_vs_baseline_summary.csv`
- `analysis/rag_vs_baseline/rag_vs_baseline_task_deltas.csv`

## Resumen oficial

| short_model | task_count | official_baseline_f1 | official_rag_f1 | official_delta_f1 | improved_tasks | regressed_tasks | delta_tokens_avg |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | 145 | 0.669154 | 0.748218 | 0.079064 | 112 | 13 | 1212.842 |
| qwen3-14b | 145 | 0.640133 | 0.734163 | 0.09403 | 111 | 14 | 1376.214 |

## Sin tasks con calls=0 en ambos lados

| short_model | both_calls_nonzero_task_count | nonzero_baseline_f1 | nonzero_rag_f1 | nonzero_delta_f1 |
| --- | --- | --- | --- | --- |
| gemma-4-e4b-it | 127 | 0.721381 | 0.815346 | 0.093965 |
| qwen3-14b | 125 | 0.688732 | 0.807654 | 0.118922 |

## Seen vs unseen

| short_model | group | task_count | baseline_f1 | rag_f1 | delta_f1 | baseline_precision | rag_precision | baseline_recall | rag_recall | baseline_calls_zero | rag_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | seen_schema | 36 | 0.652812 | 0.750586 | 0.097774 | 0.638972 | 0.764965 | 0.667265 | 0.736737 | 0 | 0 |
| gemma-4-e4b-it | unseen_schema | 109 | 0.674621 | 0.747445 | 0.072824 | 0.725437 | 0.818773 | 0.630458 | 0.687548 | 18 | 18 |
| qwen3-14b | seen_schema | 36 | 0.587996 | 0.719987 | 0.131991 | 0.621873 | 0.73378 | 0.55762 | 0.706703 | 0 | 1 |
| qwen3-14b | unseen_schema | 109 | 0.656685 | 0.738812 | 0.082127 | 0.72522 | 0.814099 | 0.599985 | 0.676272 | 18 | 19 |

## Seen vs unseen, calls>0 en ambos lados

| short_model | group | task_count | baseline_f1 | rag_f1 | delta_f1 | baseline_precision | rag_precision | baseline_recall | rag_recall | baseline_calls_zero | rag_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | seen_schema | 36 | 0.652812 | 0.750586 | 0.097774 | 0.638972 | 0.764965 | 0.667265 | 0.736737 | 0 | 0 |
| gemma-4-e4b-it | unseen_schema | 91 | 0.746773 | 0.839074 | 0.092301 | 0.725437 | 0.839074 | 0.769402 | 0.839074 | 0 | 0 |
| qwen3-14b | seen_schema | 35 | 0.574918 | 0.73378 | 0.158862 | 0.61085 | 0.73378 | 0.542978 | 0.73378 | 0 | 0 |
| qwen3-14b | unseen_schema | 90 | 0.727616 | 0.834508 | 0.106892 | 0.724103 | 0.834508 | 0.731163 | 0.834508 | 0 | 0 |

## Rutas de retrieval

| short_model | group | task_count | baseline_f1 | rag_f1 | delta_f1 | baseline_precision | rag_precision | baseline_recall | rag_recall | baseline_calls_zero | rag_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | field_embeddings | 99 | 0.708866 | 0.791127 | 0.082261 | 0.725437 | 0.829928 | 0.693035 | 0.755791 | 8 | 8 |
| gemma-4-e4b-it | retrieval_failed | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 10 |
| gemma-4-e4b-it | same_schema | 36 | 0.652812 | 0.750586 | 0.097774 | 0.638972 | 0.764965 | 0.667265 | 0.736737 | 0 | 0 |
| qwen3-14b | field_embeddings | 99 | 0.690821 | 0.782215 | 0.091394 | 0.72522 | 0.825312 | 0.659537 | 0.743395 | 8 | 9 |
| qwen3-14b | retrieval_failed | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 10 |
| qwen3-14b | same_schema | 36 | 0.587996 | 0.719987 | 0.131991 | 0.621873 | 0.73378 | 0.55762 | 0.706703 | 0 | 1 |

## Rutas de retrieval, calls>0 en ambos lados

| short_model | group | task_count | baseline_f1 | rag_f1 | delta_f1 | baseline_precision | rag_precision | baseline_recall | rag_recall | baseline_calls_zero | rag_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | field_embeddings | 91 | 0.746773 | 0.839074 | 0.092301 | 0.725437 | 0.839074 | 0.769402 | 0.839074 | 0 | 0 |
| gemma-4-e4b-it | same_schema | 36 | 0.652812 | 0.750586 | 0.097774 | 0.638972 | 0.764965 | 0.667265 | 0.736737 | 0 | 0 |
| qwen3-14b | field_embeddings | 90 | 0.727616 | 0.834508 | 0.106892 | 0.724103 | 0.834508 | 0.731163 | 0.834508 | 0 | 0 |
| qwen3-14b | same_schema | 35 | 0.574918 | 0.73378 | 0.158862 | 0.61085 | 0.73378 | 0.542978 | 0.73378 | 0 | 0 |

## Complejidad por gold keys

| short_model | group | task_count | baseline_f1 | rag_f1 | delta_f1 | baseline_precision | rag_precision | baseline_recall | rag_recall | baseline_calls_zero | rag_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | gold_keys_01_05 | 12 | 0.667947 | 0.714202 | 0.046255 | 0.601152 | 0.714202 | 0.75144 | 0.714202 | 0 | 0 |
| gemma-4-e4b-it | gold_keys_06_08 | 80 | 0.649659 | 0.711095 | 0.061436 | 0.664528 | 0.766433 | 0.635441 | 0.66321 | 10 | 10 |
| gemma-4-e4b-it | gold_keys_09_plus | 53 | 0.693392 | 0.794561 | 0.101169 | 0.76681 | 0.85913 | 0.632804 | 0.739019 | 8 | 8 |
| qwen3-14b | gold_keys_01_05 | 12 | 0.589666 | 0.709136 | 0.11947 | 0.547547 | 0.709136 | 0.638805 | 0.709136 | 0 | 0 |
| qwen3-14b | gold_keys_06_08 | 80 | 0.66651 | 0.713802 | 0.047292 | 0.689287 | 0.767752 | 0.645191 | 0.666936 | 10 | 11 |
| qwen3-14b | gold_keys_09_plus | 53 | 0.611594 | 0.760538 | 0.148944 | 0.738449 | 0.832552 | 0.521933 | 0.69999 | 8 | 9 |

## Complejidad por numero de campos

| short_model | group | task_count | baseline_f1 | rag_f1 | delta_f1 | baseline_precision | rag_precision | baseline_recall | rag_recall | baseline_calls_zero | rag_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | fields_01_03 | 13 | 0.062921 | 0.040401 | -0.02252 | 0.466667 | 0.149173 | 0.033735 | 0.023364 | 10 | 10 |
| gemma-4-e4b-it | fields_04_06 | 32 | 0.588381 | 0.677963 | 0.089582 | 0.559397 | 0.697557 | 0.620533 | 0.659439 | 0 | 0 |
| gemma-4-e4b-it | fields_07_plus | 100 | 0.718222 | 0.802581 | 0.084359 | 0.73822 | 0.837859 | 0.699279 | 0.770153 | 8 | 8 |
| qwen3-14b | fields_01_03 | 13 | 0.036948 | 0.051154 | 0.014206 | 0.325139 | 0.188877 | 0.019587 | 0.029583 | 10 | 10 |
| qwen3-14b | fields_04_06 | 32 | 0.628463 | 0.68568 | 0.057217 | 0.593379 | 0.68568 | 0.667956 | 0.68568 | 0 | 0 |
| qwen3-14b | fields_07_plus | 100 | 0.674927 | 0.783402 | 0.108475 | 0.73051 | 0.827414 | 0.627205 | 0.743837 | 8 | 10 |

## Cobertura del par complementario

| short_model | group | task_count | baseline_f1 | rag_f1 | delta_f1 | baseline_precision | rag_precision | baseline_recall | rag_recall | baseline_calls_zero | rag_calls_zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemma-4-e4b-it | coverage_gain_positive | 48 | 0.698339 | 0.800189 | 0.10185 | 0.775932 | 0.878468 | 0.634854 | 0.734719 | 8 | 8 |
| gemma-4-e4b-it | coverage_gain_zero | 51 | 0.719718 | 0.781124 | 0.061406 | 0.681099 | 0.781124 | 0.76298 | 0.781124 | 0 | 0 |
| qwen3-14b | coverage_gain_positive | 48 | 0.706979 | 0.80266 | 0.095681 | 0.786735 | 0.881181 | 0.641904 | 0.736988 | 8 | 8 |
| qwen3-14b | coverage_gain_zero | 51 | 0.673374 | 0.759398 | 0.086024 | 0.666173 | 0.767883 | 0.680734 | 0.751099 | 0 | 1 |

## Top mejoras y regresiones por task

### gemma-4-e4b-it: enriched-schema-rag vs baseline

Mejoras:

| task_id | schema_title | route_group | seen_group | baseline_f1 | rag_f1 | delta_f1 | baseline_system_minus_gold | rag_system_minus_gold | baseline_calls | rag_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_stem_astronomy_002 | CelestialObjectProperties | same_schema | seen_schema | 0.648722 | 1 | 0.351278 | -3 | 0 | 1 | 1 |
| test_cultural_literature_001 | LiteraryWork | same_schema | seen_schema | 0.42003 | 0.754788 | 0.334758 | 1 | 0 | 1 | 1 |
| test_legal_contracts_008 | ContractSummary | same_schema | seen_schema | 0.666667 | 1 | 0.333333 | 0 | 0 | 1 | 1 |
| test_general_disasters_006 | NewsArticle | same_schema | seen_schema | 0.678399 | 0.981883 | 0.303484 | -3 | 0 | 1 | 1 |
| cultural_theater_002 | TheaterPlaybill | field_embeddings | unseen_schema | 0.682463 | 0.983734 | 0.301271 | -3 | 0 | 1 | 1 |
| cultural_theater_005 | TheaterPlaybill | field_embeddings | unseen_schema | 0.715553 | 0.990736 | 0.275183 | -3 | 0 | 1 | 1 |
| cultural_theater_003 | TheaterPlaybill | field_embeddings | unseen_schema | 0.706471 | 0.980172 | 0.273701 | -3 | 0 | 1 | 1 |
| cultural_theater_001 | TheaterPlaybill | field_embeddings | unseen_schema | 0.727273 | 1 | 0.272727 | -3 | 0 | 1 | 1 |

Regresiones:

| task_id | schema_title | route_group | seen_group | baseline_f1 | rag_f1 | delta_f1 | baseline_system_minus_gold | rag_system_minus_gold | baseline_calls | rag_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_cultural_extraction_001 | TextAnswer | same_schema | seen_schema | 0.666667 | 0.483846 | -0.18282 | 1 | 0 | 1 | 1 |
| test_general_disasters_003 | NewsArticle | same_schema | seen_schema | 0.695517 | 0.53064 | -0.164877 | 1 | 0 | 1 | 1 |
| test_stem_astronomy_003 | CelestialObjectProperties | same_schema | seen_schema | 0.947368 | 0.815795 | -0.131573 | 1 | 0 | 1 | 1 |
| test_legal_judicial_003 | SentencingLogic | field_embeddings | unseen_schema | 0.727273 | 0.6 | -0.127273 | 1 | 0 | 1 | 1 |
| test_environmental_assessments_006 | EnvironmentalRuling | field_embeddings | unseen_schema | 0.69855 | 0.600826 | -0.097723 | 1 | 0 | 1 | 1 |
| test_environmental_assessments_004 | EnvironmentalRuling | field_embeddings | unseen_schema | 0.697368 | 0.608589 | -0.08878 | 1 | 0 | 1 | 1 |
| research_paper_argument_003 | PaperArgument | field_embeddings | unseen_schema | 0.636189 | 0.548815 | -0.087374 | 1 | 0 | 1 | 1 |
| test_general_disasters_002 | NewsArticle | same_schema | seen_schema | 0.581583 | 0.5083 | -0.073283 | 1 | 0 | 1 | 1 |

### qwen3-14b: enriched-schema-rag vs baseline

Mejoras:

| task_id | schema_title | route_group | seen_group | baseline_f1 | rag_f1 | delta_f1 | baseline_system_minus_gold | rag_system_minus_gold | baseline_calls | rag_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_cultural_entities_001 | NamedEntities | same_schema | seen_schema | 0 | 0.8 | 0.8 | 0 | 0 | 1 | 1 |
| test_stem_astronomy_003 | CelestialObjectProperties | same_schema | seen_schema | 0.057026 | 0.815795 | 0.758769 | -6 | 0 | 1 | 1 |
| test_cultural_people_001 | ArtistProfile | field_embeddings | unseen_schema | 0.333333 | 1 | 0.666667 | -6 | 0 | 1 | 1 |
| test_stem_astronomy_002 | CelestialObjectProperties | same_schema | seen_schema | 0.310902 | 0.888889 | 0.577987 | -6 | 0 | 1 | 1 |
| test_stem_astronomy_detailed_003 | CelestialObjectProperties | same_schema | seen_schema | 0.333333 | 0.888889 | 0.555556 | -6 | 0 | 1 | 1 |
| test_stem_astronomy_detailed_005 | CelestialObjectProperties | same_schema | seen_schema | 0.333333 | 0.888889 | 0.555556 | -6 | 0 | 1 | 1 |
| test_stem_astronomy_detailed_004 | CelestialObjectProperties | same_schema | seen_schema | 0.166667 | 0.666667 | 0.5 | -6 | 0 | 1 | 1 |
| test_cultural_people_004 | ArtistProfile | field_embeddings | unseen_schema | 0.311015 | 0.754037 | 0.443022 | -6 | 0 | 1 | 1 |

Regresiones:

| task_id | schema_title | route_group | seen_group | baseline_f1 | rag_f1 | delta_f1 | baseline_system_minus_gold | rag_system_minus_gold | baseline_calls | rag_calls |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test_general_disasters_006 | NewsArticle | same_schema | seen_schema | 0.895021 | 0 | -0.895021 | 1 | -10 | 1 | 0 |
| technical_security_incident_008 | SecurityIncident | field_embeddings | unseen_schema | 0.826459 | 0 | -0.826459 | 0 | -8 | 1 | 0 |
| test_cultural_monuments_002 | MonumentBIC | same_schema | seen_schema | 0.833333 | 0.56544 | -0.267893 | 0 | 0 | 1 | 1 |
| test_legal_judicial_004 | SentencingLogic | field_embeddings | unseen_schema | 0.408828 | 0.241608 | -0.16722 | 1 | 0 | 1 | 1 |
| test_general_disasters_003 | NewsArticle | same_schema | seen_schema | 0.630538 | 0.475439 | -0.155099 | 0 | 0 | 1 | 1 |
| test_medical_diseases_005 | DiseaseProfile | same_schema | seen_schema | 0.525916 | 0.380854 | -0.145063 | 1 | 0 | 1 | 1 |
| test_cultural_literature_004 | LiteraryWork | same_schema | seen_schema | 0.713531 | 0.578492 | -0.135039 | 1 | 0 | 1 | 1 |
| test_medical_diseases_006 | DiseaseProfile | same_schema | seen_schema | 0.375501 | 0.272917 | -0.102583 | 1 | 0 | 1 | 1 |

## Lectura preliminar

- RAG mejora al baseline en los dos modelos en la metrica oficial.
- La mejora se mantiene al excluir tasks donde alguno de los dos lados tiene `calls=0`.
- El corte seen/unseen debe leerse junto con la ruta de retrieval: en este test, los schemas vistos coinciden con la ruta same-schema y los no vistos con field-RAG/fallos.
- Las tablas por task sirven para inspeccion y seleccion de casos; las conclusiones agregadas deben usar las filas micro de `rag_vs_baseline_summary.csv`.
