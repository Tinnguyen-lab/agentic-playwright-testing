# Báo cáo Tuần 2–3

- Dự án: Agentic Playwright Testing
- Thời gian báo cáo: 2026-07-19 → 2026-08-01
- Giai đoạn: Triển khai vertical slice Requirement Analysis Agent — từ lõi (structured output + ambiguity theo rubric) đến chạy thật với LLM, bổ sung parser DOCX/PDF và bộ đánh giá định lượng cho RQ1
- Trạng thái chung: Hoàn thành hai bước của Requirement Agent; agent chạy thật với LLM; có số liệu định lượng sơ bộ. Chưa triển khai các agent phía sau, persistence và UI.

## 1. Mục tiêu tuần 2–3


1. Chốt Pydantic schema lõi cho Requirement và Ambiguity.
2. Xây Requirement Analysis Agent với structured output và ambiguity detection theo rubric.
3. Chạy được và test được offline khi nhóm chưa có OpenAI key.
4. Chạy agent với LLM thật trên tài liệu thật và bắt đầu đánh giá.
5. Bổ sung parser DOCX/PDF.
6. Xây bộ đánh giá định lượng và dataset gán nhãn để có số liệu cho RQ1.
7. Tập trung chiều sâu vào Requirement Analysis Agent và nền đánh giá định lượng

## 2. Công việc đã hoàn thành

### Requirement Agent

**2.1 Schema (Pydantic)**
- `AmbiguityType`: rubric 7 loại — `missing_actor`, `missing_precondition`, `vague_quantifier`, `missing_expected_outcome`, `underspecified_action`, `conflict`, `other`.
- `AmbiguityFinding` (type, description, source_excerpt, suggestion, severity); `StructuredRequirement` (id, title, actor, precondition, action, expected_outcome, constraints, source_excerpt, ambiguities, computed `is_ambiguous`).
- `RequirementExtraction` (đầu ra thô của LLM) và `RequirementAnalysisResult` (có ID, model_used, created_at, computed `ambiguous_count`). Ánh xạ domain entity theo architecture v0.1 (mục 10).

**2.2 LLM abstraction (tách provider, test offline)**
- `LLMClient` (Protocol); `MockLLMClient` (instance dựng sẵn → test/chạy offline, tất định); `OpenAILLMClient` (gọi API, ép JSON, validate schema).

**2.3 Requirement Analysis Agent**
- `SYSTEM_PROMPT`: luật KHÔNG bịa / KHÔNG tự làm đầy; gắn cờ mơ hồ theo rubric kèm lý do và trích nguồn.
- `analyze()`: dựng prompt → gọi LLM → gán ID `REQ-001..` tuần tự → trả kết quả kèm metadata. Fail-safe khi input rỗng.

**2.4 CLI và dataset mẫu**
- `run_requirement_agent.py`: `--file`/`--text`, `--mock`, `--out`; tự chuyển mock khi thiếu key; in tóm tắt và ghi JSON.
- `datasets/reference/sample_requirements.md`: 4 use case cố tình cài mơ hồ để kiểm chứng rubric.

**2.5 TDD**
- Viết test trước (RED) với `MockLLMClient` → hiện thực (GREEN). 6 unit test cho models và agent, chạy offline.

**2.6 Backend LLM: hỗ trợ cả cloud và local**
- `OpenAILLMClient` nhận `base_url` → dùng được cả LLM cloud (OpenAI/DeepSeek) lẫn server tương thích OpenAI chạy local (LM Studio `localhost:1234`, Ollama) mà không thêm dependency.
- `--profile` đọc `.env.<profile>` → chuyển nhanh giữa các cấu hình; `.env`/`.env.cloud` bị `.gitignore` bỏ qua nên key không lọt git.
- `use_real_llm` quyết định mock hay thật; `_extract_json` bóc JSON khi model bọc code-fence; `response_format=json_schema` (LM Studio chỉ nhận loại này) và bỏ schema lặp trong prompt → giảm khoảng 35% input token.

**2.7 Parser tài liệu**
- `document_loader.load_document()`: DOCX (python-docx), PDF (pymupdf, chèn mốc trang để truy vết), TXT/MD; xuất hiện đuôi lạ báo lỗi.

**2.8 Bộ đánh giá định lượng**
- `metrics`: đếm TP/FP/FN theo cặp (requirement, loại) → precision/recall/F1 theo loại, micro/macro, tỉ lệ over-flag.
- Dataset gán nhãn bằng **chèn khuyết tật có chủ đích**: 5 tài liệu, 15 yêu cầu, đủ 6 loại mơ hồ + yêu cầu sạch + 1 conflict toàn cục.
- `evaluator` (căn predicted↔gold theo thứ tự UC) + `evaluate_agent.py` → ghi JSON theo model và gộp thành bảng so sánh `eval-results.md`.

**2.9 Git**
- Nhánh `feature/requirement-agent` (tách từ `develop`); 4 commit và **push lên `origin`**; secrets không được track.

## 3. Sản phẩm tạo ra

| Sản phẩm | Đường dẫn | Trạng thái |
|---|---|---|
| Requirement/Ambiguity models | `src/models/requirement.py` | Hoàn thành |
| LLM client (Protocol/Mock/OpenAI, cloud+local) | `src/services/llm_client.py` | Hoàn thành |
| Requirement Analysis Agent | `src/agents/requirement_agent.py` | Hoàn thành |
| Config loader (profile cấu hình) | `src/utils/config.py` | Hoàn thành |
| CLI chạy agent | `run_requirement_agent.py` | Hoàn thành |
| Parser DOCX/PDF/TXT/MD | `src/services/document_loader.py` | Hoàn thành |
| Metrics + dataset loader + evaluator | `src/evaluation/` | Hoàn thành |
| CLI đánh giá | `evaluate_agent.py` | Hoàn thành |
| Dataset mẫu (cài mơ hồ) | `datasets/reference/sample_requirements.md` | Hoàn thành |
| Dataset gán nhãn (15 yêu cầu) | `datasets/reference/ambiguity_eval/` | Hoàn thành |
| Kết quả eval (JSON) | `datasets/processed/eval_*.json` | Sơ bộ (Gemma-12B) |
| Bảng kết quả đánh giá | `docs/development/eval-results.md` | Hoàn thành |
| Design notes | `docs/development/design-notes.md` | Hoàn thành |
| Báo cáo slice 1 và slice 2 | `docs/development/slice-01-...`, `slice-02-...` | Hoàn thành |
| Tài liệu tổng quan (primer) | `docs/learning/project-primer.md` | Hoàn thành |
| Unit tests | `tests/unit/` (models, agent, config, llm_client, parser, metrics, evaluator) | 29 test xanh |

## 4. Quyết định kỹ thuật

| ID | Quyết định | Lý do |
|---|---|---|
| TD-13 | LLM tách sau interface (Protocol) + MockLLMClient | Test/chạy offline, đổi provider không phải sửa agent |
| TD-14 | Agent output là Pydantic structured, không free-form | Validate, lưu trữ và tái lập được |
| TD-15 | Ambiguity theo rubric phân loại (loại + lý do + trích nguồn + gợi ý) | Điểm novelty; phục vụ RQ1 |
| TD-16 | Agent chỉ phát hiện mơ hồ, không tự làm đầy/giải quyết | Human-governed; chờ phê duyệt AG-01 |
| TD-17 | Gán ID `REQ-xxx` tuần tự, bỏ ID do LLM tự đặt | Traceable và tất định |
| TD-18 | Fail closed khi input rỗng/lỗi | An toàn |
| TD-19 | Dùng chung OpenAI SDK cho cloud và local qua `base_url` | Không thêm dependency; đổi backend chỉ đổi `.env`; giữ hướng cloud nhưng dev/eval được offline |
| TD-20 | `response_format=json_schema` thay `json_object` | Tương thích LM Studio; ép cấu trúc ở grammar; bỏ schema lặp tiết kiệm token |
| TD-21 | Ground truth bằng chèn khuyết tật có chủ đích | Nhãn khách quan, biết trước; đo được P/R/F1 |
| TD-22 | Đơn vị đo là cặp (requirement, loại); căn theo thứ tự UC | Định lượng chính xác theo từng loại |
| TD-23 | Dùng model local (Gemma-4-12B) cho phát triển và đánh giá sơ bộ trong kỳ |

## 5. Kết quả đánh giá sơ bộ (RQ1)

> Kết quả chạy trên **model local Gemma-4-12B** .Sẽ so sánh với LLM cloud (DeepSeek/OpenAI)

Ablation "chỉ dẫn đặt ambiguity" trên Gemma-4-12B (dataset 15 yêu cầu gán nhãn):

| Cấu hình | Micro-F1 | Macro-F1 | Recall |
|---|---|---|---|
| Trước (chưa nắn prompt) | 0.07 | 0.17 | 0.08 |
| Sau (thêm 1 dòng gắn ambiguity theo từng requirement) | **0.73** | **0.78** | **1.00** |

F1 theo loại (sau khi sửa): `missing_actor` 1.00 · `vague_quantifier` 1.00 · `conflict` 1.00 · `missing_expected_outcome` 0.75 · `underspecified_action` 0.67 · `missing_precondition` 0.25.

Nhận xét:
- Một chỉ dẫn prompt nhỏ nâng micro-F1 lên khoảng 10 lần — bộ đánh giá **định lượng hoá** được một lỗi tinh vi (model đặt ambiguity vào global thay vì gắn theo requirement).
- Sau khi sửa, recall đạt 1.00 (bắt hết khuyết tật chèn vào); mạnh ở `missing_actor`/`vague_quantifier`/`conflict`.
- Điểm yếu là precision ở `missing_precondition` và `missing_expected_outcome` (over-flag), một phần do model nhạy, một phần do gold hiện chỉ gán một khuyết tật cho mỗi yêu cầu.
- Con số phụ thuộc model local hiện dùng; cần đối chiếu với LLM cloud để kết luận vững hơn.

## 6. Vấn đề gặp phải và chưa giải quyết

| ID | Vấn đề | Mức ảnh hưởng | Hướng xử lý |
|---|---|---|---|
| OI-13 | Chưa nối database, UI và persistence | Trung bình | Cố ý để slice sau; hiện chạy JSON + CLI |
| OI-16 | Precision thấp ở `missing_precondition`/`missing_expected_outcome` | Trung bình | Tinh chỉnh prompt/calibration; dùng human-in-the-loop AG-01 lọc false positive |
| OI-17 | Nhãn gold còn chủ quan (1 khuyết tật/yêu cầu) | Trung bình | Nhóm review và sở hữu ground truth; mở rộng nhãn đa chiều |
| OI-18 | Kết quả đánh giá mới trên một model local, chưa đối chiếu cloud | Cao | Chạy `--profile cloud` (DeepSeek/OpenAI) khi có key để so sánh |
| OI-19 | LM Studio chỉ nhận `json_schema`, không nhận `json_object` | Đã xử lý | Chuyển sang `json_schema` |

## 7. Công việc chưa hoàn thành

- Chạy và đối chiếu trên LLM cloud (OpenAI/DeepSeek)
- Test Design Agent và Playwright generation/execution.
- SQL Server persistence và Streamlit + AG-01 review flow.
- Mở rộng và review dataset gán nhãn (chiều precondition/outcome).

## 8. Kế hoạch Tuần 4

1. Chạy đánh giá trên LLM cloud (DeepSeek/OpenAI) và so sánh với baseline local.
2. Thống nhất với nhóm hướng slice kế: Test Design Agent, hoặc Streamlit + AG-01, hoặc persistence SQL Server.
3. Nhóm review và mở rộng dataset gán nhãn.
4. Cân nhắc tạo pull request `feature/requirement-agent` vào `develop` sau khi nhóm review.

## 9. Phân công thành viên

- **Thành viên 1 AI/Web/Data:** hoàn thiện Requirement Agent + đánh giá; chuẩn bị Test Design Agent hoặc Streamlit review flow.
- **Thành viên 2 QA/Playwright:** review và mở rộng dataset gán nhãn; chuẩn bị target application và Playwright PoC.
- **Chung:** review nhãn ground truth, thống nhất hướng slice kế, cân nhắc PR vào `develop`.

## 10. Tự đánh giá

- **Tiến độ:** Hoàn thành lõi Requirement Agent và cho chạy được với LLM thật; có số liệu RQ1 sơ bộ kèm một ablation. Do chưa có key cloud nên phần chạy/đánh giá mới thực hiện trên model local; các agent phía sau (Test Design, Playwright) và persistence/UI còn chậm so với kế hoạch tổng.
- **Chất lượng:** Backend LLM tách sau interface nên chạy được cả cloud lẫn local; có TDD (29 test) và tài liệu thiết kế. Cần đối chiếu cloud, review nhãn ground truth và bổ sung nguồn học thuật để kết luận vững hơn.
- **Rủi ro:** Kết quả đánh giá phụ thuộc model local hiện dùng; precision của detection, tính chủ quan của ground truth và độ rộng còn lại của Thesis MVP là các rủi ro chính; kiểm soát được nếu tiếp tục đi theo vertical slice và sớm đối chiếu cloud.

## 11. Kết luận

Tuần 2–3 chuyển kiến trúc tài liệu thành một agent chạy thật: từ text/DOCX/PDF sinh ra danh sách yêu cầu có cấu trúc kèm phát hiện mơ hồ theo rubric. Phần chạy và đánh giá trong kỳ được thực hiện trên model local, và backend được thiết kế để đổi sang cloud chỉ bằng cấu hình. Bộ đánh giá đã cho kết quả định lượng sơ bộ cho RQ1 — trong đó một ablation cho thấy một chỉ dẫn prompt nhỏ nâng micro-F1 từ 0.07 lên 0.73 — làm nền để đối chiếu với LLM cloud và tái dùng cho các agent tiếp theo của pipeline.
