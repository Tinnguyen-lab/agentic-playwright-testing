"""Playwright Generation Agent (architecture v0.1, mục 5.6).

TestCase đã approved -> PlaywrightPlan (LLM) -> grounding locator trên UI thật -> script.
Grounding tách thành hàm thuần `ground_actions(actions, count_fn)` để test offline.
"""
from __future__ import annotations

from src.models.playwright_artifacts import (
    ActionType,
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
- Mỗi action: type (goto/fill/click/expect_url/expect_visible/expect_text), strategy
  (role/label/placeholder/text/test_id/css) khi cần locator, value, role_name, arg.
- Ý nghĩa trường (RẤT QUAN TRỌNG, không được nhầm):
  * strategy=role: `value` là VAI TRÒ ARIA (button/textbox/link/checkbox/heading...),
    `role_name` là TÊN HIỂN THỊ. VD nút chữ "Login" -> value="button", role_name="Login"
    (KHÔNG phải value="Login").
  * strategy=placeholder/label/text/test_id/css: `value` là chuỗi locator; để `role_name` trống.
  * goto: `arg` = URL (KHÔNG đặt URL vào `value`).  fill: `arg` = giá trị nhập.  expect_url: `arg` = URL kỳ vọng.
    expect_text: `value` = locator phần tử chứa văn bản (thường strategy=text với value là 1 phần
    của thông báo, hoặc test_id), `arg` = đoạn text kỳ vọng.
- ƯU TIÊN role/label/placeholder/text/test_id; hạn chế css.
- `nth` (mặc định -1): CHỈ đặt >= 0 khi locator khớp nhiều phần tử giống hệt nhau và cần chọn phần tử thứ nth (0-based).
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


def build_locator(page, strategy: LocatorStrategy, value: str, role_name: str, nth: int = -1):
    """Dựng Playwright locator từ (strategy, value, role_name[, nth]) trên page thật."""
    loc = _base_locator(page, strategy, value, role_name)
    return loc.nth(nth) if nth >= 0 else loc


def _base_locator(page, strategy: LocatorStrategy, value: str, role_name: str):
    if strategy == LocatorStrategy.ROLE:
        return page.get_by_role(value, name=role_name) if role_name else page.get_by_role(value)
    if strategy == LocatorStrategy.LABEL:
        return page.get_by_label(value)
    if strategy == LocatorStrategy.PLACEHOLDER:
        return page.get_by_placeholder(value)
    if strategy == LocatorStrategy.TEXT:
        return page.get_by_text(value)
    if strategy == LocatorStrategy.TEST_ID:
        return page.get_by_test_id(value)
    return page.locator(value)


def live_count_fn(page):
    """count_fn dựa trên một Playwright page thật."""
    def count(strategy: LocatorStrategy, value: str, role_name: str) -> int:
        return build_locator(page, strategy, value, role_name).count()
    return count


def _advance(page, action, locator, matched):
    """Thực thi action để đẩy trạng thái trang sang bước kế (goto/fill/click). Assertion không đổi state."""
    if action.type == ActionType.GOTO and action.arg:
        page.goto(action.arg)
    elif matched and locator is not None:
        try:
            if action.type == ActionType.FILL:
                locator.first.fill(action.arg)
            elif action.type == ActionType.CLICK:
                locator.first.click()
        except Exception:
            pass


def ground_flow(page, actions, wait_ms: int = 3000, snapshot_chars: int = 0) -> list[GroundingRecord]:
    """Multi-step grounding: đi theo luồng, ground mỗi locator trên DOM TẠI BƯỚC ĐÓ rồi mới đẩy trạng thái.

    Khác `ground_actions` (đếm trên một ảnh chụp tĩnh): phần tử xuất hiện sau điều hướng được ground đúng.
    snapshot_chars > 0: lưu aria snapshot của trang tại bước có locator khớp != 1 (làm phản hồi cho LLM).
    """
    records = []
    for index, action in enumerate(actions):
        locator = None
        matched = None
        if action.strategy is not None:
            locator = build_locator(page, action.strategy, action.value, action.role_name, action.nth)
            try:
                locator.first.wait_for(state="attached", timeout=wait_ms)
            except Exception:
                pass
            matched = locator.count()
            records.append(GroundingRecord(
                action_index=index,
                strategy=action.strategy.value,
                value=action.value or action.role_name,
                matched_count=matched,
                ok=(matched == 1),
                snapshot=page.locator("body").aria_snapshot()[:snapshot_chars] if snapshot_chars and matched != 1 else "",
            ))
        _advance(page, action, locator, matched)
    return records


class PlaywrightGenerationAgent:
    def __init__(self, llm: LLMClient, model_name: str = "unknown"):
        self._llm = llm
        self._model_name = model_name

    def plan(self, test_case: TestCase, target_url: str, page_context: str | None = None,
             feedback: str | None = None) -> PlaywrightPlan:
        """page_context: aria snapshot trang đích (RQ2 nhánh DOM-aware); None = baseline chỉ có test case.
        feedback: kết quả grounding của plan trước (xem `grounding_feedback`) để LLM sinh lại."""
        user_prompt = self._build_user_prompt(test_case, target_url, page_context, feedback)
        plan = self._llm.structured_completion(SYSTEM_PROMPT, user_prompt, PlaywrightPlan)
        return plan.model_copy(update={"test_case_id": test_case.id, "target_url": target_url})

    def generate(self, test_case: TestCase, target_url: str, count_fn=None, screenshot: str = "screenshot.png") -> GeneratedScript:
        plan = self.plan(test_case, target_url)
        grounding = ground_actions(plan.actions, count_fn) if count_fn is not None else []
        return GeneratedScript(test_case_id=test_case.id, code=render_script(plan, screenshot), grounding=grounding)

    @staticmethod
    def _build_user_prompt(test_case: TestCase, target_url: str, page_context: str | None = None,
                           feedback: str | None = None) -> str:
        steps = "\n".join(f"  - {s.action} => {s.expected or '—'}" for s in test_case.steps)
        prompt = (
            f"Website đích: {target_url}\n"
            f"Test case: {test_case.title} (loại {test_case.type.value})\n"
            f"Precondition: {', '.join(test_case.preconditions) or '—'}\n"
            f"Steps:\n{steps or '  —'}\n"
            f"Expected result: {test_case.expected_result or '—'}"
        )
        if page_context:
            prompt += (
                "\n\nAccessibility snapshot trang đích lúc vừa mở (YAML aria). Với phần tử có trong đây, "
                "chỉ dùng role/name đúng như snapshot; phần tử xuất hiện sau điều hướng thì suy luận như thường:\n"
                f"{page_context}"
            )
        if feedback:
            prompt += f"\n\n{feedback}"
        return prompt


def grounding_feedback(plan: PlaywrightPlan, records: list[GroundingRecord]) -> str | None:
    """Phản hồi cho LLM khi có locator không khớp đúng 1 phần tử trên trang thật; None nếu mọi locator đạt."""
    bad = [r for r in records if not r.ok]
    if not bad:
        return None
    lines = ["Plan trước đã được kiểm chứng trên trang thật; các locator sau KHÔNG khớp đúng 1 phần tử:"]
    for r in bad:
        a = plan.actions[r.action_index]
        lines.append(f"- action #{r.action_index} {a.type.value} {r.strategy}:{a.value}[{a.role_name}] nth={a.nth} "
                     f"khớp {r.matched_count} phần tử.")
        if r.snapshot:
            lines.append(f"  Cây trợ năng của trang tại bước này:\n{r.snapshot}")
    lines.append(f"Plan trước (JSON): {plan.model_dump_json()}")
    lines.append("Hãy sinh lại plan, chỉ sửa các locator trên sao cho mỗi locator khớp đúng 1 phần tử "
                 "(dùng role/name có trong cây trợ năng, hoặc nth khi có nhiều phần tử giống hệt nhau).")
    return "\n".join(lines)
