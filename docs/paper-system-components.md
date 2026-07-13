# DRILLER GenSIE Submission: System Components

## 1. Scope and Source of Truth

This document reconstructs the final DRILLER GenSIE submission from the repository implementation. The final submitted pipeline names are declared by `SUBMITTED_PIPELINES` in `src/gensie/baseline.py` and exposed through `OfficialParticipant`, which is the participant class configured by the container entry point. The FastAPI server in `src/gensie/server.py` loads this participant, reports its registered pipelines through `/info`, and dispatches `/run` requests by calling `OfficialParticipant.get_agent(pipeline_name)`. The implementation exposes the following submitted pipelines:

- `enriched-schema-rag`
- `enriched-inline-reasoning-rag`
- `mixed-extractors-self-consistency-rag`

These names match the expected final submitted pipelines. Several other agent wrapper classes and pipeline specs are present in the repository, but they are not registered by `OfficialParticipant` and therefore are not part of the submitted participant surface. Older design documents in `docs/` were used only as background for terminology and intent. When a document and the implementation differ, this document follows the implementation.

This is paper-oriented technical documentation. It describes algorithms, data flow, and component interactions, rather than line-by-line software behavior.

Implementation traceability map:

| System aspect | Main implementation files |
|---|---|
| Participant/server exposure | `src/gensie/baseline.py`, `src/gensie/server.py` |
| Pipeline specifications | `src/gensie/pipeline/defaults.py`, `src/gensie/pipeline/specs.py` |
| Pipeline execution | `src/gensie/pipeline/agent.py`, `src/gensie/sampling/single.py`, `src/gensie/sampling/multi.py`, `src/gensie/sampling/plans.py`, `src/gensie/sampling/budget.py` |
| Prompt construction | `src/gensie/prompts/reference.py`, `src/gensie/prompts/extraction.py`, `src/gensie/prompts/extraction_layouts.py`, `src/gensie/prompts/system.py` |
| Prompt schema rendering | `src/gensie/prompts/schema_views.py`, `src/gensie/schemas/pydantic_render.py` |
| Structured generation schema | `src/gensie/runtime/response_format.py`, `src/gensie/schemas/reasoning.py` |
| Extraction RAG | `src/gensie/fsp/rag.py`, `src/gensie/fsp/field_rag.py`, `src/gensie/fsp/retrieval.py`, `src/gensie/fsp/render_extraction.py`, `src/gensie/fsp/resources/cases/*.json` |
| Postprocessing | `src/gensie/runtime/unicode.py`, `src/gensie/schemas/coercion.py`, `src/gensie/schemas/reasoning.py` |
| Self-consistency aggregation | `src/gensie/aggregation/heuristic.py`, `src/gensie/aggregation/self_consistency.py`, `src/gensie/aggregation/clustering.py`, `src/gensie/aggregation/similarity.py`, `src/gensie/aggregation/arrays.py`, `src/gensie/aggregation/config.py` |

## 2. Task Setting Assumed by the System

The system assumes the GenSIE setting of structured information extraction from Spanish text. Each instance contains:

- a Spanish source text;
- an extraction instruction;
- a target JSON Schema;
- an expected answer that must be valid JSON and conform to the target schema.

The schema may change from instance to instance, so the extractor cannot rely on a fixed ontology. The system is designed for grounded structured extraction rather than open-ended generation: values should be supported by the input text, omitted or uncertain information should be represented with JSON `null` where the schema permits it, and the final response should contain only the requested JSON object.

## 3. Submitted Pipelines

The submitted pipelines are configured in `src/gensie/pipeline/defaults.py` and executed through the generic pipeline runner in `src/gensie/sampling/multi.py`.

| Pipeline | Uses RAG | Schema prompt/rendering style | Reasoning/value wrappers | Trials | Self-consistency | Aggregation strategy | Main purpose |
|---|---:|---|---|---:|---:|---|---|
| `enriched-schema-rag` | yes | Pydantic-style schema rendering | no | 1 | no | single extraction plus deterministic postprocessing | Direct schema-guided extraction with retrieved examples. |
| `enriched-inline-reasoning-rag` | yes | reasoned Pydantic-style rendering | top-level `{reasoning, value}` wrappers | 1 | no | unwrap reasoning plus deterministic postprocessing | Encourage field-local evidence reasoning before producing final values. |
| `mixed-extractors-self-consistency-rag` | yes | heterogeneous: reasoned Pydantic and plain Pydantic | wrappers in the inline-reasoning trials only | 4 requested | yes | schema-aware heuristic self-consistency | Combine complementary extractor styles and aggregate their outputs. |

### 3.1 `enriched-schema-rag`

`enriched-schema-rag` is a single-pass RAG extractor. For each received task, it builds a prompt from the extraction instruction, the source text, a Pydantic-style rendering of the target schema, extraction rules, and up to two retrieved few-shot examples.

The prompt schema is produced by the schema view layer in `src/gensie/prompts/schema_views.py` using `SchemaPromptMode.PYDANTIC`. The generated response is constrained with a strict JSON Schema response format built from the original target schema in `src/gensie/runtime/response_format.py`. For submitted non-baseline pipelines, the response-format builder recursively marks all object properties as required for generation. This is intended to reduce omitted fields during model generation; it does not change the final challenge schema or add values after the fact.

At runtime, `ReferenceExtractionPromptBuilder` delegates RAG prompt construction to `ExtractionPromptBuilder` with `RagExtractionFspProvider(top_k=2)`. If two sufficiently similar examples with the same normalized schema are found, the system uses the compact same-schema prompt layout. Otherwise, it uses general few-shot examples selected by field-level retrieval. The model output is parsed as JSON, normalized for Unicode artifacts, optionally coerced for nullable `"null"` strings, and returned as the final prediction.

### 3.2 `enriched-inline-reasoning-rag`

`enriched-inline-reasoning-rag` uses the same RAG machinery and overall prompt structure as `enriched-schema-rag`, but changes both the prompt schema and the generation schema. It enables `ReasoningMode.TOP_LEVEL` and `SchemaPromptMode.REASONED_PYDANTIC`.

For each top-level field in the target object, the temporary generation schema wraps the original field schema as:

```json
{
  "reasoning": "string",
  "value": "<original field schema>"
}
```

The prompt-side schema uses a corresponding `Reasoned[T]` style so that the model sees each top-level field as requiring local reasoning plus a final value. The system prompt and extraction rules instruct the model to use reasoning for evidence-based deliberation, citing or summarizing relevant source evidence and stating absence when needed.

The final challenge output does not include reasoning. After the model returns the wrapped object, `src/gensie/schemas/reasoning.py` unwraps each top-level field by retaining only its `value`. The discarded reasoning is retained only as internal trace metadata. The final prediction has the original schema shape.

### 3.3 `mixed-extractors-self-consistency-rag`

`mixed-extractors-self-consistency-rag` is the final heterogeneous self-consistency pipeline. It does not sample the same extractor four times. Instead, the trial plan combines two extractor styles:

- two trials of `enriched-inline-reasoning-rag`;
- two trials of `enriched-schema-rag`.

The trial plan is interleaved by `src/gensie/sampling/plans.py`. With the submitted fixed counts, the intended four-trial sequence is: inline-reasoning RAG, plain schema RAG, inline-reasoning RAG, plain schema RAG. Each trial independently performs RAG retrieval, prompt construction, structured generation, and deterministic postprocessing. The aggregation stage receives already-unwrapped final JSON predictions, not raw reasoning-wrapper outputs.

The final aggregation uses `HeuristicSelfConsistencyAggregator` in `src/gensie/aggregation/heuristic.py`, backed by the recursive schema-aware aggregator in `src/gensie/aggregation/self_consistency.py`. It votes and clusters values according to the target schema, handles nulls cautiously, aggregates objects field by field, and clusters array items before selecting a final array. The design intent is to combine complementary biases: direct extraction can be concise and schema-faithful, while inline reasoning can recover evidence-sensitive fields that benefit from local deliberation.

The number four is the requested sampling plan encoded in the submitted `PipelineSpec`. The execution runner also includes a dynamic trial-budget planner. By default this planner uses a maximum of 12 trials, a 32,000-token task budget with an effective ratio of 0.85, a 60-second time budget with an effective ratio of 0.85, a completion-token safety factor of 1.5, and an approximate 4 characters per token estimate. For this submitted pipeline, the fixed group counts require a four-item plan, but the loop still stops when the current `allowed_trials` estimate is reached. In ordinary documentation, the correct wording is therefore that the pipeline requests four trials, subject to runtime budget limits.

## 4. End-to-End Data Flow

The runtime flow is:

1. The FastAPI server in `src/gensie/server.py` receives a `/run` request containing a GenSIE task, a model name, and a pipeline query parameter.
2. The requested pipeline name is passed to `OfficialParticipant.get_agent()` in `src/gensie/baseline.py`; only the submitted pipeline registry is accepted by this participant.
3. The participant constructs a `ComposablePipelineAgent` from the corresponding `PipelineSpec`.
4. The agent creates a `PipelineContext` containing the task, model, usage trace, and metadata.
5. The `PipelineExecutionRunner` decides whether the spec is a single extraction or a multi-trial aggregation pipeline. The two single-pass submitted pipelines are executed once and returned directly after postprocessing; the mixed pipeline enters the trial planner and aggregator.
6. For each single extraction trial, `SingleExtractionRunner` extracts the source text, instruction, and target schema from the task.
7. The prompt builder renders the schema for the prompt and optionally retrieves RAG examples.
8. If RAG is enabled, the few-shot provider selects up to two examples using same-schema retrieval or field-level fallback.
9. The prompt is assembled from system instructions, extraction rules, schema view, examples, instruction, and source text.
10. The runtime builds a strict structured response format from the target schema, optionally after injecting reasoning/value wrappers.
11. The OpenAI-compatible chat client sends the model request using the model supplied in the GenSIE request.
12. The returned JSON is parsed and normalized.
13. If reasoning wrappers were used, the system unwraps `{reasoning, value}` objects and discards the reasoning from the final prediction.
14. Nullable string values equal to `"null"` are coerced to JSON `null` only where the schema allows null.
15. For single-pass pipelines, the normalized object is returned.
16. For the mixed pipeline, the candidate predictions from all trials are recursively aggregated into one schema-conformant output.

The main component dependencies are:

```text
request
  -> participant registry
  -> pipeline spec
  -> prompt schema rendering
  -> RAG retrieval and example rendering
  -> strict generation schema transformation
  -> model call
  -> deterministic postprocessing
  -> optional schema-aware self-consistency aggregation
  -> final JSON response
```

RAG affects only the prompt context. Reasoning wrappers affect both the prompt schema and the structured response schema, and require unwrapping after generation. Self-consistency depends on complete single-pass extractor outputs after their own postprocessing.

At the API level, the system uses the `Task` object defined in `src/gensie/task.py`. The fields consumed by the submitted pipelines are `id`, `input_text`, `instruction`, and `target_schema`; `output` may be present in local/dev runs but is not used as evidence for prediction. The task `metadata` is preserved on the task object but is not a primary extraction input in the submitted pipeline logic.

The model call is mediated by `OpenAIChatClient` in `src/gensie/runtime/client.py`. This client is OpenAI-compatible rather than tied to a hard-coded provider. It forwards the request model name, chat messages, optional `response_format`, optional temperature, and any additional request options such as `top_p`, `max_tokens`, or provider-specific `extra_body`. The submitted implementation therefore defines the extraction procedure, but the exact model identity is supplied externally at request time.

For each model call, the runner constructs a `ChatRequest` with two chat messages, a `system` message and a `user` message. The strict JSON response format is attached to the API request rather than merely described in the prompt. Single-pass extraction returns an `ExtractionResult` containing the final output, raw parsed output, optional reasoning view, errors, and request/response metadata. A result is valid only if it has an output, has no errors, and does not contain an `"error"` key. This validity check is used by the mixed self-consistency pipeline to decide which trials can be aggregated.

Usage accounting is collected through a `UsageTracker` attached to each `ComposablePipelineAgent`. The server returns the final JSON as the response body and, when usage information is available, includes an `X-GenSIE-Token-Usage` header. Tracing utilities record intermediate steps for diagnostics, but tracing is not part of the prediction returned to the evaluator.

## 5. Prompting Strategy

Prompt construction is implemented mainly in `src/gensie/prompts/extraction.py`, `src/gensie/prompts/extraction_layouts.py`, and `src/gensie/prompts/system.py`.

The system prompt frames the model as a precise Spanish information extractor. It instructs the model to return only JSON, to ground values in the source text, to use the schema and instruction to determine field meanings, and to avoid treating few-shot examples as evidence for the current instance.

The user-side prompt is organized into explicit sections:

- the extraction instruction;
- a root schema description when available;
- extraction rules in Spanish;
- retrieved few-shot examples, if any;
- the rendered target schema;
- the source text.

The extraction rules emphasize complete schema coverage, exact enum labels, grounded values, use of JSON `null` instead of string `"null"`, conservative handling of partial evidence, and verbatim preservation for textual values when appropriate.

When same-schema RAG succeeds, the layout changes. The shared schema is placed once in the system-side context, and the retrieved examples are rendered more compactly because they share the target schema. This avoids repeating the same schema for every example and makes the examples focus on instruction, source text, and output.

When reasoning wrappers are enabled, the prompt changes in two ways. First, the schema shown to the model uses a reasoned Pydantic style. Second, the rules tell the model to provide local reasoning for each top-level field before giving the final `value`. This reasoning is an internal generation aid, not part of the returned answer.

The normal RAG prompt layout uses the following user-message order:

1. `TAREA`: a fixed statement that the model must extract structured information from the source text.
2. `INSTRUCCION`: the instance-specific natural-language extraction instruction.
3. Optional root schema description, when the target schema has a root `description`.
4. Spanish extraction rules.
5. `EJEMPLOS FEW-SHOT`, if RAG selected examples.
6. Any previous-phase context. This is not active in the submitted pipelines because their extraction specs have no pre-phases.
7. `SCHEMA PYDANTIC`: the rendered current target schema.
8. `TEXTO FUENTE`: the current instance text.

The same-schema RAG layout moves shared information into the system message. In that mode, the system message contains the role instruction, extraction rules, optional root schema description, the single shared schema rendering, and guidance that the examples use the same schema but are not evidence for the new source text. The user message then contains compact examples followed by `TAREA NUEVA`, the new instruction, and the new source text. This layout reduces schema repetition when retrieved examples are structurally identical to the target schema.

Few-shot examples are rendered by `src/gensie/fsp/render_extraction.py`. In the general layout, each example includes its own instruction, schema description, schema rendering, source text, expected output, and explicit begin/end markers. In the same-schema layout, the example schema is omitted because it has already been shown once. The output format of the examples is matched to the active extractor: direct extractors show final field values, while top-level reasoning extractors show each field as `{reasoning, value}`.

For reasoning examples and model outputs, the default reasoning section labels are fixed by `ReasoningSectionLabels` in `src/gensie/fsp/examples.py`: `EL CAMPO PIDE`, `FRAGMENTOS RELEVANTES`, and `VALOR FINAL`. The prompt rules instruct the model to use these three sections, in that order, for each reasoning string. This gives the model a local evidence protocol without changing the final returned object after unwrapping.

## 6. Schema Representation and Schema Transformations

The implementation distinguishes three schema roles:

| Role | Where used | Submitted-pipeline behavior |
|---|---|---|
| Prompt schema | Text shown to the model | Pydantic-style rendering for direct extraction; reasoned Pydantic-style rendering for top-level reasoning. |
| Generation schema | Structured response format sent to the model API | Strict JSON Schema derived from the target schema; all object properties are made required for submitted non-baseline pipelines; reasoning wrappers are injected when enabled. |
| Final challenge schema | Shape expected by the evaluator | Original target schema shape after postprocessing and optional unwrapping. |

The Pydantic-style schema renderer in `src/gensie/schemas/pydantic_render.py` converts the JSON Schema into a compact class-like representation. Nullable fields are shown with nullable type syntax. In reasoned mode, top-level fields are rendered as `Reasoned[T]` to match the temporary generation structure.

The renderer maps JSON Schema constructs into type hints intended for model readability. Object schemas become `BaseModel`-like classes; `$defs` object definitions become additional classes; `$defs` enums become `Literal[...]` aliases; strings become `str`; integers become `int`; numbers become `float`; booleans become `bool`; arrays become `List[T]`; object-valued properties without a reusable `$defs` reference become nested generated model names. Field descriptions are preserved as `Field(..., description=...)` or equivalent prompt-side metadata. Required fields are represented with an ellipsis default in plain Pydantic rendering, while optional fields use `None`.

In reasoned Pydantic rendering, the prompt prelude defines a conceptual generic wrapper:

```python
class Reasoned[T](BaseModel):
    reasoning: str
    value: T
```

The submitted top-level reasoning mode renders root fields as `Reasoned[T]`. Nested fields are not wrapped unless a non-final deep reasoning mode is used. Nullable types in these prompt schemas use the readable alias `Nullable[T] = T | null`; this is a prompt convention, not executable Python.

For structured generation, `src/gensie/runtime/response_format.py` builds an OpenAI-compatible JSON Schema response format. The transformation order is important: the target schema is first transformed for the active reasoning mode, and only then, for submitted non-baseline pipelines, the builder recursively makes every declared object property required. This targets a common extraction failure mode: the model omits fields even when the final answer should contain the full schema shape.

Reasoning wrappers are injected by `src/gensie/schemas/reasoning.py`. In `ReasoningMode.TOP_LEVEL`, only root object properties are wrapped. Nested object fields are not individually wrapped by the submitted pipeline. Each temporary wrapper schema is an object with `additionalProperties: false`, properties `reasoning` and `value`, and `required: ["reasoning", "value"]`. The `value` property contains the original field schema. After generation, the wrapper is removed by replacing each top-level object:

```json
{"reasoning": "...", "value": X}
```

with `X`. The final output therefore restores the original target schema interface. If JSON parsing or reasoning-wrapper unwrapping fails, the single extraction trial is recorded as invalid rather than repaired semantically. In the mixed pipeline, invalid trial records are excluded from heuristic aggregation.

## 7. Few-Shot RAG

The submitted pipelines use the RAG provider in `src/gensie/fsp/rag.py`. Although the provider class defaults to one example, the submitted RAG prompt path in `src/gensie/prompts/reference.py` instantiates it as `RagExtractionFspProvider(top_k=2)`. Retrieval is implemented primarily by `src/gensie/fsp/field_rag.py`, with a lexical/schema fallback in `src/gensie/fsp/retrieval.py`.

### 7.1 Synthetic/Curated FSP Corpus Construction

The extraction RAG corpus is stored under `src/gensie/fsp/resources/cases`. The repository currently contains 45 JSON case resources. The extraction provider excludes `cultural_literature_quijote.json`, leaving 44 extraction cases with 244 field-level example records. The excluded Quijote case contains judge-oriented metadata and is used by non-final judge/FSP components rather than by the submitted extraction RAG provider.

The cases are organized by domain or schema family. The extraction corpus has two cases for each of the following 22 families: `cultural_entities`, `cultural_extraction`, `cultural_literature`, `cultural_media`, `cultural_monuments`, `environmental_ecology`, `general_disasters`, `legal_contracts`, `legal_entities`, `legal_extraction`, `legal_judicial`, `legal_legislation`, `lifestyle_recipes`, `medical_diseases`, `medical_drug`, `medical_entities`, `medical_extraction`, `medical_health_news`, `stem_astronomy_detailed`, `technical_entities`, `technical_extraction`, and `technical_software`. This two-case organization is aligned with the complementary-example design notes in `docs/propuesta-cases-fsp-complementarios.md`.

Each `StructuredFspCase` resource contains a case id, domain, language, tags, synthetic source text, instruction, schema, field-level expected values, optional field-level reasoning, optional enriched field descriptions, and optional judge metadata. The extraction RAG path uses the extraction-relevant parts: source text, instruction, schema, field examples, tags, and enriched descriptions. Judge metadata is only relevant to non-final judge variants.

The corpus tags indicate the intended extraction phenomena covered by the cases. In the extraction corpus, tags include `direct_string`, `summary_string`, `verbatim_answer`, `nullable`, `grounded_null`, `empty_array`, `simple_array`, `complex_object_array`, `entity_array`, `enum_classification`, `enum_array`, `boolean_inference`, `numeric_normalization`, `date_normalization`, `bounded_score`, `sentinel_pattern`, `long_verbatim_evidence`, and `nested_numeric_object_array`. These tags are not used as the primary retrieval score in the final embedding path, but they document the design coverage and are available to the lexical fallback ranker.

The design notes and representative `docs/rag/*.md` files describe a methodology based on complementary pairs. The intended pair structure covers contrasts such as:

- `null` versus grounded non-null values for nullable fields;
- empty arrays versus populated arrays;
- frequent enum values versus less frequent or contrasting enum values;
- explicit dates/numbers versus insufficient or distractor evidence;
- direct verbatim answers versus longer evidence spans;
- positive versus negative boolean evidence;
- simple arrays versus nested object arrays;
- entity mentions versus distractor mentions of nearby but wrong types.

The resources include both synthetic source text and expected structured output. Repository documentation records an iterative process: inspect curated development examples for a prefix, identify field dualities, draft synthetic cases, review input text/output/reasoning, generate JSON resources only after review, and validate resources with the FSP loader or schema-aware checks. The same documentation also records that some candidate `.md` proposals were generated autonomously before review, and later notes describe a style/enriched-description review pass across the prefixes. The safest paper wording is therefore that the FSP corpus is synthetic and curated, with manual review/validation documented in the repository; the exact authorship of every final sentence or field rationale should not be overstated.

Complementary demonstrations are intended to reduce few-shot bias. A single example can bias the model toward copying a field pattern, enum choice, or array cardinality. Selecting two examples that are both relevant and different gives the model evidence that the same schema can map to different valid outputs depending on the input text.

### 7.2 Same-Schema Retrieval

At runtime, retrieval first tries to find examples with the same normalized schema as the target task. The normalized schema fingerprint:

- canonicalizes the schema JSON;
- replaces `description` values with empty strings;
- treats `required`, `enum`, and `type` lists as unordered by sorting them;
- preserves the structural shape of objects, arrays, field names, and types.

Cases whose normalized fingerprint matches the target schema become same-schema candidates. The provider then computes a global embedding similarity between the current task and each candidate. The task representation combines the task identifier, instruction, and the textual representation of each top-level schema field. For a case, the analogous text is built from the case id, case instruction, and its field texts. The default embedding model is `BAAI/bge-small-en-v1.5` through `fastembed`, and vectors are L2-normalized before cosine similarity is computed.

The default same-schema similarity threshold is `0.6`. If at least two same-schema candidates meet the threshold, the top two are selected and marked as `schema_match=True`. This enables the compact same-schema prompt layout described in Section 7.5.

This same-schema stage is deliberately stricter than ordinary semantic retrieval. It first requires structural schema identity after description removal/canonicalization, and only then uses embeddings to rank candidate examples within that same schema family. If fewer than two candidates pass the similarity threshold, the system does not use the compact same-schema layout and falls back to field-level retrieval.

### 7.3 Field-Level Retrieval Fallback

If same-schema retrieval does not produce enough examples, the provider falls back to field-level retrieval. The target schema is decomposed into top-level field specifications. For each field, the retriever records:

- field name;
- field description;
- a textual type representation;
- a coarse type class such as `string`, `boolean`, `numeric`, `enum`, `object`, or `array[...]`;
- an embedding text of the form `name (type): description`.

Candidate FSP cases are decomposed in the same way from their schemas, not from their outputs. The retriever embeds all query and candidate field texts and computes cosine similarities between compatible fields. Compatibility constrains comparisons by coarse type class, so for example an enum field is not aligned with an arbitrary object field. Nullable and non-nullable versions of the same base type remain compatible because nullability is ignored for the coarse type class.

For each candidate case, the retriever constructs a similarity vector with one entry per target top-level field. Each entry is the best compatible field similarity found in that candidate. Negative similarities are clipped to zero. The candidate's field score is the L2 norm of this vector.

The submitted runtime does not load a prebuilt `data/fsp_index` for this extraction retrieval path. It constructs the candidate field texts from the in-repository FSP cases and embeds them at runtime. The repository contains index-building utilities and prebuilt-index paths, but those are not called by `RagExtractionFspProvider.retrieve()`.

If the embedding path fails or produces no usable candidate, the implementation falls back to a lexical/schema ranker. This fallback builds a schema profile for the query and each case, then scores candidates with explicit weights: `+100` for exact canonical schema fingerprint match, `+8` per compatible top-level field fingerprint, `+4` per matched schema/resource/field tag, `+2` per overlapping field name, up to `+6` for shared text terms, `+2` for domain-term overlap, and a small penalty for long example source text. Results with non-positive scores are discarded, and remaining candidates are sorted by descending score with resource order as the tie-breaker.

### 7.4 Complementary Pair Selection

For `top_k=2`, field-level retrieval selects a pair rather than independently taking the two highest-scoring cases. For candidate similarity vectors `v1` and `v2`, the pair score is:

```text
norm(v1 + v2) + norm(v1 - v2)
```

The first term rewards joint relevance and broad field coverage. The second term rewards complementarity: two cases with different strengths across fields receive credit for being non-redundant. The tie-breakers prefer higher total individual field score and then earlier resource order. This makes the selected demonstrations both relevant to the target schema and diverse in the fields they best illustrate.

### 7.5 Same-Schema Prompt Layout

When all selected RAG examples are same-schema matches, `src/gensie/prompts/extraction_layouts.py` uses a compact same-schema layout. The shared target schema is rendered once, not repeated inside every example. The examples then show their instruction, source text, and expected output.

This differs from the general RAG layout, where each example may carry its own schema context because the examples can come from related but non-identical schemas. Same-schema prompting is available for the direct Pydantic pipeline and for the top-level reasoning pipeline.

The Docker configuration sets `GENSIE_FSP_RAG_USE_ENRICHED_DESCRIPTIONS=1`. When this environment variable is enabled and the compact same-schema layout is active, the prompt builder can override prompt-side field descriptions with enriched descriptions stored in the selected FSP cases. These enriched descriptions affect the schema text shown in the prompt; they do not change the target schema or the structured generation schema. To verify: confirm the exact environment used for the submitted evaluation before describing enriched descriptions as always active.

## 8. Reasoning-Augmented Extraction

Reasoning-augmented extraction is used by `enriched-inline-reasoning-rag` and by two of the four trial groups inside `mixed-extractors-self-consistency-rag`.

The submitted reasoning mode is top-level only. Each root field is temporarily transformed into a `{reasoning, value}` object. The model is expected to use the `reasoning` field for local evidence-based deliberation: identifying relevant fragments, explaining why evidence is present or absent, and justifying the final value. The `value` field must contain the actual schema value.

This mechanism changes the prompt schema and the generation schema, but not the final interface. After generation, the system removes the wrapper and returns only the values in the original schema shape. Reasoning is therefore an internal scaffold for generation, not an explanation returned to the evaluator.

## 9. Postprocessing and Output Normalization

Postprocessing is deterministic and conservative. It is implemented across `src/gensie/sampling/single.py`, `src/gensie/runtime/unicode.py`, `src/gensie/schemas/reasoning.py`, and `src/gensie/schemas/coercion.py`.

The submitted pipelines perform the following steps:

- Parse the model response as JSON.
- Recursively clean literal Unicode escape artifacts such as `\u00e1` when they appear inside strings.
- Normalize strings to Unicode NFC.
- If reasoning wrappers were used, unwrap top-level `{reasoning, value}` structures and discard the reasoning from the final output.
- Recursively convert string values equal to `"null"` into JSON `null` only where the target schema permits null.
- In the heuristic aggregation pipeline, apply nullable-string null coercion again after aggregation.
- Treat parse or wrapper-unwrapping failures as invalid extraction records rather than attempting semantic repair.

These steps do not perform semantic repair. They do not infer missing facts, fill absent fields from external knowledge, or change a value merely because it seems unlikely. Their purpose is to clean common formatting artifacts and align the final object with the schema interface.

## 10. Self-Consistency and Aggregation

Self-consistency is used only by `mixed-extractors-self-consistency-rag` among the final submitted pipelines. The pipeline requests four trials: two direct RAG extractions and two inline-reasoning RAG extractions, interleaved as reasoned/direct/reasoned/direct. The trial count can be affected by runtime budget configuration, but the submitted spec requests four.

Each trial produces a complete candidate JSON object after its own postprocessing. The heuristic aggregator then combines only valid candidates recursively according to the target schema. If all trials fail to parse or unwrap, the aggregator returns an error record instead of fabricating an extraction.

Self-consistency trials receive generation options from environment variables. The default self-consistency temperature is `GENSIE_SC_TEMPERATURE=0.5`; `GENSIE_SC_FIRST_TEMPERATURE` can override only the first trial. Optional `GENSIE_SC_TOP_P`, `GENSIE_SC_MAX_TOKENS`, and `GENSIE_SC_TOP_K` values are forwarded to the model request when present. The two single-pass submitted pipelines do not set these self-consistency generation options.

Aggregation behavior by value type is:

- Scalars: cluster or vote among non-null candidates. Enums, booleans, integers, and numbers use exact matching. Strings use schema-aware string similarity, with a default scalar string threshold of `0.78`.
- Nulls: null is counted separately. For nullable fields, null wins only when its support is strictly greater than the best non-null support. Ties do not default to null.
- Objects: aggregate field by field. Optional non-root properties are included only when their support meets the configured support threshold.
- Arrays: collect items from all candidate arrays, deduplicate very similar items within a single trial using a default threshold of `0.96`, cluster items across trials, and select a final array candidate.
- Arrays of objects: optionally detect an identity-like field, such as a required name field, and use it to improve item matching.

Array aggregation uses schema-aware similarity and a recall-biased MBR-style selector. Candidate arrays are generated from clustered items using support-threshold candidates and a greedy MBR candidate. The default support floor is `2` for both simple items and object items, and additional support floors are derived from ratios `0.40`, `0.50`, and `0.60` of the number of observed arrays. Original observed arrays are not included as candidates by default. The final selector uses a default MBR tolerance of `0.06`: among candidates within that tolerance of the best score, it chooses the longest candidate array, then the higher-scoring one, then the earlier candidate. This makes the array step recall-biased.

String similarity is lexical by default, using normalization, token overlap, and character n-gram overlap. Environment variables can enable embedding or hybrid string similarity, but the default implementation path is lexical.

The key design point is that the final mixed pipeline is heterogeneous. It combines outputs from complementary extractor configurations before applying schema-aware aggregation. It is therefore different from ordinary self-consistency that repeatedly samples one prompt.

The clustering procedure is greedy and support-based. Each candidate value is represented together with the trial index that produced it. For non-exact clustering, a candidate can join an existing cluster only if no value from the same trial is already in that cluster and if its maximum similarity to a cluster member reaches the active threshold. This "at most one vote per trial per cluster" constraint matters for arrays, where a single generated list may contain duplicate or near-duplicate items. Clusters are sorted by support, where support is the number of distinct trials represented in the cluster, with first occurrence as a tie-breaker.

For scalar values, the selected cluster is represented by a medoid: the member whose average schema-aware similarity to other members in the cluster is highest. This preserves an actually generated value rather than synthesizing a new string or object. For exact types, including enums, booleans, integers, and numbers, clustering groups values by canonical JSON equality.

The default lexical string similarity normalizes strings with NFKD, removes diacritics, lowercases, and collapses whitespace. Its score combines exact normalized equality, token multiset F1, and character 3-gram F1 with weights `0.15`, `0.45`, and `0.40`, respectively. Exact normalized equality returns `1.0`.

Object similarity is field-weighted. Enum, numeric, and boolean fields receive weight `1.10`; string fields receive weight `1.20`; array fields receive weight `0.90`; other fields receive weight `1.00`. Missing fields contribute no similarity for that field when only one object contains the field. Array similarity uses greedy bipartite matching over item similarities and computes a Jaccard-like score `matches / (len(a) + len(b) - matches)`, where `matches` is the sum of matched pair similarities.

For object arrays, the identity-field heuristic scores candidate fields inside the item schema. It rewards required fields, free string fields, and names/descriptions such as `text`, `name`, `title`, `entity`, `mention`, `source`, `ingredient`, `symptom`, or `reaction`. It penalizes attribute-like fields such as `label`, `category`, `type`, `probability`, `severity`, `amount`, `unit`, `date`, `year`, `count`, `number`, and numeric/boolean/enum types. The default identity field is accepted when the best score is at least `8.0`; a margin of at least `3.0` gives high confidence, while a sufficient score with smaller margin gives medium confidence. When an identity field is selected, object-array item clustering uses identity-string similarity with default threshold `0.62`.

## 11. Component Interactions

The submitted system changes behavior depending on which components are active:

- RAG plus Pydantic schema prompting: retrieved examples are inserted into a schema-guided extraction prompt; the target schema is still rendered explicitly for the current task.
- RAG plus same-schema prompt layout: if two selected examples share the normalized target schema, the schema is shown once and examples are rendered compactly.
- RAG plus reasoning wrappers: examples are rendered in the same wrapped output format expected from the current extractor, so top-level fields contain `reasoning` and `value` during generation.
- Reasoning wrappers plus generation schema transformation: top-level fields are wrapped before building the strict response format, so the model is constrained to return reasoning/value objects.
- Reasoning wrappers plus postprocessing: the wrapper is removed before final output and before heuristic aggregation in the mixed pipeline.
- Self-consistency plus heterogeneous extractor configurations: aggregation operates over candidates generated by both the direct and reasoned pipelines.
- Self-consistency plus postprocessing: each trial is normalized first; aggregation then combines already-cleaned candidate values and performs a final nullable-string null coercion.
- Null coercion plus schema nullability: string `"null"` is converted to JSON `null` only if the corresponding schema position permits null.
- Field-level RAG plus schema field classification: field embeddings are compared only under coarse type compatibility constraints.
- Same-schema retrieval plus schema fingerprinting: the compact prompt is enabled only after normalized schema fingerprint matching and global task similarity filtering.

These interactions are important for paper writing. For example, reasoning is not just an extra prompt instruction; it also changes the structured generation schema and the output postprocessor. Likewise, RAG is not just nearest-neighbor text retrieval; it can switch the prompt layout when schema identity is detected.

## 12. Design Rationale

The final system appears to be organized around six technical choices:

- Make variable schemas more interpretable to the model by rendering them in Pydantic-style form.
- Retrieve examples that are relevant to the target schema and, when possible, complementary rather than redundant.
- Use strict structured generation and all-required object properties to reduce omitted fields.
- Add field-local reasoning in one extractor variant without changing the final output interface.
- Reduce variance by combining direct and reasoned extractor styles in the mixed pipeline.
- Apply deterministic cleanup for common formatting artifacts while avoiding semantic post-hoc correction.

Together, these choices target the central difficulty of schema-variable information extraction: the model must understand a new schema, ground values in a Spanish source text, and return a complete valid JSON object.

## 13. Notes for Paper Writing

Implementation-supported claims:

- The submitted participant exposes exactly `enriched-schema-rag`, `enriched-inline-reasoning-rag`, and `mixed-extractors-self-consistency-rag`.
- All three submitted pipelines use retrieval-augmented few-shot prompting.
- The two single-pass submitted pipelines differ mainly in whether top-level reasoning/value wrappers are used.
- The mixed pipeline combines two direct RAG trials and two top-level reasoning RAG trials, then applies schema-aware heuristic aggregation.
- The system uses Pydantic-style prompt schemas and strict JSON Schema response formats.
- The implementation suggests that complementary few-shot examples are selected using same-schema retrieval when possible and field-level diversity otherwise.
- Reasoning generated by the inline-reasoning pipeline is internal and is discarded before returning the final prediction.

Claims that require separate experimental evidence:

- Do not claim that RAG improved performance unless an ablation or official result supports it.
- Do not claim that reasoning wrappers improved performance unless supported by experiments.
- Do not claim that self-consistency improved performance unless supported by experiments.
- Do not claim that all FSP examples were manually written from scratch; the repository supports synthetic/curated examples with review, but exact authorship should be verified.
- Do not describe judge aggregation, PARSE-style extraction, deep reasoning, or fixed/super FSP variants as part of the final submitted system.
- Do not report performance numbers from local one-task files or failed experimental result files as final shared-task results.

## 14. Open Questions / Items to Verify

- To verify: the exact model and inference backend used in the final official run are not fixed in the submitted pipeline specs. The runtime receives the model name from the request.
- To verify: single-pass submitted pipelines do not set explicit temperature or top-p options in the spec; server or model defaults apply. Self-consistency trials default to a temperature of `0.5` unless environment variables override it.
- To verify: the submitted mixed pipeline requests four trials, but runtime budget environment variables can cap the number of allowed trials.
- To verify: the Docker configuration enables enriched RAG descriptions, but this remains environment-controlled through `GENSIE_FSP_RAG_USE_ENRICHED_DESCRIPTIONS`.
- To verify: the implementation warms the `fastembed` model cache in the container. The exact availability of that cache in a final evaluation image should be confirmed.
- To verify: the server's `/run` endpoint has a default query value of `pipeline=baseline`, but `OfficialParticipant` exposes only the three submitted pipelines. The evaluator should explicitly request a submitted pipeline name.
- To verify: the repository contains prebuilt/index-related RAG utilities, but the submitted extraction RAG path embeds the in-repository FSP cases at runtime rather than loading a prebuilt `data/fsp_index` artifact.
- To verify: some design documents are outdated. For example, older modularization notes predate the final RAG and aggregation paths, and same-schema prompting support in code is broader than some proposal text suggests.
