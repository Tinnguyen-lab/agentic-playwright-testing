"""Tiện ích chung cho các CLI agent: dựng LLM client theo .env/profile (mock hoặc thật)."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from src.services.llm_client import LLMClient, MockLLMClient, OpenAILLMClient
from src.utils.config import load_settings


def resolve_client(profile: str | None, mock: bool, mock_response: BaseModel) -> tuple[LLMClient, str]:
    """Trả (client, model_name). Dùng MockLLMClient(mock_response) khi --mock hoặc thiếu cấu hình LLM."""
    if profile and not Path(f".env.{profile}").exists():
        print(f"[!] Không thấy .env.{profile} -> dùng .env/mặc định.")
    settings = load_settings(profile)

    if mock or not settings.use_real_llm:
        if not mock:
            print("[i] Không có cấu hình LLM -> chế độ --mock (offline).")
        return MockLLMClient(mock_response), "mock"

    client = OpenAILLMClient(settings.openai_model, settings.openai_api_key, settings.openai_base_url)
    base = settings.openai_base_url
    where = "OpenAI" if not base else ("local" if ("localhost" in base or "127.0.0.1" in base) else "cloud")
    print(f"[i] LLM {where}: {base or 'api.openai.com'} | model={settings.openai_model}")
    return client, settings.openai_model
