"""Cấu hình từ biến môi trường / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

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
    """Đọc .env (hoặc .env.<profile>) làm cấu hình ưu tiên cho lần chạy này."""
    # Người dùng chọn provider/model trong tệp cấu hình của dự án.  Nếu không
    # override, một OPENAI_API_KEY cũ trong biến môi trường Windows sẽ âm thầm
    # được gửi sang provider khác (ví dụ DeepSeek) và dẫn tới lỗi 401 khó hiểu.
    requested = Path(f".env.{profile}") if profile else Path(".env")
    # The UI exposes a "cloud" profile, but a project may intentionally use
    # only .env.  Fall back to it explicitly; otherwise an inherited Windows
    # OPENAI_API_KEY is retained and can be sent to the wrong provider.
    load_dotenv(requested if requested.exists() else Path(".env"), override=True)
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=(os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "").strip(),
    )
