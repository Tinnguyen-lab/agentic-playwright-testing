"""Kiểm tra assertion rỗng (vacuity) cho script RQ2 đã PASS.

    python tools/rq2_vacuity.py artifacts/rq2_v2_scripts/r1 --results rq2_v2_r1.json

Với mỗi script đã pass, bỏ mọi bước thao tác (fill/click) — chỉ giữ goto và assertion — rồi chạy lại. Vẫn pass nghĩa là
assertion không phụ thuộc vào hành động của test: test "pass" mà không chứng minh được hành vi (vd thông báo lỗi có sẵn
trong DOM từ trước, hoặc locator trỏ vào đoạn văn mô tả). Script không có bước thao tác nào thì không áp dụng.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ACTION = re.compile(r"^\s*page\..*\.(fill|click)\(.*\)\s*$")


def strip_actions(code: str) -> tuple[str, int]:
    lines = code.splitlines()
    kept = [l for l in lines if not ACTION.match(l)]
    return "\n".join(kept) + "\n", len(lines) - len(kept)


def still_passes(code: str) -> bool:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "t.py"
        f.write_text(code, encoding="utf-8")
        try:
            out = subprocess.run([sys.executable, f.name], cwd=d, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return False
        return out.returncode == 0 and "PASSED" in out.stdout


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("scripts", help="thư mục chứa các nhánh (none/aria/aria_loop) với <id>.py")
    ap.add_argument("--results", required=True, help="JSON kết quả run_rq2 tương ứng (để biết script nào đã pass)")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    res = json.loads(Path(args.results).read_text(encoding="utf-8"))
    out = {}
    for cond, data in res["conditions"].items():
        folder = Path(args.scripts) / cond
        if not folder.exists():
            continue
        def judge(case):
            code, n_removed = strip_actions((folder / f"{case['id']}.py").read_text(encoding="utf-8"))
            return case["id"], "n/a" if n_removed == 0 else ("vacuous" if still_passes(code) else "ok")

        todo = [c for c in data["cases"] if c["status"] == "passed" and (folder / f"{c['id']}.py").exists()]
        with ThreadPoolExecutor(max_workers=4) as pool:  # mỗi script là một tiến trình trình duyệt riêng
            rows = dict(pool.map(judge, todo))
        vac = [k for k, v in rows.items() if v == "vacuous"]
        out[cond] = {"passed": len(rows), "checked": sum(v != "n/a" for v in rows.values()), "vacuous": vac}
        print(f"{cond:10} pass {len(rows)} | kiểm được {out[cond]['checked']} | assertion rỗng {len(vac)}: {vac}")
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
