# 03 Schema-Guided Prompting

## Purpose of This Section

This note supports the paper section on schema-guided prompting and structured generation. The key message is that DRILLER treats the schema as both a semantic object and a structural constraint. The prompt-facing schema representation helps the language model interpret field meanings, while the generation-facing response format constrains the output to JSON. The final output must return to the original challenge schema shape, especially when temporary reasoning wrappers are used.

## Spanish Extraction Prompt

The extraction prompt is framed in Spanish because the source texts and task setting are Spanish. The system prompt casts the model as a precise information extractor. It instructs the model to return only JSON, to ground values in the source text, to follow the provided instruction and schema, and to avoid treating examples as evidence for the current instance. The user-side prompt is organized into clearly separated sections rather than a single block of unstructured instruction.

The normal prompt layout includes:

- a fixed task statement telling the model to extract structured information from the source text;
- the instance-specific natural-language instruction;
- an optional root schema description, when available;
- extraction rules;
- retrieved few-shot examples, if any;
- optional previous-phase context, which is not active in the submitted pipelines;
- the rendered target schema;
- the current source text.

The paper should describe the prompt as a controlled extraction interface. Its role is to keep the model oriented toward grounded, schema-conformant output rather than open-ended summarization. The examples demonstrate the task format and schema interpretation patterns but are not evidence for the current document.

## Grounding and Fidelity Rules

The extraction rules should be summarized as a methodological component, not as a long prompt dump. The rules emphasize complete schema coverage, exact enum labels, grounded values, conservative null handling, and faithful textual extraction when appropriate. The model is instructed to return JSON `null`, not the string `"null"`, when information is missing and the schema permits null. It is also instructed not to invent values from external knowledge.

This is crucial for GenSIE because missing evidence is actively evaluated. A model may know a fact from pretraining, but if that fact is absent from the source text, it should not appear in the output. DRILLER's prompting therefore treats grounding as a first-order constraint. The source text is the only admissible evidence for factual values, while the instruction and schema define how that evidence should be interpreted.

Enum fields require particular care. The model must use exactly one of the schema labels and may need to infer the correct label from evidence that does not literally contain the label. Boolean fields and numeric/date fields can also require interpretation or normalization. The prompt rules should be described as aligning model behavior with these evaluation realities: exact-match fields leave little room for paraphrase or label drift, while free-text fields should preserve the source content when requested.

## Separation of Prompt Components

The prompt separates instruction, source text, examples, schema, and output constraints. This separation is methodologically important because each component plays a different role.

The instruction specifies the extraction goal for the current instance. It can define semantic mappings that are not fully encoded in the schema. For example, an instruction may explain how to classify an outcome into an enum based on thresholds or contextual evidence.

The source text provides the only factual evidence. It is distinct from examples and from schema descriptions. This distinction helps prevent the model from copying example values or using general knowledge when the current source lacks support.

The examples show how analogous inputs map to structured outputs. They provide demonstrations of field interpretation, null handling, array behavior, enum selection, and nested structure construction. Because examples can bias the model, DRILLER retrieves complementary examples rather than relying on a fixed example or nearest neighbor alone.

The schema tells the model what output structure and field meanings are expected. DRILLER renders this schema in a readable Pydantic-style form, while the API response format enforces the corresponding JSON structure.

The output constraint is not only textual. The model request includes a strict JSON Schema response format. The paper should emphasize this division: prompts guide interpretation, while response formats constrain generation.

## Pydantic-Style Schema Rendering

The submitted direct extractor uses a Pydantic-style schema rendering. This converts JSON Schema constructs into a compact class-like representation. Object schemas become model-like classes. String, integer, number, boolean, array, object, and enum types are shown with familiar type-like notation. Enum definitions appear as literal alternatives. Field descriptions are preserved as field metadata. Required fields are visibly required, and optional or nullable fields are represented in a way that makes absence or nullability explicit.

The motivation is readability. Raw JSON Schema can be verbose and deeply nested, with structural keywords that may distract from field semantics. A Pydantic-style rendering exposes the same essential constraints in a format that resembles typed data models. This makes it easier for the model to see the root object, fields, nested classes, arrays, enum labels, and descriptions.

The final paper can describe this as "schema-readable prompting." The schema is not hidden inside the response format; it is shown to the model in a textual form designed for interpretation. This is especially important in zero-shot schema settings, where the schema itself is the primary specification of the extraction target.

## Three Schema Roles

DRILLER distinguishes three schema roles:

| Schema role | Purpose | Submitted-system behavior |
|---|---|---|
| Prompt schema | Text shown to the model for interpretation | Pydantic-style rendering for Schema-RAG; reasoned Pydantic-style rendering for Reasoned-RAG. |
| Generation schema | Structured response format sent to the model backend | Strict JSON Schema derived from the target schema, after temporary reasoning transformation when active. |
| Final output schema | Shape expected by GenSIE evaluator | Original target schema shape after postprocessing and unwrapping. |

This distinction should be explicit in the paper. It prevents confusion between what the model sees, what the model is constrained to generate, and what the evaluator receives. For example, Reasoned-RAG temporarily changes the prompt and generation schemas by wrapping top-level fields, but the final output schema remains the original GenSIE schema.

## Strict JSON Schema Response Format

The generation request uses a strict JSON Schema response format derived from the target schema. This is stronger than merely telling the model to "return JSON." It asks the backend to produce a response conforming to a schema. The purpose is to reduce malformed JSON and structural drift, including extra prose, missing braces, invalid enum syntax, or non-object outputs.

For the submitted non-baseline pipelines, the response-format builder recursively marks all declared object properties as required during generation. This targets a common failure mode in structured extraction: the model omits fields, especially optional-looking or difficult fields, even when the evaluator expects complete schema coverage. Making all properties required in the generation schema encourages the model to return a full object with every declared field position filled.

This transformation should be worded carefully. It does not change the challenge schema, invent missing values, or alter the evaluator's expected object. It changes the generation interface so that the model is less likely to omit declared properties. Where information is absent and null is permitted, the model should fill the field with JSON `null`; where null is not permitted, the model must still choose a value permitted by the schema based on the best grounded evidence.

## Nullability Handling

Nullability appears in the prompt schema, generation schema, and postprocessing. In the prompt schema, nullable fields are shown with readable nullable notation so that the model can see that `null` is an allowed value. In the extraction rules, the model is told to use JSON `null` for missing information when allowed. In the generation schema, nullable types are preserved so the constrained output can contain nulls. In postprocessing, string values equal to `"null"` are converted to JSON `null` only where the schema permits null.

This layered handling matters because null errors can arise at several stages. A model can hallucinate a value where null is correct. It can return string `"null"` instead of JSON null. It can use null where the schema does not allow it. DRILLER addresses these cases conservatively: the prompt teaches the intended behavior, the schema allows or disallows null structurally, and postprocessing fixes only the narrow formatting artifact of a literal null string in nullable positions.

## Same-Schema Prompting Layout

When RAG retrieves two examples with the same normalized schema as the target task, DRILLER uses a compact same-schema prompt layout. In this layout, the shared schema is rendered once rather than repeated inside each example. The examples then focus on their instruction, source text, and expected output. This reduces schema repetition and makes the examples highlight how the same schema can produce different outputs depending on the source evidence.

The same-schema layout differs from the general RAG layout. In the general layout, examples may have related but non-identical schemas, so each example needs enough schema context to be interpretable. In the same-schema layout, all selected examples share the target schema after normalization, so repeating the schema would consume tokens without adding much information.

This layout interacts with reasoning wrappers. If the active extractor is Reasoned-RAG, examples are rendered in the same temporary wrapped format expected from the model: each top-level field contains reasoning and value. If the active extractor is Schema-RAG, examples show final field values directly. Thus, example rendering is aligned with the current output style.

## What to Emphasize in the Paper

The paper should present schema-guided prompting as the foundation of DRILLER. The method does not rely on a fixed ontology or a task-specific classifier. Instead, it uses the target schema dynamically at inference time, rendering it for model understanding and enforcing it through structured generation. The section should also prepare the reader for later sections: RAG retrieval selects demonstrations relative to schema fields; reasoning wrappers modify the schema temporarily; and self-consistency aggregation depends on the final schema to combine candidate values.

