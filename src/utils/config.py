"""Cấu hình từ biến môi trường / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class Settings:
    openai_api_key: str
    openai_model: str
    openai_base_url: str = ""

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def use_real_llm(self) -> bool:
        """Có thể gọi LLM thật không: cần key (OpenAI) HOẶC base_url (local, không cần key thật)."""
        return bool(self.openai_api_key) or bool(self.openai_base_url)


def load_settings(profile: str | None = None) -> Settings:
    """Đọc .env (hoặc .env.<profile> nếu chỉ định) rồi lấy OPENAI_* config."""
    load_dotenv(f".env.{profile}" if profile else None)
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=(os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "").strip(),
    )
