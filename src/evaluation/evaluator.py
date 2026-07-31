"""Chạy agent trên dataset gán nhãn và tổng hợp metrics.

Căn predicted↔gold theo THỨ TỰ index (agent gán REQ-001.. theo thứ tự UC; gold cùng thứ tự).
Lệch số lượng requirement -> đếm mismatch; requirement thừa/thiếu vẫn bị tính FP/FN.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import zip_longest

from src.evaluation.dataset import Case
from src.evaluation.metrics import Counts, accumulate_pair, macro_f1, micro


@dataclass
class EvalReport:
    by_type: dict[str, Counts] = field(default_factory=dict)
    n_cases: int = 0
    n_gold_reqs: int = 0
    n_pred_reqs: int = 0
    count_mismatches: int = 0
    clean_reqs: int = 0
    overflag_clean: int = 0

    @property
    def micro(self) -> Counts:
        return micro(self.by_type)

    @property
    def macro_f1(self) -> float:
        return macro_f1(self.by_type)


def score_case(
    report: EvalReport,
    predicted_reqs: list[set[str]],
    predicted_global: set[str],
    gold_reqs: list[set[str]],
    gold_global: set[str],
) -> None:
    report.n_cases += 1
    report.n_gold_reqs += len(gold_reqs)
    report.n_pred_reqs += len(predicted_reqs)
    if len(predicted_reqs) != len(gold_reqs):
        report.count_mismatches += 1
    for pred, gold in zip_longest(predicted_reqs, gold_reqs):
        p = pred if pred is not None else set()
        g = gold if gold is not None else set()
        accumulate_pair(report.by_type, p, g)
        if gold is not None and not g:
            report.clean_reqs += 1
            if p:
                report.overflag_clean += 1
    accumulate_pair(report.by_type, set(predicted_global), set(gold_global))


def run_dataset(agent, cases: list[Case]) -> EvalReport:
    report = EvalReport()
    for case in cases:
        result = agent.analyze(case.text, source_name=case.name)
        pred_reqs = [{a.type.value for a in r.ambiguities} for r in result.requirements]
        pred_global = {a.type.value for a in result.global_ambiguities}
        score_case(report, pred_reqs, pred_global, case.gold_reqs, case.gold_global)
    return report
