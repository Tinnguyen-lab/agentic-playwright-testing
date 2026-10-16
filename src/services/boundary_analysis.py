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
_PRESENTATION_MARKERS = (
    "kết quả", "mỗi trang", "trên trang", "hiển thị", "display", "per page",
)
_NUMBER = r"(\d[\d.,]*)"

_RANGE = [
    re.compile(rf"từ\s+{_NUMBER}\s+đến\s+{_NUMBER}", re.I),
    re.compile(rf"between\s+{_NUMBER}\s+and\s+{_NUMBER}", re.I),
    re.compile(rf"{_NUMBER}\s*(?:\.\.|to|-|–|—)\s*{_NUMBER}", re.I),
]
_MIN = re.compile(rf"(?:tối thiểu|ít nhất|lớn hơn hoặc bằng|min(?:imum)?|at least|>=|≥)\s*{_NUMBER}", re.I)
_MAX = re.compile(rf"(?:tối đa|không quá|nhiều nhất|max(?:imum)?|at most|no more than|<=|≤)\s*{_NUMBER}", re.I)


def _number(value: str) -> int:
    """Parse integer limits written as 2.000 / 2,000 in Vietnamese specs."""
    return int(value.replace(".", "").replace(",", ""))


def parse_bounds(constraint: str) -> list[dict]:
    """Nhận bound số từ một ràng buộc. Không rõ ràng -> [] (fail-closed)."""
    text = constraint.strip()
    unit = next((u for u in _UNITS if u in text.lower()), "")
    for rx in _RANGE:
        m = rx.search(text)
        if m:
            lo, hi = _number(m.group(1)), _number(m.group(2))
            if lo <= hi:
                return [{"kind": "range", "lo": lo, "hi": hi, "unit": unit, "excerpt": text}]
    m = _MIN.search(text)
    if m:
        return [{"kind": "min", "lo": _number(m.group(1)), "hi": None, "unit": unit, "excerpt": text}]
    m = _MAX.search(text)
    if m:
        return [{"kind": "max", "lo": None, "hi": _number(m.group(1)), "unit": unit, "excerpt": text}]
    return []


def _case(value: int, ttype: TestType, label: str, unit: str, excerpt: str, req: StructuredRequirement) -> TestCase:
    """Ca biên gắn với hành động của yêu cầu (không chỉ "nhập giá trị N") để người đọc và giám khảo biết nó kiểm gì."""
    u = f" {unit}" if unit else ""
    verb = "được chấp nhận" if ttype == TestType.BOUNDARY else "bị từ chối"
    return TestCase(
        title=f"{label}: giá trị {value}{u} — {req.title}",
        type=ttype,
        preconditions=[req.precondition] if req.precondition else [],
        steps=[TestStep(action=f"{req.action} với giá trị {value}{u} (ràng buộc: {excerpt})", expected=f"Hệ thống {verb}")],
        expected_result=f"Thao tác \"{req.action}\" với giá trị {value}{u} {verb}, theo ràng buộc: {excerpt}",
        source_excerpt=excerpt,
    )


def derive_boundary_cases(requirement: StructuredRequirement) -> list[TestCase]:
    """Sinh case BVA từ các ràng buộc số của requirement. Dedupe nội bộ theo (type, value, excerpt)."""
    cases: list[TestCase] = []
    seen: set = set()
    for constraint in requirement.constraints:
        # A numeric limit on rendered results (for example "at most 10 results
        # per page") is not an input domain.  Treating 11 as an input value and
        # asserting rejection invents behaviour that the requirement never says.
        # Skip it rather than producing an unsupported negative case.
        normalized = constraint.casefold()
        if any(marker in normalized for marker in _PRESENTATION_MARKERS):
            continue
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
                cases.append(_case(value, ttype, label, b["unit"], b["excerpt"], requirement))
    return cases
