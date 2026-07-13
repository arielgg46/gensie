---
type: sota-artifact
phase: plan
slug: driller-gensie-background-related-work-2026-06-17
generated_at: 2026-06-17T15:21
topic: "DRILLER GenSIE Background and Related Work"
language: en
corpus_dir: "./wiki + ./sources"
corpus_pages:
  - wiki/driller-gensie-background-map.md
  - wiki/dynamic-few-shot-example-retrieval.md
  - wiki/structured-constrained-generation.md
  - wiki/reasoning-scaffolds.md
  - wiki/self-consistency-decoding.md
  - wiki/minimum-bayes-risk-decoding.md
  - sources/2026-06-17-language-models-are-few-shot-learners.md
  - sources/2026-06-17-learning-to-retrieve-prompts-icl-arxiv.md
  - sources/2026-06-17-learning-to-retrieve-prompts-icl-acl.md
  - sources/2026-06-17-sentence-bert-sentence-embeddings.md
  - sources/2026-06-17-grammar-constrained-decoding-structured-nlp.md
  - sources/2026-06-17-jsonschemabench-structured-outputs.md
  - sources/2026-06-17-chain-of-thought-prompting.md
  - sources/2026-06-17-self-consistency-chain-of-thought.md
  - sources/2026-06-17-minimum-bayes-risk-decoding-smt.md
dimensions:
  - id: D1
    name: "Schema-guided information extraction"
    axis: "How schemas turn extraction into structured prediction and constrain the meaning of valid outputs."
    sources: ["sources/2026-06-17-grammar-constrained-decoding-structured-nlp.md", "sources/2026-06-17-jsonschemabench-structured-outputs.md"]
  - id: D2
    name: "Retrieval-based in-context demonstrations"
    axis: "How example choice becomes an inference-time retrieval problem."
    sources: ["sources/2026-06-17-language-models-are-few-shot-learners.md", "sources/2026-06-17-learning-to-retrieve-prompts-icl-acl.md", "sources/2026-06-17-sentence-bert-sentence-embeddings.md"]
  - id: D3
    name: "Structured generation"
    axis: "How grammars and schemas enforce machine-readable output formats during decoding."
    sources: ["sources/2026-06-17-grammar-constrained-decoding-structured-nlp.md", "sources/2026-06-17-jsonschemabench-structured-outputs.md"]
  - id: D4
    name: "Reasoning scaffolds"
    axis: "How intermediate steps or rationales are used to decompose model decisions."
    sources: ["sources/2026-06-17-language-models-are-few-shot-learners.md", "sources/2026-06-17-chain-of-thought-prompting.md"]
  - id: D5
    name: "Self-consistency"
    axis: "How multiple sampled reasoning paths are aggregated into a consensus answer."
    sources: ["sources/2026-06-17-chain-of-thought-prompting.md", "sources/2026-06-17-self-consistency-chain-of-thought.md"]
  - id: D6
    name: "MBR-style selection"
    axis: "How candidate generation is separated from loss-aware candidate selection."
    sources: ["sources/2026-06-17-minimum-bayes-risk-decoding-smt.md", "sources/2026-06-17-self-consistency-chain-of-thought.md"]
output_destination: "sota/sota-driller-gensie-background-related-work-2026-06-17.md"
---

# Plan SOTA - DRILLER GenSIE Background and Related Work

The user supplied the mechanism-level ontology directly: schema-guided IE, retrieval-based in-context demonstrations, structured generation, reasoning scaffolds, self-consistency, and MBR-style selection. This plan treats those dimensions as approved and builds a compact report for later use in the paper's Background and Related Work section.
