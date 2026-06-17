---
kind: method
sources: ["[[2026-06-17-language-models-are-few-shot-learners]]", "[[2026-06-17-learning-to-retrieve-prompts-icl-arxiv]]", "[[2026-06-17-learning-to-retrieve-prompts-icl-acl]]", "[[2026-06-17-sentence-bert-sentence-embeddings]]"]
created: 2026-06-17
updated: 2026-06-17
ingestion_runs: ["2026-06-17T15:21"]
---

# Dynamic Few-Shot Example Retrieval

Dynamic few-shot example retrieval treats the prompt examples shown to a language model as an inference-time selection problem. The baseline context is in-context learning: a pretrained model is given instructions and a small number of input-output demonstrations, then asked to solve a new instance without gradient updates.

The prompt-retrieval papers make the key observation that downstream performance can vary substantially with the chosen in-context examples. Rather than selecting examples randomly or by a fixed hand-written prompt, they train an efficient retriever that chooses training examples to use as prompts at test time. Their EPR procedure uses a scoring language model to label candidate examples as good or bad prompts, then trains a dense retriever from that signal.

Sentence-BERT is relevant as retrieval infrastructure rather than as an extraction method by itself. It turns sentences into semantically meaningful vectors that can be compared with cosine similarity, making semantic search and clustering far cheaper than pairwise cross-encoder comparison. This supports the general idea that example retrieval can be implemented as a fast nearest-neighbor operation over candidate examples.

## Design Pattern

For a GenSIE-style extractor, dynamic retrieval can be framed as selecting demonstrations that match the current schema, field semantics, domain, or input pattern. The retrieved examples become a compact adaptation layer: they can show output conventions, field-level interpretations, and edge cases without finetuning the base model.

## Useful Contrast

Prompt retrieval is not the same as retrieval-augmented generation over factual documents. The retrieved items are demonstrations, not necessarily external evidence. For DRILLER GenSIE, this distinction is useful if the system retrieves few-shot structured cases rather than passages to quote.

## Background Use

Use this page to justify a paragraph that says in-context learning is powerful but example choice matters; retrieval offers a principled way to select demonstrations dynamically. If DRILLER uses curated or synthetic few-shot resources, describe them as a local demonstration corpus unless the paper explicitly trains a prompt retriever.
