"""LLM client trừu tượng: đổi provider được, test/chạy offline được.

- `LLMClient`: giao diện tối thiểu (nhận prompt + schema Pydantic -> instance đã parse).
- `MockLLMClient`: trả về instance dựng sẵn, không gọi mạng (dùng cho test và `--mock`).
- `OpenAILLMClient`: gọi OpenAI thật, ép JSON, parse vào schema.
"""
from __future__ import annotations

import json
from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


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

    def __init__(self, model: str, api_key: str):
        from openai import OpenAI  # import lười: chỉ cần khi thực sự gọi OpenAI

        self._model = model
        self._client = OpenAI(api_key=api_key)

    def structured_completion(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        schema_hint = (
            "Chỉ trả về JSON hợp lệ, không kèm giải thích, khớp JSON schema sau:\n"
            + json.dumps(schema.model_json_schema(), ensure_ascii=False)
        )
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\n{schema_hint}"},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = resp.choices[0].message.content or "{}"
        return schema.model_validate_json(content)
