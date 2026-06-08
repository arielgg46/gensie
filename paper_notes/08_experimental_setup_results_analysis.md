# 08 Experimental Setup, Results, and Analysis

## Purpose of This Section

This note prepares source material for the experimental setup, results, and analysis sections. It must remain conservative because official scores, rankings, and complete evaluation metadata are not yet available in the source documents. The final paper should report the official shared-task results once known, but these notes should not invent numbers, ranks, model names, or ablation outcomes.

The section should explain what can be reported from the implementation and what must be filled later from official evaluation records.

## Known Evaluation Setting

GenSIE evaluates systems on Spanish schema-guided information extraction. Each instance provides a source text, a natural-language instruction, and a target JSON Schema. The output must be a JSON object conforming to the schema and grounded in the source text. The task includes schema-variable generalization: some test schemas may resemble development schemas, while others may be new.

The challenge uses a flattened schema scoring approach. Gold and system JSON objects are flattened into path-value pairs. Shared keys contribute value similarity according to the field type. Rigid values such as numbers, booleans, dates, and enum labels are scored by exact match. Free-text values use a combination of semantic and lexical similarity. Lists are matched in an order-insensitive way. Scores are aggregated into Micro-F1.

The primary leaderboard, according to the challenge documentation, is based on gap closed over the official baseline. For each evaluation model:

```latex
\mathrm{GapClosed} = \max\left(0, \frac{F1_s - F1_b}{1 - F1_b}\right),
```

where `F1_s` is the system Micro-F1 and `F1_b` is the baseline Micro-F1 for that model. The primary score averages this quantity across evaluation models. Secondary reporting includes raw Micro-F1 and efficiency or token-cost measures.

The paper should cite the GenSIE overview when describing these metrics and the IberLEF overview when situating the task in the shared-task venue.

## Known System Setup from Implementation

The submitted participant exposes exactly three pipelines:

- Schema-RAG;
- Reasoned-RAG;
- Mixed-SC.

All three use retrieval-augmented few-shot prompting. Schema-RAG and Reasoned-RAG are single-pass pipelines. Mixed-SC requests four trials, combining two direct Schema-RAG-style trials and two Reasoned-RAG-style trials, followed by heuristic schema-aware aggregation.

The model identity is not hard-coded in the submitted pipeline specifications. The evaluation request supplies a model name, and the runtime forwards that model name to the OpenAI-compatible inference server. The final paper should therefore report the official evaluation models only if the organizers disclose them. Otherwise, it should state that the method is model-agnostic and was evaluated under the official multi-model protocol.

Single-pass submitted pipelines do not set explicit temperature or top-p parameters in the pipeline specification, according to the source notes. Self-consistency trials use environment-configurable decoding options, with a documented default self-consistency temperature of `0.5` unless overridden. Optional top-p, maximum tokens, and related options may be forwarded when present. The final submitted configuration must be verified before reporting exact decoding parameters.

The system reports token usage when available, and the official inference server's logs are authoritative for token accounting. If efficiency results are included, use official token totals rather than local estimates.

## Unknown Information to Fill Later

The following must be filled from official records or final submission metadata:

- official primary score for each submitted pipeline;
- official rank or placement for the team and/or best pipeline;
- raw Micro-F1 per pipeline;
- gap-closed score per pipeline;
- results per evaluation model, if released;
- baseline scores used for gap-closed calculation;
- official token usage and efficiency leaderboard values;
- whether all four Mixed-SC trials ran for all instances or whether budget caps reduced some trials;
- exact model/backend names, if discloseable;
- exact decoding parameters used during official evaluation;
- final citation metadata for `gensie2026overview` and `iberlef2026overview`;
- any official constraints on how to phrase results or rank.

Do not fill any of these from memory or local experimental artifacts unless explicitly verified as official.

## Suggested Results Table Skeletons

### Official Pipeline Results Placeholder

| Pipeline | Alias | Primary gap closed | Raw Micro-F1 | Token usage | Rank/notes |
|---|---|---:|---:|---:|---|
| `enriched-schema-rag` | Schema-RAG | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER |
| `enriched-inline-reasoning-rag` | Reasoned-RAG | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER |
| `mixed-extractors-self-consistency-rag` | Mixed-SC | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER |

### Per-Model Results Placeholder

| Pipeline | Evaluation model | Baseline F1 | System F1 | Gap closed | Token usage |
|---|---|---:|---:|---:|---:|
| Schema-RAG | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER |
| Reasoned-RAG | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER |
| Mixed-SC | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER |

### Runtime Configuration Placeholder

| Setting | Value in official run | Source/verification |
|---|---|---|
| Model/backend | PLACEHOLDER | Organizer metadata or run logs |
| Single-pass temperature | PLACEHOLDER | Final config/logs |
| Mixed-SC temperature | PLACEHOLDER | Final config/logs |
| Mixed-SC requested trials | 4 | Submitted pipeline spec, subject to budget |
| Enriched RAG descriptions active | PLACEHOLDER | Final environment |
| Fastembed cache available | PLACEHOLDER | Final image/environment |

## Analysis Categories

The final paper should include qualitative analysis if official outputs or inspected examples are available. The following categories fit the system design and GenSIE task. They should be populated with real examples only after inspection.

### Unsupported Inference

This category covers cases where the system returns a value that is plausible or true in the world but not supported by the source text. It is especially relevant to nullable fields and hallucination traps. Analysis should distinguish unsupported values caused by model prior knowledge from unsupported values caused by overinterpreting weak textual evidence.

### Missing Array Items

Arrays are vulnerable to recall errors. A system may extract only the first item, miss items in long lists, omit nested object items, or lose items during aggregation if support thresholds are too high. Mixed-SC's recall-biased array selection is designed partly to address this, but it may still miss items if no trial generates them.

### Over-Extraction

Over-extraction occurs when the system includes extra values, array items, or object fields not supported by the schema or source. This can reduce precision. It may arise from examples that contain populated lists, from a permissive array aggregator, or from a model treating nearby distractor mentions as valid answers.

### Nullability Errors

Nullability errors include returning a value where `null` is correct, returning `null` where evidence supports a value, or returning the string `"null"` instead of JSON null. The postprocessor handles only the last case when schema permits null. The first two are semantic errors and should be analyzed in relation to grounding and evidence sufficiency.

### Semantically Similar Fields

Schemas may contain fields with similar names or descriptions. A model can swap values between them or use one field's evidence for another. This is especially likely in nested objects, legal schemas, medical schemas, or technical schemas with several related attributes. Field-aware prompting and retrieval are intended to reduce this but cannot eliminate all ambiguity.

### Demonstration Bias

Few-shot examples can bias output choices. If retrieved examples share an enum label, array cardinality, or null pattern, the model may imitate that pattern. DRILLER's complementary pair selection is designed to reduce such bias. Analysis could inspect whether errors correlate with retrieved demonstration outcomes.

### Aggregation Errors

Mixed-SC aggregation can introduce errors when candidates disagree. Examples include selecting the wrong medoid, merging distinct strings into one cluster, preferring null incorrectly, including extra array items because of recall bias, or using a poor identity field for object arrays. These should be discussed as trade-offs of deterministic aggregation.

## Reporting Guidance

If no official ablations are available, the results section should compare the three submitted pipelines only through official scores. It should not infer that RAG, reasoning, or self-consistency independently caused improvements. The method section can explain why these components were designed, while the results section should report only observed outcomes.

If local ablations are later added, they must be clearly labeled as development or post hoc experiments and separated from official leaderboard results. Any local evaluation should specify dataset split, model, decoding parameters, number of instances, metric implementation, and whether results are directly comparable to official scoring.

## Suggested Narrative Once Results Are Known

The final analysis can be organized around three questions:

1. How did the three submitted pipelines compare under the official primary metric?
2. Did the more expensive Mixed-SC pipeline provide robustness relative to the single-pass variants, and at what token cost?
3. Which schema phenomena remained difficult: nulls, arrays, enum inference, nested objects, or field ambiguity?

Until official data is available, these remain questions, not claims.

