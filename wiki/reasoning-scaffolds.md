---
kind: concept
sources: ["[[2026-06-17-language-models-are-few-shot-learners]]", "[[2026-06-17-chain-of-thought-prompting]]", "[[2026-06-17-self-consistency-chain-of-thought]]"]
created: 2026-06-17
updated: 2026-06-17
ingestion_runs: ["2026-06-17T15:21"]
---

# Reasoning Scaffolds

Reasoning scaffolds are prompt or output structures that encourage a model to expose intermediate steps before the final answer. GPT-3 establishes the broader few-shot setting: models can adapt to tasks from context alone, but performance varies by task and prompt design. Chain-of-thought prompting specializes this idea by placing step-by-step rationales in the demonstrations.

Wei et al. define chain of thought as a series of intermediate reasoning steps. Their experiments show that, for sufficiently large models, adding a few chain-of-thought demonstrations can improve arithmetic, commonsense, and symbolic reasoning compared with direct-answer prompting. The important background claim is not that every task benefits, but that prompt format can elicit capabilities that are hidden under standard prompting.

The same paper is also careful about limitations. Chain-of-thought text does not prove faithful internal reasoning, generated reasoning paths can be wrong, and the strongest effects were tied to large model scales. These caveats are useful for GenSIE prose because extraction rationales or field-level explanations should not be presented as guaranteed evidence of correctness.

## Design Pattern

In a schema-guided extraction setting, reasoning scaffolds can be used to make field decisions explicit: identify the relevant span, compare candidate values, resolve ambiguity, then emit the structured output. This is a prompting and interpretability pattern, not a proof that the model reasoned faithfully.

## Background Use

Use this page for a compact bridge from few-shot prompting to extraction-specific deliberation. It supports wording such as "reasoning scaffolds are intended to help the model decompose decisions" rather than unsupported causal claims about final GenSIE performance.
