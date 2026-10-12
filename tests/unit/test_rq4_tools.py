"""RQ4 command contract: no AI-versus-human timing or SUS measurement."""
from tools.rq4 import rq4


def test_rq4_uses_semantic_mutation_map_for_both_task_sets():
    assert set(rq4.MUTANT) == {"A", "B"}
    assert all(set(cases) == {"uc1", "uc2", "uc3"} for cases in rq4.MUTANT.values())


def test_rq4_check_records_review_phase_not_competing_condition(tmp_path, monkeypatch):
    monkeypatch.setattr(rq4, "OUT", tmp_path)
    parsed = {}
    original = rq4.check

    def capture(args):
        parsed.update(vars(args))
        return 0

    monkeypatch.setattr(rq4, "check", capture)
    assert rq4.main(["check", "--reviewer", "reviewer-01", "--phase", "after_review",
                     "--task", "A", "--tests", str(tmp_path)]) == 0
    assert parsed["reviewer"] == "reviewer-01"
    assert parsed["phase"] == "after_review"
    monkeypatch.setattr(rq4, "check", original)


def test_rq4_runner_resolves_a_relative_artifact_path(tmp_path, monkeypatch):
    script = tmp_path / "ok.py"
    script.write_text("print('ok')", encoding="utf-8")
    monkeypatch.chdir(tmp_path.parent)
    assert rq4._run(script.relative_to(tmp_path.parent)) is True


def test_rq4_timer_records_real_condition_without_inventing_result(tmp_path, monkeypatch):
    monkeypatch.setattr(rq4, "OUT", tmp_path)
    monkeypatch.setattr(rq4, "TIMINGS", tmp_path / "study_timings.csv")
    assert rq4.main(["timer", "start", "--participant", "P01", "--condition", "manual", "--task", "A"]) == 0
    data = (tmp_path / "study_timings.csv").read_text(encoding="utf-8")
    assert "P01,manual,A,start" in data


def test_rq4_analysis_pairs_only_real_timer_events(tmp_path, monkeypatch):
    monkeypatch.setattr(rq4, "OUT", tmp_path)
    monkeypatch.setattr(rq4, "TIMINGS", tmp_path / "study_timings.csv")
    (tmp_path / "study_timings.csv").write_text(
        "participant,condition,task,event,time\n"
        "P01,manual,A,start,2026-10-12T01:00:00+00:00\n"
        "P01,manual,A,stop,2026-10-12T01:01:30+00:00\n",
        encoding="utf-8",
    )
    assert rq4.main(["analyze"]) == 0
    payload = __import__("json").loads((tmp_path / "rq4_results.json").read_text(encoding="utf-8"))
    assert payload["timed_sessions"] == [{
        "participant": "P01", "condition": "manual", "task": "A",
        "started_at": "2026-10-12T01:00:00+00:00", "stopped_at": "2026-10-12T01:01:30+00:00",
        "duration_seconds": 90.0,
    }]
    assert payload["study_summary"]["ai_assisted"]["n_completed_timed_sessions"] == 0


def test_rq4_prepare_creates_blank_session_handoff(tmp_path, monkeypatch):
    monkeypatch.setattr(rq4, "STUDY", tmp_path / "study")
    assert rq4.main(["prepare", "--participant", "P01", "--condition", "manual", "--task", "A"]) == 0
    session = tmp_path / "study" / "P01" / "manual_A"
    assert (session / "task_A.md").exists()
    assert "Số test case đã tạo:" in (session / "SUBMISSION.md").read_text(encoding="utf-8")
