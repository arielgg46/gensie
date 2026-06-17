---
kind: method
sources: ["[[2026-06-17-chain-of-thought-prompting]]", "[[2026-06-17-self-consistency-chain-of-thought]]", "[[2026-06-17-minimum-bayes-risk-decoding-smt]]"]
created: 2026-06-17
updated: 2026-06-17
ingestion_runs: ["2026-06-17T15:21"]
---

# Self-Consistency Decoding

Self-consistency is an inference-time aggregation strategy for chain-of-thought prompting. Instead of taking one greedy reasoning path, the model samples multiple reasoning paths, extracts their final answers, and chooses the answer with the strongest agreement.

Wang et al. describe this as a sample-and-marginalize procedure: prompt with chain-of-thought exemplars, sample diverse candidate reasoning traces, then marginalize over traces by aggregating final answers. The method is unsupervised and does not require finetuning, an auxiliary verifier, or additional human annotation. Its appeal is that different correct reasoning paths may converge on the same answer, while incorrect paths are less likely to agree.

Self-consistency is closely related to consensus decoding but narrower than MBR. It usually aggregates an answer string or normalized answer value, often by majority vote. MBR instead requires a loss or utility function over candidates and chooses the candidate with minimum expected loss under an estimated distribution.

## Design Pattern

For structured extraction, self-consistency can be adapted when answers can be normalized and compared. Field-level voting, object-level voting, or schema-aware agreement could play the role of answer aggregation. The method becomes harder when outputs are long, nested, or only partially equivalent, because the system must define what counts as the same answer.

## Practical Caveats

Self-consistency increases inference cost because it samples multiple outputs. It also depends on parsing or normalizing final answers; without a reliable equivalence function, agreement can be misleading. For GenSIE prose, treat it as an aggregation idea rather than a guarantee of correctness.

## Background Use

Use this page to motivate candidate-level or field-level aggregation as a way to reduce dependence on a single sample. If DRILLER uses a different aggregation method, self-consistency can be cited as the nearby reasoning-focused precedent.
