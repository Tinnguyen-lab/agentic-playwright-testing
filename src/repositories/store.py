"""Repository — đường truy cập dữ liệu duy nhất cho UI và service (architecture v0.1, mục 5.11).

Nhận và trả model Pydantic của domain; bảng SQLAlchemy chỉ nằm sau lớp này.
Version: lưu cùng nội dung thì không tạo bản mới; nội dung đổi thì version + 1. Quyết định duyệt chỉ được thêm.
"""
from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import (
    ApprovalDecisionRow, ExecutionRun, GeneratedScriptRow, Project, RepairProposalRow, RequirementVersion,
    TestCaseVersion, TraceLink, UIEvent,
)
from src.models.approval import ApprovalDecision, ApprovalStatus
from src.models.playwright_artifacts import ExecutionResult, GeneratedScript, PlaywrightPlan
from src.models.repair import RepairProposal
from src.models.requirement import StructuredRequirement
from src.models.test_case import TestCase


class Store:
    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    # ---------- project ----------
    def get_or_create_project(self, name: str, base_url: str = "") -> int:
        with self._sessions.begin() as s:
            row = s.scalar(select(Project).where(Project.name == name))
            if row is None:
                row = Project(name=name, base_url=base_url)
                s.add(row)
                s.flush()
            return row.id

    # ---------- artifact có version ----------
    def _save_versioned(self, s: Session, model, key_col: str, key: str, project_id: int, data_json: str, **extra) -> int:
        latest = s.scalar(select(model).where(model.project_id == project_id, getattr(model, key_col) == key)
                          .order_by(model.version.desc()).limit(1))
        if latest is not None and latest.data_json == data_json:
            return latest.version
        version = 1 if latest is None else latest.version + 1
        s.add(model(project_id=project_id, version=version, data_json=data_json, **{key_col: key}, **extra))
        return version

    def save_requirements(self, project_id: int, requirements: list[StructuredRequirement], source_name: str = "") -> dict[str, int]:
        with self._sessions.begin() as s:
            return {r.id: self._save_versioned(s, RequirementVersion, "req_id", r.id, project_id,
                                               r.model_dump_json(), source_name=source_name) for r in requirements}

    def save_test_cases(self, project_id: int, test_cases: list[TestCase]) -> dict[str, int]:
        with self._sessions.begin() as s:
            versions = {}
            for tc in test_cases:
                versions[tc.id] = self._save_versioned(s, TestCaseVersion, "tc_id", tc.id, project_id,
                                                       tc.model_dump_json(), requirement_id=tc.requirement_id)
                self._link(s, project_id, "requirement", tc.requirement_id, "test_case", tc.id, "verified_by")
            return versions

    def latest_requirements(self, project_id: int) -> list[StructuredRequirement]:
        return [StructuredRequirement.model_validate_json(r.data_json)
                for r in self._latest(RequirementVersion, "req_id", project_id)]

    def latest_test_cases(self, project_id: int) -> list[TestCase]:
        return [TestCase.model_validate_json(r.data_json) for r in self._latest(TestCaseVersion, "tc_id", project_id)]

    def versions(self, project_id: int, kind: str) -> dict[str, int]:
        """Version mới nhất theo ID; kind = 'requirement' | 'test_case'."""
        model, key = (RequirementVersion, "req_id") if kind == "requirement" else (TestCaseVersion, "tc_id")
        return {getattr(r, key): r.version for r in self._latest(model, key, project_id)}

    def latest_scripts(self, project_id: int) -> dict[str, GeneratedScriptRow]:
        with self._sessions() as s:
            rows = s.scalars(select(GeneratedScriptRow).where(GeneratedScriptRow.project_id == project_id)
                             .order_by(GeneratedScriptRow.id))
            return {r.tc_id: r for r in rows}  # bản sau ghi đè bản trước

    def latest_executions(self, project_id: int) -> dict[str, ExecutionRun]:
        return {r.tc_id: r for r in self.executions(project_id)}

    def _latest(self, model, key_col: str, project_id: int):
        key = getattr(model, key_col)
        newest = (select(key, func.max(model.version).label("v")).where(model.project_id == project_id)
                  .group_by(key).subquery())
        with self._sessions() as s:
            return list(s.scalars(select(model).join(newest, (key == newest.c[key_col]) & (model.version == newest.c.v))
                                  .where(model.project_id == project_id).order_by(model.id)))

    # ---------- duyệt (append-only) ----------
    def record_decision(self, project_id: int, gate: str, artifact_type: str, artifact_id: str, approved: bool,
                        decided_by: str = "", reason: str = "", artifact_version: int = 1) -> None:
        with self._sessions.begin() as s:
            s.add(ApprovalDecisionRow(project_id=project_id, gate=gate, artifact_type=artifact_type,
                                      artifact_id=artifact_id, artifact_version=artifact_version,
                                      decision="approved" if approved else "rejected",
                                      decided_by=decided_by, reason=reason))

    def decisions(self, project_id: int, gate: str | None = None) -> list[ApprovalDecision]:
        q = select(ApprovalDecisionRow).where(ApprovalDecisionRow.project_id == project_id)
        if gate:
            q = q.where(ApprovalDecisionRow.gate == gate)
        with self._sessions() as s:
            return [ApprovalDecision(artifact_id=r.artifact_id, artifact_version=r.artifact_version,
                                     status=ApprovalStatus(r.decision), reason=r.reason, decided_by=r.decided_by,
                                     decided_at=r.created_at) for r in s.scalars(q.order_by(ApprovalDecisionRow.id))]

    # ---------- script, chạy, sửa ----------
    def save_script(self, project_id: int, plan: PlaywrightPlan, script: GeneratedScript) -> int:
        with self._sessions.begin() as s:
            prev = s.scalar(select(func.max(GeneratedScriptRow.version)).where(
                GeneratedScriptRow.project_id == project_id, GeneratedScriptRow.tc_id == script.test_case_id)) or 0
            row = GeneratedScriptRow(project_id=project_id, tc_id=script.test_case_id, version=prev + 1,
                                     plan_json=plan.model_dump_json(), code=script.code,
                                     grounding_json=json.dumps([g.model_dump() for g in script.grounding]))
            s.add(row)
            s.flush()
            self._link(s, project_id, "test_case", script.test_case_id, "script", f"{script.test_case_id}@v{prev + 1}",
                       "implemented_by")
            return row.id

    def save_execution(self, project_id: int, result: ExecutionResult, script_id: int | None = None) -> int:
        with self._sessions.begin() as s:
            row = ExecutionRun(project_id=project_id, tc_id=result.test_case_id, script_id=script_id,
                               status=result.status.value, exit_code=result.exit_code, stderr=result.stderr,
                               artifacts_json=json.dumps(result.artifacts))
            s.add(row)
            s.flush()
            self._link(s, project_id, "test_case", result.test_case_id, "execution", str(row.id), "executed_as")
            return row.id

    def save_repair(self, project_id: int, proposal: RepairProposal, execution_id: int | None = None) -> int:
        with self._sessions.begin() as s:
            row = RepairProposalRow(project_id=project_id, tc_id=proposal.test_case_id, execution_id=execution_id,
                                    risk_level=proposal.risk_level.value, outcome=proposal.outcome.value,
                                    data_json=proposal.model_dump_json())
            s.add(row)
            s.flush()
            if execution_id is not None:
                self._link(s, project_id, "execution", str(execution_id), "repair", str(row.id), "repaired_by")
            return row.id

    def repairs(self, project_id: int) -> list[tuple[int, RepairProposal]]:
        with self._sessions() as s:
            rows = s.scalars(select(RepairProposalRow).where(RepairProposalRow.project_id == project_id)
                             .order_by(RepairProposalRow.id))
            return [(r.id, RepairProposal.model_validate_json(r.data_json)) for r in rows]

    def executions(self, project_id: int) -> list[ExecutionRun]:
        with self._sessions() as s:
            return list(s.scalars(select(ExecutionRun).where(ExecutionRun.project_id == project_id)
                                  .order_by(ExecutionRun.id)))

    # ---------- truy vết, sự kiện ----------
    @staticmethod
    def _link(s: Session, project_id: int, st: str, sid: str, tt: str, tid: str, rel: str) -> None:
        if not sid:
            return
        exists = s.scalar(select(TraceLink.id).where(
            TraceLink.project_id == project_id, TraceLink.source_type == st, TraceLink.source_id == sid,
            TraceLink.target_type == tt, TraceLink.target_id == tid))
        if exists is None:
            s.add(TraceLink(project_id=project_id, source_type=st, source_id=sid, target_type=tt, target_id=tid,
                            relation=rel))

    def trace_links(self, project_id: int) -> list[tuple[str, str, str, str, str]]:
        with self._sessions() as s:
            rows = s.scalars(select(TraceLink).where(TraceLink.project_id == project_id).order_by(TraceLink.id))
            return [(r.source_type, r.source_id, r.relation, r.target_type, r.target_id) for r in rows]

    def log_event(self, project_id: int, session_id: str, event: str, actor: str = "", **payload) -> None:
        with self._sessions.begin() as s:
            s.add(UIEvent(project_id=project_id, session_id=session_id, actor=actor, event=event,
                          payload_json=json.dumps(payload, ensure_ascii=False, default=str)))

    def events(self, project_id: int, session_id: str | None = None) -> list[UIEvent]:
        q = select(UIEvent).where(UIEvent.project_id == project_id)
        if session_id:
            q = q.where(UIEvent.session_id == session_id)
        with self._sessions() as s:
            return list(s.scalars(q.order_by(UIEvent.id)))
