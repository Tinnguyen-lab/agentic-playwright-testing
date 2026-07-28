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

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)


def load_settings() -> Settings:
    """Đọc .env (nếu có) rồi lấy OPENAI_API_KEY / OPENAI_MODEL."""
    load_dotenv()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=(os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL),
    )
