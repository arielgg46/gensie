**1. Final Submitted Pipelines**
Confirmed. The final submitted DRILLER pipelines are:

- `enriched-schema-rag`, alias **Schema-RAG**
- `enriched-inline-reasoning-rag`, alias **Reasoned-RAG**
- `mixed-extractors-self-consistency-rag`, alias **Mixed-SC**

Only these should be described as submitted systems. Judge aggregation, PARSE-style extraction, static super-FSP, deep/selective reasoning, and verbatim-entity pre-phases are non-final.

**2. Proposed Final Paper Outline**
1. Abstract
2. Introduction
   - GenSIE as schema-variable Spanish schema-guided IE.
   - Main challenge: schema semantics, grounding, valid JSON, nulls.
   - DRILLER narrative: schema-readable prompting, RAG demonstrations, temporary reasoning wrappers, heterogeneous self-consistency.
3. Task and Evaluation Setting
   - Spanish input text, instruction, runtime JSON Schema.
   - Zero-shot/dynamic schema setting.
   - Flattened Schema Scoring, Micro-F1, gap-closed primary ranking.
   - Hosted OpenAI-compatible inference, model-agnostic requirement, no fine-tuning.
4. System Overview
   - Define Schema-RAG, Reasoned-RAG, Mixed-SC.
   - Shared runtime flow and component table.
5. Schema-Readable Extraction
   - Pydantic-style prompt schema rendering.
   - Strict structured response format.
   - Required-property transformation for generation.
   - Null handling and schema/interface separation.
6. Field-Aware Few-Shot Retrieval
   - Synthetic/curated FSP cases.
   - Same-schema retrieval via normalized schema fingerprint.
   - Field-level fallback with coarse type compatibility.
   - Complementary pair selection and compact same-schema layout.
7. Reasoning-Augmented Extraction
   - Top-level `{reasoning, value}` wrappers.
   - `Reasoned[T]` prompt schema.
   - Evidence-oriented field-local reasoning.
   - Unwrapping before final output.
8. Heterogeneous Self-Consistency
   - Mixed-SC trial plan: two Reasoned-RAG and two Schema-RAG trials.
   - Aggregation over postprocessed candidate JSON objects.
   - Schema-aware voting/clustering for scalars, objects, arrays, and nulls.
9. Experimental Setup and Results
   - Official models/backend once released or confirmed.
   - Official scores, rank, per-pipeline results.
   - Token/cost information if available.
10. Analysis and Discussion
   - Likely error categories: schema interpretation, grounded nulls, enum mapping, array completeness, nested objects.
   - Discuss behavior without unsupported ablation claims.
11. Conclusion
12. `\section*{Declaration on Generative AI}`
13. References

**3. Proposed Section Files**
Without creating `paper/main.tex`, I’d generate these later:

- `paper/sections/00_abstract.tex`
- `paper/sections/01_introduction.tex`
- `paper/sections/02_task_and_evaluation.tex`
- `paper/sections/03_system_overview.tex`
- `paper/sections/04_schema_readable_extraction.tex`
- `paper/sections/05_few_shot_retrieval.tex`
- `paper/sections/06_reasoning_augmented_extraction.tex`
- `paper/sections/07_heterogeneous_self_consistency.tex`
- `paper/sections/08_experimental_setup_and_results.tex`
- `paper/sections/09_analysis_and_discussion.tex`
- `paper/sections/10_conclusion.tex`
- `paper/sections/11_declaration_generative_ai.tex`

**4. Missing Information Needed Later**
- Official GenSIE results: scores, rank, primary gap-closed score, raw Micro-F1, per-model scores.
- Which submitted pipeline was best officially.
- Official model/backend identities, if disclosed, and whether held-out models can be named.
- Token usage / efficiency leaderboard data.
- Final citation metadata for `gensie2026overview`.
- Final citation metadata for `iberlef2026overview`.
- Final team author list, affiliations, title, and acknowledgments.
- Whether enriched RAG field descriptions were active in the final evaluation environment.
- Exact GenAI declaration text desired by the team.