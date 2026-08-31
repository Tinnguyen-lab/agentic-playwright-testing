"""Test RequirementAnalysisAgent với MockLLMClient (offline, tất định)."""
from src.agents.requirement_agent import RequirementAnalysisAgent
from src.models.requirement import (
    AmbiguityFinding,
    AmbiguityType,
    RequirementExtraction,
    StructuredRequirement,
)
from src.services.llm_client import MockLLMClient


def _sample_extraction() -> RequirementExtraction:
    """Bản trích xuất giả lập: 1 yêu cầu rõ, 2 yêu cầu mơ hồ, 1 mâu thuẫn toàn cục."""
    return RequirementExtraction(
        requirements=[
            StructuredRequirement(
                title="Đăng nhập",
                actor="Người dùng",
                action="Đăng nhập bằng email và mật khẩu hợp lệ",
                expected_outcome="Được chuyển tới trang chủ",
                source_excerpt="Người dùng nhập email và mật khẩu hợp lệ...",
            ),
            StructuredRequirement(
                title="Tìm kiếm sản phẩm",
                action="Tìm kiếm sản phẩm",
                source_excerpt="hệ thống phải phản hồi nhanh",
                ambiguities=[
                    AmbiguityFinding(
                        type=AmbiguityType.VAGUE_QUANTIFIER,
                        description="'nhanh' không được định lượng (bao nhiêu ms?)",
                        source_excerpt="phản hồi nhanh",
                    )
                ],
            ),
            StructuredRequirement(
                title="Xoá mục giỏ hàng",
                action="Xoá nhiều mục cùng lúc",
                source_excerpt="Có thể xoá nhiều mục cùng lúc",
                ambiguities=[
                    AmbiguityFinding(
                        type=AmbiguityType.MISSING_ACTOR,
                        description="Không rõ vai trò nào được phép xoá",
                        source_excerpt="Có thể xoá nhiều mục",
                    )
                ],
            ),
        ],
        global_ambiguities=[
            AmbiguityFinding(
                type=AmbiguityType.CONFLICT,
                description="UC-2 giới hạn 10 kết quả nhưng UC-4 nói hiển thị tất cả",
                source_excerpt="tối đa 10 ... / ... tất cả",
            )
        ],
    )


def _agent() -> RequirementAnalysisAgent:
    return RequirementAnalysisAgent(MockLLMClient(_sample_extraction()), model_name="mock")


def test_agent_assigns_ids_and_metadata():
    result = _agent().analyze("nội dung tài liệu", source_name="sample.md")
    assert [r.id for r in result.requirements] == ["REQ-001", "REQ-002", "REQ-003"]
    assert result.source_name == "sample.md"
    assert result.model_used == "mock"
    assert result.created_at is not None


def test_agent_detects_ambiguity_types():
    result = _agent().analyze("nội dung tài liệu", source_name="sample.md")
    types = {a.type for r in result.requirements for a in r.ambiguities}
    assert AmbiguityType.VAGUE_QUANTIFIER in types
    assert AmbiguityType.MISSING_ACTOR in types
    assert result.requirements[0].is_ambiguous is False  # UC-1 rõ ràng
    assert result.requirements[1].is_ambiguous is True    # UC-2 mơ hồ
    assert any(a.type == AmbiguityType.CONFLICT for a in result.global_ambiguities)


def test_agent_empty_input_no_crash():
    result = _agent().analyze("   ", source_name="empty.md")
    assert result.requirements == []
    assert result.source_name == "empty.md"
