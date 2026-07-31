"""Test parse JSON bền hơn (_extract_json) + MockLLMClient, đều offline.

Model local (LM Studio/Ollama) hay bọc JSON trong ```json ... ``` hoặc kèm lời dẫn,
nên _extract_json phải bóc được khối JSON trước khi validate.
"""
from pydantic import BaseModel

from src.services.llm_client import MockLLMClient, _extract_json


class _Toy(BaseModel):
    a: int
    b: str


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
