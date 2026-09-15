"""Test metrics đánh giá phát hiện mơ hồ: precision/recall/F1 theo loại. Thuần, offline."""
from collections import defaultdict

from src.evaluation.metrics import Counts, accumulate_pair, macro_f1, micro


def test_counts_precision_recall_f1():
    c = Counts(tp=3, fp=1, fn=1)
    assert c.precision == 0.75
    assert c.recall == 0.75
    assert round(c.f1, 3) == 0.75


def test_counts_zero_safe():
    c = Counts()
    assert c.precision == 0.0 and c.recall == 0.0 and c.f1 == 0.0


def test_accumulate_pair_tp_fp_fn():
    by = defaultdict(Counts)
    accumulate_pair(by, {"missing_actor", "conflict"}, {"missing_actor", "vague_quantifier"})
    assert by["missing_actor"].tp == 1     # bắt đúng
    assert by["conflict"].fp == 1          # báo thừa (over-flag)
    assert by["vague_quantifier"].fn == 1  # bỏ sót


def test_micro_and_macro():
    by = defaultdict(Counts)
    accumulate_pair(by, {"a"}, {"a"})   # a: tp
    accumulate_pair(by, {"b"}, set())   # b: fp
    accumulate_pair(by, set(), {"c"})   # c: fn
    m = micro(by)
    assert (m.tp, m.fp, m.fn) == (1, 1, 1)
    assert m.precision == 0.5 and m.recall == 0.5
    assert round(macro_f1(by), 3) == 0.333  # a=1.0, b=0, c=0 -> 1/3
