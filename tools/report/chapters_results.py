"""Các mục kết quả bổ sung của chương 5 (đợt 2). Số liệu đọc từ JSON; nhận xét viết tay trong notes_ext.py."""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict

from chapters_ext import ROOT, VARIANTS, mcnemar, pct


def vn(x: float, d: int = 2) -> str:
    """Số thập phân kiểu Việt Nam (dấu phẩy)."""
    return f"{x:.{d}f}".replace(".", ",")


def rq1_ambiguity(r, amb47: dict | None, notes):
    r.h3("5.1.2 Phát hiện mơ hồ trên tập mở rộng")
    if not amb47:
        r.p("Chưa chạy lại trên tập mở rộng.")
        return
    m = amb47["micro"]
    r.p(f"Tập mở rộng gồm 15 tài liệu, {amb47['n_gold_reqs']} yêu cầu, trong đó {amb47['clean_reqs']} yêu cầu sạch. "
        f"Với {amb47['model']}: micro-precision {vn(m['precision'])}, micro-recall {vn(m['recall'])}, micro-F1 {vn(m['f1'])}, "
        f"macro-F1 {vn(amb47['macro_f1'])}; {amb47['overflag_clean']}/{amb47['clean_reqs']} yêu cầu sạch bị gắn cờ nhầm.")
    rows = [[t, f"{v['tp']}/{v['fp']}/{v['fn']}", vn(v["precision"]), vn(v["recall"]), vn(v["f1"])]
            for t, v in amb47["by_type"].items()]
    r.table(f"Phát hiện mơ hồ theo loại trên {amb47['n_gold_reqs']} yêu cầu ({amb47['model']})",
            ["Loại", "TP/FP/FN", "Precision", "Recall", "F1"], rows, [6, 3, 2.3, 2.3, 2.4], center_cols=(1, 2, 3, 4))
    for para in notes.RQ1_AMB:
        r.p(para)


def _cov_kind(s, kind):
    v = s["coverage_by_kind"].get(kind, {"covered": 0, "n": 0})
    return f"{v['covered']}/{v['n']}"


def rq1_testgen(r, v1: dict, v2: dict, notes):
    r.h3("5.1.3 Chất lượng test case: pipeline có cấu trúc so với đưa thẳng tài liệu")
    r.p("Bảng dưới so sánh hai nhánh trên 15 tài liệu và 83 điều kiện gold, qua hai phiên bản quy tắc sinh test. Phiên bản 1 "
        "dùng prompt ban đầu của Test Design Agent. Phiên bản 2 thêm quy tắc chỉ sinh negative, error_guessing và "
        "alternative_flow khi tài liệu nêu phản ứng của hệ thống, áp dụng cho cả hai nhánh; ca biên BVA mang theo hành "
        "động của yêu cầu. Dòng \"có AG-01\" chỉ tính test sinh từ yêu cầu không bị Requirement Agent gắn cờ mơ hồ, mô "
        "phỏng việc người duyệt giữ các yêu cầu mơ hồ lại để làm rõ.")
    rows = []
    for tag, d in (("v1", v1), ("v2", v2)):
        for arm in ("direct", "pipeline"):
            s = d["summary"][arm]
            rows.append([f"{arm} {tag}", str(s["n_tc"]), f"{s['covered']}/{s['n_gold']} ({pct(s['covered'], s['n_gold'])})",
                         _cov_kind(s, "positive"), _cov_kind(s, "negative"), _cov_kind(s, "boundary"),
                         pct(s["unsupported"], s["n_tc"]), pct(s["traceable"], s["n_tc"])])
        g = d["summary"]["pipeline"].get("gated")
        if g:
            rows.append([f"pipeline {tag} có AG-01", str(g["n_tc"]),
                         f"{g['covered']}/{g['n_gold']} ({pct(g['covered'], g['n_gold'])})",
                         _cov_kind(g, "positive"), _cov_kind(g, "negative"), _cov_kind(g, "boundary"),
                         pct(g["unsupported"], g["n_tc"]), pct(g["traceable"], g["n_tc"])])
    r.table("Chất lượng test case theo nhánh và phiên bản quy tắc",
            ["Nhánh", "Số TC", "Độ phủ gold", "Positive", "Negative", "Biên", "Không căn cứ", "Truy vết"],
            rows, [3.3, 1.3, 2.6, 1.9, 1.9, 1.5, 2.0, 1.6], center_cols=(1, 2, 3, 4, 5, 6, 7))
    gold = json.loads((ROOT / "datasets/reference/ambiguity_eval/test_conditions.json").read_text(encoding="utf-8"))["cases"]
    allc = {(doc, g["id"]) for doc, gs in gold.items() for g in gs}
    lines = []
    for tag, d in (("1", v1), ("2", v2)):
        cov = {arm: {(x["doc"], c) for x in rows_ for c in x["judgement"]["covers"]} & allc
               for arm, rows_ in d["rows"].items()}
        b, c = len(cov["pipeline"] - cov["direct"]), len(cov["direct"] - cov["pipeline"])
        lines.append(f"phiên bản {tag}: {b} điều kiện chỉ pipeline phủ, {c} chỉ direct phủ, p = {vn(mcnemar(b, c))}")
    r.p("So sánh theo cặp trên từng điều kiện gold (McNemar chính xác): " + "; ".join(lines) + ".")
    types = defaultdict(lambda: [0, 0, 0, 0])
    for arm_i, arm in enumerate(("direct", "pipeline")):
        for x in v1["rows"][arm]:
            t = types[x["tc"]["type"]]
            t[arm_i * 2] += 1
            t[arm_i * 2 + 1] += not x["judgement"]["supported"]
    r.table("Test không căn cứ theo loại test (phiên bản 1)",
            ["Loại test", "Direct: không căn cứ / tổng", "Pipeline: không căn cứ / tổng"],
            [[k, f"{v[1]}/{v[0]}", f"{v[3]}/{v[2]}"] for k, v in sorted(types.items())], [5, 5.5, 5.5], center_cols=(1, 2))
    for para in notes.RQ1_TESTGEN:
        r.p(para)


def rq2_v2_section(r, runs: list[dict], notes):
    r.h3("5.2.3 Bản 2: grounding vòng lặp, ba lần lặp")
    if not runs:
        r.p("Chưa có kết quả.")
        return
    rows = []
    for c in ("none", "aria", "aria_loop"):
        vals = [run["conditions"][c]["passed"] for run in runs]
        sd = f" ± {vn(statistics.stdev(vals), 1)}" if len(vals) > 1 else ""
        rows.append([c, " / ".join(map(str, vals)), f"{vn(statistics.mean(vals), 1)}{sd}",
                     pct(statistics.mean(vals), runs[0]["conditions"][c]["n"])])
    r.table(f"First-run pass rate qua {len(runs)} lần lặp (50 target, {runs[0]['model']})",
            ["Nhánh", "Số target đạt từng lần", "Trung bình", "Tỉ lệ TB"], rows, [3.5, 5, 4, 3.5], center_cols=(1, 2, 3))
    prow = []
    for i, run in enumerate(runs, 1):
        for key in ("none__aria", "none__aria_loop", "aria__aria_loop"):
            p = run["paired_all"][key]
            x, y = key.split("__")
            b, c = p[f"{y}_only"], p[f"{x}_only"]
            prow.append([str(i), f"{x} → {y}", str(b), str(c), vn(mcnemar(b, c), 3)])
    r.table("So sánh theo cặp từng lần lặp", ["Lần", "Cặp", "Chỉ nhánh sau đạt", "Chỉ nhánh trước đạt", "p (McNemar)"],
            prow, [1.5, 4.5, 3.5, 3.5, 3], center_cols=(0, 2, 3, 4))
    refined = [sum(x.get("refined", False) for x in run["conditions"]["aria_loop"]["cases"]) for run in runs]
    r.p("Số target mà vòng lặp phải sinh lại (có locator khớp khác 1 khi grounding) ở mỗi lần: "
        f"{', '.join(map(str, refined))} trên 50.")
    for para in notes.RQ2_V2:
        r.p(para)


def rq3_results(r, res: dict, res_first: dict | None, notes):
    r.h2("5.3 RQ3: sửa lỗi có ràng buộc")
    s = res["summary"]
    rows = [[arm, f"{v['tech_repaired']}/{v['tech_n']}", f"{v['sem_masked']}/{v['sem_n']}", str(v["escalated"]),
             str(v["weakened"])] for arm, v in s.items()]
    r.table(f"Kết quả ba nhánh sửa trên ShopLab ({res['model']}, ngân sách {res['budget']})",
            ["Nhánh", "Technical sửa được (giữ assertion)", "Semantic bị che", "Escalate", "Lần làm yếu assertion"],
            rows, [3, 4, 3, 2.5, 3.5], center_cols=(1, 2, 3, 4))
    if res_first:
        r.p("Lần chạy đầu, khi self-healing chỉ chữa một locator mỗi lượt: " + "; ".join(
            f"{arm} sửa {v['tech_repaired']}/{v['tech_n']}, che {v['sem_masked']}/{v['sem_n']}, escalate {v['escalated']}"
            for arm, v in res_first["summary"].items()) + ".")
    by: dict = defaultdict(lambda: defaultdict(Counter))
    for x in res["cases"]:
        by[x["variant"]][x["arm"]][x["outcome"]] += 1

    def fmt(c):
        return f"{c['repaired']}/{c['escalated']}/{c['unrepaired']}"

    vrows = [[v, VARIANTS[v]["kind"], fmt(a["unconstrained"]), fmt(a["heal"]), fmt(a["constrained"])] for v, a in by.items()]
    r.table("Kết quả theo mutation (sửa được / escalate / không sửa được)",
            ["Mutation", "Lớp", "unconstrained", "heal", "constrained"], vrows, [4, 2.5, 3.2, 3, 3.3],
            center_cols=(1, 2, 3, 4))
    for para in notes.RQ3:
        r.p(para)


def rq4_results(r, rq4: dict | None, notes):
    r.h2("5.4 RQ4: công sức thủ công")
    if not rq4 or not rq4.get("rows"):
        for para in notes.RQ4_PENDING:
            r.p(para)
        return
    rows = [[x["participant"], x["condition"], x["task"], str(x["minutes"]), str(x["valid_ucs"]),
             str(x["manual_edits"] if x["manual_edits"] is not None else "—"), str(x["sus"])] for x in rq4["rows"]]
    r.table("Kết quả từng người tham gia", ["Người", "Điều kiện", "Bộ", "Phút", "Yêu cầu có test hợp lệ", "Sửa tay", "SUS"],
            rows, [2, 2.5, 1.5, 2, 3.5, 2, 2.5], center_cols=(0, 1, 2, 3, 4, 5, 6))
    for para in notes.RQ4:
        r.p(para)
