# Báo cáo Tuần 1

- Dự án: Agentic Playwright Testing
- Thời gian báo cáo: Đến ngày 2026-07-18
- Giai đoạn: Khởi tạo đề tài, khảo sát tài liệu, xác định research gap và kiến trúc sơ bộ
- Trạng thái chung: Hoàn thành phần lớn mục tiêu nghiên cứu–thiết kế của Tuần 1; chưa bắt đầu triển khai vertical slice

## 1. Mục tiêu tuần

1. Hiểu và thống nhất bài toán nghiên cứu.
2. Chốt phạm vi và giới hạn của đề tài.
3. Khảo sát các giải pháp liên quan trực tiếp.
4. Xác định research gap ban đầu.
5. Chốt Thesis MVP và luồng xử lý xuyên suốt.
6. Xây dựng kiến trúc hệ thống phiên bản 0.1.
7. Khởi tạo repository, cấu trúc nhánh và quy trình làm việc nhóm.

## 2. Công việc đã hoàn thành

### 2.1 Khởi tạo dự án và Git

- Khởi tạo Git repository cho `agentic-playwright-testing`.
- Tạo và đẩy nhánh `main`, `develop` cùng các nhánh tài liệu/tính năng đề xuất.
- Tạo cấu trúc thư mục cho source code, test, database, dataset, experiment, generated artifact và tài liệu.
- Thiết lập `.gitignore`, `.env.example`, `requirements.txt` và README ban đầu.

### 2.2 Chốt bài toán và phạm vi

- Xác định ba vấn đề nghiên cứu cốt lõi:
  1. Requirements traceability.
  2. DOM/accessibility grounding.
  3. Constrained repair có human approval.
- Chốt phạm vi functional E2E testing cho ứng dụng web bằng Playwright Python.
- Chốt các loại tài liệu đầu vào: DOCX, text-based PDF, Markdown và plain text.
- Xác định các nội dung ngoài phạm vi như performance/security testing, mobile/desktop testing, fine-tune LLM, tự sửa source code website và hệ thống hoàn toàn tự vận hành.
- Xây dựng bốn research questions cho structured requirements, UI grounding, constrained repair và hiệu quả giảm công sức thủ công.

### 2.3 Khảo sát tài liệu

- Chuẩn hóa template ghi chú nguồn để bao gồm abstract/introduction, architecture, evaluation, limitation và 12 câu hỏi đối chiếu.
- Tạo bốn file đọc và nhận xét nguồn.
- Cập nhật literature review matrix theo 18 tiêu chí/cột.
- Phân biệt rõ khả năng thực sự được triển khai với nội dung chỉ được nguồn thảo luận như một research challenge.

### 2.4 Xác định research gap

- Tạo `research_gap_v0.1.md`.
- So sánh giải pháp hiện có theo structured requirements, ambiguity detection, traceability, UI grounding, oracle validation, human approval, constrained repair, Playwright Python support và evaluation.
- Xác định sáu khoảng trống nghiên cứu ban đầu.
- Ánh xạ research gap với RQ1–RQ4 và các metric dự kiến.
- Giới hạn tuyên bố novelty ở cách tích hợp và kiểm soát pipeline, không tuyên bố phát minh từng kỹ thuật riêng lẻ.

### 2.5 Chốt Thesis MVP

- Chốt luồng xuyên suốt từ upload requirement đến traceability report.
- Xác định sáu module:
  1. Project Management.
  2. Requirement Analysis.
  3. Test Design.
  4. Playwright Generation.
  5. Execution and Repair.
  6. Report.
- Chốt các nội dung chưa làm trong Thesis MVP như multi-role authentication, phân quyền phức tạp, RAG phức tạp, distributed execution, nhiều LLM provider, CI/CD hoàn chỉnh và tự sửa source code website.

### 2.6 Xây dựng kiến trúc sơ bộ

- Tạo `architecture_v0.1.md`.
- Xây dựng component diagram và sequence diagram bằng Mermaid.
- Xác định trách nhiệm của Streamlit UI, Application Service, Agent Orchestrator, các agent, Approval Service, Traceability Service, repository và artifact storage.
- Xác định input/output của năm trách nhiệm agent.
- Xác định bảy approval gates bắt buộc.
- Đề xuất repair policy theo risk level, domain entities và traceability chain.

## 3. Sản phẩm tạo ra

| Sản phẩm | Đường dẫn | Trạng thái |
|---|---|---|
| Problem statement | `docs/project/problem_statement.md` | Hoàn thành bản đầu |
| Project scope | `docs/project/scope.md` | Hoàn thành bản đầu |
| Research questions | `docs/project/research_questions.md` | Hoàn thành bản đầu |
| Source reading notes template | `docs/literature-review/source_reading_notes_template.md` | Đã mở rộng |
| Playwright Test Agents notes | `docs/literature-review/SRC-001-playwright-test-agents.md` | Đã đọc và nhận xét |
| Playwright Codegen notes | `docs/literature-review/SRC-002-playwright-codegen-locators.md` | Đã đọc và nhận xét |
| RBTG Survey notes | `docs/literature-review/SRC-003-rbtg-survey.md` | Đã đọc và nhận xét |
| WebTestPilot notes | `docs/literature-review/SRC-004-webtestpilot.md` | Đã đọc và nhận xét |
| Literature review matrix | `docs/literature-review/literature_review_matrix.csv` | Có 4 nguồn, đã điền các tiêu chí chính |
| Research gap | `docs/literature-review/research_gap_v0.1.md` | Hoàn thành phiên bản 0.1 |
| Kiến trúc sơ bộ | `docs/architecture/architecture_v0.1.md` | Hoàn thành phiên bản 0.1 |
| Báo cáo Tuần 1 | `docs/week1/week1_report.md` | Hoàn thành |

## 4. Tài liệu đã đọc

### 4.1 Playwright Test Agents

- Ba agent: Planner, Generator và Healer.
- Điểm kế thừa: pipeline có artifact trung gian, live UI verification, sinh và sửa Playwright test.
- Điểm còn thiếu so với đề tài: requirement schema, ambiguity handling, artifact-level traceability, approval gate và repair policy có thể audit.

### 4.2 Playwright Codegen và locator best practices

- Codegen ưu tiên role, text và test ID; khuyến nghị user-facing attributes thay cho CSS/XPath phụ thuộc cấu trúc DOM.
- Nguồn này là cơ sở cho locator policy và DOM/accessibility grounding.
- Codegen không hiểu requirement, không tạo traceability và không suy luận oracle.

### 4.3 Requirements-Based Test Generation Survey

- Survey tổng hợp 267 nghiên cứu RBTG đến hết năm 2024.
- Requirement quality, chuyển abstract test thành executable test, benchmark và rigorous evaluation vẫn là các thách thức lớn.
- Chỉ 12% nghiên cứu được khảo sát có controlled comparative experiment.

### 4.4 WebTestPilot

- Chuẩn hóa natural-language requirement thành condition–action–expectation.
- Grounding UI và suy luận pre/postcondition oracle qua symbolization và DSL.
- Có evaluation trên bốn ứng dụng và bug-injected benchmark.
- Khoảng thiếu liên quan đến đề tài: không có runtime human approval, traceability artifact-level chưa đầy đủ, giả định requirement tự chứa/đầy đủ và không tập trung vào file Playwright Python có repair approval.

## 5. Quyết định kỹ thuật

| ID | Quyết định | Lý do |
|---|---|---|
| TD-01 | Xây hệ thống dưới dạng Python modular monolith | Giảm độ phức tạp triển khai nhưng vẫn giữ ranh giới module logic |
| TD-02 | Streamlit UI chỉ gọi Application Service | Tránh gắn UI trực tiếp với agent, Playwright và database |
| TD-03 | Agent Orchestrator không có quyền tự phê duyệt | Bảo đảm human-governed workflow |
| TD-04 | Approval Service và Traceability Service độc lập về trách nhiệm | Ngăn agent tự hợp thức hóa thay đổi hoặc tự sửa trace link |
| TD-05 | Agent output cốt lõi phải là JSON theo Pydantic schema | Tăng khả năng validate, lưu trữ và tái lập |
| TD-06 | Sử dụng Playwright Python/Pytest | Phù hợp phạm vi đề tài và công nghệ đã chốt |
| TD-07 | Locator ưu tiên role, label, placeholder, text, test ID | Bám Playwright best practices và giảm phụ thuộc DOM structure |
| TD-08 | Execution và Repair tách thành hai trách nhiệm logic | Execution chỉ thu bằng chứng; Repair chỉ tạo proposal |
| TD-09 | Mọi repair có ảnh hưởng ngữ nghĩa phải được phê duyệt | Ngăn làm yếu assertion hoặc thay oracle để test pass |
| TD-10 | SQL Server lưu metadata; artifact lớn lưu ngoài DB | Giảm tải lưu screenshot, trace, log và script dung lượng lớn |
| TD-11 | Artifact đã duyệt phải tạo version mới khi chỉnh sửa | Bảo toàn lịch sử và traceability |
| TD-12 | Bắt đầu bằng Chromium và chạy tuần tự | Giới hạn độ phức tạp của Thesis MVP và tăng khả năng tái lập |

Các quyết định chưa chốt gồm Playwright sync/async API, authentication setup, artifact storage convention và schema chi tiết.

## 6. Research gap ban đầu

Sáu khoảng trống được xác định:

1. **GAP-01 — Structured requirement governance:** Giải pháp hiện có chưa tích hợp đầy đủ chuẩn hóa requirement, định danh, source span, ambiguity detection và approval trước test generation.
2. **GAP-02 — End-to-end traceability:** Thiếu chuỗi truy vết thống nhất từ requirement đến test case, code, execution, repair và approval.
3. **GAP-03 — Semantic UI grounding:** Locator tồn tại/duy nhất chưa chứng minh element đúng với ý định nghiệp vụ của test step.
4. **GAP-04 — Oracle governance:** Thiếu approval gate bảo vệ assertion và expected result trước thay đổi của agent.
5. **GAP-05 — Constrained repair:** Thiếu taxonomy rủi ro, allowlist/denylist, repair budget, diff, evidence và audit history thống nhất.
6. **GAP-06 — Integrated evaluation:** Thiếu evaluation tích hợp và ablation cho toàn bộ requirement-to-execution pipeline trong bối cảnh Playwright Python.

Phát biểu research gap trung tâm:

> Thiếu một pipeline Agentic AI bán tự động, traceable và human-governed để chuyển requirement tự nhiên thành Playwright Python E2E tests có UI grounding, đồng thời ngăn self-healing làm thay đổi test oracle hoặc ý nghĩa test case khi chưa được phê duyệt.

## 7. Vấn đề gặp phải và chưa giải quyết

| ID | Vấn đề | Mức ảnh hưởng | Hướng xử lý |
|---|---|---|---|
| OI-01 | Literature review hiện mới có bốn nhóm nguồn chính | Trung bình | Bổ sung bài peer-reviewed về ambiguity, traceability, self-healing và human–AI collaboration |
| OI-02 | Chưa chọn ba target web applications cho evaluation | Cao | Xây tiêu chí lựa chọn và chốt ứng dụng trong Tuần 2 |
| OI-03 | Chưa có ground-truth requirement/test-case dataset | Cao | Chọn một ứng dụng đầu tiên và xây bộ requirement mẫu có review |
| OI-04 | Chưa chốt Playwright sync hay async API | Trung bình | Thử PoC nhỏ và chọn một API duy nhất |
| OI-05 | Chưa chốt cách xử lý authentication/setup | Cao | So sánh seed test, storage state và manual setup |
| OI-06 | Chưa có schema Pydantic chính thức | Cao | Chốt bốn schema lõi đầu Tuần 2 |
| OI-07 | Chưa có ERD và migration | Trung bình | Thiết kế domain model trước, sau đó SQLAlchemy/Alembic |
| OI-08 | Chưa có failure taxonomy và repair policy chi tiết | Cao | Xây allowlist/denylist, risk levels và approval conditions |
| OI-09 | Chưa có vertical slice chạy được | Cao | Ưu tiên một requirement → một test → một execution trong Tuần 2 |
| OI-10 | Các tài liệu mới chưa được commit/push/PR | Trung bình | Review nội bộ, commit theo nhóm tài liệu và tạo pull request |
| OI-11 | Chưa xác nhận thành viên còn lại đã clone và làm việc được | Trung bình | Kiểm tra quyền truy cập và quy trình branch/PR |

## 8. Công việc chưa hoàn thành

- Chưa bổ sung thêm nguồn học thuật ngoài bốn nhóm nguồn chính.
- Chưa hoàn thiện meeting note với ngày, người tham gia và quyết định thực tế.
- Chưa chốt target applications và experimental dataset.
- Chưa xây schema, ERD hoặc migration.
- Chưa khởi tạo Streamlit skeleton.
- Chưa triển khai agent hoặc OpenAI API integration.
- Chưa triển khai Playwright exploration/generation/execution.
- Chưa triển khai approval và traceability persistence.
- Chưa có vertical slice.
- Chưa commit, push và tạo pull request cho bộ tài liệu Tuần 1 mới.

## 9. Kế hoạch Tuần 2

### Mục tiêu Tuần 2

1. Chốt domain schema và state machine.
2. Chốt target application đầu tiên.
3. Xây vertical slice tối thiểu bằng file/JSON trước khi nối đầy đủ UI và database.
4. Tạo PoC Requirement Analysis và Test Design dùng structured output.
5. Tạo PoC Playwright Python cho một test case đã duyệt.
6. Chuẩn bị nền tảng persistence và Streamlit review flow.

### Backlog ưu tiên

| Mức | Công việc | Đầu ra mong đợi |
|---|---|---|
| P0 | Chốt `Requirement`, `TestCase`, `UIGroundingRecord`, `RepairProposal` schema | Pydantic models và ví dụ JSON hợp lệ |
| P0 | Chốt project/artifact workflow và approval gates | State machine v0.1 |
| P0 | Chọn target application đầu tiên và 5 requirement mẫu | Dataset seed có ground truth ban đầu |
| P0 | PoC document text → structured requirement | Requirement Agent chạy được |
| P0 | PoC approved requirement → test cases | Test Design Agent chạy được |
| P0 | PoC test case → Playwright Python → execution | Một test chạy được trên Chromium |
| P1 | Thiết kế ERD và repository interfaces | ERD v0.1 và model mapping |
| P1 | Chốt sync/async API và authentication setup | Architecture decision record |
| P1 | Streamlit project/upload/requirement review skeleton | UI flow ban đầu |
| P1 | Failure taxonomy và repair rules v0.1 | Policy document/test fixtures |
| P2 | Bổ sung literature review | Thêm nguồn và cập nhật research gap nếu cần |
| P2 | Chuẩn bị evaluation logging | Lưu thời gian, token, manual edits và run metadata |

## 10. Phân công thành viên Tuần 2

### Thành viên 1 — QA/Playwright

- Chọn và đánh giá target application đầu tiên.
- Xây 5 requirement/test-case ground truth mẫu.
- Định nghĩa tiêu chí test-case validity và requirement coverage.
- Chốt locator policy và làm Playwright exploration PoC.
- Sinh/chạy một Playwright Python test trên Chromium.
- Xây failure taxonomy và repair allowlist/denylist ban đầu.

### Thành viên 2 — AI/Web/Data

- Thiết kế bốn Pydantic schema lõi.
- Xây Requirement Analysis Agent PoC với structured output.
- Xây Test Design Agent PoC với structured output.
- Thiết kế workflow state machine, ERD và repository interfaces.
- Khởi tạo Streamlit project/upload/requirement review skeleton.
- Thiết kế model/prompt versioning và agent-run metadata.

### Công việc chung

- Review và chốt schema/ID/versioning convention.
- Chốt target application và ground truth.
- Kết nối thành một vertical slice.
- Review research gap/architecture với giảng viên nếu có thể.
- Commit, push và tạo pull request cho deliverable Tuần 1–2.

## 11. Rủi ro về tiến độ

| Rủi ro | Khả năng | Ảnh hưởng | Biện pháp giảm thiểu |
|---|---|---|---|
| Scope Thesis MVP gồm nhiều module | Cao | Cao | Xây modular monolith và vertical slice trước, không mở rộng chiều sâu sớm |
| UI exploration/grounding trở thành crawler tổng quát | Cao | Cao | Chỉ khảo sát theo approved test step và start URL |
| Repair Agent khó phân biệt lỗi test với bug website | Cao | Cao | Dùng failure taxonomy, evidence bundle và trạng thái blocked-for-review |
| Agent sinh output không đúng schema | Trung bình | Cao | Pydantic validation, retry có giới hạn và fail closed |
| Chưa có dataset/ground truth làm chậm evaluation | Cao | Cao | Chọn một ứng dụng và tạo seed dataset ngay đầu Tuần 2 |
| Học đồng thời Streamlit, SQLAlchemy, SQL Server, Playwright và LLM API | Cao | Cao | Chia theo thành viên, làm PoC độc lập và tích hợp dần |
| Tích hợp SQL Server quá sớm làm chậm luồng nghiên cứu | Trung bình | Trung bình | Chạy vertical slice bằng JSON/in-memory trước rồi thêm repository |
| Authentication của target website phức tạp | Trung bình | Cao | Ưu tiên ứng dụng có seed/setup rõ; khóa một phương pháp authentication |
| Kết quả LLM không tái lập | Trung bình | Cao | Khóa model/config, lưu prompt version, input/output và run metadata |
| Thiếu review/commit định kỳ | Trung bình | Trung bình | Chia PR nhỏ theo artifact và review cuối mỗi tuần |

## 12. Tự đánh giá

- **Tiến độ:** Phần nghiên cứu nền tảng, literature notes, research gap, Thesis MVP và kiến trúc v0.1 đã hoàn thành. Phần triển khai mã nguồn chưa bắt đầu; các deliverable mới chưa được commit/PR.
- **Chất lượng:** Tài liệu có liên kết tương đối nhất quán giữa problem statement, scope, research questions, research gap và architecture. Tuyên bố novelty đã được giới hạn thận trọng. Cần thêm nguồn peer-reviewed và xác nhận với giảng viên.
- **Rủi ro:** Cao nhất là độ rộng Thesis MVP, UI grounding, constrained repair và thiếu dataset/ground truth. Rủi ro có thể kiểm soát nếu Tuần 2 ưu tiên schema, target application và vertical slice thay vì xây rộng từng module.

## 13. Kết luận tuần

Tuần 1 đã tạo được nền tảng nghiên cứu và thiết kế cần thiết để chuyển sang triển khai. Hướng đề tài được chốt là pipeline Agentic AI bán tự động có structured requirements, end-to-end traceability, UI grounding, constrained repair và human approval. Mục tiêu quan trọng nhất của Tuần 2 là biến kiến trúc tài liệu thành một vertical slice chạy được trên một requirement, một approved test case và một target website trước khi mở rộng toàn bộ Thesis MVP.
