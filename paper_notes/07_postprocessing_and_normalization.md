# 07 Postprocessing and Normalization

## Purpose of This Section

This note supports a concise but important method section on deterministic postprocessing. Postprocessing is not an extra extraction model and does not perform semantic repair. Its role is to convert the model response into a clean JSON object in the expected schema shape, remove temporary reasoning wrappers when present, normalize common string artifacts, and handle a narrow class of null-formatting mistakes.

## JSON Parsing

The first postprocessing step is JSON parsing. The submitted pipelines expect the model response to be JSON because the generation request uses a strict response format. Nevertheless, parsing remains an explicit boundary: the model response must be converted into a data structure before the system can normalize or aggregate it.

If parsing fails, the extraction trial is not semantically repaired. The system does not attempt to recover a plausible object from malformed text or infer missing braces. In the single-pass pipelines, a parsing failure prevents a valid prediction from that trial. In Mixed-SC, the failed trial is treated as invalid and excluded from aggregation. This conservative behavior avoids introducing ungrounded repair logic.

## Unicode Escape Cleanup

The system recursively cleans literal Unicode escape artifacts inside strings. This addresses cases where the model returns text containing escape sequences such as `\u00e1` as literal characters rather than decoded text. Because the source texts are Spanish, preserving accents and other Unicode characters matters for value fidelity and lexical/semantic evaluation.

The cleanup should be described as formatting normalization, not content transformation. It does not change the semantic value selected by the model; it repairs representation artifacts that can arise in generated JSON strings.

## Unicode NFC Normalization

After escape cleanup, strings are normalized to Unicode NFC. This makes canonically equivalent strings use a consistent representation. For example, a composed accented character and a base character plus combining mark can look identical but differ at the codepoint level. NFC normalization reduces such accidental differences.

This is especially relevant for Spanish text, where accents and special characters can appear in names, titles, and quoted spans. The final paper can mention this as a low-level but important step for faithful Spanish structured extraction.

## Reasoning/Value Unwrapping

For Reasoned-RAG and the reasoned trials inside Mixed-SC, postprocessing removes temporary reasoning/value wrappers. Each top-level field is expected to be an object with `reasoning` and `value`. The final output keeps only the `value`.

Conceptually:

```json
{"reasoning": "...", "value": X}
```

becomes:

```json
X
```

This restores the original target schema shape. The reasoning strings are discarded before final output and before self-consistency aggregation. If wrapper unwrapping fails, the trial is treated as invalid rather than repaired by guessing.

The final paper should connect this step to the reasoning section: reasoning is an internal generation scaffold, not an output field.

## String `"null"` to JSON Null

The postprocessor recursively converts string values equal to `"null"` into JSON `null` only when the corresponding schema position permits null. This handles a common language-model formatting error: the model may understand that a field should be null but emit the string `"null"` instead of the JSON literal.

The schema condition is essential. DRILLER does not globally replace every string `"null"` with null. If a schema position does not permit null, conversion would create a schema-invalid value. The conversion is therefore constrained by the target schema's nullability.

This step should be described as conservative null coercion. It fixes a representation error in nullable positions but does not decide whether null is semantically correct. The semantic decision still comes from the model output and, in Mixed-SC, from aggregation support.

## No Semantic Repair

The paper should explicitly state that postprocessing does not perform semantic repair. It does not infer missing facts, fill omitted fields from external knowledge, rewrite enum labels, normalize wrong categories, add array items, remove hallucinated values, or validate evidence against the source text. Its purpose is interface hygiene: parse JSON, normalize strings, unwrap temporary structures, and convert legal null strings.

This distinction is important because otherwise the system could be misread as a rule-based correction layer. DRILLER's methodological contribution is inference-time schema guidance and aggregation, not post-hoc answer editing.

## Invalid Trial Handling

A trial can be invalid because the model response cannot be parsed, because reasoning wrappers are malformed, or because the result contains an error record rather than a usable output. In Mixed-SC, invalid trials are excluded from aggregation. If no valid candidates remain, the aggregator returns an error record instead of fabricating a final extraction.

The final paper can mention this as a safety property: aggregation combines candidate predictions but does not invent one when all model calls fail. In official evaluation, the ideal behavior is that strict generation prevents most parsing failures, but the invalid-trial path documents how the system handles failures.

## Interaction with Mixed-SC

Postprocessing is a prerequisite for Mixed-SC. Each trial is independently normalized before aggregation. This means the aggregator receives comparable final-shape objects from both Schema-RAG and Reasoned-RAG trials. It also means that string null coercion and Unicode normalization are applied before clustering, reducing superficial differences among candidate values.

After aggregation, nullable-string null coercion can be applied again. This is useful because aggregation may select a representative string value from a cluster, and if that value is `"null"` in a nullable position, it should be converted to JSON null. As before, this is schema-constrained.

## Suggested Paper Framing

The final paper can present postprocessing as "deterministic and conservative." It is necessary for turning structured generations into evaluator-ready JSON, but it does not add new information. This preserves the paper's grounding narrative: values are produced by the model under schema-guided prompting and optionally aggregated across trials; postprocessing only cleans the interface.

