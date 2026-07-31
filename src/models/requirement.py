"""Structured artifacts cho Requirement Analysis Agent.

Ánh xạ các domain entity `Requirement` / `AmbiguityFinding` (architecture v0.1, mục 10).
Nguyên tắc: agent CHỈ phát hiện mơ hồ (không tự giải quyết); mỗi artifact có nguồn trích dẫn.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class AmbiguityType(str, Enum):
    """Rubric phân loại mơ hồ trong yêu cầu."""

    MISSING_ACTOR = "missing_actor"
    MISSING_PRECONDITION = "missing_precondition"
    VAGUE_QUANTIFIER = "vague_quantifier"
    MISSING_EXPECTED_OUTCOME = "missing_expected_outcome"
    UNDERSPECIFIED_ACTION = "underspecified_action"
    CONFLICT = "conflict"
    OTHER = "other"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AmbiguityFinding(BaseModel):
    """Một phát hiện mơ hồ, kèm loại + lý do + trích đoạn nguồn + gợi ý."""

    type: AmbiguityType
    description: str
    source_excerpt: str = ""
    suggestion: str | None = None
    severity: Severity = Severity.MEDIUM


class StructuredRequirement(BaseModel):
    """Một yêu cầu đã chuẩn hoá."""

    id: str = ""
    title: str
    actor: str | None = None
    precondition: str | None = None
    action: str
    expected_outcome: str | None = None
    constraints: list[str] = Field(default_factory=list)
    source_excerpt: str = ""
    ambiguities: list[AmbiguityFinding] = Field(default_factory=list)

    @computed_field
    @property
    def is_ambiguous(self) -> bool:
        return len(self.ambiguities) > 0


class RequirementExtraction(BaseModel):
    """Đầu ra thô của LLM: chỉ requirements + mâu thuẫn toàn cục (chưa gán ID/metadata)."""

    requirements: list[StructuredRequirement] = Field(default_factory=list)
    global_ambiguities: list[AmbiguityFinding] = Field(default_factory=list)


class RequirementAnalysisResult(BaseModel):
    """Kết quả cuối của agent: có ID, nguồn và metadata tái lập được."""

    source_name: str
    requirements: list[StructuredRequirement] = Field(default_factory=list)
    global_ambiguities: list[AmbiguityFinding] = Field(default_factory=list)
    model_used: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field
    @property
    def ambiguous_count(self) -> int:
        """Số yêu cầu mơ hồ + số mâu thuẫn toàn cục."""
        return sum(1 for r in self.requirements if r.is_ambiguous) + len(self.global_ambiguities)
