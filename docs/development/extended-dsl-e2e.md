# Extended Playwright DSL verification

Date: 2026-10-14

## Purpose

The initial MVP DSL handled only `goto`, `fill`, `click`, and three assertions.
This verification adds controlled support for interaction patterns needed by web E2E
testing while retaining a typed plan that can be grounded, reviewed, rendered, and
classified by the constrained-repair policy.

## Added DSL operations

| Group | Supported types |
|---|---|
| Interaction | `select_option`, `check`, `uncheck`, `press`, `hover`, `dblclick`, `upload_file`, `drag_to` |
| Assertion | `expect_value`, `expect_checked`, `expect_enabled`, `expect_count` |

`drag_to` stores a typed source locator and typed target locator. `expect_count`
checks the intended cardinality rather than applying the normal unique-locator rule.
`upload_file` is rendered with a path guard: the selected file must exist below the
approved test-data root passed to the renderer.

## Reproducible E2E fixture

`tests/fixtures/extended_dsl.html` is a local deterministic page. It covers a
dropdown, mouse hover, Enter key, double click, checkbox, enabled control, file
upload, HTML drag-and-drop, and a two-item collection. The approved upload data is
`tests/fixtures/extended_dsl_upload.txt`.

The test `tests/integration/test_extended_dsl_e2e.py` builds one `PlaywrightPlan`,
runs multi-step DOM grounding, renders the standalone Playwright Python script, and
runs that script through `ExecutionAgent`. It verifies the screenshot and Playwright
trace artifacts as well as the `PASSED` execution status.

## Result

Commands run from the repository root:

```powershell
python -m pytest tests/integration/test_extended_dsl_e2e.py -q
python -m pytest -q
```

Result: the extended E2E test passed; the full regression suite passed with
`131 passed`.

## Repair and review boundary

Changing an action type, adding/removing a step, or changing any of the seven
assertion forms is still semantic and requires human approval. Locator changes are
reviewed by policy; no generated plan can inject arbitrary Playwright or JavaScript.
