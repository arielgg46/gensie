---
kind: method
sources: ["[[2026-06-17-minimum-bayes-risk-decoding-smt]]", "[[2026-06-17-self-consistency-chain-of-thought]]"]
created: 2026-06-17
updated: 2026-06-17
ingestion_runs: ["2026-06-17T15:21"]
---

# Minimum Bayes-Risk Decoding

Minimum Bayes-Risk decoding is a decision rule for choosing a candidate output that minimizes expected loss. Kumar and Byrne present it for statistical machine translation: given alternative translations and a loss function tied to an evaluation criterion, the decoder selects the translation that is closest on average to likely translations under that loss.

The paper is useful for GenSIE background because it separates candidate generation from candidate selection. A model or system can generate an n-best list, then a decision rule chooses among candidates according to a task-specific loss. This is different from maximum probability decoding, which chooses the individually most likely candidate without directly optimizing the downstream loss.

MBR also highlights the importance of the loss function. In machine translation, losses can be based on strings, alignments, or syntactic structure. In schema-guided extraction, an analogous loss might consider field-level exact match, normalized value equivalence, missing fields, spurious fields, type validity, or schema-level consistency.

## Relation To Self-Consistency

Self-consistency can be viewed as a simple consensus method over sampled answers. MBR is more general: it can choose a candidate by expected utility under a structured loss, not just by majority agreement on a final answer. The cost is that MBR requires a candidate set, an estimated distribution, and a meaningful loss or similarity function.

## Background Use

Use this page to justify aggregation or reranking language in the paper. Safe wording: "MBR-style decision rules motivate selecting among candidate extractions according to task-specific agreement or loss." Avoid saying DRILLER optimizes MBR unless the implementation actually defines and minimizes such a loss.
