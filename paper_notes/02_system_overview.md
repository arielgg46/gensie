# 02 System Overview

## Purpose of This Section

This note supports the system overview section of the paper. It should define the three submitted pipelines, explain the common extraction architecture, and show how the components interact. The overview should be detailed enough that later method sections can expand each component without forcing the reader to reconstruct the whole runtime flow.

The final submitted pipelines are:

- `enriched-schema-rag`, abbreviated as Schema-RAG after first definition;
- `enriched-inline-reasoning-rag`, abbreviated as Reasoned-RAG after first definition;
- `mixed-extractors-self-consistency-rag`, abbreviated as Mixed-SC after first definition.

Only these three should be described as submitted systems. Other implemented variants are not part of the final submission and should not appear in the main system overview except possibly as explicitly excluded alternatives in limitations or future work.

## Pipeline Summary Table

| Submitted pipeline | Short alias | RAG | Schema rendering | Temporary reasoning wrappers | Requested trials | Aggregation | Main role |
|---|---|---:|---|---|---:|---|---|
| `enriched-schema-rag` | Schema-RAG | yes | Pydantic-style schema view | no | 1 | none beyond deterministic postprocessing | Direct schema-guided extraction with retrieved demonstrations. |
| `enriched-inline-reasoning-rag` | Reasoned-RAG | yes | Reasoned Pydantic-style schema view | top-level `{reasoning, value}` wrappers | 1 | wrapper unwrapping plus deterministic postprocessing | Field-local evidence reasoning before returning final values. |
| `mixed-extractors-self-consistency-rag` | Mixed-SC | yes | heterogeneous: Schema-RAG and Reasoned-RAG views | only in the Reasoned-RAG-style trials | 4 requested | recursive schema-aware heuristic self-consistency | Combine complementary extractor styles and reduce variance. |

## Shared Extraction Architecture

All three submitted pipelines share the same broad extraction architecture. Each receives a GenSIE task with a Spanish source text, an instruction, and a target schema. The system then builds a schema-guided prompt, optionally retrieves few-shot demonstrations, sends a structured generation request to an OpenAI-compatible chat backend, parses the JSON response, applies deterministic postprocessing, and returns a JSON object in the original target schema shape. In Mixed-SC, this process is repeated for several trials and followed by aggregation.

The useful high-level flow for the final paper is:

```text
input task -> schema rendering -> RAG retrieval -> prompt construction -> strict JSON generation -> postprocessing -> optional aggregation -> final JSON
```

The overview should emphasize that these steps are not independent add-ons. Schema rendering informs the model's interpretation of the target fields. RAG retrieval selects examples based on schema similarity and field compatibility. Prompt construction presents the instruction, source text, schema, rules, and examples in a controlled layout. The strict JSON response format constrains the model to return a JSON object. Postprocessing normalizes the output and removes temporary reasoning structures. Aggregation, when present, operates only after each trial has produced a final-shape candidate.

## Schema-RAG

Schema-RAG is the direct single-pass extraction pipeline. It receives the task, renders the target schema in a Pydantic-style form, retrieves up to two few-shot examples, constructs the Spanish extraction prompt, and requests a structured JSON response. It does not use reasoning/value wrappers and does not perform self-consistency. Its output after deterministic normalization is returned directly.

The purpose of Schema-RAG is to provide a strong schema-readable extractor with minimal extra inference cost. It relies on two forms of schema control. First, the prompt contains a readable schema view that makes field names, types, descriptions, enums, arrays, and nested objects visible to the model. Second, the generation request includes a strict response format derived from the target schema. These two schema views serve different purposes: the prompt schema supports semantic interpretation, while the response format supports structural validity.

Schema-RAG is useful to present as the cleanest instantiation of DRILLER's core extraction hypothesis: if the model is given a readable schema and demonstrations selected for schema relevance, it can align its generation with a schema that may be unseen at development time.

## Reasoned-RAG

Reasoned-RAG keeps the same RAG machinery and general prompt organization as Schema-RAG but changes how top-level fields are represented during generation. Each top-level field is temporarily wrapped as an object with two properties: `reasoning` and `value`. The prompt schema mirrors this transformation using a `Reasoned[T]` style notation, where `T` is the original field type.

The reasoning string is intended to make the model perform field-local evidence analysis. It should identify what the field asks for, point to relevant evidence or absence of evidence, and justify the final value. The `value` property contains the actual answer in the original field type. After generation, the system discards the reasoning and unwraps each top-level field to recover the final schema shape.

The overview should be clear that Reasoned-RAG does not return explanations to the evaluator. It uses reasoning as an internal generation scaffold. This matters because the final output still conforms to the original GenSIE target schema. It also matters for the later self-consistency section: Mixed-SC aggregates unwrapped Reasoned-RAG outputs, not raw reasoning-wrapper objects.

## Mixed-SC

Mixed-SC is the heterogeneous self-consistency pipeline. It requests four extraction trials: two Reasoned-RAG-style trials and two Schema-RAG-style trials, interleaved in the intended order reasoned/direct/reasoned/direct. Each trial independently performs retrieval, prompt construction, structured generation, parsing, reasoning unwrapping when needed, and deterministic cleanup. The aggregator receives final-shape JSON candidates.

This design is different from standard self-consistency that repeatedly samples the same prompt. DRILLER uses heterogeneous self-consistency because the two extractor styles have complementary biases. Direct extraction can be concise, structurally faithful, and less token-expensive. Reasoning-augmented extraction can be more evidence-sensitive for fields that require semantic mapping, null decisions, or careful interpretation of field descriptions. Mixed-SC attempts to combine these strengths while reducing variance across individual model calls.

The final aggregation is recursive and schema-aware. It does not simply choose one candidate object. Scalars, strings, nulls, objects, arrays, and arrays of objects are handled with type-specific rules. For objects, aggregation proceeds field by field. For arrays, items are clustered and selected with a recall-biased strategy. For arrays of objects, identity-like fields may be used to improve matching across candidates.

The paper should describe the four-trial count as requested by the submitted pipeline, subject to runtime budget limits. The source notes indicate that the execution runner includes trial-budget logic. Therefore, a careful wording is "Mixed-SC requests four trials, subject to runtime budget constraints."

## End-to-End Data Flow in More Detail

The end-to-end flow begins with a GenSIE task. The system uses the task instruction, source text, target schema, and task identifier for prompt construction and retrieval. The expected output, if present in local development runs, is not used as evidence for prediction.

The schema rendering step creates a prompt-facing representation. For Schema-RAG, this is a Pydantic-style schema. For Reasoned-RAG, the same basic schema is modified so that root fields appear as `Reasoned[T]`. This prompt schema is placed in the extraction prompt together with extraction rules and examples.

RAG retrieval selects up to two demonstrations. The retrieval system first attempts same-schema retrieval using normalized schema fingerprints. If two sufficiently similar same-schema examples are found, the prompt uses a compact same-schema layout. If not, retrieval falls back to field-level matching, where top-level fields from the target schema are compared to fields in the demonstration corpus using compatible type classes and embedding similarity.

Prompt construction separates the components of the task: the instruction, source text, rules, schema, and examples. The examples are not presented as evidence for the current instance; they demonstrate how analogous schemas and instructions map source text to outputs. The rules emphasize grounded extraction, complete schema coverage, exact enum labels, and `null` for missing information when permitted.

The generation step uses an OpenAI-compatible chat request with a system message, a user message, and a strict JSON response format. For Reasoned-RAG trials, the response format is built after injecting reasoning/value wrappers. For the submitted non-baseline pipelines, declared object properties are recursively made required during generation to reduce omitted fields. This does not change the final target schema; it changes only the generation interface.

Postprocessing parses the model output, normalizes Unicode artifacts, unwraps reasoning/value objects when present, and converts string `"null"` to JSON `null` only where the schema allows null. Semantic repair is deliberately avoided. If parsing or unwrapping fails, a trial is treated as invalid.

For Schema-RAG and Reasoned-RAG, the postprocessed object is the final output. For Mixed-SC, valid candidate objects are sent to the schema-aware aggregator. The aggregator produces one final JSON object, followed by conservative null coercion where appropriate.

## Component Interactions

The main interactions to highlight in the overview are:

- RAG and schema prompting work together: retrieved examples are useful because they are selected according to schema and field relevance, and they are rendered in the same output style expected from the current extractor.
- Reasoning changes both prompt and generation schema: it is not only an instruction to "think"; it creates temporary structured fields that are later removed.
- Same-schema retrieval changes the prompt layout: if examples share the target schema, the schema can be shown once and examples can focus on instruction, source text, and output.
- Postprocessing is a prerequisite for aggregation: Mixed-SC aggregates normalized final-shape candidates, not raw model responses.
- Null handling appears in multiple places: prompting instructs grounded nulls, structured generation preserves nullable positions, postprocessing coerces string `"null"` only where legal, and aggregation treats null as a separate candidate with cautious support logic.

The overview should leave the reader with the sense that DRILLER is a modular but coherent inference-time system. Its central contribution is not any single trick but the alignment of schema-readable prompting, schema-aware demonstration retrieval, temporary field-local reasoning, and recursive schema-aware aggregation.

