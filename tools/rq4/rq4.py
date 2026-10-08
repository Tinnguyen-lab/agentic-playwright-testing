"""Công cụ thí nghiệm RQ4 (xem docs/development/rq4-protocol.md).

    python tools/rq4/rq4.py timer start --participant P1 --condition manual --task A
    python tools/rq4/rq4.py timer stop  --participant P1 --condition manual --task A
    python tools/rq4/rq4.py export --project rq4-P1-B --out artifacts/rq4/P1_system      # script hệ thống sinh, lấy từ DB
    python tools/rq4/rq4.py check  --participant P1 --condition manual --task A --tests artifacts/rq4/P1_manual
    python tools/rq4/rq4.py analyze                                                       # bảng tổng hợp

Chấm test (cả hai điều kiện như nhau): test của UC-k phải PASS trên ShopLab v0 và FAIL trên mutation ngữ nghĩa phá đúng
hành vi của UC-k. Đạt cả hai = test hợp lệ. File test đặt tên bắt đầu bằng uc1/uc2/uc3 (vd uc2_login_sai.py); file có
"def test_" chạy bằng pytest, còn lại chạy bằng python (thoát mã 0 = pass).
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from run_rq3 import serve  # noqa: E402

OUT = ROOT / "artifacts/rq4"
TIMINGS = OUT / "timings.csv"
SUS = OUT / "sus.csv"  # participant,condition,q1..q10 (1-5) — người điều phối nhập
PORT = 5100  # tài liệu nhiệm vụ ghi cứng cổng này
MUTANT = {"A": {"uc1": "S4_redirect", "uc2": "S1_error_msg", "uc3": "S6_add_noop"},
          "B": {"uc1": "S2_total", "uc2": "S3_validation", "uc3": "S5_locked"}}


def timer(args) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new = not TIMINGS.exists()
    with open(TIMINGS, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["participant", "condition", "task", "event", "time"])
        w.writerow([args.participant, args.condition, args.task, args.action, datetime.now(timezone.utc).isoformat()])
    print(f"[✓] {args.participant} {args.condition} {args.task} {args.action}")
    return 0


def export(args) -> int:
    from src.database import session_factory
    from src.repositories.store import Store

    store = Store(session_factory(args.db))
    pid = store.get_or_create_project(args.project)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    scripts = store.latest_scripts(pid)
    tcs = {tc.id: tc for tc in store.latest_test_cases(pid)}
    for tc_id, row in scripts.items():
        uc = f"uc{int(tcs[tc_id].requirement_id.split('-')[1])}" if tc_id in tcs and tcs[tc_id].requirement_id else "uc0"
        (out / f"{uc}_{tc_id}.py").write_text(row.code, encoding="utf-8")
    print(f"[✓] {len(scripts)} script -> {out}")
    return 0


def _run(test: Path) -> bool:
    cmd = ([sys.executable, "-m", "pytest", "-q", str(test)] if "def test_" in test.read_text(encoding="utf-8")
           else [sys.executable, str(test)])
    try:
        return subprocess.run(cmd, cwd=test.parent, capture_output=True, timeout=180).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def check(args) -> int:
    tests = sorted(Path(args.tests).glob("uc*.py"))
    by_uc = defaultdict(list)
    for t in tests:
        by_uc[t.name[:3]].append(t)
    with serve("v0", PORT):
        on_v0 = {t: _run(t) for t in tests}
    on_mut = {}
    for uc, variant in MUTANT[args.task].items():
        if by_uc[uc]:
            with serve(variant, PORT):
                on_mut |= {t: _run(t) for t in by_uc[uc]}
    result = {uc: {"tests": [t.name for t in by_uc[uc]],
                   "pass_v0": any(on_v0[t] for t in by_uc[uc]),
                   # hợp lệ: có ít nhất một test pass trên v0 VÀ fail trên mutation phá đúng UC đó
                   "valid": any(on_v0[t] and not on_mut[t] for t in by_uc[uc])}
              for uc in MUTANT[args.task]}
    rec = {"participant": args.participant, "condition": args.condition, "task": args.task, "ucs": result,
           "valid_ucs": sum(r["valid"] for r in result.values())}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"check_{args.participant}_{args.condition}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec, indent=2))
    return 0


def sus_score(answers: list[int]) -> float:
    """System Usability Scale: câu lẻ (1,3,..) điểm-1, câu chẵn 5-điểm, tổng × 2,5 -> 0..100."""
    return 2.5 * sum((a - 1) if i % 2 == 0 else (5 - a) for i, a in enumerate(answers))


def minutes(rows: list[dict]) -> dict[tuple, float]:
    start, out = {}, {}
    for r in rows:
        k = (r["participant"], r["condition"])
        t = datetime.fromisoformat(r["time"])
        if r["event"] == "start":
            start[k] = t
        elif k in start:
            out[k] = (t - start[k]).total_seconds() / 60
    return out


def analyze(args) -> int:
    rows = list(csv.DictReader(open(TIMINGS, encoding="utf-8"))) if TIMINGS.exists() else []
    mins = minutes(rows)
    checks = {(c["participant"], c["condition"]): c for c in
              (json.loads(p.read_text(encoding="utf-8")) for p in OUT.glob("check_*.json"))}
    sus = {(r["participant"], r["condition"]): sus_score([int(r[f"q{i}"]) for i in range(1, 11)])
           for r in (csv.DictReader(open(SUS, encoding="utf-8")) if SUS.exists() else [])}
    edits = _system_edits(args.db)
    table = []
    for k in sorted(set(mins) | set(checks)):
        table.append({"participant": k[0], "condition": k[1], "task": checks.get(k, {}).get("task", ""),
                      "minutes": round(mins[k], 1) if k in mins else None,
                      "valid_ucs": checks.get(k, {}).get("valid_ucs"), "sus": sus.get(k),
                      "manual_edits": edits.get(k[0]) if k[1] == "system" else None})
    summary = {}
    for cond in ("manual", "system"):
        r = [x for x in table if x["condition"] == cond]
        med = lambda key: statistics.median([x[key] for x in r if x[key] is not None]) if any(x[key] is not None for x in r) else None  # noqa: E731
        summary[cond] = {"n": len(r), "median_minutes": med("minutes"), "median_valid_ucs": med("valid_ucs"),
                         "median_sus": med("sus")}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rq4_results.json").write_text(json.dumps({"rows": table, "summary": summary}, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    for row in table:
        print(row)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _system_edits(db: str | None) -> dict[str, int]:
    """Số lần sửa tay trên UI (sửa test case, sửa plan) theo người tham gia (actor), từ bảng ui_event."""
    from sqlalchemy import select

    from src.database import session_factory
    from src.database.models import UIEvent

    sessions = session_factory(db)
    with sessions() as s:
        rows = s.scalars(select(UIEvent).where(UIEvent.event.in_(["edit_test_case", "edit_plan"])))
        out = defaultdict(int)
        for r in rows:
            out[r.actor] += 1
    return dict(out)


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="RQ4: thí nghiệm có người tham gia")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("timer")
    t.add_argument("action", choices=["start", "stop"])
    for p in (t, c := sub.add_parser("check")):
        p.add_argument("--participant", required=True)
        p.add_argument("--condition", required=True, choices=["manual", "system"])
        p.add_argument("--task", required=True, choices=["A", "B"])
    c.add_argument("--tests", required=True)
    e = sub.add_parser("export")
    e.add_argument("--project", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--db")
    a = sub.add_parser("analyze")
    a.add_argument("--db")
    args = ap.parse_args(argv)
    return {"timer": timer, "check": check, "export": export, "analyze": analyze}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
