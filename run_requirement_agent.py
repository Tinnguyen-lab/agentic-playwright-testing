"""CLI chạy Requirement Analysis Agent (slice đầu tiên).

Ví dụ:
    # Chạy offline với LLM giả lập (không cần API key):
    python run_requirement_agent.py --file datasets/reference/sample_requirements.md --mock

    # Chạy thật (cần .env có OPENAI_API_KEY):
    python run_requirement_agent.py --file tai_lieu.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.agents.requirement_agent import RequirementAnalysisAgent
from src.models.requirement import (
    AmbiguityFinding,
    AmbiguityType,
    RequirementAnalysisResult,
    RequirementExtraction,
    Severity,
    StructuredRequirement,
)
from src.services.document_loader import load_document
from src.services.llm_client import MockLLMClient, OpenAILLMClient
from src.utils.config import load_settings


def default_mock_extraction() -> RequirementExtraction:
    """Bản trích xuất giả lập khớp datasets/reference/sample_requirements.md (dùng cho --mock)."""
    return RequirementExtraction(
        requirements=[
            StructuredRequirement(
                title="Đăng nhập",
                actor="Người dùng",
                action="Nhập email và mật khẩu hợp lệ để đăng nhập",
                expected_outcome="Đăng nhập thành công và chuyển tới trang chủ; sai thì báo lỗi",
                source_excerpt="Người dùng nhập email và mật khẩu hợp lệ thì đăng nhập thành công...",
            ),
            StructuredRequirement(
                title="Tìm kiếm sản phẩm",
                actor="Người dùng",
                action="Tìm kiếm sản phẩm",
                expected_outcome="Hiển thị tối đa 10 kết quả/trang",
                source_excerpt="hệ thống phải phản hồi nhanh và hiển thị tối đa 10 kết quả",
                ambiguities=[
                    AmbiguityFinding(
                        type=AmbiguityType.VAGUE_QUANTIFIER,
                        description="'nhanh' không được định lượng (bao nhiêu ms?)",
                        source_excerpt="phản hồi nhanh",
                        suggestion="Định lượng: ví dụ 'phản hồi < 500ms cho 95% truy vấn'",
                    )
                ],
            ),
            StructuredRequirement(
                title="Xoá mục trong giỏ hàng",
                action="Xoá nhiều mục cùng lúc khỏi giỏ hàng",
                source_excerpt="Có thể xoá nhiều mục cùng lúc khỏi giỏ hàng.",
                ambiguities=[
                    AmbiguityFinding(
                        type=AmbiguityType.MISSING_ACTOR,
                        description="Không rõ vai trò nào được phép xoá",
                        source_excerpt="Có thể xoá nhiều mục",
                        suggestion="Nêu rõ chủ thể, ví dụ 'Người dùng đã đăng nhập'",
                    ),
                ],
            ),
            StructuredRequirement(
                title="Trang kết quả tìm kiếm",
                actor="Người dùng",
                action="Hiển thị tất cả sản phẩm khớp từ khoá",
                expected_outcome="Người dùng thấy toàn bộ sản phẩm khớp để so sánh",
                source_excerpt="Trang kết quả tìm kiếm hiển thị tất cả sản phẩm khớp với từ khoá",
            ),
        ],
        global_ambiguities=[
            AmbiguityFinding(
                type=AmbiguityType.CONFLICT,
                description="UC-2 giới hạn 'tối đa 10' kết quả nhưng UC-4 nói hiển thị 'tất cả'",
                source_excerpt="UC-2: tối đa 10 kết quả / UC-4: hiển thị tất cả sản phẩm",
                severity=Severity.HIGH,
            )
        ],
    )


def _print_summary(result: RequirementAnalysisResult, *, mock: bool) -> None:
    tag = " [MOCK - kết quả giả lập]" if mock else ""
    print(f"\n=== KẾT QUẢ PHÂN TÍCH: {result.source_name}{tag} ===")
    print(f"Model: {result.model_used} | Số yêu cầu: {len(result.requirements)} "
          f"| Điểm mơ hồ: {result.ambiguous_count}\n")

    for req in result.requirements:
        flag = "⚠ MƠ HỒ" if req.is_ambiguous else "✓ rõ"
        print(f"[{req.id}] {req.title}  ({flag})")
        print(f"    actor           : {req.actor or '—'}")
        print(f"    action          : {req.action}")
        print(f"    expected_outcome: {req.expected_outcome or '—'}")
        for amb in req.ambiguities:
            print(f"    ↳ ambiguity [{amb.type.value}] {amb.description}")
            if amb.suggestion:
                print(f"        gợi ý: {amb.suggestion}")
        print()

    if result.global_ambiguities:
        print("--- Mâu thuẫn / mơ hồ toàn cục ---")
        for amb in result.global_ambiguities:
            print(f"  [{amb.type.value}] {amb.description}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Requirement Analysis Agent")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="Đường dẫn tài liệu (TXT/MD)")
    src.add_argument("--text", help="Nội dung yêu cầu dán trực tiếp")
    parser.add_argument("--mock", action="store_true", help="Dùng LLM giả lập (offline)")
    parser.add_argument("--out", default="result.json", help="File JSON đầu ra")
    parser.add_argument("--profile", help="Hồ sơ .env: 'cloud' -> đọc .env.cloud (mặc định đọc .env)")
    args = parser.parse_args(argv)

    if args.file:
        doc = load_document(args.file)
        text, source_name = doc.text, doc.source_name
    else:
        text = args.text
        source_name = "inline"

    if args.profile and not Path(f".env.{args.profile}").exists():
        print(f"[!] Không thấy .env.{args.profile} -> dùng .env/biến môi trường mặc định.")
    settings = load_settings(args.profile)
    use_mock = args.mock or not settings.use_real_llm

    if use_mock:
        if not args.mock:
            print("[i] Không có OPENAI_API_KEY/OPENAI_BASE_URL -> tự chuyển sang chế độ --mock (offline).")
        agent = RequirementAnalysisAgent(MockLLMClient(default_mock_extraction()), model_name="mock")
    else:
        client = OpenAILLMClient(
            settings.openai_model, settings.openai_api_key, settings.openai_base_url
        )
        if settings.openai_base_url:
            local = "localhost" in settings.openai_base_url or "127.0.0.1" in settings.openai_base_url
            print(f"[i] LLM {'local' if local else 'cloud'}: {settings.openai_base_url} | model={settings.openai_model}")
        else:
            print(f"[i] OpenAI (trả phí) | model={settings.openai_model}")
        agent = RequirementAnalysisAgent(client, model_name=settings.openai_model)

    result = agent.analyze(text, source_name=source_name)
    _print_summary(result, mock=use_mock)

    Path(args.out).write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(f"\n[✓] Đã ghi JSON: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
