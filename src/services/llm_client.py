"""LLM client trừu tượng: đổi provider được, test/chạy offline được.

- `LLMClient`: giao diện tối thiểu (nhận prompt + schema Pydantic -> instance đã parse).
- `MockLLMClient`: trả về instance dựng sẵn, không gọi mạng (dùng cho test và `--mock`).
- `OpenAILLMClient`: gọi OpenAI thật, ép JSON, parse vào schema.
"""
from __future__ import annotations

import re
from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _extract_json(content: str) -> str:
    """Bóc khối JSON ngoài cùng từ đầu ra LLM (cắt code fence / lời dẫn)."""
    text = content.strip()
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text


class LLMClient(Protocol):
    def structured_completion(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        ...


class MockLLMClient:
    """LLM giả lập: trả về một instance dựng sẵn, bỏ qua prompt. Tất định, offline."""

    def __init__(self, response: BaseModel):
        self._response = response

    def structured_completion(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        if not isinstance(self._response, schema):
            raise TypeError(
                f"MockLLMClient được cấu hình trả {type(self._response).__name__} "
                f"nhưng agent yêu cầu {schema.__name__}"
            )
        return self._response


class OpenAILLMClient:
    """Gọi OpenAI Chat Completions, ép trả JSON và parse vào schema Pydantic."""

    def __init__(self, model: str, api_key: str, base_url: str = ""):
        from openai import OpenAI

        self._model = model
        self._client = OpenAI(api_key=api_key or "local", base_url=base_url or None)

    def structured_completion(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        json_schema = schema.model_json_schema()
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "schema": json_schema},
            },
            temperature=0,
        )
        content = resp.choices[0].message.content or "{}"
        return schema.model_validate_json(_extract_json(content))
