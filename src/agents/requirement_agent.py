"""Requirement Analysis Agent (architecture v0.1, mục 5.4).

Vào: text tài liệu. Ra: RequirementAnalysisResult (structured requirements + ambiguity findings).
Nguyên tắc: KHÔNG bịa/không làm đầy phần thiếu; CHỈ gắn cờ mơ hồ; trích nguồn cho mọi mục.
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.models.requirement import RequirementAnalysisResult, RequirementExtraction
from src.services.llm_client import LLMClient

SYSTEM_PROMPT = """\
Bạn là chuyên viên phân tích yêu cầu phần mềm. Nhiệm vụ: đọc tài liệu yêu cầu và tách thành
danh sách yêu cầu CÓ CẤU TRÚC, đồng thời PHÁT HIỆN các điểm mơ hồ.

Với mỗi yêu cầu, trích: title, actor (vai trò), precondition, action, expected_outcome,
constraints, và source_excerpt (đoạn văn gốc làm bằng chứng).

QUY TẮC BẮT BUỘC:
- KHÔNG bịa thông tin. Nếu tài liệu thiếu, để trống (null) và tạo một ambiguity finding.
- KHÔNG tự "làm đầy" phần thiếu bằng giả định.
- Gắn cờ mơ hồ theo rubric (type):
  * missing_actor: không rõ ai thực hiện.
  * missing_precondition: thiếu điều kiện tiên quyết.
  * vague_quantifier: định lượng mơ hồ ("nhanh", "phù hợp", "nhiều", "đủ").
  * missing_expected_outcome: không rõ kết quả mong đợi.
  * underspecified_action: hành động mô tả chưa đủ để kiểm thử.
  * conflict: mâu thuẫn giữa các yêu cầu (đưa vào global_ambiguities).
  * other: loại khác.
- Mỗi ambiguity phải có description (lý do) và source_excerpt (trích đoạn liên quan).
- Gắn MỖI ambiguity vào đúng requirement chứa nó (trường "ambiguities" của requirement đó).
  CHỈ mâu thuẫn giữa NHIỀU yêu cầu (conflict) mới đưa vào "global_ambiguities".

ĐỘ CHÍNH XÁC (giảm gắn cờ nhầm — QUAN TRỌNG):
- CHỈ gắn cờ khi trường thực sự VẮNG MẶT hoặc mơ hồ RÕ RÀNG. Nếu thông tin suy ra được hợp lý
  từ source_excerpt thì KHÔNG gắn cờ. Không đủ chắc thì KHÔNG gắn.
- missing_precondition: chỉ gắn khi yêu cầu HOÀN TOÀN không nêu điều kiện tiên quyết nào VÀ
  hành động thực sự đòi hỏi một điều kiện. Câu ngắn nhưng đủ nghĩa thì KHÔNG gắn.
- missing_expected_outcome: chỉ gắn khi KHÔNG thể xác định kết quả mong đợi từ mô tả. Nếu
  kết quả đã ngụ ý rõ thì KHÔNG gắn.
- Phân vân với precondition/outcome: ƯU TIÊN KHÔNG gắn.
- Vẫn gắn đầy đủ các ca RÕ RÀNG: missing_actor, vague_quantifier, conflict, underspecified_action
  khi có căn cứ (không bỏ sót).

Trả về JSON gồm: requirements[] và global_ambiguities[]. KHÔNG gán ID (hệ thống tự gán).\
"""


class RequirementAnalysisAgent:
    def __init__(self, llm: LLMClient, model_name: str = "unknown"):
        self._llm = llm
        self._model_name = model_name

    def analyze(self, document_text: str, source_name: str) -> RequirementAnalysisResult:
        if not document_text or not document_text.strip():
            return self._empty_result(source_name)

        user_prompt = self._build_user_prompt(document_text)
        extraction = self._llm.structured_completion(
            SYSTEM_PROMPT, user_prompt, RequirementExtraction
        )

        for index, requirement in enumerate(extraction.requirements, start=1):
            requirement.id = f"REQ-{index:03d}"

        return RequirementAnalysisResult(
            source_name=source_name,
            requirements=extraction.requirements,
            global_ambiguities=extraction.global_ambiguities,
            model_used=self._model_name,
            created_at=datetime.now(timezone.utc),
        )

    def _empty_result(self, source_name: str) -> RequirementAnalysisResult:
        return RequirementAnalysisResult(
            source_name=source_name,
            requirements=[],
            global_ambiguities=[],
            model_used=self._model_name,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _build_user_prompt(document_text: str) -> str:
        return (
            "Phân tích tài liệu yêu cầu dưới đây và trả về JSON theo hướng dẫn.\n\n"
            "===== TÀI LIỆU =====\n"
            f"{document_text}\n"
            "===== HẾT ====="
        )
