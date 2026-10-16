"""Streamlit UI — quy trình human-in-the-loop đầy đủ, lưu vào DB.

    streamlit run src/ui/app.py

① Phân tích yêu cầu → AG-01 · ② Thiết kế test (sửa được) → AG-02 · ③ Sinh script (aria snapshot + grounding
vòng lặp) và chạy · ④ Đề xuất sửa khi lỗi (self-healing → LLM có ràng buộc) → AG-03/04/05 · ⑤ Lịch sử, truy vết.
Mọi quyết định, version và thao tác được ghi DB (DATABASE_URL, mặc định SQLite) — thao tác dùng làm dữ liệu RQ4.
Tác vụ trình duyệt chạy ở tiến trình con (src/services/browser_tasks.py).
"""
from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]  # src/ui/app.py -> gốc dự án
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))  # để 'streamlit run' (chỉ thêm src/ui vào path) import được gốc

import streamlit as st

from run_requirement_agent import default_mock_extraction
from src.agents.execution_agent import ExecutionAgent, visible_browser_code
from src.agents.playwright_generation_agent import (
    PlaywrightGenerationAgent, grounding_feedback, normalize_navigation_urls,
)
from src.agents.repair_agent import RepairAgent
from src.agents.requirement_agent import RequirementAnalysisAgent
from src.agents.test_design_agent import TestDesignAgent
from src.database import session_factory
from src.models.playwright_artifacts import (
    ActionType, ExecStatus, ExecutionResult, GeneratedScript, GroundingRecord, LocatorStrategy, PlaywrightAction,
    PlaywrightPlan,
)
from src.models.approval import is_approved
from src.models.repair import RepairDraft
from src.models.test_case import TestCase, TestCaseDraft, TestPriority, TestSeverity, TestType
from src.repositories.store import Store
from src.services.browser_tasks import BrowserTaskError, run_task
from src.services.auth_state import has_state, state_path
from src.services.document_loader import load_document
from src.services.llm_errors import llm_failure_message
from src.services.manual_script import is_manual_script, validate_manual_script
from src.services.script_template import render_script
from src.services.test_triage import evaluate_test_case, triage_sort_key
from src.ui.review import approved_requirement_ids, approved_test_case_ids, edited_test_case, repair_gate
from src.utils.cli import resolve_client

SAMPLE = _ROOT / "datasets/reference/sample_requirements.md"
WORKDIR = _ROOT / "artifacts/exec_ui"


# ---------- mock cho chế độ offline ----------
def _design_mock() -> TestCaseDraft:
    return TestCaseDraft(test_cases=[TestCase(title="Luồng hợp lệ", type=TestType.POSITIVE),
                                     TestCase(title="Dữ liệu không hợp lệ", type=TestType.NEGATIVE)])


def _plan_mock(url: str) -> PlaywrightPlan:
    return PlaywrightPlan(actions=[PlaywrightAction(type=ActionType.GOTO, arg=url),
                                   PlaywrightAction(type=ActionType.EXPECT_VISIBLE, strategy=LocatorStrategy.ROLE,
                                                    value="heading", role_name="ShopLab")])


# ---------- hạ tầng ----------
@st.cache_resource
def _store() -> Store:
    return Store(session_factory())


def _client(mock_response):
    if BACKEND.startswith("mock"):
        return resolve_client(None, True, mock_response)
    return resolve_client(None, False, mock_response)


def log(event: str, **payload) -> None:
    store.log_event(pid, SID, event, actor=ACTOR, **payload)


def show_browser_task_error(exc: BrowserTaskError, tc_id: str) -> None:
    detail = str(exc)
    log("browser_task_failed", tc=tc_id, error=detail[:300])
    if "ERR_CONNECTION_REFUSED" in detail:
        st.error(f"Không thể kết nối website đích {BASE_URL}. Hãy chạy ứng dụng đích rồi thử lại.")
    else:
        st.error(f"Không thể khảo sát website đích: {detail}")


def badge(decisions, artifact_id: str) -> str:
    for d in reversed(decisions):
        if d.artifact_id == artifact_id:
            return {"approved": "✅ đã duyệt", "rejected": "⛔ từ chối"}.get(d.status.value, "⏳ chờ")
    return "⏳ chờ duyệt"


def decide(gate: str, kind: str, artifact_id: str, approved: bool, version: int = 1) -> None:
    store.record_decision(pid, gate, kind, artifact_id, approved, decided_by=ACTOR, artifact_version=version)
    log("decision", gate=gate, artifact=artifact_id, approved=approved)


def generate(tc: TestCase) -> bool:
    """DOM-aware: aria snapshot trang đích → LLM → grounding trên trang thật → nếu locator khớp != 1 thì sinh lại 1 lần."""
    snap = run_task("snapshot", {"url": BASE_URL, **auth_payload()}).get("snapshot", "")
    client, model = _client(_plan_mock(BASE_URL))
    agent = PlaywrightGenerationAgent(client, model_name=model)
    plan = agent.plan(tc, BASE_URL, page_context=snap or None)
    records = _ground(plan)
    if (fb := grounding_feedback(plan, records)) is not None:
        plan = agent.plan(tc, BASE_URL, page_context=snap or None, feedback=fb)
        records = _ground(plan)
    if any(not record.ok for record in records):
        log("generation_blocked_grounding", tc=tc.id,
            invalid_actions=[record.action_index for record in records if not record.ok])
        return False
    save_plan(tc.id, plan, records)
    log("generate_script", tc=tc.id, refined=fb is not None)
    return True


def _ground(plan: PlaywrightPlan) -> list[GroundingRecord]:
    out = run_task("ground", {"plan": plan.model_dump(mode="json"), **auth_payload()})
    return [GroundingRecord(**r) for r in out.get("records", [])]


def save_plan(tc_id: str, plan: PlaywrightPlan, records=None) -> int:
    plan = normalize_navigation_urls(plan, BASE_URL)
    script = GeneratedScript(test_case_id=tc_id, code=render_script(plan, screenshot=f"{tc_id}.png"),
                             grounding=records or [])
    return store.save_script(pid, plan, script)


def save_grounded_plan(tc_id: str, plan: PlaywrightPlan) -> bool:
    """Persist a manually edited or repaired plan only after live grounding."""
    plan = normalize_navigation_urls(plan, BASE_URL)
    records = _ground(plan)
    if any(not record.ok for record in records):
        log("plan_save_blocked_grounding", tc=tc_id,
            invalid_actions=[record.action_index for record in records if not record.ok])
        return False
    save_plan(tc_id, plan, records)
    return True


def auth_payload() -> dict:
    return {"storage_state": str(AUTH_FILE)} if USE_AUTH and AUTH_FILE is not None else {}


def execute(tc_id: str, capture_auth: bool = False) -> ExecutionResult:
    row = store.latest_scripts(pid)[tc_id]
    result = ExecutionAgent().run(
        GeneratedScript(test_case_id=tc_id, code=row.code), WORKDIR,
        auth_state_in=AUTH_FILE if USE_AUTH and not capture_auth else None,
        auth_state_save=AUTH_FILE if capture_auth else None,
    )
    store.save_execution(pid, result, row.id)
    log("execute", tc=tc_id, status=result.status.value, auth_saved=result.auth_state_saved)
    return result


def propose_repair(tc: TestCase) -> None:
    """Hệ thống có ràng buộc: self-healing tất định trước, LLM có ràng buộc sau; policy phân mức, KHÔNG tự áp dụng."""
    row = store.latest_scripts(pid)[tc.id]
    run = store.latest_executions(pid)[tc.id]
    plan = PlaywrightPlan.model_validate_json(row.plan_json)
    result = ExecutionResult(test_case_id=tc.id, status=ExecStatus(run.status), exit_code=run.exit_code,
                             stderr=run.stderr, artifacts=json.loads(run.artifacts_json))
    attempt = 1 + sum(1 for _, p in store.repairs(pid) if p.test_case_id == tc.id)
    probe = run_task("probe_heal", {"plan": plan.model_dump(mode="json"), **auth_payload()})
    if probe.get("healed"):
        healed = {int(k): PlaywrightAction(**v) for k, v in probe["healed"].items()}
        proposal = RepairAgent(model_name="self-healing").propose_with_healing(plan, healed, result, tc, attempt)
    else:
        client, model = _client(RepairDraft(new_plan=plan))
        proposal = RepairAgent(client, model).propose(plan, result, tc, attempt,
                                                      page_context=probe.get("evidence", ""))
    store.save_repair(pid, proposal, run.id)
    log("propose_repair", tc=tc.id, risk=proposal.risk_level.value, kinds=proposal.changed_kinds)


# ---------- giao diện ----------
st.set_page_config(page_title="Agentic Playwright", page_icon="🧪", layout="wide")
store = _store()
SID = st.session_state.setdefault("sid", uuid.uuid4().hex[:12])

with st.sidebar:
    st.header("⚙️ Cấu hình")
    ACTOR = st.text_input("Người dùng / mã người tham gia", value="reviewer")
    PROJECT = st.text_input("Dự án", value="ShopLab")
    BASE_URL = st.text_input("URL ứng dụng đích", value="http://127.0.0.1:5100/login")
    BACKEND = st.selectbox(
        "LLM backend",
        ["DeepSeek (.env)", "mock (offline)"],
        help="DeepSeek là backend LLM duy nhất dùng khóa API. Mock hoạt động hoàn toàn offline.",
    )
    DESIGN_MODE = "Expanded — cần duyệt"
    st.caption("Thiết kế test: Expanded — các case thiếu oracle phải được người duyệt xác nhận.")
    if BACKEND.startswith("mock"):
        st.caption("Mock offline always returns a fixed number of cases; choose local/cloud for expanded generation.")
    st.caption(f"Phiên: `{SID}`")
    st.divider()
    st.header("📄 Tài liệu yêu cầu")
    mode = st.radio("Nguồn", ["Tài liệu mẫu", "Dán văn bản", "Tải lên (DOCX/PDF/TXT/MD)"])
    doc_text = ""
    if mode == "Tài liệu mẫu":
        doc_text = SAMPLE.read_text(encoding="utf-8") if SAMPLE.exists() else ""
    elif mode == "Dán văn bản":
        doc_text = st.text_area("Nội dung", height=200, placeholder="Dán tài liệu yêu cầu...")
    else:
        up = st.file_uploader("Tệp yêu cầu", type=["docx", "pdf", "txt", "md"])
        if up:
            suffix = Path(up.name).suffix.lower()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
                temp.write(up.getvalue())
                temp_path = Path(temp.name)
            try:
                doc_text = load_document(temp_path).text
            except Exception as exc:
                st.error(f"Không đọc được tài liệu: {exc}")
            finally:
                temp_path.unlink(missing_ok=True)
    run_req = st.button("① Phân tích yêu cầu", type="primary", use_container_width=True)

pid = store.get_or_create_project(PROJECT, BASE_URL)
try:
    AUTH_FILE = state_path(pid, BASE_URL)
except ValueError:
    AUTH_FILE = None
with st.sidebar:
    st.divider()
    st.subheader("Phiên đăng nhập dùng lại")
    auth_available = AUTH_FILE is not None and has_state(AUTH_FILE)
    USE_AUTH = st.checkbox(
        "Dùng phiên đã lưu cho trang được bảo vệ",
        disabled=not auth_available,
        key=f"use_auth_{pid}_{AUTH_FILE.name if AUTH_FILE else 'invalid'}",
        help="Bật cho test trên trang cần đăng nhập; tắt khi kiểm thử đăng nhập, đăng xuất hoặc truy cập không xác thực.",
    ) and auth_available
    st.caption("Đã có phiên cho website này." if auth_available else
               "Chưa có phiên. Chạy thành công script đăng nhập và chọn 'Chạy & lưu phiên'.")
    if auth_available and st.button("Xóa phiên đã lưu", key=f"clear_auth_{pid}_{AUTH_FILE.name}"):
        AUTH_FILE.unlink(missing_ok=True)
        st.rerun()
    if notice := st.session_state.pop("auth_notice", None):
        st.success(notice)
if not st.session_state.get("started"):
    st.session_state.started = True
    log("session_start")

st.title("🧪 Agentic Playwright")
st.caption("Agent chỉ ĐỀ XUẤT; con người quyết định ở các cổng AG-01..AG-08. Mọi quyết định và thao tác được lưu DB.")

if run_req:
    if doc_text.strip():
        with st.spinner("Đang phân tích yêu cầu..."):
            try:
                client, model = _client(default_mock_extraction())
                result = RequirementAnalysisAgent(client, model_name=model).analyze(doc_text, source_name="ui")
            except Exception as exc:
                # Do not expose a provider traceback (or credential details) in
                # the reviewer UI. The reviewer can retry after configuration is
                # corrected; no requirement/approval is persisted on failure.
                log("analyze_failed", error_type=type(exc).__name__)
                st.error(llm_failure_message(exc))
            else:
                store.save_requirements(pid, result.requirements, source_name="ui")
                st.session_state.global_amb = [a.description for a in result.global_ambiguities]
                log("analyze", n=len(result.requirements))
    else:
        st.warning("Chưa có nội dung tài liệu.")

tab_flow, tab_hist = st.tabs(["Quy trình", "Lịch sử & truy vết"])

with tab_flow:
    reqs = store.latest_requirements(pid)
    if not reqs:
        st.info("Chọn nguồn tài liệu ở thanh bên rồi bấm **① Phân tích yêu cầu**.")
        st.stop()

    # ① AG-01
    d1 = store.decisions(pid, "AG-01")
    rv = store.versions(pid, "requirement")
    st.subheader(f"① Yêu cầu ({len(reqs)}) — cổng AG-01")
    for req in reqs:
        with st.container(border=True):
            left, right = st.columns([5, 2])
            left.markdown(f"**[{req.id}] v{rv[req.id]} {req.title}** — {badge(d1, req.id)}")
            left.caption(f"actor: {req.actor or '—'} · action: {req.action} · outcome: {req.expected_outcome or '—'}")
            for a in req.ambiguities:
                left.markdown(f"&nbsp;&nbsp;⚠ `{a.type.value}` — {a.description}")
            b1, b2 = right.columns(2)
            if b1.button("Duyệt", key=f"ap_{req.id}", use_container_width=True):
                decide("AG-01", "requirement", req.id, True, rv[req.id])
                st.rerun()
            if b2.button("Từ chối", key=f"re_{req.id}", use_container_width=True):
                decide("AG-01", "requirement", req.id, False, rv[req.id])
                st.rerun()
    for g in st.session_state.get("global_amb", []):
        st.warning(f"🔺 Mâu thuẫn toàn cục: {g}")

    # ② AG-02
    approved_reqs = approved_requirement_ids(reqs, d1, rv)
    st.subheader(f"② Test case — {len(approved_reqs)}/{len(reqs)} yêu cầu đã duyệt · cổng AG-02")
    if not approved_reqs:
        st.info("Duyệt ít nhất một yêu cầu ở trên.")
        st.stop()
    if st.button("Thiết kế test cho các yêu cầu đã duyệt"):
        with st.spinner("Đang thiết kế test..."):
            try:
                client, model = _client(_design_mock())
                agent = TestDesignAgent(client, model_name=model)
                designed = [agent.design(req) for req in reqs if req.id in approved_reqs]
            except Exception as exc:
                log("design_failed", error_type=type(exc).__name__)
                st.error(llm_failure_message(exc))
            else:
                for result in designed:
                    store.save_test_cases(pid, result.test_cases)
                log("design", reqs=approved_reqs)
                st.rerun()
    tcs = sorted(
        (evaluate_test_case(tc) for tc in store.latest_test_cases(pid) if tc.requirement_id in approved_reqs),
        key=triage_sort_key,
    )
    d2 = store.decisions(pid, "AG-02")
    tv = store.versions(pid, "test_case")
    for tc in tcs:
        with st.container(border=True):
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.markdown(f"`{tc.id}` v{tv[tc.id]} · **{tc.priority.value} / {tc.severity.value}** "
                        f"· {tc.type.value} · {tc.title} — {badge(d2, tc.id)}")
            c1.caption(f"Ưu tiên/tác động ({tc.triage_source}): {tc.triage_reason}")
            if tc.scenario_id:
                c1.caption(f"Scenario: {tc.scenario_id}")
            if tc.review_required:
                c1.warning(f"Cần xác nhận: {tc.review_note or 'Case này có giả định ngoài requirement.'}")
            if c2.button("Duyệt", key=f"aptc_{tc.id}", use_container_width=True):
                decide("AG-02", "test_case", tc.id, True, tv[tc.id])
                st.rerun()
            if c3.button("Từ chối", key=f"retc_{tc.id}", use_container_width=True):
                decide("AG-02", "test_case", tc.id, False, tv[tc.id])
                st.rerun()
            with st.expander("Xem / sửa test case"):
                title = st.text_input("Tiêu đề", tc.title, key=f"t_{tc.id}")
                steps = st.text_area("Các bước (mỗi dòng một bước)", "\n".join(s.action for s in tc.steps), key=f"s_{tc.id}")
                expected = st.text_input("Kết quả mong đợi", tc.expected_result, key=f"e_{tc.id}")
                p_options = list(TestPriority)
                s_options = list(TestSeverity)
                priority = st.selectbox("Priority", p_options, index=p_options.index(tc.priority),
                                        format_func=lambda value: value.value, key=f"priority_{tc.id}_v{tv[tc.id]}")
                severity = st.selectbox("Severity", s_options, index=s_options.index(tc.severity),
                                        format_func=lambda value: value.value, key=f"severity_{tc.id}_v{tv[tc.id]}")
                triage_reason = st.text_input("Lý do xếp hạng", tc.triage_reason,
                                              key=f"triage_reason_{tc.id}_v{tv[tc.id]}")
                if st.button("Lưu thành version mới", key=f"sv_{tc.id}"):
                    if (new := edited_test_case(tc, title, steps, expected,
                                                priority, severity, triage_reason)) is not None:
                        store.save_test_cases(pid, [new])
                        log("edit_test_case", tc=tc.id)
                        st.rerun()

    # ③ sinh + chạy
    approved_tcs = [tc for tc in tcs if tc.id in approved_test_case_ids(tcs, d2, tv)]
    st.subheader(f"③ Sinh script và chạy — {len(approved_tcs)} test case đã duyệt")
    st.caption("Khi bấm Chạy, Chromium mở toàn màn hình trên máy đang chạy hệ thống và tự đóng sau khi test kết thúc.")
    scripts, runs = store.latest_scripts(pid), store.latest_executions(pid)
    for tc in approved_tcs:
        with st.container(border=True):
            row, run = scripts.get(tc.id), runs.get(tc.id)
            status = f"{'✅' if run.status == 'passed' else '❌'} {run.status}" if run else "chưa chạy"
            d8 = store.decisions(pid, "AG-08")
            script_approved = bool(row and is_approved(d8, tc.id, row.version))
            c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1])
            review_state = "✅ script đã duyệt" if script_approved else "⏳ chờ duyệt script"
            c1.markdown(f"`{tc.id}` **{tc.priority.value} / {tc.severity.value}** · {tc.title} "
                        f"· script: {f'v{row.version}' if row else '—'} · {review_state} · {status}")
            if c2.button("Sinh script", key=f"g_{tc.id}", use_container_width=True):
                try:
                    with st.spinner("Snapshot → LLM → grounding..."):
                        saved = generate(tc)
                except BrowserTaskError as exc:
                    show_browser_task_error(exc, tc.id)
                    st.stop()
                except Exception as exc:
                    log("generation_failed", tc=tc.id, error_type=type(exc).__name__)
                    st.error(llm_failure_message(exc))
                    st.stop()
                if not saved:
                    st.error("Script was not saved: grounding still has unmatched locators. Edit and approve the test case before trying again.")
                    st.stop()
                st.rerun()
            if row and c3.button("Approve script", key=f"aps_{tc.id}", use_container_width=True):
                decide("AG-08", "script", tc.id, True, row.version)
                st.rerun()
            if row and c4.button("Chạy", key=f"x_{tc.id}", use_container_width=True, disabled=not script_approved):
                with st.spinner("Đang chạy..."):
                    execute(tc.id)
                st.rerun()
            can_capture = bool(row and script_approved and tc.type == TestType.POSITIVE and
                               AUTH_FILE is not None and "AGENTIC_AUTH_STATE_OUT" in row.code)
            if row and c5.button("Chạy & lưu phiên", key=f"auth_{tc.id}", use_container_width=True,
                                 disabled=not can_capture,
                                 help="Chạy từ browser sạch; chỉ lưu cookie/localStorage nếu script đạt."):
                with st.spinner("Đang đăng nhập và lưu phiên..."):
                    result = execute(tc.id, capture_auth=True)
                if result.auth_state_saved:
                    st.session_state.auth_notice = "Đã lưu phiên. Bật 'Dùng phiên đã lưu' cho các case trang được bảo vệ."
                elif result.status == ExecStatus.PASSED:
                    st.error("Test đạt nhưng không có cookie/localStorage để lưu. Website có thể dùng sessionStorage hoặc script cũ chưa hỗ trợ lưu phiên.")
                    st.stop()
                st.rerun()
            if row and tc.type == TestType.POSITIVE and "AGENTIC_AUTH_STATE_OUT" not in row.code:
                st.caption("Script cũ chưa hỗ trợ lưu phiên; hãy sinh lại script rồi duyệt phiên bản mới.")
            if row:
                with st.expander("Plan, grounding và mã"):
                    if is_manual_script(row.code):
                        st.warning("Script đã sửa tay: plan/grounding cũ chỉ để tham khảo; self-healing tự động bị tắt.")
                    grounding = json.loads(row.grounding_json)
                    if grounding:
                        st.dataframe([{k: g[k] for k in ("action_index", "strategy", "value", "matched_count", "ok")}
                                      for g in grounding], hide_index=True)
                    edited = st.text_area("Plan (JSON, sửa được)", json.dumps(json.loads(row.plan_json), indent=2,
                                                                              ensure_ascii=False), height=220, key=f"p_{tc.id}")
                    if st.button("Lưu plan", key=f"sp_{tc.id}"):
                        try:
                            new_plan = PlaywrightPlan.model_validate_json(edited)
                        except Exception as e:
                            st.error(f"Plan không hợp lệ: {e}")
                        else:
                            try:
                                grounded = save_grounded_plan(tc.id, new_plan)
                            except BrowserTaskError as exc:
                                show_browser_task_error(exc, tc.id)
                                st.stop()
                            if not grounded:
                                st.error("Không lưu plan: grounding có locator không khớp đúng một phần tử.")
                                st.stop()
                            log("edit_plan", tc=tc.id)
                            st.rerun()
                    st.code(visible_browser_code(row.code), language="python")
                    st.caption("Sửa Python thủ công chỉ dành cho người duyệt tin cậy. Bản sửa không được grounding lại "
                               "và phải duyệt script phiên bản mới trước khi chạy.")
                    edited_code = st.text_area("Sửa mã Playwright Python", row.code, height=420,
                                               key=f"code_{tc.id}_v{row.version}")
                    if st.button("Lưu script sửa tay", key=f"save_code_{tc.id}_v{row.version}"):
                        if edited_code.replace("\r\n", "\n").strip() == row.code.replace("\r\n", "\n").strip():
                            st.info("Mã chưa thay đổi.")
                        else:
                            try:
                                validated_code = validate_manual_script(edited_code)
                            except ValueError as exc:
                                st.error(str(exc))
                            else:
                                plan = PlaywrightPlan.model_validate_json(row.plan_json)
                                store.save_script(pid, plan, GeneratedScript(test_case_id=tc.id,
                                                                            code=validated_code))
                                log("edit_script_manual", tc=tc.id, previous_version=row.version)
                                st.rerun()
            if run:
                # ExecutionAgent creates an isolated artifact directory per run.
                # Read the persisted paths instead of guessing the legacy shared
                # screenshot location, so evidence remains visible after retries.
                artifact_paths = [Path(p) for p in json.loads(run.artifacts_json)]
                screenshots = [p for p in artifact_paths if p.suffix.lower() == ".png" and p.exists()]
                traces = [p for p in artifact_paths if p.suffix.lower() == ".zip" and p.exists()]
                if screenshots:
                    st.image(str(screenshots[-1]), width=420)
                if traces:
                    st.caption(f"Trace: {traces[-1]}")

    # ④ sửa lỗi có ràng buộc
    manual_failed = [tc for tc in approved_tcs if tc.id in runs and runs[tc.id].status != "passed"
                     and tc.id in scripts and is_manual_script(scripts[tc.id].code)]
    failed = [tc for tc in approved_tcs if tc.id in runs and runs[tc.id].status != "passed"
              and tc not in manual_failed]
    if manual_failed:
        st.info("Script sửa tay bị lỗi: hãy sửa trực tiếp mã hoặc sinh lại từ plan; không tự đề xuất self-healing.")
    decided = {d.artifact_id for g in ("AG-03", "AG-04", "AG-05", "REPAIR-LOW") for d in store.decisions(pid, g)}
    pending = [(rid, p) for rid, p in store.repairs(pid) if f"repair-{rid}" not in decided
               and p.test_case_id not in {tc.id for tc in manual_failed}]
    st.subheader(f"④ Sửa lỗi có ràng buộc — {len(failed)} test lỗi · {len(pending)} đề xuất chờ duyệt")
    for tc in failed:
        if not any(p.test_case_id == tc.id for _, p in pending) and st.button(f"Đề xuất sửa cho {tc.id}", key=f"r_{tc.id}"):
            try:
                with st.spinner("Dò bước hỏng → self-healing → LLM có ràng buộc..."):
                    propose_repair(tc)
            except BrowserTaskError as exc:
                show_browser_task_error(exc, tc.id)
                st.stop()
            st.rerun()
    for rid, p in pending:
        old = PlaywrightPlan.model_validate_json(scripts[p.test_case_id].plan_json)
        gate = repair_gate(old, p.new_plan or old, p.changed_kinds)
        with st.container(border=True):
            st.markdown(f"**Đề xuất #{rid}** cho `{p.test_case_id}` · rủi ro **{p.risk_level.value}** · cổng **{gate}** · "
                        f"thay đổi: `{', '.join(p.changed_kinds) or '—'}` · trạng thái policy: `{p.outcome.value}`")
            if p.semantic_impact:
                st.error("Đề xuất làm đổi ý nghĩa test (assertion/bước). Chỉ duyệt nếu yêu cầu thật sự đã đổi.")
            st.text(p.reason)
            st.code(p.diff or "(không có diff)", language="diff")
            b1, b2 = st.columns(2)
            if b1.button("Duyệt và chạy lại", key=f"rap_{rid}", disabled=p.new_plan is None or p.outcome.value != "proposed"):
                try:
                    grounded = save_grounded_plan(p.test_case_id, p.new_plan)
                except BrowserTaskError as exc:
                    show_browser_task_error(exc, p.test_case_id)
                    st.stop()
                if not grounded:
                    st.error("Không áp dụng repair: grounding có locator không khớp đúng một phần tử.")
                    st.stop()
                decide(gate, "repair", f"repair-{rid}", True)
                execute(p.test_case_id)
                st.rerun()
            if b2.button("Từ chối", key=f"rre_{rid}"):
                decide(gate, "repair", f"repair-{rid}", False)
                st.rerun()

with tab_hist:
    reqs, tcs_all = store.latest_requirements(pid), store.latest_test_cases(pid)
    runs_all = store.executions(pid)
    m = st.columns(5)
    m[0].metric("Yêu cầu", len(reqs))
    m[1].metric("Test case", len(tcs_all))
    m[2].metric("Lần chạy", len(runs_all))
    m[3].metric("Pass (lần chạy mới nhất)", sum(r.status == "passed" for r in store.latest_executions(pid).values()))
    m[4].metric("Đề xuất sửa", len(store.repairs(pid)))
    st.markdown("**Chuỗi truy vết**")
    st.dataframe([dict(zip(("nguồn", "id nguồn", "quan hệ", "đích", "id đích"), link)) for link in store.trace_links(pid)],
                 hide_index=True)
    st.markdown("**Quyết định (append-only)**")
    st.dataframe([{"thời điểm": d.decided_at, "artifact": d.artifact_id, "version": d.artifact_version,
                   "quyết định": d.status.value, "người duyệt": d.decided_by} for d in store.decisions(pid)], hide_index=True)
    st.markdown(f"**Thao tác của phiên `{SID}`**")
    st.dataframe([{"thời điểm": e.created_at, "sự kiện": e.event, "chi tiết": e.payload_json}
                  for e in store.events(pid, SID)], hide_index=True)
