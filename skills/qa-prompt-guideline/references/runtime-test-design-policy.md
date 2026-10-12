# Runtime test-design policy

This file is loaded by `src.services.test_design_policy` for every test-design request.

## Analyse before generating

Before creating test cases, silently build a coverage map for the approved requirement:

| Dimension | Apply when | Evidence status |
|---|---|---|
| Business flow and alternate flow | an action or branch is documented | requirement-backed |
| Validation and equivalence classes | the requirement has an input, rule, or constraint | heuristic unless an error response is documented |
| Boundary values | a numeric/range/length constraint is documented | requirement-backed only for deterministic values |
| State and lifecycle | the action changes login, cart, data, workflow, or navigation state | heuristic unless the resulting state is documented |
| Resilience | submit, navigation, network or asynchronous behavior is relevant | heuristic |
| UI/UX and accessibility | a human interacts with the UI | heuristic |

Choose a small set of distinct, high-risk dimensions. Do not pad the output with superficial variants
that exercise the same risk (for example, several password mutations with no different hypothesis).

## Case quality contract

- Each case must name the risk or behaviour it explores and differ in setup, data class, state, or oracle.
- A requirement-backed case may state an expected result only when the approved requirement supplies it.
- A heuristic case is an exploratory charter, not a claimed defect: set `review_required=true`, leave
  `expected_result` empty, and write the unknown acceptance criterion in `review_note`.
- Prefer one representative case for each relevant technique over many cosmetic variants.
- Do not claim a result is a defect, pass, accessibility violation, or security issue without verification.

## Target coverage

Produce six to ten useful cases when the requirement is sufficiently rich. Include at least one
requirement-backed positive flow when available; use the remaining budget for the most relevant risks.
Include UI/UX or resilience only as clearly-labelled exploratory charters when they are applicable.

## Required taxonomy

For every generated suite, represent these techniques with a case of the matching type whenever the
target has an applicable interaction: `negative`, `error_guessing`, `boundary`,
`equivalence_partition`, `state_transition`, and `exploratory`. A case may be an exploratory
charter when its exact oracle is unknown; it must then be review-gated.
