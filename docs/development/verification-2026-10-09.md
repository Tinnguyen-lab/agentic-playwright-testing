# Verification audit — 2026-10-09

This audit records observed results, not target claims.  Cloud runs used the
configured `deepseek-chat` endpoint; results can vary between runs.

## Reproduce

```powershell
python -m pytest -q
python run_playwright_pipeline.py --mock --out artifacts/retest/final_playwright_pipeline.json
python evaluate_rq1.py --out artifacts/retest/rq1_deepseek_final_v2.json
python run_rq2.py --context both --out artifacts/retest/rq2_deepseek.json
python run_rq3.py --out artifacts/retest/rq3_deepseek.json
python tools/rq4/rq4.py analyze
```

## Observed evidence

| Scope | Evidence | Observed result |
|---|---|---|
| Regression | `python -m pytest -q` | 113 passed |
| End-to-end execution | `artifacts/retest/final_playwright_pipeline.json` | 3/3 locators grounded; Playwright passed; isolated PNG, trace ZIP, source, stdout and stderr persisted |
| RQ1 | `artifacts/retest/rq1_deepseek_final_v2.json` | pipeline: 170 cases, 75.9% gold-condition coverage, 170/170 trace links, 6.5% unsupported according to LLM judge |
| RQ2 | `artifacts/retest/rq2_deepseek.json` | 50 targets: baseline 35/50 (70%), ARIA context 39/50 (78%) |
| RQ3 | `artifacts/retest/rq3_deepseek.json` | constrained arm: 28/46 technical repairs, 0/23 semantic mutations masked, 24 escalations, 0 assertion weakenings |
| RQ4 | `artifacts/rq4/rq4_results.json` | historical snapshot: protocol/tooling existed before a real review session was logged; it is not a user-study comparison |

## Interpretation boundaries

- RQ1 unsupported is not zero.  The requirement-review gate must remain in the
  workflow; ambiguous or contradictory requirements are not automatically
  approved.
- RQ2 combines model, network and target-site variability.  The failure
  taxonomy in `run_rq2.py` must be used before attributing a failure to the
  model.
- RQ3 demonstrates constrained-repair behaviour only on ShopLab mutations.
- RQ4-S had no real-review outcome at the time of this historical snapshot; later review evidence must be reported separately without a participant comparison.
  Do not present `n=0` as a usability or effort-reduction result.
