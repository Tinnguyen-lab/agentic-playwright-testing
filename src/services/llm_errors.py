"""Safe, actionable UI messages for LLM failures; never expose a token or raw response."""
from __future__ import annotations

from pydantic import ValidationError


def llm_failure_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return ("DeepSeek đã phản hồi nhưng JSON vẫn sai cấu trúc sau một lần thử hiệu chỉnh. "
                "Chưa lưu kết quả; hãy thử lại hoặc rút gọn tài liệu đầu vào.")
    status = getattr(exc, "status_code", None)
    if status == 401:
        return "DeepSeek từ chối API key (HTTP 401). Kiểm tra khóa trong .env."
    if status == 402:
        return "DeepSeek báo không đủ số dư/quota (HTTP 402). Kiểm tra tài khoản rồi thử lại."
    if status == 429:
        return "DeepSeek đang giới hạn số yêu cầu (HTTP 429). Chờ một lát rồi thử lại."
    if isinstance(status, int) and status >= 500:
        return f"DeepSeek đang lỗi phía máy chủ (HTTP {status}). Thử lại sau."
    if status is not None:
        return f"DeepSeek từ chối yêu cầu (HTTP {status}). Kiểm tra model và định dạng yêu cầu."
    if type(exc).__name__ in {"APIConnectionError", "APITimeoutError", "TimeoutError"}:
        return "Không kết nối được DeepSeek hoặc yêu cầu quá thời gian. Kiểm tra mạng rồi thử lại."
    return f"Không thể xử lý kết quả LLM ({type(exc).__name__}). Chưa lưu dữ liệu; hãy thử lại."
