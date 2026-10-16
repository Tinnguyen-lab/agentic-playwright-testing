# RQ4 — Manual versus AI-assisted human-in-the-loop testing

**RQ4:** Does AI-assisted, human-in-the-loop test design reduce the effort to create test cases and Playwright scripts while maintaining semantic test quality?

The comparison is not *tester versus autonomous AI*. In both conditions a person owns the test oracle and the final submitted scripts. The AI-assisted condition gives that person requirement analysis, test-case proposals, Playwright generation, locator grounding and approval gates.

## Conditions

| Condition | Person's work | System role |
|---|---|---|
| `manual` | Read the requirement, write test cases and Playwright scripts from scratch, validate them. | No generation assistance. |
| `ai_assisted` | Review/edit requirements and proposed tests, approve the grounded script, correct decisions where needed. | Propose artifacts and execute grounding; never self-approves. |

Use a crossover allocation: half of participants complete Task A manually then Task B with assistance; the other half use the reverse order. A participant must not repeat the same task in both conditions.

## Tasks and outcome

Tasks A and B each contain three equivalent ShopLab use cases in `datasets/reference/rq4/`. A use case is **semantically valid** only when its submitted script passes ShopLab `v0` and fails the assigned semantic mutation.

Record for every real session:

- elapsed time (`timer start` to `timer stop`);
- number of created test cases and scripts;
- first-run runnable use cases;
- semantically valid use cases;
- review edits, approvals and rejections from SQLite.

Do not invent participants, timing, SUS scores, or manual artifacts. Empty cells mean the study has not been run.

## Running a real session

```powershell
# Prepare an isolated handoff folder; this does not create a result.
python tools/rq4/rq4.py prepare --participant P01 --condition manual --task A

# At the beginning/end of the participant's actual work
python tools/rq4/rq4.py timer start --participant P01 --condition manual --task A
python tools/rq4/rq4.py timer stop  --participant P01 --condition manual --task A

# Put the participant's manually written scripts in a folder, named uc1_*.py, uc2_*.py, uc3_*.py
python tools/rq4/rq4.py check --reviewer P01 --condition manual --phase after_review --task A --tests artifacts/rq4/P01_manual_A

# The same checker is used for an AI-assisted project after the person has approved its artifacts.
python tools/rq4/rq4.py export --project P01-assisted-B --out artifacts/rq4/P01_ai_B
python tools/rq4/rq4.py check --reviewer P01 --condition ai_assisted --phase after_review --task B --tests artifacts/rq4/P01_ai_B
python tools/rq4/rq4.py analyze
```

`analyze` only pairs logged start/stop events and reports incomplete or invalid timer pairs. It leaves a metric empty when a real session has not supplied it.

## Existing controlled evidence

The completed `RQ4-HIL-*` ShopLab runs remain quality-gate evidence: after grounding and AG-08, all six use cases passed `v0` and failed their assigned semantic mutations. They are **not** manual-versus-assisted participant results and must not be included in a productivity comparison.

## Valid conclusion

If real sessions show lower completion time for `ai_assisted` without lower semantic validity or behavioral coverage, conclude that the system accelerates artifact creation while retaining human responsibility for validation. Do not conclude that it replaces a tester.
