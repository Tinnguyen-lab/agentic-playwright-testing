# RQ4 completion evidence — 2026-10-11

Projects: `RQ4-HIL-20261010-A` (Task A) and `RQ4-HIL-20261011-B` (Task B). The approval actions made through the Codex session are logged as `user-authorized`; they are not presented as actions of another participant.

| Phase | Runnable UC on v0 | Semantically valid UC | Interpretation |
|---|---:|---:|---|
| Before correction/review gate | 2/3 | 2/3 | REQ-003 used unsuitable login data and a locator/oracle that did not match ShopLab. |
| After correction, grounding and AG-08 | 3/3 | 3/3 | Every script passes v0 and fails its assigned semantic mutation. |
| Task B after grounding and AG-08 | 3/3 | 3/3 | All remaining protocol use cases pass v0 and fail their assigned semantic mutations. |

The intervention produced test-case version 2 and script version 2 for `REQ-003-TC-01`. Grounding verified every locator in that script matched exactly one live element. The execution evidence, approvals, versions and UI events are stored in local SQLite (`artifacts/app.db`).

Semantic validity means a script passes the correct ShopLab build and fails the mutation that violates its assigned requirement. This is evidence for the quality gate on this controlled task; it is not a usability survey, time study, or claim that the system replaces a tester.

Machine-readable evidence:

- `artifacts/rq4/RQ4-HIL-20261010-A/before_review/`
- `artifacts/rq4/RQ4-HIL-20261010-A/after_review/`
- `artifacts/rq4/RQ4-HIL-20261011-B/after_review/`
- `artifacts/rq4/check_user-authorized_before_review_A.json`
- `artifacts/rq4/check_user-authorized_after_review_A.json`
- `artifacts/rq4/check_user-authorized_after_review_B.json`
- `artifacts/rq4/rq4_results.json`
