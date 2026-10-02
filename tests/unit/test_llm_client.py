"""Test parse JSON bền hơn (_extract_json) + MockLLMClient, đều offline.

Model local (LM Studio/Ollama) hay bọc JSON trong ```json ... ``` hoặc kèm lời dẫn,
nên _extract_json phải bóc được khối JSON trước khi validate.
"""
import types

import pytest
from pydantic import BaseModel

from src.services.llm_client import (
    MockLLMClient,
    OpenAILLMClient,
    _extract_json,
    _is_response_format_error,
)


class _Toy(BaseModel):
    a: int
    b: str


class _FakeCompletions:
    """Giả lập openai client.chat.completions: ghi lại loại response_format đã thử."""

    def __init__(self, fail_types=(), error_msg="'response_format.type' must be 'json_object'"):
        self.fail_types = set(fail_types)
        self.error_msg = error_msg
        self.calls = []

    def create(self, *, model, messages, response_format, temperature):
        self.calls.append(response_format["type"])
        if response_format["type"] in self.fail_types:
            raise RuntimeError(self.error_msg)
        msg = types.SimpleNamespace(content='{"a": 7, "b": "ok"}')
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


class _FakeClient:
    def __init__(self, fail_types=(), error_msg="'response_format.type' must be 'json_object'"):
        self.chat = types.SimpleNamespace(completions=_FakeCompletions(fail_types, error_msg))


def test_extract_json_plain():
    assert _extract_json('{"a": 1, "b": "x"}') == '{"a": 1, "b": "x"}'


def test_extract_json_strips_code_fence():
    raw = '```json\n{"a": 1, "b": "x"}\n```'
    out = _extract_json(raw)
    _Toy.model_validate_json(out)  # parse được
    assert out.strip() == '{"a": 1, "b": "x"}'


def test_extract_json_strips_prose():
    raw = 'Đây là kết quả phân tích:\n{"a": 1, "b": "x"}\nHy vọng giúp ích.'
    out = _extract_json(raw)
    assert out.startswith("{") and out.endswith("}")
    _Toy.model_validate_json(out)


def test_mock_client_returns_preset():
    toy = _Toy(a=5, b="hi")
    client = MockLLMClient(toy)
    assert client.structured_completion("s", "u", _Toy) is toy


def test_is_response_format_error():
    assert _is_response_format_error(RuntimeError("'response_format.type' must be 'json_object'"))
    assert _is_response_format_error(RuntimeError("json_schema is not supported"))
    assert not _is_response_format_error(RuntimeError("rate limit exceeded"))


def test_uses_json_schema_when_supported():
    client = _FakeClient(fail_types=())
    llm = OpenAILLMClient("m", "k", client=client)
    assert llm.structured_completion("sys", "usr", _Toy) == _Toy(a=7, b="ok")
    assert client.chat.completions.calls == ["json_schema"]  # không phải fallback


def test_falls_back_to_json_object_when_schema_rejected():
    client = _FakeClient(fail_types={"json_schema"})
    llm = OpenAILLMClient("m", "k", client=client)
    assert llm.structured_completion("sys", "usr", _Toy) == _Toy(a=7, b="ok")
    assert client.chat.completions.calls == ["json_schema", "json_object"]  # đã fallback


def test_non_response_format_error_propagates():
    client = _FakeClient(fail_types={"json_schema"}, error_msg="rate limit exceeded")
    llm = OpenAILLMClient("m", "k", client=client)
    with pytest.raises(RuntimeError, match="rate limit"):
        llm.structured_completion("sys", "usr", _Toy)
