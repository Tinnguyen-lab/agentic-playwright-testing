"""Bảo vệ fixture RQ4-S: đây là ablation cố định, không phải dữ liệu người dùng."""
from tools.rq4.simulate import cases


def test_simulation_has_six_cases_per_arm():
    data = cases()
    assert set(data) == {"system_only", "reviewed"}
    assert sum(len(task) for task in data["system_only"].values()) == 6
    assert sum(len(task) for task in data["reviewed"].values()) == 6


def test_review_restores_the_two_missing_oracles_only():
    data = cases()
    assert "Invalid username or password" not in data["system_only"]["A"]["uc2"]
    assert "Invalid username or password" in data["reviewed"]["A"]["uc2"]
    assert "First name is required" not in data["system_only"]["B"]["uc2"]
    assert "First name is required" in data["reviewed"]["B"]["uc2"]
