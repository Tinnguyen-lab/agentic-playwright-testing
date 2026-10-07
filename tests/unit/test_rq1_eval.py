"""Số đo RQ1 (độ phủ điều kiện gold, unsupported, truy vết) và kappa — thuần, offline."""
from evaluate_rq1 import cohen_kappa, score

GOLD = {"d": [{"id": "A", "kind": "positive"}, {"id": "B", "kind": "boundary"}, {"id": "C", "kind": "negative"}]}


def _row(covers, supported=True, req="", typ="positive"):
    return {"doc": "d", "tc": {"requirement_id": req, "type": typ},
            "judgement": {"covers": covers, "supported": supported}}


def test_score_coverage_union_and_rates():
    s = score([_row(["A"], req="REQ-001"), _row(["A", "B"], typ="boundary"), _row([], supported=False)], GOLD)
    assert (s["covered"], s["n_gold"], s["n_tc"]) == (2, 3, 3)
    assert s["coverage_by_kind"]["negative"] == {"covered": 0, "n": 1}
    assert (s["unsupported"], s["no_gold_match"], s["traceable"], s["boundary_tc"]) == (1, 1, 1, 1)


def test_cohen_kappa():
    assert cohen_kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert abs(cohen_kappa([True, True, False, False], [True, False, True, False])) < 1e-9
