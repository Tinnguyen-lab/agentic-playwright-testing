"""CLI đánh giá Requirement Agent trên dataset gán nhãn -> bảng precision/recall/F1.

    python evaluate_agent.py                 # model trong .env (Gemma local)
    python evaluate_agent.py --profile cloud # .env.cloud (DeepSeek)

Mỗi lần chạy ghi datasets/processed/eval_<model>.json và tổng hợp mọi lần chạy thành
bảng so sánh docs/development/eval-results.md (local vs cloud).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from src.agents.requirement_agent import RequirementAnalysisAgent
from src.evaluation.dataset import load_dataset
from src.evaluation.evaluator import EvalReport, run_dataset
from src.services.llm_client import MockLLMClient, OpenAILLMClient
from src.utils.config import load_settings

DEFAULT_DATASET = "datasets/reference/ambiguity_eval"
PROCESSED_DIR = Path("datasets/processed")
RESULTS_MD = Path("docs/development/eval-results.md")


def _slug(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model)


def _overflag_rate(r: dict) -> float:
    return r["overflag_clean"] / r["clean_reqs"] if r["clean_reqs"] else 0.0


def report_to_dict(model: str, r: EvalReport) -> dict:
    def c(x):
        return {"tp": x.tp, "fp": x.fp, "fn": x.fn,
                "precision": round(x.precision, 3), "recall": round(x.recall, 3), "f1": round(x.f1, 3)}

    return {
        "model": model,
        "n_cases": r.n_cases, "n_gold_reqs": r.n_gold_reqs, "n_pred_reqs": r.n_pred_reqs,
        "count_mismatches": r.count_mismatches, "clean_reqs": r.clean_reqs, "overflag_clean": r.overflag_clean,
        "by_type": {t: c(v) for t, v in sorted(r.by_type.items())},
        "micro": c(r.micro), "macro_f1": round(r.macro_f1, 3),
    }


def render_markdown(runs: list[dict]) -> str:
    types = sorted({t for run in runs for t in run["by_type"]})
    out = ["# Kết quả đánh giá — phát hiện mơ hồ (Requirement Agent)\n",
           "Ground truth: nhãn chèn có chủ đích trong `datasets/reference/ambiguity_eval`. "
           "Đơn vị so khớp: cặp (requirement, loại mơ hồ). Căn predicted↔gold theo thứ tự UC.\n",
           "## Tổng hợp\n",
           "| Model | Micro-P | Micro-R | Micro-F1 | Macro-F1 | Over-flag* | Lệch số req |",
           "|---|---|---|---|---|---|---|"]
    for r in runs:
        m = r["micro"]
        out.append(f"| {r['model']} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} "
                   f"| {r['macro_f1']:.2f} | {_overflag_rate(r):.2f} | {r['count_mismatches']} |")
    out.append("\n*Over-flag = tỉ lệ requirement SẠCH bị gắn cờ nhầm (thấp là tốt).\n")
    out.append("## F1 theo từng loại mơ hồ\n")
    out.append("| Loại | " + " | ".join(r["model"] for r in runs) + " |")
    out.append("|---|" + "---|" * len(runs))
    for t in types:
        cells = []
        for r in runs:
            bt = r["by_type"].get(t)
            cells.append(f"{bt['f1']:.2f}" if bt else "—")
        out.append(f"| {t} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def _build_agent(profile: str | None, mock: bool):
    settings = load_settings(profile)
    use_mock = mock or not settings.use_real_llm
    if use_mock:
        from run_requirement_agent import default_mock_extraction
        return RequirementAnalysisAgent(MockLLMClient(default_mock_extraction()), model_name="mock"), "mock"
    client = OpenAILLMClient(settings.openai_model, settings.openai_api_key, settings.openai_base_url)
    where = settings.openai_base_url or "OpenAI"
    print(f"[i] LLM: {where} | model={settings.openai_model}")
    return RequirementAnalysisAgent(client, model_name=settings.openai_model), settings.openai_model


def _print_console(data: dict) -> None:
    print(f"\n=== ĐÁNH GIÁ: {data['model']} ===")
    print(f"Cases: {data['n_cases']} | gold req: {data['n_gold_reqs']} | pred req: {data['n_pred_reqs']} "
          f"| lệch số req: {data['count_mismatches']} | over-flag: {data['overflag_clean']}/{data['clean_reqs']}")
    print(f"{'loại':<26}{'P':>6}{'R':>6}{'F1':>6}  (tp/fp/fn)")
    for t, v in data["by_type"].items():
        print(f"{t:<26}{v['precision']:>6.2f}{v['recall']:>6.2f}{v['f1']:>6.2f}  ({v['tp']}/{v['fp']}/{v['fn']})")
    m = data["micro"]
    print(f"{'MICRO':<26}{m['precision']:>6.2f}{m['recall']:>6.2f}{m['f1']:>6.2f}   | macro-F1={data['macro_f1']:.2f}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Đánh giá Requirement Agent trên dataset gán nhãn")
    ap.add_argument("--dataset", default=DEFAULT_DATASET, help="Thư mục dataset (có labels.json)")
    ap.add_argument("--profile", help="Hồ sơ .env: 'cloud' -> .env.cloud")
    ap.add_argument("--mock", action="store_true", help="LLM giả lập (chỉ để smoke test)")
    args = ap.parse_args(argv)

    if args.profile and not Path(f".env.{args.profile}").exists():
        print(f"[!] Không thấy .env.{args.profile} -> dùng .env/mặc định.")

    agent, model = _build_agent(args.profile, args.mock)
    cases = load_dataset(args.dataset)
    print(f"[i] Chạy {len(cases)} tài liệu...")
    data = report_to_dict(model, run_dataset(agent, cases))

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    json_path = PROCESSED_DIR / f"eval_{_slug(model)}.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(PROCESSED_DIR.glob("eval_*.json"))]
    RESULTS_MD.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_MD.write_text(render_markdown(runs), encoding="utf-8")

    _print_console(data)
    print(f"\n[✓] JSON: {json_path} | Bảng so sánh: {RESULTS_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
