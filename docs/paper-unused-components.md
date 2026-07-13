# Implemented Components Not Used in the Final Submitted Pipelines

## 1. Scope

This file lists implemented or partially implemented components that are present in the repository but should not be described as part of the final DRILLER submitted system unless they are explicitly discussed as explored variants.

The final submitted pipelines are declared in `src/gensie/baseline.py` as:

- `enriched-schema-rag`
- `enriched-inline-reasoning-rag`
- `mixed-extractors-self-consistency-rag`

Everything below is outside that submitted set, even if it is implemented, registered in the internal default registry, exposed through a compatibility wrapper class, or referenced by older design documents. The relevant distinction is the participant surface: `OfficialParticipant` copies only `SUBMITTED_PIPELINES` into the registry returned by `/info` and accepted by `/run`.

## 2. Unused or Non-Final Pipelines

The repository contains several additional pipeline specs in `src/gensie/pipeline/defaults.py` and compatibility wrapper classes in `src/gensie/baseline.py`.

| Name | Short description | Likely purpose | Why non-final or unused |
|---|---|---|---|
| `baseline` | Minimal extraction baseline. | Reference implementation or early comparison point. | Not included in `SUBMITTED_PIPELINES`. |
| `inline-reasoning` | Top-level reasoning without the enriched submitted configuration. | Early reasoning variant. | Not included in `SUBMITTED_PIPELINES`. |
| `enriched-inline-reasoning` | Reasoned Pydantic extraction without RAG. | Non-RAG ablation of the reasoning extractor. | Final submitted equivalent uses RAG. |
| `enriched-schema` | Pydantic-style schema prompting without RAG. | Non-RAG ablation of schema prompting. | Final submitted equivalent uses RAG. |
| `selective-inline-reasoning-rag` | Selective top-level reasoning with RAG. | Experiment to reason only over selected fields. | Implemented but not final. |
| `verbatim-entities-enriched-inline-reasoning` | Adds a verbatim entity pre-phase before inline reasoning. | Experiment using pre-extracted entity evidence. | Not included in `SUBMITTED_PIPELINES`. |
| `enriched-inline-reasoning-deep` | Deep reasoning wrappers beyond top-level fields. | Experiment with more pervasive reasoning scaffolds. | Final reasoning pipeline uses top-level wrappers only. |
| `enriched-inline-reasoning-super-fsp` | Inline reasoning with a static "super" few-shot prompt. | Experiment with fixed demonstrations. | Final pipelines use RAG, not the static super FSP. |
| `enriched-inline-reasoning-self-consistency` | Homogeneous self-consistency over inline-reasoning trials. | Early self-consistency variant. | Final mixed pipeline uses heterogeneous extractors. |
| `enriched-inline-reasoning-super-fsp-self-consistency` | Self-consistency with static super FSP. | Experiment combining fixed examples and multiple trials. | Not final. |
| `enriched-inline-reasoning-self-consistency-judge` | Self-consistency followed by judge aggregation. | Judge-based aggregation experiment. | Final mixed pipeline uses heuristic aggregation. |
| `enriched-inline-reasoning-self-consistency-verdict-judge` | Candidate verdict judge aggregation. | Alternative judge design. | Not final. |
| `mixed-extractors-self-consistency-judge` | Mixed extractors with scoped judge aggregation. | Alternative aggregation for mixed candidates. | Final mixed pipeline uses heuristic aggregation. |
| `mixed-extractors-self-consistency-verdict-judge` | Mixed extractors with verdict judge aggregation. | Alternative candidate judging. | Not final. |
| `mixed-extractors-self-consistency-verdict-judge-rag` | Verdict judge aggregation with judge RAG examples. | RAG-assisted judging experiment. | Not final; local result artifacts indicate this variant was experimental. |
| `mixed-extractors-self-consistency-verdict-judge-rag-slots` | Verdict judge using slot-oriented candidate presentation. | Prompt-layout experiment for judging. | Not final. |

The repository also contains `src/gensie/parse_pipeline.py`, a PARSE-style multi-stage agent with schema optimization, extraction, guardrails, and reflection logic. It is not registered as one of the final submitted pipelines.

Two distinctions are especially important for paper writing:

- The final `mixed-extractors-self-consistency-rag` pipeline is a four-trial RAG pipeline with heuristic schema-aware aggregation. It uses two `enriched-inline-reasoning-rag` trials and two `enriched-schema-rag` trials.
- The non-final mixed judge pipelines are six-trial heterogeneous experiments. Their groups are `baseline`, `enriched-schema`, and `enriched-inline-reasoning`, each with ratio `1.0` and minimum count `1`, followed by judge or verdict-judge aggregation. These are not equivalent to the final mixed RAG pipeline.

The non-final homogeneous self-consistency variants also differ from the final mixed pipeline. For example, `enriched-inline-reasoning-self-consistency` repeatedly samples the same fixed-FSP inline-reasoning extractor for 12 requested trials, whereas the final submitted mixed pipeline combines two different RAG extractor styles and requests four trials.

## 3. Unused Aggregation or Judge Components

The final submitted mixed pipeline uses `HeuristicSelfConsistencyAggregator`. The following judge-related components are implemented but not used by the final submitted pipelines:

- `src/gensie/aggregation/judge.py`: scoped judge aggregation over disputed fields, including reduced schemas and judge-specific model calls.
- `src/gensie/aggregation/judge_prompt.py`, `judge_schema.py`, `judge_fsp.py`, and `judge_scope.py`: prompt, schema, fixed examples, and field-selection support for scoped judging.
- `src/gensie/aggregation/verdict_judge.py`: candidate-level verdict judge aggregation.
- `src/gensie/aggregation/verdict_prompt.py`, `verdict_schema.py`, and `verdict_fsp.py`: verdict-judge prompt layouts, response schemas, example providers, validation, and reporting logic.
- RAG-backed verdict judge examples, including resources associated with judge metadata rather than extraction RAG.

These components may be discussed as explored aggregation variants, but they should not be described as part of the submitted system.

The scoped judge design differs from heuristic self-consistency in mechanism and cost. It identifies disputed fields from candidate outputs, builds a reduced judge scope, prompts a model to adjudicate those fields, and then merges judge outputs back into a full object. The verdict-judge design presents candidate values and asks a model for structured verdicts over candidates. The slots variant changes candidate presentation by using fixed candidate slots rather than only an array-style candidate list. All of these paths introduce an additional model call for aggregation; the final submitted mixed pipeline does not.

The RAG-backed verdict judge provider is also separate from extraction RAG. It filters FSP cases that contain judge metadata and renders examples for candidate adjudication, not examples for source-text extraction. The current extraction RAG corpus deliberately excludes the Quijote judge-oriented case from `default_extraction_fsp_cases()`.

## 4. Unused RAG Variants

The final extraction RAG provider uses `RagExtractionFspProvider(top_k=2)` with same-schema retrieval, field-level fallback, and compact same-schema prompting when applicable. Other RAG or FSP-related components exist but are not part of the final submitted pipelines:

- Fixed few-shot providers in `src/gensie/fsp/fixed.py`, including the Don Quijote-style fixed example path.
- The static "super FSP" provider in `src/gensie/fsp/super.py`.
- The Quijote case resource, which is excluded from `default_extraction_fsp_cases()` and appears tied to judge-oriented examples.
- RAG-backed verdict-judge example retrieval.
- Prebuilt field-index utilities and artifacts such as `FieldIndex`, `build_case_index`, percentile variants, and `data/fsp_index`. The final extraction RAG path embeds the in-repository case resources at runtime rather than loading those index artifacts.
- Schema projection utilities used by non-final judge/verdict RAG paths.

The lexical/schema retrieval fallback in `src/gensie/fsp/retrieval.py` is not unused: it can be used by the final RAG provider if embedding-based field retrieval fails.

The prebuilt-index utilities deserve a specific warning. `src/gensie/fsp/field_rag.py` contains code to build NPZ embedding matrices and metadata sidecars for `data/dev` or FSP cases, including `full`, `p25`, `p50`, and FSP-case index paths under `data/fsp_index`. The final submitted extraction provider does not load those artifacts in its retrieval call. It constructs and embeds FSP-case field texts at runtime.

## 5. Other Experimental Components

Other implemented components that should be kept separate from the final system include:

- Deep and selective reasoning schema transformations in `src/gensie/schemas/reasoning.py`.
- Alternative schema prompt modes such as clean JSON-schema prompting and non-submitted inline wrapper styles.
- The verbatim entity extraction pre-phase in `src/gensie/phases/verbatim_entities.py`.
- The PARSE pipeline implementation in `src/gensie/parse_pipeline.py`.
- Analysis, ranking, and evaluation helper scripts under `src/gensie/analysis`, `scripts`, and related result-processing utilities.
- Debugging, trace, and report-generation utilities that support development but are not prediction-time components of the submitted pipelines.

These modules can be useful for ablations, diagnostics, or future work, but they should not be folded into the main system description.

The PARSE implementation is especially separate from the submitted system. It defines an ARCHITECT stage that asks a model to refine a JSON Schema, a SCOPE stage that performs strict extraction with validation and reflection retries, and a RELAY stage that returns data in the original schema shape. It uses environment variables such as `GENSIE_PARSE_SKIP_ARCHITECT` and `GENSIE_PARSE_SCOPE_MAX_RETRIES`, and it makes additional model calls outside the composable pipeline runner used by the submitted pipelines. Since `OfficialParticipant` does not register this agent, it should be treated only as an implementation artifact or explored alternative.

The verbatim entity pre-phase is also non-final. Its purpose is to make an extra model call that extracts flat verbatim entities before the main extraction prompt. The only default spec that uses it is `verbatim-entities-enriched-inline-reasoning`, which is not submitted. The final submitted RAG pipelines do not add a pre-extraction entity list to their prompts.

## 6. Paper-Writing Warning

Components in this file should not be presented as part of the final DRILLER submitted system. They may be mentioned only as explored variants, implementation artifacts, or future work.

Any performance claim involving these components requires separate experimental evidence. In particular, judge aggregation, PARSE-style extraction, static super FSP prompting, deep reasoning, selective reasoning, and verbatim-entity pre-phases should not be attributed to the final submitted pipelines.
