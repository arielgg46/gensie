---
kind: method
sources: ["[[2026-06-17-grammar-constrained-decoding-structured-nlp]]", "[[2026-06-17-jsonschemabench-structured-outputs]]"]
created: 2026-06-17
updated: 2026-06-17
ingestion_runs: ["2026-06-17T15:21"]
---

# Structured And Constrained Generation

Structured generation is the problem of producing outputs that are not just fluent, but valid under a required format, vocabulary, grammar, or schema. This matters for information extraction because outputs are consumed by evaluation scripts and downstream systems rather than only read by humans.

Grammar-constrained decoding formulates valid outputs as a formal grammar and modifies decoding so only grammar-compliant continuations remain available. Geng et al. emphasize that many structured NLP tasks can be represented this way, including closed information extraction, entity disambiguation, and constituency parsing. Their input-dependent grammars are especially relevant when the valid output space depends on the current input.

JSONSchemaBench shifts the discussion from task-specific grammars to the modern structured-output stack built around JSON Schema. It frames constrained decoding along three practical dimensions: efficiency, coverage of schema features, and quality of generated outputs. It also distinguishes declared coverage, empirical coverage, true coverage, and compliance rate, which is useful vocabulary for avoiding vague claims that a system "supports" a schema.

## Design Pattern

Constrained decoding can be described as an inference-time reliability layer. It does not teach the model new facts; it narrows the next-token choices so generation remains inside a valid output language. For extraction systems, this separates semantic correctness from syntactic validity: a valid JSON object can still contain wrong field values, but invalid structures can be ruled out by construction when the grammar or schema is correctly enforced.

## Practical Caveats

The constrained-generation sources also warn against simple guarantees. Complex schemas can vary in feature support and runtime behavior across engines. Some frameworks may accept a schema but fail to enforce all of its intended semantics, and empirical compliance depends on the model, decoding setup, timeout, and schema complexity.

## Background Use

Use this page to position DRILLER GenSIE near structured-output work. If the system relies on prompting, validation, repair, or schema-aware aggregation rather than hard token masking, call that out as a design choice instead of labeling it constrained decoding.
