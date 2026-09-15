"""Nạp dataset gán nhãn cho đánh giá phát hiện mơ hồ.

labels.json: mỗi case trỏ tới file tài liệu + danh sách requirement (theo thứ tự UC) với
tập loại mơ hồ kỳ vọng, cùng expected_global (mâu thuẫn toàn cục).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.services.document_loader import load_document


@dataclass
class Case:
    name: str
    text: str
    gold_reqs: list[set[str]]
    gold_global: set[str]


def load_dataset(root: str | Path) -> list[Case]:
    root = Path(root)
    labels = json.loads((root / "labels.json").read_text(encoding="utf-8"))
    cases = []
    for c in labels["cases"]:
        text = load_document(root / c["file"]).text
        gold_reqs = [set(r["expected"]) for r in c["requirements"]]
        gold_global = set(c.get("expected_global", []))
        cases.append(Case(c["file"], text, gold_reqs, gold_global))
    return cases
