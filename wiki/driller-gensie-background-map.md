---
kind: map
sources: ["[[2026-06-17-language-models-are-few-shot-learners]]", "[[2026-06-17-learning-to-retrieve-prompts-icl-arxiv]]", "[[2026-06-17-learning-to-retrieve-prompts-icl-acl]]", "[[2026-06-17-sentence-bert-sentence-embeddings]]", "[[2026-06-17-grammar-constrained-decoding-structured-nlp]]", "[[2026-06-17-jsonschemabench-structured-outputs]]", "[[2026-06-17-chain-of-thought-prompting]]", "[[2026-06-17-self-consistency-chain-of-thought]]", "[[2026-06-17-minimum-bayes-risk-decoding-smt]]"]
created: 2026-06-17
updated: 2026-06-17
ingestion_runs: ["2026-06-17T15:21"]
---

# DRILLER GenSIE Background Map

This compact wiki organizes the pulled sources around inference-time techniques relevant to a DRILLER GenSIE background section: [[dynamic-few-shot-example-retrieval]], [[structured-constrained-generation]], [[reasoning-scaffolds]], [[self-consistency-decoding]], and [[minimum-bayes-risk-decoding]].

## Core Thread

The shared theme is that modern language-model systems can be adapted at inference time without changing model weights. GPT-3 frames this broadly through zero-, one-, and few-shot in-context learning, where examples and instructions condition an otherwise fixed model. Prompt-retrieval work then asks how those examples should be selected, showing that in-context performance is sensitive to the chosen demonstrations and that retrieval can make selection more systematic.

Structured generation work addresses a different failure mode: even when a model has the right semantic content, machine-consumed outputs must obey a format or schema. Grammar-constrained decoding and JSON-Schema-based constrained decoding intervene during generation so invalid continuations are blocked, while also raising practical questions about coverage, overhead, and semantic quality.

Reasoning-scaffold work adds intermediate natural-language steps to the context or output. Chain-of-thought prompting makes multi-step reasoning explicit; self-consistency replaces one greedy reasoning trace with multiple sampled traces and aggregates the final answers. MBR decoding gives an older decision-theoretic lens: choose the candidate that minimizes expected task loss under a candidate distribution.

## Background Use

For DRILLER GenSIE, these pages support a concise related-work arc:

1. Dynamic few-shot retrieval motivates selecting schema- and instance-relevant examples rather than relying only on fixed prompts.
2. Structured and constrained generation motivates the need for reliable machine-readable outputs in extraction systems.
3. Reasoning scaffolds motivate intermediate deliberation or field-level rationales, while their limitations argue for validation and aggregation.
4. Self-consistency and MBR motivate candidate aggregation as inference-time decision procedures, without implying that DRILLER reports official gains from them unless the paper explicitly does.

## Boundaries

Do not overclaim official GenSIE results from this background corpus. The sources establish prior methods and evaluation patterns, not DRILLER rankings, scores, or causal evidence.
