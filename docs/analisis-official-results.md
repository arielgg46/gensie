# Official DRILLER results analysis

Computed from `results/DRILLER/summary.json`, `results/DRILLER/reports/*.json`, and retrieval diagnostics with the official 20-instance drop-set removed.

- Rank: 1
- Avg gap closed: 0.2158
- Official baselines: Gemma 4 E4B no-think F1=0.7895; Qwen3-14B no-think F1=0.7805.
- Drop-set domains: medical_trials=8, cultural_monuments=2, stem_biology=10.

## All official cells

| model_label | pipeline_label | mode | precision | recall | f1 | gap_closed_pct | source_event |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma | Mixed-SC | think | 0.8285 | 0.8285 | 0.8285 | 18.5 | 2026-06-formal-eval |
| Gemma | Schema-RAG | think | 0.8256 | 0.8256 | 0.8256 | 17.1 | 2026-06-formal-eval |
| Gemma | Schema-RAG | nothink | 0.8211 | 0.8211 | 0.8211 | 15 | 2026-07-06-final-harvest |
| Gemma | Reasoned-RAG | think | 0.8249 | 0.8115 | 0.8181 | 13.6 | 2026-06-formal-eval |
| Gemma | Reasoned-RAG | nothink | 0.8239 | 0.8113 | 0.8176 | 13.3 | 2026-07-06-final-harvest |
| Gemma | Mixed-SC | nothink | 0.8241 | 0.809 | 0.8165 | 12.8 | 2026-07-06-final-harvest |
| Qwen | Schema-RAG | nothink | 0.8346 | 0.8346 | 0.8346 | 24.6 | 2026-07-08-ainbox-missing-eval |
| Qwen | Reasoned-RAG | think | 0.8297 | 0.8297 | 0.8297 | 22.4 | 2026-07-06-final-harvest |
| Qwen | Reasoned-RAG | nothink | 0.828 | 0.828 | 0.828 | 21.6 | 2026-07-08-ainbox-missing-eval |
| Qwen | Schema-RAG | think | 0.8201 | 0.8201 | 0.8201 | 18 | 2026-06-formal-eval |
| Qwen | Mixed-SC | think | 0.8177 | 0.8177 | 0.8177 | 16.9 | 2026-06-formal-eval |
| Qwen | Mixed-SC | nothink | 0.8129 | 0.8129 | 0.8129 | 14.8 | 2026-07-06-final-harvest |

## Best cell by model and pipeline

| model_label | pipeline_label | mode | precision | recall | f1 | gap_closed_pct |
| --- | --- | --- | --- | --- | --- | --- |
| Gemma | Reasoned-RAG | think | 0.8249 | 0.8115 | 0.8181 | 13.6 |
| Gemma | Schema-RAG | think | 0.8256 | 0.8256 | 0.8256 | 17.1 |
| Gemma | Mixed-SC | think | 0.8285 | 0.8285 | 0.8285 | 18.5 |
| Qwen | Reasoned-RAG | think | 0.8297 | 0.8297 | 0.8297 | 22.4 |
| Qwen | Schema-RAG | nothink | 0.8346 | 0.8346 | 0.8346 | 24.6 |
| Qwen | Mixed-SC | think | 0.8177 | 0.8177 | 0.8177 | 16.9 |

## Best-cell route diagnostics

| model_label | pipeline_label | mode | route | task_count | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma | Reasoned-RAG | think | same_schema | 34 | 0.8074 | 0.8074 | 0.8074 |
| Gemma | Reasoned-RAG | think | field_rag | 91 | 0.8312 | 0.8129 | 0.822 |
| Gemma | Schema-RAG | think | same_schema | 34 | 0.777 | 0.777 | 0.777 |
| Gemma | Schema-RAG | think | field_rag | 91 | 0.8429 | 0.8429 | 0.8429 |
| Gemma | Mixed-SC | think | same_schema | 34 | 0.8067 | 0.8067 | 0.8067 |
| Gemma | Mixed-SC | think | field_rag | 91 | 0.8363 | 0.8363 | 0.8363 |
| Qwen | Reasoned-RAG | think | same_schema | 34 | 0.7836 | 0.7836 | 0.7836 |
| Qwen | Reasoned-RAG | think | field_rag | 91 | 0.8461 | 0.8461 | 0.8461 |
| Qwen | Schema-RAG | nothink | same_schema | 34 | 0.7819 | 0.7819 | 0.7819 |
| Qwen | Schema-RAG | nothink | field_rag | 91 | 0.8534 | 0.8534 | 0.8534 |
| Qwen | Mixed-SC | think | same_schema | 34 | 0.7795 | 0.7795 | 0.7795 |
| Qwen | Mixed-SC | think | field_rag | 91 | 0.8314 | 0.8314 | 0.8314 |

## Mixed-SC vs Schema-RAG

| comparison_type | model_label | schema_mode | mixed_mode | schema_f1 | mixed_f1 | delta_mixed_minus_schema |
| --- | --- | --- | --- | --- | --- | --- |
| best_cell | Gemma | think | think | 0.8256 | 0.8285 | 0.0029 |
| nothink_controlled | Gemma | nothink | nothink | 0.8211 | 0.8165 | -0.0046 |
| best_cell | Qwen | nothink | think | 0.8346 | 0.8177 | -0.0169 |
| nothink_controlled | Qwen | nothink | nothink | 0.8346 | 0.8129 | -0.0217 |

## Retrieval composition

| task_count | same_schema_route_count | field_rag_route_count | retrieval_failed_count | field_rag_pair_diagnostics_count | field_rag_positive_coverage_gain_count |
| --- | --- | --- | --- | --- | --- |
| 125 | 34 | 91 | 0 | 91 | 40 |

## Schema composition

| total_schemas | seen_schemas | unseen_schemas | total_tasks | seen_schema_tasks | unseen_schema_tasks |
| --- | --- | --- | --- | --- | --- |
| 20 | 9 | 11 | 125 | 34 | 91 |

## Notes

- Route diagnostics are system-only cuts; no official per-route baseline reports are present in `results/DRILLER`.
- Timing is intentionally omitted because the hosted backend and model generation latency are confounded with user-code execution.
