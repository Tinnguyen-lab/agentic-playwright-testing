"""Artifacts cho Playwright Generation + Execution Agent (architecture v0.1, mục 5.6-5.7)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    GOTO = "goto"
    FILL = "fill"
    CLICK = "click"
    EXPECT_URL = "expect_url"
    EXPECT_VISIBLE = "expect_visible"
    EXPECT_TEXT = "expect_text"


class LocatorStrategy(str, Enum):
    ROLE = "role"
    LABEL = "label"
    PLACEHOLDER = "placeholder"
    TEXT = "text"
    TEST_ID = "test_id"
    CSS = "css"


class PlaywrightAction(BaseModel):
    type: ActionType
    strategy: LocatorStrategy | None = None
    value: str = ""       # giá trị locator (css/text/placeholder/label/testid) hoặc role
    role_name: str = ""   # accessible name khi strategy=role
    arg: str = ""         # fill text / url / expected text


class PlaywrightPlan(BaseModel):
    test_case_id: str = ""
    target_url: str = ""
    actions: list[PlaywrightAction] = Field(default_factory=list)


class GroundingRecord(BaseModel):
    action_index: int
    strategy: str
    value: str
    matched_count: int
    ok: bool


class GeneratedScript(BaseModel):
    test_case_id: str
    code: str
    grounding: list[GroundingRecord] = Field(default_factory=list)


class ExecStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    BLOCKED = "blocked"


class ExecutionResult(BaseModel):
    test_case_id: str
    status: ExecStatus
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    artifacts: list[str] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
