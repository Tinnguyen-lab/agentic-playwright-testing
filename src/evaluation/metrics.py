"""Metrics đánh giá phát hiện mơ hồ: đếm TP/FP/FN theo từng loại rồi tính P/R/F1.

Đơn vị so khớp là cặp (requirement, ambiguity_type): với mỗi requirement, so tập loại
mơ hồ dự đoán vs tập loại đúng (gold). Thuần hàm, không phụ thuộc LLM -> test tất định.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def accumulate_pair(by_type: dict[str, Counts], predicted: set[str], gold: set[str]) -> None:
    """Cộng dồn TP/FP/FN cho một requirement vào bảng đếm theo loại."""
    for t in predicted & gold:
        by_type.setdefault(t, Counts()).tp += 1
    for t in predicted - gold:
        by_type.setdefault(t, Counts()).fp += 1
    for t in gold - predicted:
        by_type.setdefault(t, Counts()).fn += 1


def micro(by_type: dict[str, Counts]) -> Counts:
    """Gộp mọi loại thành một Counts (micro-average)."""
    total = Counts()
    for c in by_type.values():
        total.tp += c.tp
        total.fp += c.fp
        total.fn += c.fn
    return total


def macro_f1(by_type: dict[str, Counts]) -> float:
    """Trung bình F1 qua các loại (macro-average)."""
    if not by_type:
        return 0.0
    return sum(c.f1 for c in by_type.values()) / len(by_type)
