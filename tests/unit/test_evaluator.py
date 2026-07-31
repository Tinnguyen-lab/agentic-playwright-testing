"""Test evaluator: căn predicted↔gold theo index, đếm mismatch/over-flag, load dataset. Offline."""
import json

from src.agents.requirement_agent import RequirementAnalysisAgent
from src.evaluation.dataset import Case, load_dataset
from src.evaluation.evaluator import EvalReport, run_dataset, score_case
from src.models.requirement import (
    AmbiguityFinding,
    AmbiguityType,
    RequirementExtraction,
    StructuredRequirement,
)
from src.services.llm_client import MockLLMClient


def test_score_case_perfect_match():
    r = EvalReport()
    score_case(r, [{"missing_actor"}, set()], set(), [{"missing_actor"}, set()], set())
    assert (r.micro.tp, r.micro.fp, r.micro.fn) == (1, 0, 0)
    assert r.clean_reqs == 1 and r.overflag_clean == 0
    assert r.count_mismatches == 0


def test_score_case_overflag_and_mismatch():
    r = EvalReport()
    score_case(
        r,
        [{"missing_actor"}, {"vague_quantifier"}, {"conflict"}],
        set(),
        [{"missing_actor"}, set()],
        set(),
    )
    assert r.count_mismatches == 1                      # 3 dự đoán vs 2 gold
    assert r.clean_reqs == 1 and r.overflag_clean == 1  # gold[1] sạch nhưng bị gắn cờ
    assert r.by_type["vague_quantifier"].fp == 1
    assert r.by_type["conflict"].fp == 1                # requirement thừa -> FP


def test_score_case_global_conflict():
    r = EvalReport()
    score_case(r, [], {"conflict"}, [], {"conflict"})
    assert r.by_type["conflict"].tp == 1


def test_load_dataset(tmp_path):
    (tmp_path / "cases").mkdir()
    (tmp_path / "cases" / "a.md").write_text("UC-1 nội dung", encoding="utf-8")
    (tmp_path / "labels.json").write_text(
        json.dumps({"cases": [
            {"file": "cases/a.md",
             "requirements": [{"hint": "x", "expected": ["missing_actor"]}],
             "expected_global": ["conflict"]}
        ]}),
        encoding="utf-8",
    )
    cases = load_dataset(tmp_path)
    assert len(cases) == 1
    assert cases[0].gold_reqs == [{"missing_actor"}]
    assert cases[0].gold_global == {"conflict"}


def test_run_dataset_with_mock():
    extraction = RequirementExtraction(
        requirements=[
            StructuredRequirement(
                title="x", action="y",
                ambiguities=[AmbiguityFinding(type=AmbiguityType.MISSING_ACTOR, description="d")],
            )
        ],
        global_ambiguities=[],
    )
    agent = RequirementAnalysisAgent(MockLLMClient(extraction), model_name="mock")
    cases = [Case(name="c", text="doc", gold_reqs=[{"missing_actor"}], gold_global=set())]
    r = run_dataset(agent, cases)
    assert r.by_type["missing_actor"].tp == 1
    assert r.micro.fp == 0 and r.micro.fn == 0
