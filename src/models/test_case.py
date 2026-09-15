"""Structured artifacts cho Test Design Agent (architecture v0.1, mục 5.5).

Test case sinh từ requirement đã approved, gắn requirement_id để truy vết.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class TestType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    ERROR_GUESSING = "error_guessing"
    ALTERNATIVE_FLOW = "alternative_flow"


class TestStep(BaseModel):
    action: str
    expected: str = ""


class TestCase(BaseModel):
    id: str = ""
    requirement_id: str = ""
    title: str
    type: TestType
    preconditions: list[str] = Field(default_factory=list)
    steps: list[TestStep] = Field(default_factory=list)
    expected_result: str = ""
    source_excerpt: str = ""


class TestCaseDraft(BaseModel):
    """Đầu ra thô của LLM cho một requirement: chưa gán ID/requirement_id."""

    test_cases: list[TestCase] = Field(default_factory=list)


class TraceLink(BaseModel):
    from_id: str
    to_id: str
    link_type: str


class TestDesignResult(BaseModel):
    source_requirement_id: str
    test_cases: list[TestCase] = Field(default_factory=list)
    trace_links: list[TraceLink] = Field(default_factory=list)
    model_used: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field
    @property
    def type_coverage(self) -> list[str]:
        return sorted({tc.type.value for tc in self.test_cases})
