# 04 Field-Aware Few-Shot Retrieval

## Purpose of This Section

This note supports the most technically detailed method section of the paper. The final paper should treat few-shot retrieval not as generic example lookup, but as a schema-aware mechanism for aligning a model with a task-specific extraction schema. The submitted DRILLER pipelines all use retrieval-augmented few-shot prompting. The retrieval system selects up to two demonstrations for each task, preferring examples with the same normalized schema when possible and otherwise falling back to field-level similarity and complementary pair selection.

The central claim that can be made without ablation results is methodological: DRILLER designs retrieval around field semantics and complementary outcomes because GenSIE requires dynamic schema interpretation. The paper should not claim that retrieval improved official performance unless official analyses or ablations later support that claim.

## Role of Few-Shot Retrieval in DRILLER

In GenSIE, each task includes a target JSON Schema that may differ from the schemas seen during development. This makes conventional nearest-neighbor retrieval over raw source text insufficient. A source text about a medical trial may be lexically similar to another medical text, but the requested fields may differ substantially. Conversely, a legal, medical, or technical task may share important schema phenomena such as nullable evidence, enum classification, object arrays, or date normalization even when the surface domain differs.

DRILLER therefore retrieves demonstrations according to schema structure and field-level semantics. The purpose is to show the model examples of how field names, descriptions, types, and instructions map source evidence into structured values. The demonstrations are not evidence for the current instance. They are analogies for schema interpretation and output behavior.

This design is especially relevant for small or medium open-weight models. These models may know how to produce JSON, but they can be brittle when a schema asks for an unseen field or an enum label whose meaning must be inferred from a description. A retrieved example can anchor the model's behavior: how to return `null` when evidence is absent, how to populate arrays, how to preserve nested object structure, how to classify into enum alternatives, or how to normalize numeric/date values.

## Synthetic and Curated FSP Corpus

The extraction RAG corpus is a local set of structured few-shot prompt cases. According to the system-component source notes, the repository contains 45 JSON case resources, one of which is excluded from the final extraction RAG provider because it is judge-oriented. The submitted extraction RAG path therefore uses 44 extraction cases with 244 field-level example records. These numbers can be included in the final paper if verified against the final submitted artifact.

The cases are organized by domain or schema family. The source notes list two cases each for 22 families: cultural entities, cultural extraction, cultural literature, cultural media, cultural monuments, environmental ecology, general disasters, legal contracts, legal entities, legal extraction, legal judicial, legal legislation, lifestyle recipes, medical diseases, medical drug, medical entities, medical extraction, medical health news, detailed astronomy, technical entities, technical extraction, and technical software. The important methodological point is not the exact domain list but the balanced two-case organization: each family can provide contrasting examples rather than a single pattern.

Each structured case contains a case identifier, domain metadata, language, tags, synthetic source text, an extraction instruction, a schema, expected field-level values, optional field-level reasoning, optional enriched field descriptions, and optional metadata for non-final judge experiments. The submitted extraction provider uses the extraction-relevant parts: source text, instruction, schema, field values, tags, and enriched descriptions where the active prompt path supports them. Judge metadata should not be described as part of the final extraction system.

The safest final-paper wording is that the FSP corpus is synthetic and curated, with documented review and validation. The source notes warn not to overstate exact authorship of every final sentence or field rationale. A paper-ready formulation could say: "We constructed a local synthetic/curated demonstration corpus covering recurring schema phenomena in the development setting. Cases were organized in complementary pairs and validated for consistency with their schemas." Avoid claiming all examples were manually written from scratch unless that is independently verified.

## Complementary Pair Design

The corpus was designed around complementary pairs rather than isolated demonstrations. The idea is that a single few-shot example can overcondition the model toward one outcome: always filling a nullable field, always returning a populated array, choosing the most common enum label, or copying a particular surface form. Two examples that are both relevant and different can demonstrate that the same or similar schema can yield different outputs depending on the source evidence.

Complementarity is especially valuable in GenSIE because many fields are not simple named entities. A nullable field may be correct as `null` in one instance and non-null in another. An enum may require choosing among several labels based on a threshold or contextual interpretation. An array may be empty when no evidence is present or contain several objects when the text lists entities. A date may be explicit, partial, or absent. A field may have distractor mentions that should not be selected.

DRILLER's retrieval method mirrors this design. When it cannot use a same-schema pair, the field-level fallback scores candidate pairs by both joint relevance and difference across fields. This makes retrieval a mechanism for presenting complementary schema behavior at inference time, not just retrieving the two highest individual neighbors.

## Field Outcome Diversity

The demonstration corpus is designed to cover field outcome diversity. The final paper should describe these categories as examples of extraction phenomena rather than as an exhaustive taxonomy.

### Null versus Non-Null

Nullable fields are one of the most important phenomena. A field can permit `null`, but the model must decide whether the source text supports a value. Demonstrations should show both outcomes: cases where the source contains enough evidence for a non-null value and cases where the correct output is `null` because the information is absent. This contrast helps prevent the model from treating nullability either as an invitation to omit difficult fields or as a field that should always be filled.

### Absent versus Present Evidence

A related distinction is the difference between absent evidence and present but implicit evidence. For example, an enum or boolean field may not have a literal answer string in the source, but the source may contain enough information to infer the value. Conversely, a well-known external fact may be absent from the text and should not be used. Demonstrations can show the model that evidence can be direct, inferential, or insufficient.

### Enum Alternatives

Enum fields are exact-match targets. The correct output must be one of the labels defined by the schema. The label may not appear verbatim in the source text. Complementary examples can show different enum alternatives and reduce bias toward the most common or most semantically positive label. They can also show that enum selection is governed by the instruction and field description, not by generic sentiment or prior knowledge.

### Empty versus Non-Empty Arrays

Arrays introduce cardinality decisions. Some source texts support no items, some support one item, and others support multiple items. Few-shot examples should show both empty and non-empty arrays so that the model does not assume every list field must be populated. This is important because hallucinated array items increase false positives, while missing items reduce recall.

### Nested Objects

Nested objects require preserving internal structure. A demonstration can show how evidence for several related subfields should be grouped into one object. This helps the model avoid flattening nested values, omitting subfields, or mixing values from different parts of the text.

### Arrays of Objects

Arrays of objects are harder than arrays of strings because the model must identify item boundaries and attach attributes to the correct item. Demonstrations can show entity arrays, event arrays, symptom arrays, ingredient arrays, or software/component arrays where each item has its own fields. The useful lesson is that object identity matters: the model should not combine a name from one mention with a date or label from another.

### Direct String Extraction

Some fields require direct string extraction or verbatim evidence. Demonstrations can teach preservation of source wording, especially when a field description asks for a name, title, quote, or phrase. This differs from summary fields, where paraphrase may be acceptable. The final paper can mention that DRILLER's RAG corpus includes both direct/verbatim and summary-like string phenomena.

### Numeric and Date Normalization

Numeric and date fields often require normalization. A source may contain a number with punctuation, a percentage, a written quantity, a partial date, or a date embedded in prose. Demonstrations can show how to convert evidence into the schema's expected type. The paper should be cautious here: unless results demonstrate robust normalization, describe this as a design target of the examples rather than a proven performance claim.

### Distractor Mentions

GenSIE examples may include nearby mentions that are semantically related but not answers to the target field. Demonstrations with distractors help show that extraction is schema-guided: the model must use the field description and instruction to select the right mention. This is particularly important for entity arrays, nested objects, and technical/legal fields where many terms appear close together.

## Why Complementary Demonstrations Reduce Few-Shot Bias

Few-shot prompting can introduce bias because the model tends to imitate example outputs. If the retrieved example has a populated array, the model may over-generate array items. If it has `null` for a nullable field, the model may become too conservative. If it uses one enum label, the model may over-select that label even when the current evidence differs. This is a known practical issue with demonstration prompting: examples communicate both task format and accidental distributional cues.

Complementary demonstrations mitigate this by showing variation. The model sees that the same structural slot can be filled or null, that arrays can be empty or populated, that enums can take different labels, and that similar-looking schemas can require different output shapes. The final paper can phrase this as an inductive bias: DRILLER attempts to teach conditional behavior, not a single canonical output pattern.

The design is also token-efficient. Instead of many demonstrations, the submitted RAG prompt uses up to two selected examples. The retrieval objective therefore makes the pair carry as much information as possible: the examples should jointly cover the target fields while differing in which fields they best illustrate.

## Runtime Retrieval Overview

Runtime retrieval has two main stages:

1. same-schema retrieval;
2. field-level fallback retrieval.

The provider first attempts to find examples whose normalized schema fingerprint matches the target schema. If at least two same-schema examples are sufficiently similar to the current task, they are used and rendered with a compact same-schema prompt layout. If this condition is not met, the provider decomposes the target schema and candidate schemas into top-level field representations and retrieves examples by field-level similarity and complementarity.

This staged design is important. Same-schema retrieval is precise when available: if the schema structure is the same, the examples are highly relevant to the output shape. Field-level fallback provides coverage for genuinely unseen schemas by retrieving cases that illustrate similar field types or semantic roles even when the full schema differs.

## Same-Schema Retrieval

Same-schema retrieval starts by computing a normalized schema fingerprint. The normalization process canonicalizes the schema JSON while neutralizing details that should not prevent structural matching. In particular, description values are replaced with empty strings. Lists whose order is not semantically meaningful, such as `required`, `enum`, and `type`, are sorted. The structural shape of objects, arrays, field names, and types is preserved.

This means that two schemas can match even if descriptions differ or unordered lists appear in a different order. However, they must still share the same structural field organization. The goal is to identify examples whose schema is effectively the same target interface, not merely topically similar.

Description neutralization deserves explanation. Field descriptions are important for model interpretation, but they can be verbose, edited, or enriched without changing the schema's structural identity. If fingerprints included description text, two otherwise identical schemas with slightly different descriptions might fail to match. By neutralizing descriptions, DRILLER treats same-schema matching as a structural condition.

Canonicalization of unordered schema elements is also important. JSON arrays are ordered syntactically, but in schema constructs such as `required`, `enum`, and a union `type`, the order does not define different extraction semantics. Sorting these lists makes fingerprints stable.

After structural matching, same-schema candidates are ranked semantically. The task representation combines the task identifier, the instruction, and textual representations of the top-level schema fields. Candidate case representations are built analogously from the case identifier, instruction, and field texts. The default embedding model in the source notes is `BAAI/bge-small-en-v1.5` through `fastembed`; vectors are L2-normalized and compared with cosine similarity.

The source notes state a default same-schema similarity threshold of `0.6`. If at least two same-schema candidates meet this threshold, the top two are selected and marked as same-schema matches. The threshold should be included only if it is verified as part of the final submitted configuration; the system-component source treats it as the default.

This same-schema stage is stricter than ordinary nearest-neighbor retrieval. It first requires normalized structural identity, then uses semantic similarity only to rank within that schema family. If fewer than two candidates pass the threshold, DRILLER does not force a same-schema layout; it falls back to field-level retrieval.

## Field-Level Fallback

When same-schema retrieval does not provide two usable examples, the system falls back to field-level retrieval. The target schema is decomposed into top-level field specifications. For each top-level field, the retriever records:

- the field name;
- the field description;
- a textual type representation;
- a coarse type class;
- an embedding text combining name, type, and description.

The coarse type class can be `string`, `boolean`, `numeric`, `enum`, `object`, or an array class such as `array[...]`. The important point is that retrieval does not compare every field to every other field indiscriminately. It compares fields under type compatibility constraints. An enum field is not treated as interchangeable with an arbitrary object field. A nullable string and a non-nullable string can remain compatible because nullability is ignored for the coarse class.

Candidate FSP cases are decomposed in the same way from their schemas, not from their outputs. This matters because retrieval is schema-driven. The system is not looking for an example whose answer values are textually similar to the current unknown answer. It is looking for examples whose fields are semantically and structurally useful for interpreting the current target schema.

The retriever embeds all query and candidate field texts and computes cosine similarities for compatible fields. For each candidate case, it constructs a similarity vector with one entry per target top-level field. Each entry is the best compatible field similarity found in that candidate. Negative similarities are clipped to zero. The candidate's individual field score is the L2 norm of this vector.

This vector representation is useful because it records not only how relevant a candidate is overall, but which target fields it covers well. A candidate may be strong for enum fields and weak for arrays; another may be strong for arrays and weak for numeric fields. The complementary pair selection step uses this distribution.

## Lexical and Schema Fallback

If embedding-based retrieval fails or returns no usable candidates, the implementation includes a lexical/schema fallback ranker. The fallback builds a schema profile and uses explicit weighted signals. The system-component notes list weights such as a large bonus for exact canonical schema fingerprint match, bonuses for compatible top-level field fingerprints, schema/resource/field tag matches, overlapping field names, shared text terms, domain-term overlap, and a small penalty for long example source text.

The final paper does not need all exact weights unless space permits, but it can state that retrieval has a deterministic lexical/schema fallback. This is useful in an isolated evaluation environment where embedding availability or runtime failures should not collapse the entire RAG system. The fallback should be framed as robustness, not as a separately evaluated retrieval method.

The paper should also avoid implying that the final extraction RAG path loads a prebuilt field index. The system-component notes say that the submitted extraction provider constructs candidate field texts from in-repository FSP cases and embeds them at runtime; prebuilt index utilities exist but are not part of the submitted extraction path.

## Complementary Pair Scoring

For `top_k=2`, field-level retrieval selects a pair rather than independently taking the two best individual candidates. Let `v_1` and `v_2` be the field-similarity vectors for two candidate cases. The pair score is:

```latex
s(c_1,c_2) = \lVert v_1 + v_2\rVert_2 + \lVert v_1 - v_2\rVert_2 .
```

The first term, `\lVert v_1 + v_2\rVert_2`, rewards joint relevance and broad coverage. If both candidates cover the target fields well, their sum vector has a large norm. This term encourages the selected pair to be useful for the current schema as a whole.

The second term, `\lVert v_1 - v_2\rVert_2`, rewards complementarity. If two candidates have identical strengths and weaknesses, their difference vector is small. If one candidate strongly covers fields that the other covers weakly, the difference norm grows. This term therefore favors pairs that are relevant but non-redundant.

The combination is a compact way to express DRILLER's retrieval philosophy. The examples should jointly cover the target schema while showing different field phenomena. The pair should not consist of two near-duplicates that teach the same pattern twice. Tie-breakers prefer higher total individual field score and then earlier resource order.

The final paper should explain this equation in prose, because it is one of the clearest methodological details in the system. It also supports the paper's central narrative: DRILLER aligns examples to schema fields, not only to source text.

## Same-Schema Prompt Layout

When the selected RAG examples are same-schema matches, the prompt uses a compact layout. The shared target schema is rendered once, typically in the system-side context or common prompt context, and each example shows its instruction, source text, and output without repeating the schema. The new task then follows with its instruction and source text.

This layout has two benefits. First, it saves tokens by avoiding repeated schema text. Second, it sharpens the instructional signal: the examples demonstrate how the same schema can yield different values for different source texts. This is especially useful for complementary cases, because the model sees multiple outcomes under one schema interface.

In the general layout, examples may have related but non-identical schemas. In that case, each example needs enough schema context to make its output meaningful. The general layout therefore includes the example instruction, schema description, schema rendering, source text, and expected output.

## Interaction with Reasoning Wrappers

Retrieval interacts with reasoning wrappers through example rendering. Reasoned-RAG expects top-level fields to be temporary objects containing `reasoning` and `value`. Therefore, few-shot examples for Reasoned-RAG are rendered in that same wrapped format. The reasoning text in examples follows a field-local evidence protocol, including what the field asks for, relevant fragments, and the final value. This shows the model how to use the temporary wrapper.

Schema-RAG, by contrast, renders examples as final values directly. The same retrieved case can therefore be displayed differently depending on the active extractor. The retrieval selection is about which cases to show; the rendering stage adapts the selected cases to the current output style.

This interaction is important for the final paper because it prevents a misleading description of RAG as independent from reasoning. In DRILLER, RAG is integrated with the active schema view and generation format.

## Interaction with Schema Rendering

RAG examples are interpreted through schema rendering. In same-schema mode, the current schema can be shown once and shared by the examples. In general mode, each example may carry its own rendered schema. The schema rendering style also changes with the extractor: Pydantic-style for direct extraction and reasoned Pydantic-style for reasoning extraction.

The source notes mention environment-controlled enriched descriptions for same-schema prompting. If enabled, prompt-side field descriptions can be overridden by enriched descriptions stored in selected FSP cases. These enriched descriptions affect only the prompt schema, not the target schema or generation schema. The paper should mention this only if the final submitted evaluation environment confirms that the feature was active. Otherwise, keep it as an internal note or omit it.

## Claims to Make and Avoid

Safe claims:

- All final submitted pipelines use retrieval-augmented few-shot prompting.
- Retrieval selects up to two examples.
- Same-schema retrieval uses normalized schema fingerprints before semantic ranking.
- Field-level fallback decomposes schemas into top-level fields and compares compatible field representations.
- For two examples, pair selection rewards both joint relevance and complementarity.
- Examples are rendered in the format expected by the active extractor.

Claims to avoid unless supported later:

- Do not claim that RAG improved official score.
- Do not claim that complementary pair selection outperformed nearest-neighbor retrieval.
- Do not claim that enriched descriptions were active unless verified.
- Do not claim every FSP example was manually written from scratch.
- Do not describe judge-oriented RAG examples or verdict-judge retrieval as part of the submitted extraction system.
- Do not imply that prebuilt field-index artifacts are loaded by the submitted extraction RAG path.

## Suggested Paper Framing

A strong paper paragraph could frame this section as follows in final prose: "Because the schema is the primary task specification in GenSIE, DRILLER retrieves demonstrations by schema behavior rather than by document topic alone. Retrieval first attempts structurally identical schemas, using normalized fingerprints that ignore description text and unordered schema-list ordering. If no sufficiently similar same-schema pair is available, the system decomposes the target schema into top-level fields, matches type-compatible fields to the demonstration corpus, and selects a pair whose field-similarity vectors are jointly relevant and complementary."

This paragraph can then be followed by the equation and detailed subsections.

