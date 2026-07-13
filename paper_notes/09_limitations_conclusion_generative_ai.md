# 09 Limitations, Conclusion, and Generative AI Declaration

## Purpose of This Section

This note prepares source material for the paper's limitations, conclusion, and mandatory Declaration on Generative AI section. The final paper should be honest about the system's constraints while highlighting the coherent methodological contribution: DRILLER addresses schema-variable Spanish schema-guided extraction with schema-readable prompting, field-aware retrieved demonstrations, temporary reasoning/value transformations, deterministic postprocessing, and heterogeneous schema-aware self-consistency.

## Limitations

### Dependence on Model Capability

DRILLER is an inference-time system that relies on the organizer-provided language model. It does not fine-tune model weights or train a task-specific extractor. As a result, its performance is bounded by the model's ability to follow instructions, interpret schemas, use Spanish evidence, and comply with structured output constraints. Schema-readable prompts and strict response formats can improve the interface, but they cannot guarantee semantic correctness when the model lacks the necessary reasoning or language understanding.

The official evaluation uses multiple models. Because the pipeline receives the model name at runtime, it is designed to be model-agnostic. However, model-agnostic does not mean model-invariant. Different models may respond differently to Pydantic-style schemas, reasoning wrappers, RAG examples, or strict response formats. The final paper should discuss model sensitivity if per-model results are released.

### Prompt and Token Cost

The system uses detailed prompts, schema renderings, and retrieved examples. Reasoned-RAG adds reasoning strings for top-level fields, and Mixed-SC requests four trials. These choices can improve robustness in principle, but they increase token usage and latency relative to a single minimal prompt. The challenge includes efficiency considerations, so the final paper should report official token usage and discuss the trade-off between robustness and cost.

This limitation is particularly important for Mixed-SC. It may produce more stable outputs, but it makes multiple model calls and includes reasoning tokens in half of the requested trials. If official results show only modest gains over single-pass pipelines, the paper should acknowledge the cost-performance trade-off.

### Reliance on Demonstration Corpus Coverage

The RAG component depends on a local synthetic/curated FSP corpus. The corpus is designed to cover diverse schema phenomena, but it cannot cover every possible domain, schema pattern, or field interpretation. For unseen schemas, field-level retrieval may find useful analogies, but those analogies may still be imperfect. Retrieval can also select examples that bias the model toward an inappropriate enum label, array cardinality, or null behavior.

Same-schema retrieval is precise when matching cases exist, but it is unavailable for genuinely new schemas without matching fingerprints. Field-level fallback is more flexible but less exact. The final paper should present RAG as a schema-alignment aid, not as a guarantee of coverage.

### Heuristic Aggregation

Mixed-SC uses deterministic heuristic aggregation rather than a learned or model-judged aggregator. This has advantages: it is transparent, schema-aware, and does not require additional model calls for judging. It also has limitations. Similarity thresholds may merge distinct values or split equivalent values. Null support rules may be too conservative or too aggressive depending on candidate quality. Array selection is recall-biased and may include extra items if several trials over-extract. Identity-like field detection for object arrays can fail when the schema lacks a clear identity field.

The aggregator cannot recover information that no trial produced. It can combine and select among candidates, but it does not read the source text independently. Its quality therefore depends on the diversity and correctness of the generated candidates.

### No Semantic Post-Hoc Verification

Postprocessing deliberately avoids semantic repair. It normalizes Unicode, unwraps reasoning values, and coerces string `"null"` to JSON null only when schema-permitted. It does not verify every generated value against the source text after generation. Unsupported inference can therefore remain in the final output if the model or aggregator selects it.

This limitation follows from the design choice to keep the system simple, deterministic after generation, and within inference budgets. A future system could add evidence verification or field-level entailment checks, but those are not part of the submitted pipelines.

### Reasoning Is Internal and Not Evaluated Directly

Reasoned-RAG generates reasoning strings, but these strings are discarded before final output. The official evaluator scores only the final JSON values. Therefore, even if the reasoning text appears plausible, it is useful only insofar as it improves the generated values. The paper should not present the reasoning as a user-facing explanation or as an evaluated justification.

## Conclusion Source Material

The conclusion should return to the central GenSIE difficulty: schema-variable information extraction is not solved by JSON validity alone. A system must understand a task-specific schema, map Spanish evidence to field semantics, handle nullability and grounding, preserve nested structures, and remain robust across models.

DRILLER's submitted systems address this by combining several inference-time mechanisms. Schema-RAG uses readable schema prompts and retrieved demonstrations for direct extraction. Reasoned-RAG adds temporary field-local reasoning while preserving the final schema interface. Mixed-SC combines both extractor styles and aggregates their final-shape outputs with recursive schema-aware heuristics.

The conclusion can state that DRILLER's design emphasizes alignment between the target schema and the model's generation process. The schema appears in multiple roles: as prompt text for interpretation, as response format for structural control, as a guide for retrieval, as a template for reasoning wrappers, and as the recursive structure used for aggregation. This is the strongest unifying theme.

The final paragraph should mention future work only briefly. Possible directions include stronger evidence verification, improved retrieval corpora, learned or calibrated aggregation thresholds, more efficient self-consistency, and deeper analysis of model-specific behavior under schema-variable extraction. Avoid implying that non-final implemented components were part of the submitted system.

## Declaration on Generative AI

The final paper must include the mandatory section title exactly:

```latex
\section*{Declaration on Generative AI}
```

Official required wording must be verified before camera-ready submission. The CEURART sample includes a minimal declaration, but the actual workshop or publisher may require a more specific statement. The wording below is cautious draft material only.

### Cautious Draft Wording to Verify

"During the preparation of this work, the authors used generative AI assistance to support drafting, editing, and organization of paper text. The authors reviewed, corrected, and approved all content, and they remain responsible for the final manuscript. The submitted system itself uses language models only through the official GenSIE inference interface described in the paper; no model weights were fine-tuned as part of the submitted pipelines."

If the authors did not use generative AI in writing, replace the first sentence with the appropriate negative declaration. If the venue requires disclosure of specific tools, dates, or purposes, add them according to the official instructions.

## Missing Information Before Finalizing This Section

The final limitations and conclusion should be adjusted after official results are available. In particular:

- If Mixed-SC performs best, discuss the accuracy/cost trade-off.
- If a single-pass pipeline performs best, discuss whether heterogeneous self-consistency was too costly or noisy.
- If results vary strongly by model, emphasize model sensitivity.
- If arrays or nulls dominate errors, make those the main limitation examples.
- If official efficiency metrics are released, connect them to prompt length and trial count.

The generative AI declaration must be finalized by the human authors based on actual writing assistance and official venue policy.

