"""Playwright Generation Agent (architecture v0.1, mục 5.6).

TestCase đã approved -> PlaywrightPlan (LLM) -> grounding locator trên UI thật -> script.
Grounding tách thành hàm thuần `ground_actions(actions, count_fn)` để test offline.
"""
from __future__ import annotations

from src.models.playwright_artifacts import (
    GeneratedScript,
    GroundingRecord,
    LocatorStrategy,
    PlaywrightPlan,
)
from src.models.test_case import TestCase
from src.services.llm_client import LLMClient
from src.services.script_template import render_script

SYSTEM_PROMPT = """\
Bạn là kỹ sư tự động hoá Playwright. Chuyển MỘT test case đã duyệt thành chuỗi action
Playwright chạy trên website đích.

QUY TẮC:
- Mỗi action: type (goto/fill/click/expect_url/expect_visible/expect_text),
  strategy (role/label/placeholder/text/test_id/css) khi cần locator, value, role_name
  (khi strategy=role), arg (giá trị fill / url / text kỳ vọng).
- ƯU TIÊN locator theo role/label/placeholder/text/test_id; hạn chế css.
- Bắt đầu bằng goto tới URL đích. Kết thúc bằng ít nhất một expect kiểm chứng expected_result.
- Không bịa bước ngoài test case.

Trả JSON PlaywrightPlan: { "actions": [ ... ] }.\
"""


def ground_actions(actions, count_fn) -> list[GroundingRecord]:
    """Đếm số element khớp cho mỗi action có locator. count_fn(strategy, value, role_name)->int."""
    records = []
    for index, action in enumerate(actions):
        if action.strategy is None:
            continue
        matched = count_fn(action.strategy, action.value, action.role_name)
        records.append(GroundingRecord(
            action_index=index,
            strategy=action.strategy.value,
            value=action.value or action.role_name,
            matched_count=matched,
            ok=(matched == 1),
        ))
    return records


def live_count_fn(page):
    """count_fn dựa trên một Playwright page thật."""
    def count(strategy: LocatorStrategy, value: str, role_name: str) -> int:
        if strategy == LocatorStrategy.ROLE:
            loc = page.get_by_role(value, name=role_name) if role_name else page.get_by_role(value)
        elif strategy == LocatorStrategy.LABEL:
            loc = page.get_by_label(value)
        elif strategy == LocatorStrategy.PLACEHOLDER:
            loc = page.get_by_placeholder(value)
        elif strategy == LocatorStrategy.TEXT:
            loc = page.get_by_text(value)
        elif strategy == LocatorStrategy.TEST_ID:
            loc = page.get_by_test_id(value)
        else:
            loc = page.locator(value)
        return loc.count()
    return count


class PlaywrightGenerationAgent:
    def __init__(self, llm: LLMClient, model_name: str = "unknown"):
        self._llm = llm
        self._model_name = model_name

    def plan(self, test_case: TestCase, target_url: str) -> PlaywrightPlan:
        user_prompt = self._build_user_prompt(test_case, target_url)
        plan = self._llm.structured_completion(SYSTEM_PROMPT, user_prompt, PlaywrightPlan)
        return plan.model_copy(update={"test_case_id": test_case.id, "target_url": target_url})

    def generate(self, test_case: TestCase, target_url: str, count_fn=None, screenshot: str = "screenshot.png") -> GeneratedScript:
        plan = self.plan(test_case, target_url)
        grounding = ground_actions(plan.actions, count_fn) if count_fn is not None else []
        return GeneratedScript(test_case_id=test_case.id, code=render_script(plan, screenshot), grounding=grounding)

    @staticmethod
    def _build_user_prompt(test_case: TestCase, target_url: str) -> str:
        steps = "\n".join(f"  - {s.action} => {s.expected or '—'}" for s in test_case.steps)
        return (
            f"Website đích: {target_url}\n"
            f"Test case: {test_case.title} (loại {test_case.type.value})\n"
            f"Precondition: {', '.join(test_case.preconditions) or '—'}\n"
            f"Steps:\n{steps or '  —'}\n"
            f"Expected result: {test_case.expected_result or '—'}"
        )
