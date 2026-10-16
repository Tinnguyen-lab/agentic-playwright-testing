"""Artifacts cho Playwright Generation + Execution Agent (architecture v0.1, mục 5.6-5.7)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ActionType(str, Enum):
    GOTO = "goto"
    FILL = "fill"
    CLICK = "click"
    SELECT_OPTION = "select_option"
    CHECK = "check"
    UNCHECK = "uncheck"
    PRESS = "press"
    HOVER = "hover"
    DBLCLICK = "dblclick"
    UPLOAD_FILE = "upload_file"
    DRAG_TO = "drag_to"
    EXPECT_URL = "expect_url"
    EXPECT_VISIBLE = "expect_visible"
    EXPECT_TEXT = "expect_text"
    EXPECT_VALUE = "expect_value"
    EXPECT_CHECKED = "expect_checked"
    EXPECT_ENABLED = "expect_enabled"
    EXPECT_COUNT = "expect_count"


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
    nth: int = -1         # >= 0: chọn phần tử thứ nth (0-based) khi locator khớp nhiều phần tử giống nhau


    target_strategy: LocatorStrategy | None = None
    target_value: str = ""
    target_role_name: str = ""
    target_nth: int = -1

    @model_validator(mode="after")
    def validate_action_contract(self):
        if self.type == ActionType.DRAG_TO and self.target_strategy is None:
            raise ValueError("drag_to requires a target locator")
        if self.type == ActionType.EXPECT_COUNT:
            try:
                if int(self.arg) < 0:
                    raise ValueError
            except (TypeError, ValueError) as exc:
                raise ValueError("expect_count requires a non-negative integer arg") from exc
        return self


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
    locator_part: str = "source"
    snapshot: str = ""  # aria snapshot tại bước khi khớp != 1 (chỉ khi được yêu cầu)


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
    run_id: str = ""
    artifact_dir: str = ""
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    artifacts: list[str] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
