"""Test Pydantic models cho Requirement Analysis Agent."""
from datetime import datetime, timezone

from src.models.requirement import (
    AmbiguityFinding,
    AmbiguityType,
    RequirementAnalysisResult,
    StructuredRequirement,
)


def test_ambiguity_type_values():
    assert AmbiguityType.VAGUE_QUANTIFIER.value == "vague_quantifier"
    assert AmbiguityType("missing_actor") is AmbiguityType.MISSING_ACTOR


def test_is_ambiguous_computed():
    req_clear = StructuredRequirement(title="Đăng nhập", action="Người dùng đăng nhập")
    assert req_clear.is_ambiguous is False

    req_amb = StructuredRequirement(
        title="Tìm kiếm",
        action="Tìm sản phẩm",
        ambiguities=[
            AmbiguityFinding(
                type=AmbiguityType.VAGUE_QUANTIFIER,
                description="'nhanh' không định lượng",
                source_excerpt="phản hồi nhanh",
            )
        ],
    )
    assert req_amb.is_ambiguous is True


def test_result_json_roundtrip():
    result = RequirementAnalysisResult(
        source_name="doc.md",
        requirements=[StructuredRequirement(id="REQ-001", title="X", action="do x")],
        model_used="mock",
        created_at=datetime.now(timezone.utc),
    )
    data = result.model_dump_json()
    loaded = RequirementAnalysisResult.model_validate_json(data)

    assert loaded.source_name == "doc.md"
    assert loaded.requirements[0].id == "REQ-001"
    assert loaded.requirements[0].is_ambiguous is False
