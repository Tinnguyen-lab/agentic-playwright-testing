"""RQ4 evidence tools for the human-in-the-loop workflow.

The comparison is manual work against AI-assisted work, with a human owning
the submitted oracle and script in *both* conditions.  This module only
records events and artifacts produced in real sessions; it never creates
participant results or infers missing timings.

    python tools/rq4/rq4.py export --project RQ4-HIL-20261010-A --out artifacts/rq4/session
    python tools/rq4/rq4.py check --reviewer reviewer-01 --phase after_review --task A --tests artifacts/rq4/session
    python tools/rq4/rq4.py analyze
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from run_rq3 import serve  # noqa: E402

OUT = ROOT / "artifacts/rq4"
TIMINGS = OUT / "study_timings.csv"
STUDY = OUT / "study"
PORT = 5100
MUTANT = {
    "A": {"uc1": "S4_redirect", "uc2": "S1_error_msg", "uc3": "S6_add_noop"},
    "B": {"uc1": "S2_total", "uc2": "S3_validation", "uc3": "S5_locked"},
}


def export(args) -> int:
    """Export the latest scripts from a reviewed project without altering them."""
    from src.database import session_factory
    from src.repositories.store import Store

    store = Store(session_factory(args.db))
    pid = store.get_or_create_project(args.project)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    scripts = store.latest_scripts(pid)
    cases = {tc.id: tc for tc in store.latest_test_cases(pid)}
    for tc_id, row in scripts.items():
        requirement_id = cases.get(tc_id).requirement_id if tc_id in cases else ""
        uc = f"uc{int(requirement_id.split('-')[1])}" if requirement_id else "uc0"
        (out / f"{uc}_{tc_id}.py").write_text(row.code, encoding="utf-8")
    print(f"exported {len(scripts)} script(s) to {out}")
    return 0


def _run(test: Path) -> bool:
    # ``check`` receives a relative artifact directory in normal use.  Resolve
    # before switching cwd to the artifact directory, otherwise Python looks
    # for ``artifacts/.../artifacts/.../test.py`` and every run is a false fail.
    test = test.resolve()
    command = ([sys.executable, "-m", "pytest", "-q", str(test)]
               if "def test_" in test.read_text(encoding="utf-8") else [sys.executable, str(test)])
    try:
        return subprocess.run(command, cwd=test.parent, capture_output=True, timeout=180).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def check(args) -> int:
    """Assess semantic validity of the supplied scripts for one task set."""
    tests = sorted(Path(args.tests).glob("uc*.py"))
    by_uc: dict[str, list[Path]] = defaultdict(list)
    for test in tests:
        by_uc[test.name[:3]].append(test)

    with serve("v0", PORT):
        on_v0 = {test: _run(test) for test in tests}
    on_mutant: dict[Path, bool] = {}
    for uc, variant in MUTANT[args.task].items():
        if by_uc[uc]:
            with serve(variant, PORT):
                on_mutant.update({test: _run(test) for test in by_uc[uc]})

    ucs = {
        uc: {
            "tests": [test.name for test in by_uc[uc]],
            "runnable": any(on_v0[test] for test in by_uc[uc]),
            "valid": any(on_v0[test] and not on_mutant[test] for test in by_uc[uc]),
        }
        for uc in MUTANT[args.task]
    }
    record = {
        "reviewer": args.reviewer,
        "condition": args.condition or "quality_gate",
        "phase": args.phase,
        "task": args.task,
        "ucs": ucs,
        "runnable_ucs": sum(value["runnable"] for value in ucs.values()),
        "valid_ucs": sum(value["valid"] for value in ucs.values()),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    # Historical quality-gate evidence predates the comparative study and
    # keeps its original filename. Study records include condition so a
    # participant cannot overwrite their manual result with assisted one.
    suffix = f"_{args.condition}" if args.condition else ""
    path = OUT / f"check_{args.reviewer}{suffix}_{args.phase}_{args.task}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def timer(args) -> int:
    """Append an auditable start/stop event for a real crossover study session."""
    OUT.mkdir(parents=True, exist_ok=True)
    new = not TIMINGS.exists()
    with TIMINGS.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if new:
            writer.writerow(["participant", "condition", "task", "event", "time"])
        writer.writerow([args.participant, args.condition, args.task, args.action,
                         datetime.now(timezone.utc).isoformat()])
    print(f"recorded {args.action}: {args.participant} / {args.condition} / task {args.task}")
    return 0


def prepare(args) -> int:
    """Create a blank, per-session handoff folder without fabricating data."""
    session = STUDY / args.participant / f"{args.condition}_{args.task}"
    if session.exists() and any(session.iterdir()):
        print(f"session folder already exists: {session}", file=sys.stderr)
        return 2
    session.mkdir(parents=True, exist_ok=True)
    task = ROOT / "datasets" / "reference" / "rq4" / f"task_{args.task}.md"
    (session / f"task_{args.task}.md").write_text(task.read_text(encoding="utf-8"), encoding="utf-8")
    if args.condition == "manual":
        instructions = """# Nộp bài phiên RQ4 (manual)

1. Đọc `task_{task}.md` và tự thiết kế test case, sau đó tự viết các script Playwright.
2. Lưu script theo tên `uc1_*.py`, `uc2_*.py`, `uc3_*.py` trong thư mục này.
3. Chỉ khi đã hoàn thành, ghi số test case đã tạo và các ghi chú ngắn bên dưới.

- Số test case đã tạo: _
- Ghi chú về chỉnh sửa/thử lại: _

Không mở hay sửa mã hệ thống sinh AI trong điều kiện manual.
""".format(task=args.task)
    else:
        instructions = """# Nộp bài phiên RQ4 (AI-assisted)

1. Dùng giao diện hệ thống để phân tích requirement, xem/sửa test case và script đề xuất.
2. Người tham gia phải tự xác nhận expected result, locator/grounding và script trước khi nộp.
3. Sau khi export, lưu các script `uc1_*.py`, `uc2_*.py`, `uc3_*.py` trong thư mục này.
4. Chỉ khi đã hoàn thành, ghi số test case và các chỉnh sửa/approval bên dưới.

- Số test case đã duyệt: _
- Chỉnh sửa hoặc rejection đáng chú ý: _

AI không được tự phê duyệt thay người tham gia.
"""
    (session / "SUBMISSION.md").write_text(instructions, encoding="utf-8")
    print(f"prepared blank real-session folder: {session}")
    return 0


def _timed_sessions() -> tuple[list[dict], list[dict]]:
    """Pair real timer events by participant/condition/task, without guessing."""
    if not TIMINGS.exists():
        return [], []
    starts: dict[tuple[str, str, str], list[datetime]] = defaultdict(list)
    completed: list[dict] = []
    issues: list[dict] = []
    with TIMINGS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row.get("participant", ""), row.get("condition", ""), row.get("task", ""))
            try:
                point = datetime.fromisoformat(row.get("time", ""))
            except ValueError:
                issues.append({"kind": "invalid_time", "row": row})
                continue
            if row.get("event") == "start":
                starts[key].append(point)
            elif row.get("event") == "stop":
                if not starts[key]:
                    issues.append({"kind": "stop_without_start", "participant": key[0],
                                   "condition": key[1], "task": key[2], "time": row.get("time")})
                    continue
                started = starts[key].pop(0)
                if point < started:
                    issues.append({"kind": "stop_before_start", "participant": key[0],
                                   "condition": key[1], "task": key[2]})
                    continue
                completed.append({"participant": key[0], "condition": key[1], "task": key[2],
                                  "started_at": started.isoformat(), "stopped_at": point.isoformat(),
                                  "duration_seconds": round((point - started).total_seconds(), 3)})
            else:
                issues.append({"kind": "invalid_event", "row": row})
    for (participant, condition, task), pending in starts.items():
        for point in pending:
            issues.append({"kind": "start_without_stop", "participant": participant,
                           "condition": condition, "task": task, "time": point.isoformat()})
    return completed, issues


def analyze(_args) -> int:
    """Combine immutable check records into a report-ready RQ4 evidence file."""
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(OUT.glob("check_*.json"))]
    summary: dict[str, dict[str, int]] = {}
    for phase in ("before_review", "after_review"):
        phase_rows = [row for row in rows if row.get("phase") == phase]
        summary[phase] = {
            "n_checks": len(phase_rows),
            "runnable_ucs": sum(row.get("runnable_ucs", 0) for row in phase_rows),
            "valid_ucs": sum(row.get("valid_ucs", 0) for row in phase_rows),
        }
    sessions, timing_issues = _timed_sessions()
    by_condition = {}
    for condition in ("manual", "ai_assisted"):
        condition_rows = [row for row in rows if row.get("condition") == condition]
        condition_sessions = [row for row in sessions if row["condition"] == condition]
        durations = [row["duration_seconds"] for row in condition_sessions]
        by_condition[condition] = {
            "n_checks": len(condition_rows),
            "runnable_ucs": sum(row.get("runnable_ucs", 0) for row in condition_rows),
            "valid_ucs": sum(row.get("valid_ucs", 0) for row in condition_rows),
            "n_completed_timed_sessions": len(condition_sessions),
            "total_duration_seconds": round(sum(durations), 3),
            "mean_duration_seconds": round(sum(durations) / len(durations), 3) if durations else None,
        }
    payload = {
        "metric": "A valid use case has a script that passes v0 and fails its semantic mutation.",
        "rows": rows,
        "summary": summary,
        "study_summary": by_condition,
        "timed_sessions": sessions,
        "timing_issues": timing_issues,
        "limitations": "Comparative timing/quality results require real logged manual and AI-assisted sessions; no values are inferred.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rq4_results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="RQ4 human-in-the-loop evidence tools")
    sub = parser.add_subparsers(dest="cmd", required=True)
    exporter = sub.add_parser("export", help="export latest reviewed scripts from SQLite")
    exporter.add_argument("--project", required=True)
    exporter.add_argument("--out", required=True)
    exporter.add_argument("--db")
    checker = sub.add_parser("check", help="check scripts against v0 and semantic mutations")
    checker.add_argument("--reviewer", required=True, help="identifier recorded by the real review session")
    checker.add_argument("--condition", choices=["manual", "ai_assisted"],
                         help="optional crossover-study condition; omit for historical quality-gate evidence")
    checker.add_argument("--phase", required=True, choices=["before_review", "after_review"])
    checker.add_argument("--task", required=True, choices=["A", "B"])
    checker.add_argument("--tests", required=True)
    timing = sub.add_parser("timer", help="record real study-session start/stop time")
    timing.add_argument("action", choices=["start", "stop"])
    timing.add_argument("--participant", required=True)
    timing.add_argument("--condition", required=True, choices=["manual", "ai_assisted"])
    timing.add_argument("--task", required=True, choices=["A", "B"])
    prepare_parser = sub.add_parser("prepare", help="create a blank handoff folder for one real session")
    prepare_parser.add_argument("--participant", required=True,
                                help="pseudonymous participant identifier, e.g. P01")
    prepare_parser.add_argument("--condition", required=True, choices=["manual", "ai_assisted"])
    prepare_parser.add_argument("--task", required=True, choices=["A", "B"])
    sub.add_parser("analyze", help="summarize check records")
    args = parser.parse_args(argv)
    return {"export": export, "check": check, "timer": timer, "prepare": prepare, "analyze": analyze}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
