"""In mục RQ2 (markdown) từ JSON kết quả để dán vào docs/development/eval-results.md."""
import json
import sys

from build_report import SITE_NAME, mcnemar_exact_p, pct

sys.stdout.reconfigure(encoding="utf-8")
res = json.load(open(sys.argv[1], encoding="utf-8"))
oracle_pass = int(sys.argv[2])
none, aria, pr = res["conditions"]["none"], res["conditions"]["aria"], res["paired"]
n = none["n"]
p = mcnemar_exact_p(pr["aria_only"], pr["none_only"])
out = [
    "", "# Kết quả RQ2 — ngữ cảnh DOM (aria snapshot) và first-run pass rate", "",
    f"Catalog `datasets/reference/rq2_targets.json`: {n} target, {len(none['by_site'])} site; oracle viết tay đạt "
    f"**{oracle_pass}/{n}** (`python run_rq2.py --context oracle`). Model `{res['model']}`, mỗi nhánh chạy 1 lần, "
    "script không qua repair. Lệnh: `python run_rq2.py --profile cloud --context both --out rq2_results_both.json`.", "",
    "| Site | n | Baseline (none) | DOM-aware (aria) |", "|---|---|---|---|",
]
for s in sorted(none["by_site"], key=lambda k: -none["by_site"][k]["n"]):
    a, b = none["by_site"][s], aria["by_site"][s]
    out.append(f"| {SITE_NAME[s]} | {a['n']} | {a['passed']} ({pct(a['passed'], a['n'])}) | {b['passed']} ({pct(b['passed'], b['n'])}) |")
out += [f"| **Tổng** | {n} | **{none['passed']} ({pct(none['passed'], n)})** | **{aria['passed']} ({pct(aria['passed'], n)})** |", "",
        f"Theo cặp: cả hai đạt {pr['both_pass']}, chỉ aria đạt {pr['aria_only']}, chỉ baseline đạt {pr['none_only']}, "
        f"cả hai trượt {pr['both_fail']}. McNemar chính xác p = {p:.3f}.", "",
        "Kiểm soát nhiễu: Chromium chạy `--disable-http2` (HTTP/2 tới heroku treo ở mạng của nhóm), `expect` timeout 10s; "
        "script fail vì `Page.goto: Timeout` được chạy lại đúng script đó 1 lần (`infra_retry`)."]
print("\n".join(out))
