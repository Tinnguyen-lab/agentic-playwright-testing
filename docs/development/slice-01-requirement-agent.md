# Báo cáo: Slice 1 — Requirement Analysis Agent

> Ghi nhớ tiến độ hiện thực agent đầu tiên của pipeline (nhận tài liệu yêu cầu → sinh
> *structured requirements* + *ambiguity findings*). Cập nhật: 2026-07-29.

---

## 1. Tổng quan

Đây là **lát cắt dọc (vertical slice) đầu tiên** biến thiết kế trong
[docs/architecture/architecture_v0.1.md](../architecture/architecture_v0.1.md) thành code chạy được.

- **Đầu vào:** văn bản tài liệu yêu cầu (TXT/MD).
- **Đầu ra:** danh sách yêu cầu đã cấu trúc (actor / precondition / action / expected_outcome / constraints) + các điểm **mơ hồ** được phân loại theo rubric, kèm trích đoạn nguồn.
- **Phạm vi cố ý tối giản:** chỉ agent — chưa DB (SQL Server), chưa Streamlit, chưa parser DOCX/PDF, chưa async.
- **Chạy được 3 chế độ:** offline giả lập (`--mock`), **AI local (LM Studio/Ollama)** miễn phí, hoặc OpenAI thật.

---

## 2. Trạng thái Git

- **Nhánh:** `feature/requirement-agent` (tách từ `develop`).
- **Đã commit** `8766f65` — 15 file, +560 dòng: toàn bộ agent lõi + test.
- **Chưa commit** (phần bổ sung *chạy bằng AI local*): sửa `llm_client.py`, `config.py`, `run_requirement_agent.py`, `.env.example` + thêm 2 file test (`test_config.py`, `test_llm_client.py`).

---

## 3. Danh sách file & chức năng

| File | Chức năng |
|------|-----------|
| `src/models/requirement.py` | Các model Pydantic (structured output). Gồm `AmbiguityType` (7 loại), `Severity`, `AmbiguityFinding`, `StructuredRequirement` (có `is_ambiguous` suy ra tự động), `RequirementExtraction`, `RequirementAnalysisResult`. |
| `src/services/llm_client.py` | Trừu tượng LLM. `LLMClient` (Protocol); `MockLLMClient` (trả kết quả dựng sẵn — test/chạy offline); `OpenAILLMClient` (gọi endpoint tương thích OpenAI, hỗ trợ `base_url` local, ép `json_schema`, `_extract_json` bóc JSON khi model bọc code-fence). |
| `src/agents/requirement_agent.py` | `RequirementAnalysisAgent`. Chứa `SYSTEM_PROMPT` (vai trò analyst, luật **không bịa**, gắn cờ mơ hồ theo rubric, không tự làm đầy phần thiếu). `analyze()` dựng prompt → gọi LLM → hậu xử lý (gán ID `REQ-001…`, metadata) → trả kết quả. Input rỗng không crash. |
| `src/utils/config.py` | `Settings` + `load_settings()` đọc `.env`. Khoá: `OPENAI_API_KEY`, `OPENAI_MODEL` (mặc định `gpt-4o-mini`), `OPENAI_BASE_URL`. Property `use_real_llm` = có key **hoặc** base_url. |
| `run_requirement_agent.py` | CLI: `--file`/`--text`, `--mock`, `--out`. Tự chọn backend: có base_url → LLM local; có key → OpenAI; không có gì → tự chuyển `--mock`. In tóm tắt dễ đọc + ghi JSON. |
| `datasets/reference/sample_requirements.md` | Tài liệu mẫu 4 use case, **cố tình cài mơ hồ** (định lượng "nhanh", thiếu actor, mâu thuẫn "tối đa 10" vs "tất cả") để demo rubric. |
| `tests/unit/test_requirement_models.py` | 3 test: validate enum, `is_ambiguous`, round-trip JSON. |
| `tests/unit/test_requirement_agent.py` | 3 test: gán ID/metadata, phát hiện đúng *loại* ambiguity, input rỗng an toàn (dùng `MockLLMClient`). |
| `tests/unit/test_config.py` | 4 test: đọc `OPENAI_BASE_URL`; `use_real_llm` đúng khi chỉ có base_url / chỉ có key / trống. |
| `tests/unit/test_llm_client.py` | 4 test: `_extract_json` bóc JSON khi bị bọc ```` ```json ```` / kèm lời dẫn; `MockLLMClient`. |
| `conftest.py` | Thêm gốc repo vào `sys.path` để `import src...` chạy trên Windows. |
| `.env.example` | Bổ sung `OPENAI_BASE_URL` + khối cấu hình mẫu LM Studio / Ollama. |

---

## 4. Nguyên tắc thiết kế đã bám (theo architecture v0.1)

- **Structured output:** agent trả Pydantic, không free-form text.
- **Traceable:** mỗi requirement & ambiguity mang `source_excerpt` + ID `REQ-xxx`.
- **Agent chỉ *phát hiện* mơ hồ,** không tự đánh dấu đã giải quyết, không tự làm đầy phần thiếu (chờ người phê duyệt — human-in-the-loop).
- **Reproducible:** lưu `model_used`, `created_at`.
- **LLM tách sau interface** → test tất định (MockLLMClient), đổi provider không sửa agent.
- **Fail-safe:** input rỗng → trả kết quả rỗng, không văng lỗi.

---

## 5. Rubric phân loại mơ hồ (điểm novelty)

7 loại: `MISSING_ACTOR`, `MISSING_PRECONDITION`, `VAGUE_QUANTIFIER`,
`MISSING_EXPECTED_OUTCOME`, `UNDERSPECIFIED_ACTION`, `CONFLICT`, `OTHER`.
Mỗi phát hiện có: *loại + mô tả + trích đoạn nguồn + gợi ý sửa*. Đây là phần chưa
nguồn nào trong 12 tài liệu khảo sát hiện thực (xem
[research_gap_v0.1](../literature-review/research_gap_v0.1.md)).

---

## 6. Cách chạy

```powershell
# A. Kiểm thử tự động (offline, không tốn token)
python -m pytest tests/unit -q            # 14 passed

# B. Demo giả lập (offline)
python run_requirement_agent.py --file datasets/reference/sample_requirements.md --mock

# C. Chạy thật bằng AI local (LM Studio) — điền .env rồi bỏ --mock
#   OPENAI_BASE_URL=http://localhost:1234/v1
#   OPENAI_MODEL=qwen2.5-coder-7b-instruct   (nên đổi sang qwen2.5-7b-INSTRUCT để phân tích tốt hơn)
#   OPENAI_API_KEY=lm-studio
python run_requirement_agent.py --file datasets/reference/sample_requirements.md
```

**Lưu ý AI local:** phải bật *Local Server* trong LM Studio (Settings → Local Model API →
Running) trước khi chạy. Bản LM Studio này chỉ nhận `response_format=json_schema` (đã xử lý
trong code). Model `-coder` cho kết quả nông với văn bản tiếng Việt → dùng bản `-instruct`
hoặc model lớn hơn để trích xuất field chính xác hơn (đây là chuyện chọn model, không phải code).

---

## 7. Kết quả kiểm thử

- **Đơn vị:** 14/14 test xanh (6 gốc + 8 bổ sung), theo TDD RED→GREEN.
- **Tích hợp thật:** đã chạy end-to-end qua LM Studio (`qwen2.5-coder-7b-instruct` tại
  `localhost:1234`) → trả JSON hợp lệ, đúng cấu trúc.

---

## 8. Ngoài phạm vi / việc kế tiếp

Parser DOCX/PDF · lưu SQL Server (SQLAlchemy/Alembic) · Streamlit UI · Approval &
Traceability service · Test Design Agent (agent thứ 2) · async.
