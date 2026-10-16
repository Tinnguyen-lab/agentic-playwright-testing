"""Auth state must be scoped and never publish an empty login attempt."""
import json

from src.services.auth_state import has_state, promote_state, state_path


def test_state_path_is_scoped_to_project_and_origin():
    first = state_path(4, "https://example.test/login")
    assert first == state_path(4, "https://example.test/private")
    assert first != state_path(5, "https://example.test/login")
    assert first != state_path(4, "https://other.test/login")


def test_promote_state_rejects_empty_candidate_without_replacing_existing(tmp_path):
    destination = tmp_path / "auth.json"
    destination.write_text(json.dumps({"cookies": [{"name": "session"}], "origins": []}), encoding="utf-8")
    candidate = tmp_path / "candidate.json"
    candidate.write_text('{"cookies": [], "origins": []}', encoding="utf-8")
    assert not promote_state(candidate, destination)
    assert not candidate.exists()
    assert has_state(destination)


def test_promote_state_moves_valid_candidate(tmp_path):
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps({"cookies": [{"name": "session"}], "origins": []}), encoding="utf-8")
    destination = tmp_path / "private" / "auth.json"
    assert promote_state(candidate, destination)
    assert has_state(destination)
    assert not candidate.exists()
