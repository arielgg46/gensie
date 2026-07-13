# 05 Reasoning-Augmented Extraction

## Purpose of This Section

This note supports the paper section on Reasoned-RAG and the reasoning-augmented trials inside Mixed-SC. The final paper should explain reasoning augmentation as a temporary schema transformation that changes how the model generates field values, not as an explanation returned to the evaluator. The submitted reasoning mode is top-level only: each root field is wrapped during generation as `{reasoning, value}`, and the wrapper is removed before the final output.

## Motivation for Field-Local Reasoning

GenSIE fields often require more than copying a visible string. A field may ask for a semantic classification, a boolean decision, a normalized date or number, a grounded null, or an array item that must be distinguished from distractor mentions. In these cases, a model may fail because it commits to a value too quickly, follows a superficial word overlap, or uses parametric knowledge instead of source evidence.

DRILLER's reasoning-augmented extraction encourages the model to perform local deliberation for each top-level field. The intended reasoning is not broad free-form chain-of-thought about the whole document. It is field-specific: what does this field ask for, what source evidence is relevant, is evidence absent or insufficient, and what final value follows from that evidence?

This design matches the structure of schema-guided extraction. The schema decomposes the task into fields, and each field may have a different type, description, and evidence requirement. A single global explanation may not help the model distinguish these requirements. Field-local reasoning makes the model revisit the schema field by field.

## Temporary `{reasoning, value}` Wrappers

Reasoned-RAG transforms each top-level field of the target object into a temporary wrapper object with two properties:

```json
{
  "reasoning": "string",
  "value": "<original field schema>"
}
```

The `reasoning` property is a string. The `value` property contains the original field schema. If the original field is a string, the value remains a string. If it is an enum, the value remains one of the enum labels. If it is an array or object, the value contains that array or object. If it is nullable, nullability remains inside the value position.

Only root object properties are wrapped in the submitted reasoning mode. Nested fields are not individually wrapped. This keeps the reasoning scaffold relatively compact and prevents the prompt and output from becoming too large for deeply nested schemas. It also aligns with the idea that top-level fields are often the main semantic units in the target schema.

The final paper should explicitly say that deeper reasoning modes are not part of the submitted system. The repository contains other reasoning transformations, but the final submitted pipelines use top-level wrappers only.

## Prompt Schema Transformation

The prompt-side schema changes from ordinary Pydantic-style rendering to a reasoned Pydantic-style rendering. The conceptual wrapper can be described as:

```python
class Reasoned[T](BaseModel):
    reasoning: str
    value: T
```

A top-level field that would normally be shown as type `T` is instead shown as `Reasoned[T]`. This tells the model that the field output should contain a reasoning string plus the final value. Nullable types and nested structures are still represented in readable schema notation, but they appear inside the `value` component for the top-level field.

This prompt transformation is important because it makes the temporary generation format visible and interpretable. The model is not merely told to "think before answering"; it is shown a structured output type that reserves a place for evidence reasoning and a separate place for the final value.

## Generation Schema Transformation

The generation-facing schema changes as well. The structured response format is built from the target schema after injecting the top-level reasoning wrappers. This means the backend is asked to generate JSON whose top-level fields are wrapper objects, each with required `reasoning` and `value` properties. The wrapper has no additional properties.

This is a stronger intervention than an instruction-only chain-of-thought prompt. The model must produce a structured reasoning/value object for each top-level field. The separation reduces the risk that reasoning text contaminates the final value position. It also makes unwrapping deterministic: after generation, the system can replace each wrapper with its `value`.

The paper should emphasize the transformation order: the reasoning wrapper is applied before the strict response format is built. For the submitted non-baseline pipelines, the generation schema then also requires all declared object properties. This ensures that both the wrapper properties and the original field positions are present during generation.

## Expected Contents of the Reasoning Field

The reasoning field is intended for evidence-based deliberation. The prompt rules and examples guide the model to include three kinds of information:

- what the field asks for;
- relevant fragments or observations from the source text;
- the final value and why it follows.

If evidence is absent, the reasoning should say that the source text does not provide the requested information. For nullable fields, this should lead to a `null` value. For non-null fields, the model must still follow the schema and instruction, but the reasoning should remain grounded in the available text.

The paper does not need to reproduce exact Spanish labels unless useful. It can describe the protocol abstractly as field-local evidence reasoning. If labels are mentioned, make clear they are prompt-internal scaffolding, not final output fields.

## Why Reasoning Is Discarded

The final GenSIE output must conform to the target schema. The target schema does not include reasoning fields. Therefore, after the model returns the wrapped object, DRILLER unwraps each top-level field and retains only its `value`. The reasoning strings are internal generation traces and are discarded from the final prediction.

This design has two advantages. First, it allows reasoning to influence generation without changing the official interface. Second, it avoids exposing extra text that would violate the target schema. The evaluator receives the same shape it would receive from Schema-RAG.

The final paper should be precise: reasoning is not returned to the evaluator and is not part of the challenge answer. It is a temporary transformation used during inference.

## Interaction with RAG Examples

Reasoning augmentation interacts with RAG because examples must be rendered in the active output format. For Reasoned-RAG, retrieved examples show each top-level field as a reasoning/value wrapper. This teaches the model how to use the wrapper and how to place the final answer in `value`. For Schema-RAG, the same kind of example is rendered as final values without wrappers.

This interaction helps keep the prompt consistent. If the model is expected to output wrapped fields but examples show unwrapped fields, the prompt would give conflicting signals. DRILLER avoids this by adapting example rendering to the current extractor.

The examples also provide field-level reasoning demonstrations. These demonstrations can show how to reason about absent evidence, enum choices, arrays, or normalization. Again, the paper should avoid claiming measured improvement without evidence, but it can describe this as the intended role of reasoned examples.

## Interaction with Postprocessing

Postprocessing is essential for reasoning-augmented extraction. After JSON parsing and Unicode normalization, the system unwraps top-level `{reasoning, value}` objects. If unwrapping fails, the extraction trial is considered invalid rather than semantically repaired. This is conservative: the system does not try to guess which part of a malformed response should be treated as the final value.

In Mixed-SC, reasoning-augmented trials are unwrapped before aggregation. The aggregator never sees the reasoning strings. It receives final-shape JSON candidates from both direct and reasoned trials. This makes aggregation uniform across extractor styles.

## Not Chain-of-Thought Disclosure in the Final Answer

The final paper should be careful with terminology. The method uses reasoning strings as an internal structured scaffold, but the final answer does not disclose chain-of-thought. It returns only the schema-conformant JSON object. A concise formulation is: "Reasoning is used as an intermediate generation aid and removed before submission to the evaluator."

This distinction is also important for reproducibility and evaluation. Token usage includes generated reasoning tokens, because they are produced during the model call. However, the official output contains no reasoning fields. The experimental setup should report this if token efficiency is discussed.

## Claims to Make and Avoid

Safe claims:

- Reasoned-RAG wraps top-level fields as `{reasoning, value}` during generation.
- The prompt schema and generation schema are both transformed to reflect the wrapper.
- The wrapper is removed before final output.
- Reasoning examples are rendered in the same wrapped format.
- Mixed-SC includes two reasoning-augmented trials.

Claims to avoid unless later supported:

- Do not claim reasoning improved official results without ablation or official comparison.
- Do not describe deep or selective reasoning as part of the submitted system.
- Do not present reasoning strings as user-facing explanations.
- Do not imply that reasoning performs external verification or retrieval beyond the source text and examples.

