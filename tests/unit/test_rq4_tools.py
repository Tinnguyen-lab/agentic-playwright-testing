"""Tính điểm SUS và thời gian từ nhật ký bấm giờ (RQ4) — thuần, offline."""
from tools.rq4.rq4 import minutes, sus_score


def test_sus_score_bounds():
    assert sus_score([5, 1] * 5) == 100.0
    assert sus_score([1, 5] * 5) == 0.0
    assert sus_score([3] * 10) == 50.0


def test_minutes_pairs_start_stop():
    rows = [{"participant": "P1", "condition": "manual", "event": "start", "time": "2026-10-10T08:00:00+00:00"},
            {"participant": "P1", "condition": "manual", "event": "stop", "time": "2026-10-10T08:25:30+00:00"}]
    assert minutes(rows) == {("P1", "manual"): 25.5}
