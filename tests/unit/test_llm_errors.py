from pydantic import BaseModel, ValidationError

from src.services.llm_errors import llm_failure_message


class _Required(BaseModel):
    value: int


def test_validation_failure_does_not_blame_api_key():
    try:
        _Required.model_validate({"value": "not a number"})
    except ValidationError as exc:
        message = llm_failure_message(exc)
    assert "JSON" in message
    assert "API key" not in message


def test_auth_and_quota_messages_are_distinct():
    class ProviderError(Exception):
        def __init__(self, status_code):
            self.status_code = status_code

    assert "API key" in llm_failure_message(ProviderError(401))
    assert "quota" in llm_failure_message(ProviderError(402))
    assert "HTTP 429" in llm_failure_message(ProviderError(429))
