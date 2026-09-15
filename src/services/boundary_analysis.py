"""Suy diễn test biên/âm bản theo Boundary Value Analysis (đào sâu Test Design, mục 5.5).

Từ ràng buộc SỐ tường minh trong requirement, sinh case BVA tất định, grounded (không vượt
phạm vi requirement). Augment kết quả LLM để ĐẢM BẢO phủ biên thay vì phó mặc LLM tự nhớ.

# ponytail: heuristic regex, chỉ nhận bound số tường minh; nâng cấp = parser ràng buộc có cấu trúc.
"""
from __future__ import annotations

import re

from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCase, TestStep, TestType

_UNITS = ("ký tự", "kí tự", "characters", "chars")

_RANGE = [
    re.compile(r"từ\s+(\d+)\s+đến\s+(\d+)", re.I),
    re.compile(r"between\s+(\d+)\s+and\s+(\d+)", re.I),
    re.compile(r"(\d+)\s*(?:\.\.|to|-|–|—)\s*(\d+)", re.I),
]
_MIN = re.compile(r"(?:tối thiểu|ít nhất|lớn hơn hoặc bằng|min(?:imum)?|at least|>=|≥)\s*(\d+)", re.I)
_MAX = re.compile(r"(?:tối đa|không quá|nhiều nhất|max(?:imum)?|at most|no more than|<=|≤)\s*(\d+)", re.I)


def parse_bounds(constraint: str) -> list[dict]:
    """Nhận bound số từ một ràng buộc. Không rõ ràng -> [] (fail-closed)."""
    text = constraint.strip()
    unit = next((u for u in _UNITS if u in text.lower()), "")
    for rx in _RANGE:
        m = rx.search(text)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo <= hi:
                return [{"kind": "range", "lo": lo, "hi": hi, "unit": unit, "excerpt": text}]
    m = _MIN.search(text)
    if m:
        return [{"kind": "min", "lo": int(m.group(1)), "hi": None, "unit": unit, "excerpt": text}]
    m = _MAX.search(text)
    if m:
        return [{"kind": "max", "lo": None, "hi": int(m.group(1)), "unit": unit, "excerpt": text}]
    return []


def _case(value: int, ttype: TestType, label: str, unit: str, excerpt: str) -> TestCase:
    u = f" {unit}" if unit else ""
    verb = "chấp nhận" if ttype == TestType.BOUNDARY else "bị từ chối"
    return TestCase(
        title=f"{label}: giá trị {value}{u}",
        type=ttype,
        steps=[TestStep(action=f"Nhập giá trị {value}{u}", expected=f"Hệ thống {verb}")],
        expected_result=f"{value}{u} — {verb} (ràng buộc: {excerpt})",
        source_excerpt=excerpt,
    )


def derive_boundary_cases(requirement: StructuredRequirement) -> list[TestCase]:
    """Sinh case BVA từ các ràng buộc số của requirement. Dedupe nội bộ theo (type, value, excerpt)."""
    cases: list[TestCase] = []
    seen: set = set()
    for constraint in requirement.constraints:
        for b in parse_bounds(constraint):
            pairs: list[tuple[int, TestType, str]] = []
            if b["kind"] in ("range", "min"):
                pairs.append((b["lo"], TestType.BOUNDARY, "Biên dưới"))
                pairs.append((b["lo"] - 1, TestType.NEGATIVE, "Dưới biên"))
            if b["kind"] in ("range", "max"):
                pairs.append((b["hi"], TestType.BOUNDARY, "Biên trên"))
                pairs.append((b["hi"] + 1, TestType.NEGATIVE, "Trên biên"))
            for value, ttype, label in pairs:
                key = (ttype, value, b["excerpt"])
                if key in seen:
                    continue
                seen.add(key)
                cases.append(_case(value, ttype, label, b["unit"], b["excerpt"]))
    return cases
