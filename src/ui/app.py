"""Streamlit UI — bảng duyệt human-in-the-loop: AG-01 duyệt yêu cầu, AG-02 duyệt test case.

    streamlit run src/ui/app.py

Lớp mỏng trên các agent đã test (RequirementAnalysisAgent, TestDesignAgent). Quyết định lưu trong
session_state (persistence SQL Server: giai đoạn sau). Playwright gen/exec/repair trong trình duyệt:
mở rộng sau — hiện chạy bằng CLI (run_full_pipeline.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]  # src/ui/app.py -> gốc dự án
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))  # để 'streamlit run' (chỉ thêm src/ui vào path) import được gốc

import streamlit as st

from run_requirement_agent import default_mock_extraction
from src.agents.requirement_agent import RequirementAnalysisAgent
from src.agents.test_design_agent import TestDesignAgent
from src.models.approval import ApprovalDecision, ApprovalStatus
from src.models.test_case import TestCase, TestCaseDraft, TestType
from src.ui.review import approved_requirement_ids
from src.utils.cli import resolve_client

SAMPLE = _ROOT / "datasets/reference/sample_requirements.md"


def _design_mock() -> TestCaseDraft:
    return TestCaseDraft(test_cases=[
        TestCase(title="Luồng hợp lệ", type=TestType.POSITIVE),
        TestCase(title="Dữ liệu không hợp lệ", type=TestType.NEGATIVE),
    ])


def _decisions() -> list[ApprovalDecision]:
    return st.session_state.setdefault("decisions", [])


def _record(artifact_id: str, status: ApprovalStatus) -> None:
    _decisions().append(ApprovalDecision(artifact_id=artifact_id, status=status, decided_by="reviewer"))


def _badge(artifact_id: str) -> str:
    for d in reversed(_decisions()):
        if d.artifact_id == artifact_id:
            return {"approved": "✅ đã duyệt", "rejected": "⛔ từ chối"}.get(d.status.value, "⏳ chờ")
    return "⏳ chờ duyệt"


def _client(mock_response):
    if _BACKEND.startswith("mock"):
        return resolve_client(None, True, mock_response)
    if _BACKEND.startswith("local"):
        return resolve_client(None, False, mock_response)
    return resolve_client("cloud", False, mock_response)


st.set_page_config(page_title="Agentic Playwright — Review", page_icon="🧪", layout="wide")
st.title("🧪 Agentic Playwright — Bảng duyệt (human-in-the-loop)")
st.caption("AG-01 duyệt yêu cầu · AG-02 duyệt test case. Agent chỉ ĐỀ XUẤT; con người quyết định. "
           "Quyết định lưu tạm trong phiên (persistence SQL: giai đoạn sau).")

with st.sidebar:
    st.header("⚙️ Cấu hình")
    _BACKEND = st.selectbox("LLM backend", ["mock (offline)", "local (.env)", "cloud (.env.cloud)"])
    st.divider()
    st.header("📄 Tài liệu yêu cầu")
    mode = st.radio("Nguồn", ["Tài liệu mẫu", "Dán văn bản", "Tải lên (.txt/.md)"])
    doc_text = ""
    if mode == "Tài liệu mẫu":
        doc_text = SAMPLE.read_text(encoding="utf-8") if SAMPLE.exists() else ""
        st.caption(str(SAMPLE))
    elif mode == "Dán văn bản":
        doc_text = st.text_area("Nội dung", height=200, placeholder="Dán tài liệu yêu cầu...")
    else:
        up = st.file_uploader("Tệp .txt/.md", type=["txt", "md"])
        if up:
            doc_text = up.read().decode("utf-8", errors="ignore")
    run_req = st.button("① Phân tích yêu cầu (AG-01)", type="primary", use_container_width=True)

if run_req:
    if doc_text.strip():
        with st.spinner("Đang phân tích yêu cầu..."):
            client, model = _client(default_mock_extraction())
            st.session_state.req_result = RequirementAnalysisAgent(client, model_name=model).analyze(doc_text, source_name="ui")
        st.session_state.decisions = []
        st.session_state.pop("designs", None)
    else:
        st.warning("Chưa có nội dung tài liệu.")

result = st.session_state.get("req_result")
if not result:
    st.info("Chọn nguồn tài liệu ở thanh bên rồi bấm **① Phân tích yêu cầu** để bắt đầu.")
    st.stop()

# ---- AG-01: duyệt yêu cầu ----
st.subheader(f"① Yêu cầu trích xuất ({len(result.requirements)}) — cổng duyệt AG-01")
for req in result.requirements:
    with st.container(border=True):
        left, right = st.columns([5, 2])
        with left:
            st.markdown(f"**[{req.id}] {req.title}** — {_badge(req.id)}")
            st.caption(f"actor: {req.actor or '—'} · action: {req.action} · outcome: {req.expected_outcome or '—'}")
            for a in req.ambiguities:
                st.markdown(f"&nbsp;&nbsp;⚠ `{a.type.value}` — {a.description}")
        with right:
            b1, b2 = st.columns(2)
            if b1.button("Duyệt", key=f"ap_{req.id}", use_container_width=True):
                _record(req.id, ApprovalStatus.APPROVED)
                st.rerun()
            if b2.button("Từ chối", key=f"re_{req.id}", use_container_width=True):
                _record(req.id, ApprovalStatus.REJECTED)
                st.rerun()
if result.global_ambiguities:
    st.warning("🔺 Mâu thuẫn toàn cục: " + " · ".join(a.description for a in result.global_ambiguities))

# ---- AG-02: thiết kế test cho yêu cầu đã duyệt ----
approved_ids = approved_requirement_ids(result.requirements, _decisions())
st.subheader(f"② Thiết kế test — {len(approved_ids)}/{len(result.requirements)} yêu cầu đã duyệt")
if not approved_ids:
    st.info("Duyệt ít nhất một yêu cầu ở trên để thiết kế test (AG-02).")
    st.stop()
if st.button("② Thiết kế test cho các yêu cầu ĐÃ DUYỆT (AG-02)", type="primary"):
    with st.spinner("Đang thiết kế test..."):
        client, model = _client(_design_mock())
        agent = TestDesignAgent(client, model_name=model)
        st.session_state.designs = {req.id: agent.design(req) for req in result.requirements if req.id in approved_ids}

designs = st.session_state.get("designs", {})
for req_id, dr in designs.items():
    with st.container(border=True):
        st.markdown(f"**{req_id}** — {len(dr.test_cases)} test case · loại: `{', '.join(dr.type_coverage) or '—'}`")
        for tc in dr.test_cases:
            c1, c2 = st.columns([6, 1])
            c1.markdown(f"&nbsp;&nbsp;`{tc.id}` · **{tc.type.value}** · {tc.title} — {_badge(tc.id)}")
            if c2.button("Duyệt", key=f"aptc_{tc.id}", use_container_width=True):
                _record(tc.id, ApprovalStatus.APPROVED)
                st.rerun()

# ---- Truy vết & độ phủ ----
if designs:
    st.subheader("③ Truy vết & độ phủ")
    n_tc = sum(len(d.test_cases) for d in designs.values())
    types = sorted({t for d in designs.values() for t in d.type_coverage})
    m1, m2, m3 = st.columns(3)
    m1.metric("Yêu cầu đã duyệt", len(approved_ids))
    m2.metric("Test case sinh ra", n_tc)
    m3.metric("Loại test phủ", len(types))
    st.caption("Loại phủ: " + (", ".join(types) or "—") + " · Chuỗi truy vết Req → TC (AG-01 → AG-02).")
