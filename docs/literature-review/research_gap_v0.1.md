# Research Gap v0.1

## 1. Mục đích

Tài liệu này tổng hợp khoảng trống nghiên cứu ban đầu cho đề tài **“Nghiên cứu và xây dựng hệ thống Agentic AI bán tự động sinh và kiểm chứng kiểm thử đầu-cuối dựa trên Playwright”**. Phân tích tập trung vào chuỗi xử lý từ tài liệu yêu cầu đến test case, mã Playwright, kết quả thực thi và đề xuất sửa lỗi.

Research gap được xác định trong phạm vi functional end-to-end testing cho ứng dụng web, sử dụng Playwright Python và có con người tham gia phê duyệt. Các nội dung performance testing, security testing, mobile/desktop testing, tự sửa mã nguồn ứng dụng và tự động suy luận hoàn toàn test oracle từ yêu cầu mơ hồ nằm ngoài phạm vi.

## 2. Cơ sở đối chiếu

Phiên bản 0.1 dựa trên bốn nhóm nguồn chính:

1. [Playwright Test Agents](SRC-001-playwright-test-agents.md): pipeline Planner–Generator–Healer để lập kế hoạch, sinh và sửa Playwright test.
2. [Playwright Codegen và locator policy](SRC-002-playwright-codegen-locators.md): sinh thao tác/locator từ UI thật và ưu tiên role, text, test ID.
3. [Requirements-Based Test Generation Survey](SRC-003-rbtg-survey.md): tổng hợp 267 nghiên cứu về sinh kiểm thử dựa trên yêu cầu.
4. [WebTestPilot](SRC-004-webtestpilot.md): kiểm thử E2E từ đặc tả ngôn ngữ tự nhiên với UI symbolization và oracle dạng precondition/postcondition.

Bốn nguồn trên đại diện cho baseline sản phẩm trực tiếp, kỹ thuật locator/grounding, nền tảng học thuật của RBTG và một phương pháp agentic E2E gần với đề tài. Do số nguồn chuyên sâu hiện còn giới hạn, các kết luận trong tài liệu này là **research gap ban đầu**, cần tiếp tục được kiểm chứng bằng các nghiên cứu peer-reviewed về requirement ambiguity, test traceability, self-healing tests và human-in-the-loop testing.

## 3. Bảng tổng hợp khả năng và khoảng thiếu

| Tiêu chí | Playwright Test Agents | Playwright Codegen | RBTG Survey | WebTestPilot | Nhu cầu của đề tài |
|---|---|---|---|---|---|
| Chuẩn hóa requirement | Một phần qua Markdown plan; không có schema bắt buộc | Không | Phân loại nhiều dạng requirement; không cung cấp implementation | Có cấu trúc condition–action–expectation | Schema requirement có ID, nguồn gốc, precondition, action, expected outcome và trạng thái duyệt |
| Phát hiện ambiguity | Không được mô tả | Không; chỉ xử lý locator không duy nhất | Xác định là thách thức mở | Chưa có clarification workflow trong implementation | Phát hiện thiếu, mơ hồ, mâu thuẫn và chuyển cho con người xác nhận |
| Requirement traceability | Một phần qua spec/seed comment | Không | Được khảo sát nhưng không có cơ chế chung | Có trace ở cấp step–predicate–state | Truy vết artifact-level từ requirement đến scenario, test case, code, execution và repair |
| UI grounding | Có khám phá và kiểm chứng live | Mạnh ở locator role/text/test ID | Không phải trọng tâm | Có visual grounding, Set-of-Mark và page reidentification | Ground từng test step/locator trên UI thật và lưu evidence có thể audit |
| Test oracle | Expected result được chuyển thành assertion nhưng không có oracle model độc lập | Chỉ assertion visibility/text/value do người dùng chọn | Xác định oracle/test data là vấn đề khó | Mạnh về symbolized pre/postconditions và cross-state oracle | Chỉ sinh assertion từ expected outcome đã được duyệt; không tự đoán khi requirement mơ hồ |
| Human approval | Không có approval gate bắt buộc | Có tương tác thủ công nhưng không phải approval workflow | Chỉ thống kê human involvement | Không có approval gate trong runtime | Approval rõ ràng trước test generation và trước mọi repair có ảnh hưởng ngữ nghĩa |
| Constrained repair | Có guardrail nhưng không đặc tả chi tiết | Không | Không phải trọng tâm | Retry hữu hạn; không phải code-healing có approval | Repair policy theo mức rủi ro, giới hạn vòng lặp, lưu diff/lý do/bằng chứng và quyết định duyệt |
| Playwright Python | Tài liệu agent chủ yếu minh họa Playwright Test/TypeScript | Hỗ trợ Playwright tooling | Không cụ thể | Dùng Playwright trong benchmark/ground truth | Sinh, chạy và kiểm chứng trực tiếp Playwright Python |
| Evaluation | Ví dụ TodoMVC, không có benchmark/metric công bố | Không có dataset/metric | Chỉ 12% nghiên cứu có controlled comparative experiment | Evaluation mạnh nhưng trên bốn ứng dụng và giả định requirement đầy đủ | Ablation/baseline trên khoảng ba ứng dụng, đo validity, coverage, first-run success và semantic preservation |

## 4. Các khoảng trống nghiên cứu

### GAP-01 — Requirement được dùng làm context nhưng chưa được quản trị như artifact có cấu trúc

Các giải pháp hiện có có thể nhận yêu cầu hoặc PRD làm đầu vào, nhưng chưa cho thấy một quy trình thống nhất gồm chuẩn hóa requirement, gắn định danh, lưu vị trí nguồn, phát hiện thiếu/mơ hồ/mâu thuẫn và yêu cầu người dùng xác nhận trước khi sinh test. WebTestPilot cấu trúc requirement thành condition–action–expectation nhưng vẫn giả định đầu vào tự chứa và đầy đủ; Playwright Test Agents xem PRD là context tùy chọn.

Hệ quả là LLM có thể tạo test case hoặc expected result dựa trên giả định không được requirement hỗ trợ. Đây là khoảng trống trực tiếp liên quan đến RQ1.

### GAP-02 — Thiếu traceability xuyên suốt và có thể kiểm tra

Playwright Test Agents duy trì liên kết ở mức file/comment và WebTestPilot duy trì execution trace ở mức step/state. Tuy nhiên, chưa có bằng chứng trong các nguồn đã khảo sát về một mô hình truy vết thống nhất:

```text
Requirement
→ Test Scenario
→ Test Case
→ Test Step
→ Playwright Statement
→ Execution Result
→ Repair Proposal
→ Approval Decision
```

Thiếu chuỗi liên kết này khiến người dùng khó xác định một dòng mã hoặc assertion xuất phát từ requirement nào, thay đổi repair ảnh hưởng artifact nào, và requirement nào chưa được kiểm thử.

### GAP-03 — Locator grounding chưa đồng nghĩa với semantic (ngữ nghĩa) grounding

Playwright Codegen có chính sách locator thực dụng và Playwright Test Agents có thể kiểm chứng selector trên UI thật. WebTestPilot tiến xa hơn bằng visual grounding. Tuy nhiên, locator tồn tại và khớp duy nhất vẫn chưa chứng minh element đó đúng với ý định nghiệp vụ của test step.

Khoảng trống cần giải quyết là liên kết đồng thời ba loại bằng chứng:

1. Ý định của requirement/test step.
2. Thuộc tính semantic của UI như role, accessible name, label hoặc test ID.
3. Kết quả kiểm chứng locator trên ứng dụng thật.

Đây là cơ sở của RQ2 và giúp phân biệt **locator validity** với **semantic correctness**.

### GAP-04 — Oracle cần được quản trị bằng approval thay vì để agent tự điều chỉnh

Codegen chỉ sinh các assertion đơn giản do người dùng chọn; Playwright Test Agents có thể sinh và heal assertion nhưng không công bố approval policy; WebTestPilot suy luận oracle mạnh nhưng không có human approval gate trong runtime và giả định requirement đầy đủ.

Trong bối cảnh requirement mơ hồ, tự động suy luận hoặc sửa oracle có thể làm test pass bằng cách thay đổi expected behavior thay vì sửa lỗi kỹ thuật. Khoảng trống của đề tài là bảo đảm assertion và expected result chỉ bắt nguồn từ requirement đã được phê duyệt; mọi thay đổi ngữ nghĩa phải được con người quyết định.

### GAP-05 — Self-healing thiếu taxonomy (hệ thống phân loại) rủi ro và audit trail (Nhật ký đầy đủ của mọi thay đổi) chuẩn hóa

Healer có thể cập nhật locator, wait hoặc test data, nhưng guardrail (Luật hạn chế AI) được mô tả ở mức cao. WebTestPilot dùng retry hữu hạn để giảm hallucination (AI tự bịa), không tập trung vào repair file Playwright lâu dài. Các nguồn đã khảo sát chưa cung cấp đầy đủ cơ chế kết hợp:

- Phân loại lỗi ứng dụng và lỗi test automation.
- Allowlist cho thay đổi kỹ thuật an toàn.
- Denylist hoặc approval bắt buộc cho thay đổi assertion, expected result, test step và traceability.
- Repair budget (Giới hạn sửa) và điều kiện dừng.
- Diff (giữa trước - sau khi sửa), lý do, bằng chứng, kết quả chạy lại và lịch sử phê duyệt.

Đây là khoảng trống trực tiếp của RQ3.

### GAP-06 — Thiếu đánh giá tích hợp cho toàn bộ pipeline requirement-to-execution

RBTG Survey cho thấy evaluation trong lĩnh vực còn thiếu benchmark chuẩn và controlled comparative experiments. Playwright Test Agents và Codegen không công bố evaluation định lượng. WebTestPilot có benchmark tốt cho oracle/bug detection nhưng không tập trung vào approval workflow, artifact-level traceability hoặc file Playwright Python có thể bảo trì.

Cần một evaluation protocol giữ cố định requirement, ứng dụng, phiên bản Playwright, model và retry budget để đo riêng đóng góp của:

1. Structured requirement representation.
2. UI grounding.
3. Constrained repair và human approval.

## 5. Phát biểu research gap chính thức

Các giải pháp hiện có đã hỗ trợ từng phần của quy trình sinh kiểm thử E2E bằng AI, bao gồm lập kế hoạch và sinh Playwright test, tạo locator từ UI thật, chuyển requirement thành test và suy luận oracle dựa trên trạng thái GUI. Tuy nhiên, trong phạm vi các nguồn đã khảo sát, chưa có một quy trình tích hợp cho Playwright Python đồng thời: (1) chuẩn hóa và kiểm tra ambiguity của requirement trước khi sinh test; (2) duy trì traceability có thể kiểm toán từ requirement đến test case, mã, kết quả thực thi và repair; (3) grounding test step trên bằng chứng UI thật; và (4) giới hạn repair theo mức ảnh hưởng ngữ nghĩa với human approval bắt buộc.

Do đó, khoảng trống mà đề tài hướng đến là **thiếu một pipeline Agentic AI bán tự động, traceable và human-governed để chuyển requirement tự nhiên thành Playwright Python E2E tests có UI grounding, đồng thời ngăn quá trình self-healing làm thay đổi test oracle hoặc ý nghĩa test case khi chưa được phê duyệt**.

## 6. Đóng góp dự kiến của đề tài

### C1 — Structured Requirement Representation

Đề xuất schema chuẩn hóa use case, user story, acceptance criteria và functional requirement thành các trường có định danh, nguồn gốc, precondition, action, expected outcome, constraints, ambiguity flags và approval status.

### C2 — End-to-End Traceability Model

Xây dựng mô hình dữ liệu và traceability matrix liên kết requirement, scenario, test case, test step, Playwright code, execution result, repair proposal và approval decision.

### C3 — Requirement-Aware UI Grounding

Đề xuất quy trình khảo sát DOM/accessibility tree, ưu tiên locator theo Playwright best practices, kiểm tra uniqueness và lưu UI evidence để chứng minh locator vừa tồn tại vừa phù hợp với test step.

### C4 — Risk-Based Constrained Repair

Xây dựng repair policy phân biệt thay đổi kỹ thuật an toàn với thay đổi ngữ nghĩa. Thay đổi locator tương đương hoặc synchronization có thể được tự động đề xuất/thực hiện trong giới hạn; thay đổi assertion, expected result, test step, test data nghiệp vụ hoặc traceability phải được phê duyệt.

### C5 — Evaluation Protocol

Thiết kế thực nghiệm trên khoảng ba ứng dụng web, so sánh direct prompting với pipeline đề xuất và thực hiện ablation cho structured requirements, UI grounding và constrained repair.

## 7. Ánh xạ research gap với câu hỏi nghiên cứu

| Research question | Gap liên quan | Thành phần được đánh giá | Chỉ số dự kiến |
|---|---|---|---|
| RQ1: Structured requirement có cải thiện test case không? | GAP-01, GAP-02 | Requirement Analysis, Test Design, Traceability | Test-case validity, requirement coverage, unsupported-test rate, ambiguity resolution rate, số chỉnh sửa thủ công |
| RQ2: DOM/accessibility grounding có cải thiện first-run execution không? | GAP-03 | UI Explorer/Grounder, Playwright Generator | Locator validity, locator uniqueness, first-run execution rate, element-not-found rate, tỷ lệ chạy đến assertion |
| RQ3: Constrained repair có giữ nguyên ý nghĩa test không? | GAP-04, GAP-05 | Failure Classifier, Repair Policy, Human Approval | Repair success rate, semantic preservation rate, assertion weakening rate, approval rate, số vòng repair |
| RQ4: Hệ thống giảm bao nhiêu công sức thủ công? | GAP-06 | Toàn bộ pipeline | Thời gian hoàn thành, số thao tác/chỉnh sửa, số approval, chi phí/token nếu áp dụng |

## 8. Phạm vi tuyên bố novelty

Đề tài không tuyên bố phát minh mới từng thành phần riêng lẻ: LLM-based test generation, Playwright locator generation, requirement structuring, traceability và human approval đều đã tồn tại dưới các hình thức khác nhau. Novelty dự kiến nằm ở **cách tích hợp và kiểm soát** các thành phần này trong một pipeline Playwright Python bán tự động, cùng mô hình traceability và repair policy có thể audit.

Đề tài cũng không đặt mục tiêu:

- Suy luận hoàn toàn test oracle từ requirement mơ hồ.
- Tự sửa source code của ứng dụng được kiểm thử.
- Cho phép agent tự động xóa, skip hoặc làm yếu assertion để đạt trạng thái pass.
- Thay thế hoàn toàn kiểm thử viên.
- Chứng minh hiệu quả trên mọi loại ứng dụng hoặc mọi loại kiểm thử.

## 9. Kết luận

Research gap trung tâm không phải là thiếu công cụ sinh Playwright test, mà là thiếu cơ chế bảo đảm test được sinh **có căn cứ, có truy vết, có bằng chứng UI và được sửa trong giới hạn an toàn**. Đề tài vì vậy nên được định vị là một hệ thống hỗ trợ kiểm thử viên ra quyết định, trong đó AI thực hiện phân tích, sinh và đề xuất; con người giữ quyền quyết định đối với requirement, test oracle và mọi repair làm thay đổi ý nghĩa kiểm thử.

Phiên bản tiếp theo của research gap cần bổ sung thêm nghiên cứu peer-reviewed về ambiguity detection, requirement–test traceability, self-healing test automation, semantic-preserving repair và human–AI collaboration để củng cố tuyên bố novelty trước khi đưa vào luận văn chính thức.
