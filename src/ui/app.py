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
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]  # src/ui/app.py -> gốc dự án
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))  # để 'streamlit run' (chỉ thêm src/ui vào path) import được gốc

import streamlit as st

from run_requirement_agent import default_mock_extraction
from src.agents.execution_agent import ExecutionAgent
from src.agents.playwright_generation_agent import PlaywrightGenerationAgent, grounding_feedback
from src.agents.repair_agent import RepairAgent
from src.agents.requirement_agent import RequirementAnalysisAgent
from src.agents.test_design_agent import TestDesignAgent
from src.database import session_factory
from src.models.playwright_artifacts import (
    ActionType, ExecStatus, ExecutionResult, GeneratedScript, GroundingRecord, LocatorStrategy, PlaywrightAction,
    PlaywrightPlan,
)
from src.models.repair import RepairDraft
from src.models.test_case import TestCase, TestCaseDraft, TestType
from src.repositories.store import Store
from src.services.browser_tasks import run_task
from src.services.script_template import render_script
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
    return resolve_client(None if BACKEND.startswith("local") else "cloud", False, mock_response)


def log(event: str, **payload) -> None:
    store.log_event(pid, SID, event, actor=ACTOR, **payload)


def badge(decisions, artifact_id: str) -> str:
    for d in reversed(decisions):
        if d.artifact_id == artifact_id:
            return {"approved": "✅ đã duyệt", "rejected": "⛔ từ chối"}.get(d.status.value, "⏳ chờ")
    return "⏳ chờ duyệt"


def decide(gate: str, kind: str, artifact_id: str, approved: bool, version: int = 1) -> None:
    store.record_decision(pid, gate, kind, artifact_id, approved, decided_by=ACTOR, artifact_version=version)
    log("decision", gate=gate, artifact=artifact_id, approved=approved)


def generate(tc: TestCase) -> None:
    """DOM-aware: aria snapshot trang đích → LLM → grounding trên trang thật → nếu locator khớp != 1 thì sinh lại 1 lần."""
    snap = run_task("snapshot", {"url": BASE_URL}).get("snapshot", "")
    client, model = _client(_plan_mock(BASE_URL))
    agent = PlaywrightGenerationAgent(client, model_name=model)
    plan = agent.plan(tc, BASE_URL, page_context=snap or None)
    records = _ground(plan)
    if (fb := grounding_feedback(plan, records)) is not None:
        plan = agent.plan(tc, BASE_URL, page_context=snap or None, feedback=fb)
        records = _ground(plan)
    save_plan(tc.id, plan, records)
    log("generate_script", tc=tc.id, refined=fb is not None)


def _ground(plan: PlaywrightPlan) -> list[GroundingRecord]:
    out = run_task("ground", {"plan": plan.model_dump(mode="json")})
    return [GroundingRecord(**r) for r in out.get("records", [])]


def save_plan(tc_id: str, plan: PlaywrightPlan, records=None) -> int:
    script = GeneratedScript(test_case_id=tc_id, code=render_script(plan, screenshot=f"{tc_id}.png"),
                             grounding=records or [])
    return store.save_script(pid, plan, script)


def execute(tc_id: str) -> None:
    row = store.latest_scripts(pid)[tc_id]
    result = ExecutionAgent().run(GeneratedScript(test_case_id=tc_id, code=row.code), WORKDIR)
    store.save_execution(pid, result, row.id)
    log("execute", tc=tc_id, status=result.status.value)


def propose_repair(tc: TestCase) -> None:
    """Hệ thống có ràng buộc: self-healing tất định trước, LLM có ràng buộc sau; policy phân mức, KHÔNG tự áp dụng."""
    row = store.latest_scripts(pid)[tc.id]
    run = store.latest_executions(pid)[tc.id]
    plan = PlaywrightPlan.model_validate_json(row.plan_json)
    result = ExecutionResult(test_case_id=tc.id, status=ExecStatus(run.status), exit_code=run.exit_code,
                             stderr=run.stderr, artifacts=json.loads(run.artifacts_json))
    attempt = 1 + sum(1 for _, p in store.repairs(pid) if p.test_case_id == tc.id)
    probe = run_task("probe_heal", {"plan": plan.model_dump(mode="json")})
    if probe.get("healed"):
        healed = {int(k): PlaywrightAction(**v) for k, v in probe["healed"].items()}
        proposal = RepairAgent(model_name="self-healing").propose_with_healing(plan, healed, result, tc, attempt)
    else:
        client, model = _client(RepairDraft(new_plan=plan))
        proposal = RepairAgent(client, model).propose(plan, result, tc, attempt,
                                                      page_context=f"{probe.get('note', '')}\n{probe.get('snapshot', '')}")
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
    BACKEND = st.selectbox("LLM backend", ["mock (offline)", "local (.env)", "cloud (.env.cloud)"])
    st.caption(f"Phiên: `{SID}`")
    st.divider()
    st.header("📄 Tài liệu yêu cầu")
    mode = st.radio("Nguồn", ["Tài liệu mẫu", "Dán văn bản", "Tải lên (.txt/.md)"])
    doc_text = ""
    if mode == "Tài liệu mẫu":
        doc_text = SAMPLE.read_text(encoding="utf-8") if SAMPLE.exists() else ""
    elif mode == "Dán văn bản":
        doc_text = st.text_area("Nội dung", height=200, placeholder="Dán tài liệu yêu cầu...")
    else:
        up = st.file_uploader("Tệp .txt/.md", type=["txt", "md"])
        if up:
            doc_text = up.read().decode("utf-8", errors="ignore")
    run_req = st.button("① Phân tích yêu cầu", type="primary", use_container_width=True)

pid = store.get_or_create_project(PROJECT, BASE_URL)
if not st.session_state.get("started"):
    st.session_state.started = True
    log("session_start")

st.title("🧪 Agentic Playwright")
st.caption("Agent chỉ ĐỀ XUẤT; con người quyết định ở các cổng AG-01..05. Mọi quyết định và thao tác được lưu DB.")

if run_req:
    if doc_text.strip():
        with st.spinner("Đang phân tích yêu cầu..."):
            client, model = _client(default_mock_extraction())
            result = RequirementAnalysisAgent(client, model_name=model).analyze(doc_text, source_name="ui")
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
    approved_reqs = approved_requirement_ids(reqs, d1)
    st.subheader(f"② Test case — {len(approved_reqs)}/{len(reqs)} yêu cầu đã duyệt · cổng AG-02")
    if not approved_reqs:
        st.info("Duyệt ít nhất một yêu cầu ở trên.")
        st.stop()
    if st.button("Thiết kế test cho các yêu cầu đã duyệt"):
        with st.spinner("Đang thiết kế test..."):
            client, model = _client(_design_mock())
            agent = TestDesignAgent(client, model_name=model)
            for req in reqs:
                if req.id in approved_reqs:
                    store.save_test_cases(pid, agent.design(req).test_cases)
        log("design", reqs=approved_reqs)
        st.rerun()
    tcs = [tc for tc in store.latest_test_cases(pid) if tc.requirement_id in approved_reqs]
    d2 = store.decisions(pid, "AG-02")
    tv = store.versions(pid, "test_case")
    for tc in tcs:
        with st.container(border=True):
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.markdown(f"`{tc.id}` v{tv[tc.id]} · **{tc.type.value}** · {tc.title} — {badge(d2, tc.id)}")
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
                if st.button("Lưu thành version mới", key=f"sv_{tc.id}"):
                    if (new := edited_test_case(tc, title, steps, expected)) is not None:
                        store.save_test_cases(pid, [new])
                        log("edit_test_case", tc=tc.id)
                        st.rerun()

    # ③ sinh + chạy
    approved_tcs = [tc for tc in tcs if tc.id in approved_test_case_ids(tcs, d2)]
    st.subheader(f"③ Sinh script và chạy — {len(approved_tcs)} test case đã duyệt")
    scripts, runs = store.latest_scripts(pid), store.latest_executions(pid)
    for tc in approved_tcs:
        with st.container(border=True):
            row, run = scripts.get(tc.id), runs.get(tc.id)
            status = f"{'✅' if run.status == 'passed' else '❌'} {run.status}" if run else "chưa chạy"
            c1, c2, c3 = st.columns([5, 1, 1])
            c1.markdown(f"`{tc.id}` {tc.title} · script: {f'v{row.version}' if row else '—'} · {status}")
            if c2.button("Sinh script", key=f"g_{tc.id}", use_container_width=True):
                with st.spinner("Snapshot → LLM → grounding..."):
                    generate(tc)
                st.rerun()
            if row and c3.button("Chạy", key=f"x_{tc.id}", use_container_width=True):
                with st.spinner("Đang chạy..."):
                    execute(tc.id)
                st.rerun()
            if row:
                with st.expander("Plan, grounding và mã"):
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
                            save_plan(tc.id, new_plan)
                            log("edit_plan", tc=tc.id)
                            st.rerun()
                    st.code(row.code, language="python")
            shot = WORKDIR / f"{tc.id}.png"
            if run and shot.exists():
                st.image(str(shot), width=420)

    # ④ sửa lỗi có ràng buộc
    failed = [tc for tc in approved_tcs if tc.id in runs and runs[tc.id].status != "passed"]
    decided = {d.artifact_id for g in ("AG-03", "AG-04", "AG-05", "REPAIR-LOW") for d in store.decisions(pid, g)}
    pending = [(rid, p) for rid, p in store.repairs(pid) if f"repair-{rid}" not in decided]
    st.subheader(f"④ Sửa lỗi có ràng buộc — {len(failed)} test lỗi · {len(pending)} đề xuất chờ duyệt")
    for tc in failed:
        if not any(p.test_case_id == tc.id for _, p in pending) and st.button(f"Đề xuất sửa cho {tc.id}", key=f"r_{tc.id}"):
            with st.spinner("Dò bước hỏng → self-healing → LLM có ràng buộc..."):
                propose_repair(tc)
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
                decide(gate, "repair", f"repair-{rid}", True)
                save_plan(p.test_case_id, p.new_plan)
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
