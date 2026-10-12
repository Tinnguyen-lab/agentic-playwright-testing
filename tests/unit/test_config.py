"""Configuration loading must not retain a stale parent-process API key."""
from src.utils.config import load_settings


def test_missing_profile_falls_back_to_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=project-key\nOPENAI_MODEL=deepseek-chat\nOPENAI_BASE_URL=https://api.deepseek.com\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "stale-parent-key")

    settings = load_settings("cloud")

    assert settings.openai_api_key == "project-key"
    assert settings.openai_model == "deepseek-chat"
