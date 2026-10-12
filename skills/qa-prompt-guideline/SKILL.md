---
name: qa-prompt-guideline
description: Design or revise prompts used by this project's requirement-analysis, test-design, Playwright-generation, or repair agents. Use it whenever an LLM prompt produces too few test cases, vague requirements, ungrounded scripts, or needs a clearer structured output.
---

# QA prompt guideline

Use this skill for prompts sent to the project's LLM agents. It adapts the supplied
prompting guide to a human-in-the-loop testing system; it does not turn unsupported
assumptions into test evidence.

## Runtime binding

The test-design agent loads [references/runtime-test-design-policy.md](references/runtime-test-design-policy.md)
on every generation through `src.services.test_design_policy`. Update that reference when changing
test-design policy; it is the runtime source of truth, not merely documentation.

## Prompt structure

State these parts explicitly and in this order when they help the task:

1. **Persona** — the agent's testing role and its responsibility.
2. **Task** — one concrete command, such as extract, decompose, design, ground, or repair.
3. **Context** — only the requirement fields, DOM evidence, execution evidence, and policy facts
   that the agent may rely on.
4. **Format** — the schema, requested quantity, ordering, and fields that make output reviewable.

Use short, direct language. Ask for a plan internally, but require only the structured schema as
the final response. Put variable source data in the user prompt, not the system prompt.

## Test-case design

Exploratory coverage is mandatory in this project; do not offer or implement a strict-only generation path.
Requirement-backed cases and exploratory cases have different evidence status, not different generation modes.

For a large requirement, request a controlled decomposition before test cases:

- keep one evidence-backed positive case for every explicit scenario;
- request distinct cases by changing a documented flow, rule, state, input class, or boundary;
- use documented error/alternative behaviour as the oracle for non-positive cases;
- in **Expanded** ideation, label a useful but unsupported candidate with
  `review_required=true`, an empty `expected_result`, and a precise `review_note`;
- never represent a candidate as a verified requirement and never invent a pass condition.

Give an exact range when coverage needs to be broader (for example, six to ten cases). After
requirement-backed coverage, use exploratory heuristics such as validation, boundaries, state
transitions, duplicate submission, empty/loading states, keyboard accessibility and responsive UI;
label those ideas for review rather than inventing their oracle.
say what makes cases distinct. If the model returns too few, retry once with the shortfall and
the same evidence; do not silently pad the research baseline.

## Grounding and repair

For generated Playwright plans, give the target URL, the approved test case, and only observed DOM
or run evidence. Require locators and assertions traceable to that evidence. If a necessary setup,
oracle, selector, or repair policy is absent, return a reviewable block rather than guessing.

## Human review

Treat LLM output as a draft. Preserve trace links and approval gates. A reviewer validates
assumptions, generated scripts, and real execution outcomes before they count as research evidence.
