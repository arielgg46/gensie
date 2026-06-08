# 01 Introduction and Task Setting

## Purpose of This Section

These notes support the opening sections of the DRILLER GenSIE 2026 system paper. The final paper should introduce GenSIE as a Spanish schema-guided information extraction task in which systems receive a source text, a natural-language extraction instruction, and a target JSON Schema at inference time. The central point is that the system must not merely emit syntactically valid JSON. It must interpret a previously unseen or task-specific schema, understand the intended semantics of each field, ground every value in the provided Spanish text, and represent missing evidence with JSON `null` when the schema permits it.

The first mention of the task should cite the GenSIE 2026 overview paper with `gensie2026overview`. The first mention of the workshop/shared-task setting should cite the IberLEF 2026 overview paper with `iberlef2026overview`. A natural placement is the first paragraph of the introduction: "GenSIE 2026, organized at IberLEF 2026, evaluates schema-guided information extraction from Spanish texts..." with both citations attached.

## Problem Motivation

GenSIE belongs to a family of tasks that are becoming important for language-model-based systems that communicate through structured interfaces. Modern information extraction increasingly asks models to produce JSON objects, API arguments, database records, or other structured data rather than free-form summaries. However, many practical deployments cannot assume a fixed ontology. The desired output schema may vary by document type, user request, domain, or downstream tool. GenSIE therefore treats the schema itself as part of the input: the extractor must adapt to a JSON Schema that defines the target structure for the current instance.

The task is especially demanding because the input text is in Spanish and the schema is variable. A system cannot rely on a fixed label inventory, a fixed slot list, or precomputed extractors for known entity classes. Instead, it must use field names, descriptions, types, enum labels, array structures, and nullability information as dynamic instructions. The schema is not only a validator for the output; it is a semantic specification that tells the model what counts as a correct answer.

The final paper should avoid framing the problem as simply "produce valid JSON." Validity is necessary but insufficient. A JSON object can conform syntactically to the schema while still being wrong in several ways: it may choose the wrong enum label, fill a nullable field with unsupported world knowledge, omit a required array item, invent an object inside a nested list, collapse multiple distinct entities into one string, or treat a field name superficially rather than following its description. DRILLER's narrative should therefore distinguish structural conformance from schema-semantic alignment.

## Why Schema Semantics Matter

Field semantics are central because GenSIE schemas can encode different kinds of extraction behavior within the same formal JSON vocabulary. A string field may ask for a verbatim mention, a normalized name, a brief description, or a longer evidence span. A boolean may require inference from the text rather than a literal word match. An enum may define categories that never appear in the source text and must be selected by interpreting the instruction and field description. Numeric and date fields may require normalization, while arrays require deciding both which items are present and how to represent each item.

Nullability is also semantic. If a field permits `null`, the system must decide whether the source text contains enough evidence to fill it. Returning `null` is not a generic fallback; it is correct only when the requested information is not present or cannot be grounded. Conversely, returning a non-null value can be a hallucination even when the value is true in the real world. The challenge documentation explicitly emphasizes grounding and hallucination traps: a schema may ask for information that is widely known but absent from the source, and the correct response is `null`.

Nested objects and arrays compound this problem. In a flat schema, each field can often be considered independently. In nested structures, a system must preserve relationships among values. For an array of objects, it must decide item boundaries, avoid merging attributes from different entities, and maintain local coherence inside each object. For example, an object item might contain a name, date, role, and classification; extracting all values but assigning one attribute to the wrong item still fails the schema's intended semantics. The paper should present this as one reason DRILLER uses schema-aware prompting and aggregation rather than a purely text-nearest-neighbor strategy.

## Minimal Task Setting

The task input can be described with three main elements:

- a Spanish source text;
- a natural-language extraction instruction;
- a target JSON Schema defining the output object.

The output is a JSON object that should conform to the target schema and contain only information supported by the source text and the instruction. The paper can mention that the schema may include object properties, arrays, nested objects, enum strings, nullable types, numbers, booleans, and field descriptions. It should also mention that GenSIE evaluates both structural validity and value accuracy using a flattened schema scoring metric, with exact matching for rigid values and semantic/lexical comparison for free-text values. Do not over-describe the metric in the introduction; reserve details for the task/evaluation paragraph or experimental setup.

The challenge setting is model-agnostic. At evaluation time, the participant system receives the model name and must call the organizer-provided OpenAI-compatible inference endpoint. The final submitted system should therefore be described as an inference-time extraction method rather than a trained model. DRILLER does not fine-tune model weights. Its contribution lies in prompt design, schema representation, retrieval of demonstrations, temporary reasoning structures, postprocessing, and self-consistency aggregation.

## DRILLER's High-Level Response

DRILLER treats GenSIE as schema-variable Spanish schema-guided information extraction. The core difficulty is aligning the model's interpretation of each field with a task-specific schema. The submitted system responds with four main methodological ideas.

First, DRILLER renders schemas in a schema-readable form. Instead of showing the model only raw JSON Schema, the submitted pipelines use a compact Pydantic-style view that exposes object structure, field names, types, enum labels, nullable types, and descriptions in a format likely to be more interpretable to instruction-tuned models. This prompt schema is paired with a strict JSON Schema response format for generation, so readability and structured output constraints are handled separately.

Second, DRILLER retrieves few-shot demonstrations that are selected with schema awareness. The final pipelines use retrieval-augmented few-shot prompting. When examples with the same normalized schema are available, they are preferred and shown in a compact same-schema layout. Otherwise, the system falls back to field-level retrieval, decomposing schemas into top-level fields and matching fields by type-compatible semantic similarity. The retrieval design intentionally selects two examples that are both relevant and complementary, so that the prompt demonstrates multiple possible outcomes rather than a single output pattern.

Third, one submitted extractor uses temporary reasoning/value transformations. For top-level fields, the model is asked to produce a wrapper containing a reasoning string and a final value. The reasoning string is intended to make the model articulate field-local evidence, absence of evidence, and semantic mappings before committing to the field value. This wrapper is temporary: it changes the generation process but is removed before the final challenge output.

Fourth, the final mixed pipeline uses heterogeneous self-consistency. Instead of sampling one prompt repeatedly, it combines direct schema-RAG trials with reasoning-augmented RAG trials. The resulting candidates are already in the final schema shape before aggregation. A recursive schema-aware heuristic aggregator then combines scalar values, nulls, objects, arrays, and arrays of objects according to type-specific logic.

## Suggested Paper Claims

The introduction can safely claim that DRILLER submitted three pipelines built around schema-readable prompting, field-aware retrieved demonstrations, temporary reasoning wrappers, deterministic normalization, and heterogeneous schema-aware self-consistency. It can claim that all three submitted pipelines use RAG and that the mixed pipeline combines direct and reasoning-augmented extractors. It should not claim that any individual component improved performance unless official results or ablations are later provided.

The paper should use the aliases after first definition:

- `enriched-schema-rag` as Schema-RAG;
- `enriched-inline-reasoning-rag` as Reasoned-RAG;
- `mixed-extractors-self-consistency-rag` as Mixed-SC.

The final introduction should not discuss unused components such as judge aggregation, PARSE-style extraction, deep reasoning wrappers, selective reasoning, static super-FSP prompting, or verbatim entity pre-phases. These were implemented or explored but are not part of the submitted participant surface.

## Citation Placement Notes

Use `gensie2026overview` when introducing GenSIE and when describing the official task formulation and evaluation. Use `iberlef2026overview` when situating the task within IberLEF 2026. Later sections can cite these again when discussing official metrics or shared-task results, but the introduction should establish both citations early.

