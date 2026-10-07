"""RQ1 — test case sinh từ yêu cầu có cấu trúc (pipeline) so với đưa thẳng tài liệu cho LLM (direct).

    python evaluate_rq1.py --profile cloud               # sinh + chấm, ghi rq1_results.json + mẫu chấm tay
    python evaluate_rq1.py --kappa rq1_judge_sample.csv  # độ đồng thuận người chấm vs giám khảo LLM

Nhánh:
- direct:   cả tài liệu -> LLM -> test case (cùng các quy tắc chống bịa như pipeline).
- pipeline: Requirement Agent -> (duyệt mô phỏng: chấp nhận mọi yêu cầu) -> Test Design Agent + BVA tất định.
Số đo (so với điều kiện gold trong datasets/reference/ambiguity_eval/test_conditions.json):
- độ phủ: tỉ lệ điều kiện gold có ít nhất một test case kiểm (theo loại positive/negative/boundary);
- unsupported: tỉ lệ test case có kết quả mong đợi không có căn cứ trong tài liệu;
- truy vết: tỉ lệ test case gắn được về một yêu cầu có ID.
Giám khảo là LLM (structured output); một mẫu 20% được xuất CSV để người chấm lại và tính kappa.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from src.agents.requirement_agent import RequirementAnalysisAgent
from src.agents.test_design_agent import TestDesignAgent
from src.models.test_case import TestCase, TestCaseDraft
from src.services.document_loader import load_document
from src.utils.cli import resolve_client

ROOT = Path("datasets/reference/ambiguity_eval")
DIRECT_PROMPT = """\
Bạn là kỹ sư thiết kế kiểm thử. Đọc TOÀN BỘ tài liệu yêu cầu dưới đây và sinh các test case kiểm thử chức năng
bao phủ tài liệu.

QUY TẮC BẮT BUỘC:
- Sinh test case theo các loại KHI CÓ CĂN CỨ: positive, negative, boundary, error_guessing, alternative_flow.
- Mỗi test case gồm: title, type, preconditions, steps (mỗi step có action và expected), expected_result.
- KHÔNG tạo expected_result vượt quá phạm vi tài liệu.
- KHÔNG gán ID.

Trả về JSON gồm: test_cases[].\
"""
JUDGE_PROMPT = """\
Bạn là giám khảo đánh giá test case. Nhận một tài liệu yêu cầu, danh sách ĐIỀU KIỆN KIỂM THỬ chuẩn (có id) và danh
sách test case đã đánh số. Với MỖI test case, trả về:
- covers: id các điều kiện mà test case thực sự kiểm (hành động và kết quả mong đợi khớp ý của điều kiện; điều kiện
  boundary chỉ được tính khi test dùng đúng giá trị tại biên hoặc ngay ngoài biên). Không khớp thì để rỗng.
- supported: true nếu kết quả mong đợi của test case được tài liệu nêu hoặc suy ra trực tiếp; false nếu test case bịa
  hành vi, thông báo, con số hoặc quy tắc không có trong tài liệu.
- reason: một câu ngắn.
Trả JSON { "judgements": [ {"tc_index", "covers", "supported", "reason"} ] } với đủ mọi test case.\
"""


class Judgement(BaseModel):
    tc_index: int
    covers: list[str] = Field(default_factory=list)
    supported: bool = True
    reason: str = ""


class JudgeResult(BaseModel):
    judgements: list[Judgement] = Field(default_factory=list)


def gen_direct(client, text: str) -> list[TestCase]:
    return client.structured_completion(DIRECT_PROMPT, f"Tài liệu yêu cầu:\n\n{text}", TestCaseDraft).test_cases


def gen_pipeline(client, model: str, text: str, name: str) -> list[TestCase]:
    analysis = RequirementAnalysisAgent(client, model_name=model).analyze(text, source_name=name)
    designer = TestDesignAgent(client, model_name=model)
    return [tc for req in analysis.requirements for tc in designer.design(req).test_cases]


def _tc_line(i: int, tc: TestCase) -> str:
    steps = "; ".join(f"{s.action} => {s.expected or '—'}" for s in tc.steps)
    return f"[{i}] ({tc.type.value}) {tc.title} | bước: {steps or '—'} | mong đợi: {tc.expected_result or '—'}"


def judge(client, text: str, gold: list[dict], tcs: list[TestCase]) -> list[Judgement]:
    if not tcs:
        return []
    user = (f"Tài liệu:\n{text}\n\nĐiều kiện chuẩn:\n" + "\n".join(f"{g['id']}: ({g['kind']}) {g['condition']}" for g in gold)
            + "\n\nTest case:\n" + "\n".join(_tc_line(i, tc) for i, tc in enumerate(tcs)))
    valid = {g["id"] for g in gold}
    by_idx = {j.tc_index: j for j in client.structured_completion(JUDGE_PROMPT, user, JudgeResult).judgements}
    # giám khảo bỏ sót test case nào thì tính là không phủ, có căn cứ (không phạt)
    return [Judgement(tc_index=i, covers=[c for c in by_idx.get(i, Judgement(tc_index=i)).covers if c in valid],
                      supported=by_idx.get(i, Judgement(tc_index=i)).supported, reason=by_idx.get(i, Judgement(tc_index=i)).reason)
            for i in range(len(tcs))]


def score(rows: list[dict], gold_all: dict[str, list[dict]]) -> dict:
    """rows: [{doc, tc (dict), judgement (dict)}] của một nhánh."""
    covered = defaultdict(set)
    for r in rows:
        covered[r["doc"]] |= set(r["judgement"]["covers"])
    by_kind = defaultdict(lambda: [0, 0])
    for doc, gold in gold_all.items():
        for g in gold:
            by_kind[g["kind"]][1] += 1
            by_kind[g["kind"]][0] += g["id"] in covered[doc]
    n_gold = sum(v[1] for v in by_kind.values())
    n_cov = sum(v[0] for v in by_kind.values())
    n_tc = len(rows)
    return {
        "n_tc": n_tc, "n_gold": n_gold, "covered": n_cov, "coverage": n_cov / n_gold if n_gold else 0.0,
        "coverage_by_kind": {k: {"covered": v[0], "n": v[1]} for k, v in sorted(by_kind.items())},
        "unsupported": sum(not r["judgement"]["supported"] for r in rows),
        "unsupported_rate": sum(not r["judgement"]["supported"] for r in rows) / n_tc if n_tc else 0.0,
        "no_gold_match": sum(not r["judgement"]["covers"] for r in rows),
        "traceable": sum(bool(r["tc"].get("requirement_id")) for r in rows),
        "boundary_tc": sum(r["tc"]["type"] == "boundary" for r in rows),
    }


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def kappa_report(path: str) -> int:
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8-sig")) if r["human_supported"].strip()]
    if not rows:
        print("[!] Chưa có dòng nào được chấm (cột human_supported trống).")
        return 1
    truthy = lambda s: s.strip().lower() in ("1", "true", "x", "có", "co", "yes")  # noqa: E731
    k = cohen_kappa([truthy(r["judge_supported"]) for r in rows], [truthy(r["human_supported"]) for r in rows])
    jac = [len(set(r["judge_covers"].split()) & set(r["human_covers"].split())) /
           max(1, len(set(r["judge_covers"].split()) | set(r["human_covers"].split()))) for r in rows]
    print(f"{len(rows)} dòng | kappa (supported) = {k:.2f} | Jaccard trung bình (covers) = {sum(jac) / len(jac):.2f}")
    return 0


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="RQ1: structured pipeline vs direct prompting")
    ap.add_argument("--profile")
    ap.add_argument("--out", default="rq1_results.json")
    ap.add_argument("--sample", default="rq1_judge_sample.csv")
    ap.add_argument("--kappa", help="CSV đã chấm tay -> in kappa rồi thoát")
    args = ap.parse_args(argv)
    if args.kappa:
        return kappa_report(args.kappa)

    gold_all = json.loads((ROOT / "test_conditions.json").read_text(encoding="utf-8"))["cases"]
    client, model = resolve_client(args.profile, False, TestCaseDraft())
    rows = {"direct": [], "pipeline": []}
    for doc, gold in gold_all.items():
        text = load_document(ROOT / doc).text
        for arm in rows:
            tcs = gen_direct(client, text) if arm == "direct" else gen_pipeline(client, model, text, doc)
            js = judge(client, text, gold, tcs)
            rows[arm] += [{"doc": doc, "tc": tc.model_dump(mode="json"), "judgement": j.model_dump()} for tc, j in zip(tcs, js)]
            cov = len({c for j in js for c in j.covers})
            print(f"  {doc:22} {arm:9} {len(tcs):3} TC | phủ {cov}/{len(gold)} | unsupported {sum(not j.supported for j in js)}")

    summary = {arm: score(r, gold_all) for arm, r in rows.items()}
    for arm, s in summary.items():
        print(f"=== {arm:9} {s['n_tc']} TC | độ phủ {s['covered']}/{s['n_gold']} = {s['coverage']:.0%} "
              f"| unsupported {s['unsupported_rate']:.0%} | truy vết {s['traceable']}/{s['n_tc']} | boundary {s['boundary_tc']}")
    Path(args.out).write_text(json.dumps({"model": model, "summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
                              encoding="utf-8")

    # mẫu 20% cho người chấm lại
    rng = random.Random(42)
    flat = [(arm, r) for arm, rs in rows.items() for r in rs]
    sample = rng.sample(flat, max(1, len(flat) // 5))
    with open(args.sample, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arm", "doc", "tc_title", "tc_type", "tc_expected", "judge_covers", "judge_supported",
                    "human_covers", "human_supported"])
        for arm, r in sample:
            w.writerow([arm, r["doc"], r["tc"]["title"], r["tc"]["type"], r["tc"]["expected_result"],
                        " ".join(r["judgement"]["covers"]), r["judgement"]["supported"], "", ""])
    print(f"[✓] JSON: {args.out} | mẫu chấm tay ({len(sample)} dòng): {args.sample}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
