# OrangeHRM public-demo live exploration and pipeline run

Date: 2026-10-14

Target: `https://opensource-demo.orangehrmlive.com/web/index.php/auth/login`
Safety scope: read-only exploration. No employee, directory, leave, or configuration record was created, edited, or deleted.

## Observed pages and UI evidence

The public login page publishes demo credentials and provides Username, Password,
and Login controls. A successful login opened the Dashboard. The authenticated
sidepanel exposed PIM, Directory, Leave, Time, Recruitment, My Info, Performance,
Dashboard, Maintenance, Claim, and Buzz.

The PIM employee-list page displayed Employee Information, employee filters,
Search/Reset, and an employee result table. The Directory page displayed Employee
Name, Job Title, and Location filters, Search/Reset, and directory result cards.
Activating the Directory Job Title control opened a custom ARIA listbox that included
`HR Manager`, `QA Engineer`, and `Software Engineer`.

The requirement source is `docs/inputs/orangehrm_observed_requirements_2026-10-14.md`.
It deliberately excludes unobserved save/edit/delete/search outcomes and volatile
record totals from test oracles.

## LLM pipeline results

Requirement Analysis Agent, using `deepseek-chat`, extracted five structured
requirements with no ambiguity finding from the observed document.

Test Design Agent, using `deepseek-chat`, produced 38 traceable test cases for all
five requirements. Coverage was 100% at requirement and trace levels. The generated
portfolio covered positive, negative, error guessing, boundary, equivalence
partition, state transition, exploratory, and alternative-flow categories. Only
requirement-backed positive cases were eligible for direct unattended execution;
exploratory candidates retained `review_required=true`.

## Live execution: public-demo login

Input: `datasets/experiments/orangehrm_execution_seed.json`.

The first LLM plan used `get_by_label` for the login textboxes. Runtime grounding
correctly found zero matching elements because OrangeHRM's visible text is not an
associated HTML label. The execution CLI was updated to use a current ARIA snapshot,
multi-step grounding, and one bounded LLM re-plan with grounding feedback before it
writes the script.

Final result: **passed**. The re-planned script used role-based textboxes, all six
grounded locators matched exactly one element, and the generated script completed
with exit code 0. Evidence is stored under
`artifacts/exec/REQ-001-TC-01/20261014T142015180021Z-6247ddb4/` and the machine
result is `artifacts/orangehrm/playwright_results_final.json`.

## Live execution: Directory Job Title listbox

Input: `datasets/experiments/orangehrm_directory_listbox_execution_seed.json`.

The generated plan correctly logged in, opened Directory, and found the listbox and
its expected options. It then selected `get_by_text("-- Select --")` for the Job
Title control. The live page has two controls with that text (Job Title and Location),
so grounding reported two matches and Playwright strict mode stopped the script rather
than clicking an arbitrary control. Result: **error, correctly fail-closed**.

This is not classified as an OrangeHRM defect. It exposes a product limitation: the
current locator DSL has role/label/placeholder/text/test-id/CSS plus `nth`, but no
semantic parent/child locator chaining (for example, "the select control in the
field labelled Job Title"). The next implementation task is a typed contextual
locator operation; it must remain subject to grounding and human review rather than
blindly choosing `nth(0)`.

## Regression status

After the pipeline change, the full local regression suite passed:

```text
131 passed
```
