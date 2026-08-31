"""LLM client trừu tượng: đổi provider được, test/chạy offline được.

- `LLMClient`: giao diện tối thiểu (nhận prompt + schema Pydantic -> instance đã parse).
- `MockLLMClient`: trả về instance dựng sẵn, không gọi mạng (dùng cho test và `--mock`).
- `OpenAILLMClient`: gọi OpenAI thật, ép JSON, parse vào schema.
"""
from __future__ import annotations

import json
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


def _is_response_format_error(exc: Exception) -> bool:
    """True nếu lỗi do backend không hỗ trợ kiểu response_format đang dùng (vd DeepSeek từ chối json_schema)."""
    msg = str(exc).lower()
    return "response_format" in msg or "json_schema" in msg


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

    def __init__(self, model: str, api_key: str, base_url: str = "", client=None):
        self._model = model
        if client is not None:
            self._client = client
        else:
            from openai import OpenAI

            self._client = OpenAI(api_key=api_key or "local", base_url=base_url or None)

    def structured_completion(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        json_schema = schema.model_json_schema()
        try:
            content = self._call(
                system_prompt,
                user_prompt,
                {"type": "json_schema", "json_schema": {"name": schema.__name__, "schema": json_schema}},
            )
        except Exception as exc:
            if not _is_response_format_error(exc):
                raise
            hint = "Chỉ trả JSON hợp lệ khớp schema sau:\n" + json.dumps(json_schema, ensure_ascii=False)
            content = self._call(f"{system_prompt}\n\n{hint}", user_prompt, {"type": "json_object"})
        return schema.model_validate_json(_extract_json(content))

    def _call(self, system_prompt: str, user_prompt: str, response_format: dict) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=response_format,
            temperature=0,
        )
        return resp.choices[0].message.content or "{}"
