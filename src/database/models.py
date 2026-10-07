"""Schema lưu trữ (architecture v0.1, mục 10–11). Chạy trên SQLite (dev/test) và SQL Server (demo) qua SQLAlchemy.

- Artifact có thể sửa sau review (yêu cầu, test case, script) có `version`; bản mới là một dòng mới, không ghi đè.
- Quyết định duyệt, kết quả chạy, đề xuất sửa và sự kiện UI là append-only.
- Nội dung có cấu trúc lưu JSON (Text) để dùng chung model Pydantic, không phụ thuộc kiểu JSON riêng của từng DB.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class _Row:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Project(_Row, Base):
    __tablename__ = "project"
    name: Mapped[str] = mapped_column(String(200))
    base_url: Mapped[str] = mapped_column(String(500), default="")


class _ProjectRow(_Row):
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)


class RequirementVersion(_ProjectRow, Base):
    __tablename__ = "requirement_version"
    __table_args__ = (UniqueConstraint("project_id", "req_id", "version"),)
    req_id: Mapped[str] = mapped_column(String(50))
    version: Mapped[int] = mapped_column(Integer)
    source_name: Mapped[str] = mapped_column(String(300), default="")
    data_json: Mapped[str] = mapped_column(Text)  # StructuredRequirement


class TestCaseVersion(_ProjectRow, Base):
    __tablename__ = "test_case_version"
    __table_args__ = (UniqueConstraint("project_id", "tc_id", "version"),)
    tc_id: Mapped[str] = mapped_column(String(80))
    requirement_id: Mapped[str] = mapped_column(String(50), default="")
    version: Mapped[int] = mapped_column(Integer)
    data_json: Mapped[str] = mapped_column(Text)  # TestCase


class ApprovalDecisionRow(_ProjectRow, Base):
    __tablename__ = "approval_decision"
    gate: Mapped[str] = mapped_column(String(10))            # AG-01 .. AG-07
    artifact_type: Mapped[str] = mapped_column(String(30))   # requirement / test_case / repair
    artifact_id: Mapped[str] = mapped_column(String(80))
    artifact_version: Mapped[int] = mapped_column(Integer, default=1)
    decision: Mapped[str] = mapped_column(String(20))        # approved / rejected
    decided_by: Mapped[str] = mapped_column(String(100), default="")
    reason: Mapped[str] = mapped_column(Text, default="")


class GeneratedScriptRow(_ProjectRow, Base):
    __tablename__ = "generated_script"
    tc_id: Mapped[str] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer)
    plan_json: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text)
    grounding_json: Mapped[str] = mapped_column(Text, default="[]")


class ExecutionRun(_ProjectRow, Base):
    __tablename__ = "execution_run"
    tc_id: Mapped[str] = mapped_column(String(80))
    script_id: Mapped[int | None] = mapped_column(ForeignKey("generated_script.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    exit_code: Mapped[int] = mapped_column(Integer, default=0)
    stderr: Mapped[str] = mapped_column(Text, default="")
    artifacts_json: Mapped[str] = mapped_column(Text, default="[]")


class RepairProposalRow(_ProjectRow, Base):
    __tablename__ = "repair_proposal"
    tc_id: Mapped[str] = mapped_column(String(80))
    execution_id: Mapped[int | None] = mapped_column(ForeignKey("execution_run.id"), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20))
    outcome: Mapped[str] = mapped_column(String(30))
    data_json: Mapped[str] = mapped_column(Text)  # RepairProposal (gồm diff, changed_kinds, new_plan)


class TraceLink(_ProjectRow, Base):
    __tablename__ = "trace_link"
    source_type: Mapped[str] = mapped_column(String(30))
    source_id: Mapped[str] = mapped_column(String(80))
    target_type: Mapped[str] = mapped_column(String(30))
    target_id: Mapped[str] = mapped_column(String(80))
    relation: Mapped[str] = mapped_column(String(30))
    created_by: Mapped[str] = mapped_column(String(100), default="system")


class UIEvent(_ProjectRow, Base):
    """Nhật ký thao tác trên giao diện — dữ liệu thời gian/số lần sửa tay cho RQ4."""
    __tablename__ = "ui_event"
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(100), default="")
    event: Mapped[str] = mapped_column(String(60))
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
