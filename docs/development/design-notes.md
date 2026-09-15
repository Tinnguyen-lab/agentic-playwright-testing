# Design Notes — Requirement Analysis Agent

> Ghi lý do các quyết định thiết kế (rationale) để code giữ gọn. Đọc file này khi cần hiểu
> "vì sao làm thế". Cập nhật khi thiết kế đổi.

## 1. LLM tách sau interface (`src/services/llm_client.py`)
- `LLMClient` (Protocol) — giao diện tối thiểu: `structured_completion(system, user, schema) -> instance`.
- `MockLLMClient` trả instance dựng sẵn → test/chạy **offline, tất định**, không tốn token.
- `OpenAILLMClient` gọi endpoint tương thích OpenAI.
- **Vì sao:** đổi provider (OpenAI/DeepSeek/LM Studio/Ollama) không phải sửa agent; test không cần mạng.

## 2. Structured output = `response_format=json_schema` (không phải `json_object`)
- **Vì sao:** LM Studio (bản đang dùng) **từ chối** `json_object`, chỉ nhận `json_schema` hoặc `text`. OpenAI (gpt-4o+) và DeepSeek đều nhận `json_schema`. Nó ép cấu trúc ở **mức grammar (GBNF)** → model buộc sinh JSON đúng field/kiểu.

## 3. Bỏ "schema_hint" khỏi prompt
- Trước đây schema JSON bị nhét cả trong system prompt **và** `response_format` (gửi 2 lần).
- Đã bỏ bản trong prompt → **tiết kiệm ~35% input token/lần** (đo bằng tiktoken). Grammar của `response_format` vẫn ép cấu trúc nên không mất gì về mặt hợp lệ.
- **Lưu ý (đã xử lý):** khi bỏ, Gemma dồn ambiguity xuống `global_ambiguities`. Đã thêm 1 dòng vào `SYSTEM_PROMPT` yêu cầu gắn ambiguity theo từng requirement → micro-F1 nhảy **0.07 → 0.73** (xem `eval-results.md`).

## 4. `_extract_json` — parse bền hơn
- Model local hay bọc JSON trong ```` ```json … ``` ```` hoặc kèm lời dẫn → hàm cắt code-fence / lấy khối `{ … }` ngoài cùng trước khi validate. An toàn cho cả cloud.

## 5. `base_url` + `use_real_llm` (`src/utils/config.py`)
- `OPENAI_BASE_URL` trỏ tới endpoint local (LM Studio `:1234/v1`, Ollama `:11434/v1`).
- Local **không cần key thật** → SDK vẫn đòi chuỗi khác rỗng nên truyền giá trị giả (`"local"`).
- `use_real_llm` = có key **hoặc** có base_url; nếu không có gì → tự chuyển `--mock`.

## 6. Switch nhanh local ↔ cloud: `--profile`
- `load_settings(profile)` đọc `.env.<profile>` thay cho `.env`. Giữ `.env` = local, thêm `.env.cloud` = DeepSeek/OpenAI. Chạy `--profile cloud` để đổi. Cả hai file bị `.gitignore` bỏ qua → key không lọt git.

## 7. Gán ID tuần tự `REQ-001…` (`src/agents/requirement_agent.py`)
- Hệ thống tự đánh ID theo thứ tự, **bỏ qua ID do LLM tự đặt** → traceable & tất định (LLM đặt ID không ổn định).

## 8. Fail-safe input rỗng
- Tài liệu rỗng → trả kết quả rỗng, **không gọi LLM**, không văng lỗi (fail closed).

## 9. Document parsing (`src/services/document_loader.py`)
- Dispatch theo đuôi: `.docx` (python-docx, nối paragraph), `.pdf` (pymupdf, chèn mốc `[trang N]` để truy vết nguồn), `.txt/.md` (đọc thẳng). Đuôi lạ → `ValueError` rõ ràng.

## 10. Đánh giá định lượng (`src/evaluation/`)
- **Ground truth = chèn khuyết tật có chủ đích** (`datasets/reference/ambiguity_eval`): mỗi UC có nhãn loại mơ hồ biết trước + vài UC **sạch** để đo over-flag/precision.
- **Đơn vị so khớp:** cặp *(requirement, loại mơ hồ)*. Căn predicted↔gold **theo thứ tự UC** (agent đánh REQ-001.. cùng thứ tự). Lệch số requirement → đếm `count_mismatches`; requirement thừa/thiếu vẫn tính FP/FN.
- Metrics: P/R/F1 **theo từng loại**, micro (gộp) + macro (trung bình loại), tỉ lệ over-flag trên requirement sạch, conflict xử lý như một loại ở `global_ambiguities`.

## 11. Chọn model (quan sát)
- `qwen2.5-coder-7b`: yếu (dồn global, không tách field). `qwen2.5-7b-instruct`: khá hơn nhưng over-flag, bỏ sót conflict. **`gemma-4-12b` (local, GPU 8GB)**: tách field tốt, bắt được conflict → mặc định local. Cloud **DeepSeek** cho chất lượng ~gpt-4o mà rẻ, dùng khi cần đối chiếu.
- Chi phí cloud: xem ước tính token × giá trong báo cáo slice; local = 0đ.
