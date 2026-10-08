"""Test load_settings đọc cấu hình LLM, kể cả chạy local qua OPENAI_BASE_URL.

Patch load_dotenv thành no-op để test tất định, không phụ thuộc file .env thật trên máy.
"""
from src.utils import config as config_module


def _load(monkeypatch, **env):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *a, **k: False)
    for key in ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    for key, val in env.items():
        monkeypatch.setenv(key, val)
    return config_module.load_settings()


def test_reads_base_url(monkeypatch):
    s = _load(monkeypatch, OPENAI_BASE_URL="http://localhost:1234/v1")
    assert s.openai_base_url == "http://localhost:1234/v1"


def test_use_real_llm_true_with_only_base_url(monkeypatch):
    # Local (LM Studio/Ollama): có base_url, KHÔNG cần key thật.
    s = _load(monkeypatch, OPENAI_BASE_URL="http://localhost:1234/v1")
    assert s.has_openai_key is False
    assert s.use_real_llm is True


def test_use_real_llm_true_with_only_key(monkeypatch):
    s = _load(monkeypatch, OPENAI_API_KEY="sk-abc")
    assert s.use_real_llm is True


def test_use_real_llm_false_when_empty(monkeypatch):
    s = _load(monkeypatch)
    assert s.openai_base_url == ""
    assert s.use_real_llm is False
    assert s.openai_model == config_module.DEFAULT_MODEL


def _capture_dotenv_path(monkeypatch):
    captured = {}
    def fake_load_dotenv(path=None, *a, **k):
        captured["path"] = path
        return False
    monkeypatch.setattr(config_module, "load_dotenv", fake_load_dotenv)
    for key in ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    return captured


def test_profile_loads_named_env(monkeypatch):
    captured = _capture_dotenv_path(monkeypatch)
    config_module.load_settings(profile="cloud")
    assert captured["path"] == ".env.cloud"


def test_no_profile_uses_default(monkeypatch):
    captured = _capture_dotenv_path(monkeypatch)
    config_module.load_settings()
    assert captured["path"] is None
