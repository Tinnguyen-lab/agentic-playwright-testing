# Research Gap v0.1

> Phiên bản này rà soát khoảng trống nghiên cứu trên cơ sở **12 nguồn** (SRC-001…012), bao phủ đủ các mảng: baseline sản phẩm, requirement→test, traceability, DOM grounding/locator robustness, và self-healing/constrained repair.

## 1. Mục đích

Tài liệu này tổng hợp khoảng trống nghiên cứu cho đề tài **"Nghiên cứu và xây dựng hệ thống Agentic AI bán tự động sinh và kiểm chứng kiểm thử đầu-cuối dựa trên Playwright"**. Phân tích tập trung vào chuỗi xử lý từ tài liệu yêu cầu đến test case, mã Playwright, kết quả thực thi và đề xuất sửa lỗi.

Research gap được xác định trong phạm vi functional end-to-end testing cho ứng dụng web, sử dụng Playwright Python và có con người tham gia phê duyệt. Các nội dung performance testing, security testing, mobile/desktop testing, tự sửa mã nguồn ứng dụng và tự động suy luận hoàn toàn test oracle từ yêu cầu mơ hồ nằm ngoài phạm vi.

## 2. Cơ sở đối chiếu

Tài liệu dựa trên 12 nguồn, chia thành năm nhóm theo vai trò đối chiếu:

**A. Baseline sản phẩm & nền tảng học thuật**
1. [Playwright Test Agents](SRC-001-playwright-test-agents.md) — pipeline Planner–Generator–Healer cho Playwright.
2. [Playwright Codegen & locator policy](SRC-002-playwright-codegen-locators.md) — sinh thao tác/locator từ UI thật, ưu tiên role/text/test ID.
3. [Requirements-Based Test Generation Survey](SRC-003-rbtg-survey.md) — tổng hợp 267 nghiên cứu về RBTG.
4. [WebTestPilot](SRC-004-webtestpilot.md) — agentic E2E từ đặc tả NL, oracle symbolized (gần đề tài nhất).

**B. Requirement → test case bằng LLM**
5. [LLM Test Case Scenario Tool](SRC-005-llm-testcase-scenario-gen.md) — user story → test scenario (proof-of-concept).
6. [GHL — High-Level Test Cases](SRC-007-ghl-llm-test-cases.md) — requirement → HL test case theo ISO/IEC/IEEE 29119-4, chỉ bằng prompt.
7. [System Test Case Design from SRS (ChatGPT)](SRC-011-system-testcase-chatgpt.md) — SRS → test case bảng chuẩn + human review.

**C. Traceability**
8. [ReqToCode](SRC-009-reqtocode-traceability.md) — traceability compile-time requirement↔code↔test.

**D. DOM grounding & locator robustness**
9. [Steward](SRC-010-steward-nl-web-automation.md) — NL web automation, grounding hybrid DOM + screenshot, tích hợp Playwright.
10. [Zero-Cost Self-Healing (DOM a11y)](SRC-006-zero-cost-self-healing-dom.md) — grounding a11y-first + self-healing locator deterministic.
11. [Web Element Relocalization (Similo)](SRC-012-web-element-relocalization.md) — relocate locator đa thuộc tính, genetic-optimized.

**E. Self-healing / constrained repair & giới hạn autonomy**
12. [Practical Limits of Autonomous Test Repair](SRC-008-autonomous-test-repair-limits.md) — bằng chứng công nghiệp về thất bại của autonomy không ràng buộc + 5 design guideline.

Nhóm B, C, D, E được đưa vào để bao phủ đúng các mảng cần đối chiếu sâu: requirement structuring/ambiguity, traceability, self-healing và human-in-the-loop. Lưu ý mức độ tin cậy: SRC-009 là preprint chưa peer-review và **không có evaluation định lượng**; SRC-005/006/008 là preprint (proof-of-concept/case study); SRC-004/007/010/011/012 là research paper có số liệu; SRC-003 là survey. Các kết luận vẫn cần đối chiếu thêm nguồn peer-reviewed về **ambiguity detection** (xem mục 9).

## 3. Ma trận năng lực (12 nguồn × 8 tiêu chí)

Ký hiệu: **✓** = có/mạnh · **◑** = một phần/yếu · **✗** = không.

| Nguồn | Struct. req | Ambiguity | Traceability | DOM grounding | Oracle | Human approval | Constr. repair | Playwright |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| SRC-001 Playwright Test Agents | ◑ | ✗ | ◑ | ✓ | ◑ | ✗ | ◑ | ✓ |
| SRC-002 Codegen/locator | ✗ | ✗ | ✗ | ✓ | ◑ | ◑ | ✗ | ✓ |
| SRC-003 RBTG Survey | ◑ | ◑¹ | ◑¹ | ✗ | ◑¹ | ◑¹ | ✗ | ✗ |
| SRC-004 WebTestPilot | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ◑ | ✓ |
| SRC-005 LLM Scenario Tool | ◑ | ✗ | ✗ | ✗ | ◑ | ◑ | ✗ | ✗ |
| SRC-006 Zero-Cost Self-Healing | ✗ | ✗ | ◑² | ✓ | ◑ | ✗ | ✓ | ✓ |
| SRC-007 GHL (ISO 29119-4) | ◑ | ✗ | ◑ | ✗ | ◑ | ◑ | ✗ | ✗ |
| SRC-008 Autonomous Repair Limits | ◑ | ✗ | ◑ | ◑³ | ✗⁴ | ◑⁵ | ✓ | ✓ |
| SRC-009 ReqToCode | ✓ | ✗ | ✓ | ✗ | ✗ | ◑ | ✗ | ✗ |
| SRC-010 Steward | ✗ | ✗ | ✗ | ✓ | ◑ | ✗ | ◑ | ✓ |
| SRC-011 System TC (ChatGPT) | ✓ | ✗ | ◑ | ✗ | ◑ | ✓⁶ | ✗ | ✗ |
| SRC-012 Web Element Relocalization | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ | ◑⁷ |
| **Nhu cầu đề tài** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** |

¹ Chỉ khảo sát/nêu là thách thức, không có implementation. ² Chỉ business-level L0/L1/L2, không phải requirement-level. ³ Có tool DOM nhưng agent sinh mã bỏ qua → hallucination; guideline khuyến nghị bắt buộc. ⁴ Thiếu oracle là *root cause* chính (bằng chứng phản chứng mạnh). ⁵ Không có trong runtime nhưng *kết luận bắt buộc phải có*. ⁶ Mạnh nhưng ở khâu evaluation, không phải cổng phê duyệt runtime. ⁷ Library cho Selenium, không phải Playwright.

**Quan sát tổng thể:** cột **Ambiguity** là **✗ trên toàn bộ 12 nguồn** — khoảng trống được xác nhận rõ nhất. Không nguồn nào phủ đủ 8 tiêu chí; mỗi nguồn chỉ mạnh ở một vài mảnh, còn "Nhu cầu đề tài" cần cả tám. Điều này củng cố định vị novelty là **tích hợp và kiểm soát**, không phải phát minh từng thành phần.

## 4. Các khoảng trống nghiên cứu

### GAP-01 — Requirement được cấu trúc hóa nhưng thiếu phát hiện ambiguity và phê duyệt trước khi sinh test

Việc **cấu trúc hóa requirement** đã được nhiều nghiên cứu chứng minh khả thi ở các mức khác nhau: condition–action–expectation (SRC-004), test design techniques theo ISO 29119-4 (SRC-007), bảng test case chuẩn condition/input/expected/comments (SRC-011), user story ưu tiên hóa (SRC-005), và Traceable typed element có metadata (SRC-009). Tuy nhiên:

- **Không nguồn nào triển khai phát hiện ambiguity** (thiếu/mơ hồ/mâu thuẫn) rồi chặn quy trình để con người xác nhận. SRC-003 nêu đây là thách thức mở; SRC-004 giả định requirement tự chứa và đầy đủ; SRC-011 ghi nhận LLM "hiểu hành vi hệ thống hạn chế chỉ từ SRS" nên bỏ sót test nhưng không có detector.
- Các phương pháp trên **sinh test ngay** từ requirement mà không có cổng phê duyệt requirement-đã-chuẩn-hóa trước bước generation.

⇒ Khoảng trống thu hẹp ở phần "biểu diễn có cấu trúc" nhưng **vẫn mở hoàn toàn** ở phần "ambiguity detection + approval trước generation". Liên quan trực tiếp **RQ1**.

### GAP-02 — Traceability chưa bao phủ chuỗi requirement→execution→repair→approval

SRC-009 (ReqToCode) là nguồn traceability mạnh nhất trong bộ đọc: hard link, bidirectional, compile-time, branch-scoped, coverage-at-revision. Nhưng nó nhằm vào **mã viết tay/sinh bởi LLM ở mức source code**, và tự nêu chỉ đảm bảo *structural presence, không semantic correctness*; nó **không** mô hình hóa chuỗi đặc thù của đề tài:

```text
Requirement → Test Scenario → Test Case → Test Step
→ Playwright Statement → Execution Result → Repair Proposal → Approval Decision
```

Các nguồn khác chỉ trace từng đoạn: SRC-001 ở mức file/comment, SRC-004 ở mức step–predicate–state, SRC-011 map ngầm theo use case. Chưa nguồn nào gắn **Execution Result → Repair Proposal → Approval Decision** vào cùng một mô hình truy vết artifact-level.

⇒ Khoảng trống về *cơ chế* traceability đã có tham chiếu tốt (mượn ý tưởng "trace là dependency, broken trace = broken build" của SRC-009), nhưng *phạm vi* trace bao gồm thực thi–sửa lỗi–phê duyệt vẫn chưa được nguồn nào giải quyết. Liên quan **RQ1** và nền tảng cho **RQ3**.

### GAP-03 — Locator grounding đã phong phú nhưng chưa hợp nhất với ý định requirement (semantic grounding)

Bộ nguồn nay bao phủ tốt grounding cấp DOM theo nhiều trường phái:
- A11y-first deterministic — ưu tiên `get_by_role`/ARIA/`data-testid` (SRC-006), phù hợp Playwright best practices (SRC-002).
- Hybrid DOM + vision — lọc DOM (CSS selector) + chỉ số hóa top-15 + screenshot (SRC-010), visual + Set-of-Mark (SRC-004).
- Relocalization đa thuộc tính — similarity scoring trên tag/class/id/xpath/aria-label/text/location, genetic-optimized (SRC-012).

Tuy vậy, các kỹ thuật này chứng minh **locator tồn tại và bền**, không chứng minh element **đúng với ý định nghiệp vụ** của test step. Khoảng trống là liên kết đồng thời ba loại bằng chứng: (1) ý định requirement/test step, (2) thuộc tính semantic của UI (role, accessible name, label, test ID), (3) kết quả kiểm chứng locator trên ứng dụng thật. SRC-008 còn cung cấp bằng chứng phản chứng: khi grounding bị bỏ qua, agent sinh selector ảo giác gây cascading timeout.

⇒ Cơ sở của **RQ2**; giúp phân biệt **locator validity** với **semantic correctness**.

### GAP-04 — Oracle cần được quản trị bằng approval thay vì để agent tự điều chỉnh (nay có bằng chứng công nghiệp mạnh)

SRC-008 biến GAP này từ suy đoán thành **bằng chứng định lượng**: trong 300 báo cáo thực thi, 2/7 họ scenario "hội tụ" thực chất do **làm yếu assertion** (`toBe(5)` → `toBeTruthy()`) hoặc **xóa test case**, khiến convergence 70% "bề mặt" chỉ còn 50% "nghiêm ngặt"; root cause là **thiếu correctness oracle**. SRC-011 cho thấy con người *có thể* thẩm định oracle (cột expected output), nhưng ở khâu evaluation chứ không phải cổng runtime. SRC-004 suy luận oracle mạnh nhưng không có human approval gate và giả định requirement đầy đủ; SRC-007 để "expected result khi execution" thành future work.

⇒ Khoảng trống: bảo đảm assertion/expected result **chỉ bắt nguồn từ requirement đã phê duyệt**, và mọi thay đổi ngữ nghĩa của oracle phải do con người quyết định. Liên quan **RQ3**, nay được biện minh vững hơn nhiều.

### GAP-05 — Self-healing thiếu một chính sách hợp nhất: taxonomy rủi ro + allowlist/denylist + budget + audit + approval

Các mảnh của lời giải nay đã xuất hiện rải rác:
- **Taxonomy lỗi + guideline**: SRC-008 đưa ra 5 nguyên tắc (runtime grounding bắt buộc, bounded iteration + escalation, coi test là behavioral spec, tách environment failure khỏi test failure, explicit interface contract) và phân bố failure signature.
- **Thay đổi kỹ thuật an toàn (ứng viên cho allowlist)**: relocalization locator deterministic (SRC-012), targeted re-extraction chỉ selector hỏng (SRC-006) — sửa được locator mà không đụng ngữ nghĩa.
- **Denylist/approval bắt buộc**: đề xuất trong SRC-008 (semantic-drift detection, test-count reduction → human review).

Tuy nhiên **chưa nguồn nào hợp nhất** thành một repair policy đầy đủ gồm: phân loại lỗi ứng dụng vs lỗi test automation; allowlist cho thay đổi kỹ thuật; denylist/approval cho assertion, expected result, test step, traceability; repair budget và điều kiện dừng; và lưu diff/lý do/bằng chứng/kết quả chạy lại/lịch sử phê duyệt. SRC-006/012 mạnh về repair xác định nhưng **không có tầng approval**; SRC-008 mạnh về ranh giới nhưng là phân tích failure, không phải hệ hoàn chỉnh.

⇒ Khoảng trống trực tiếp của **RQ3**.

### GAP-06 — Thiếu đánh giá tích hợp cho toàn bộ pipeline requirement-to-execution

Các nguồn chỉ đánh giá **từng mảnh riêng lẻ**: SRC-007 đo recall test case (0.81/0.37); SRC-011 đo % valid trên 5 SRS; SRC-012 đo % relocalization (98.8%); SRC-010 đo task completion (40%); SRC-008 phân tích failure mode; SRC-006 đo pass rate/heal time trên một site demo. Không nguồn nào đánh giá **pipeline tích hợp** requirement → grounding → oracle → execution → constrained repair có approval và traceability. SRC-003 xác nhận lĩnh vực còn thiếu benchmark chuẩn và chỉ ~12% nghiên cứu có controlled comparative experiment.

⇒ Cần protocol giữ cố định requirement, ứng dụng, phiên bản Playwright, model và retry budget để đo riêng đóng góp của (1) structured requirement, (2) UI grounding, (3) constrained repair + human approval. Liên quan **RQ4**.

## 5. Phát biểu research gap chính thức

Các giải pháp hiện có đã hỗ trợ **từng phần** của quy trình sinh kiểm thử E2E bằng AI: lập kế hoạch và sinh Playwright test (SRC-001), tạo locator từ UI thật (SRC-002, SRC-006, SRC-012), chuyển requirement thành test (SRC-004, SRC-005, SRC-007, SRC-011), suy luận oracle dựa trên trạng thái GUI (SRC-004), grounding thao tác trên web thật (SRC-010), nhúng traceability vào codebase (SRC-009), và chỉ ra ranh giới cần thiết cho autonomous repair (SRC-008).

Tuy nhiên, trong phạm vi 12 nguồn đã khảo sát, **chưa có một quy trình tích hợp cho Playwright Python** đồng thời: (1) chuẩn hóa **và phát hiện ambiguity** của requirement, có phê duyệt trước khi sinh test; (2) duy trì **traceability kiểm toán được** kéo dài đến execution, repair proposal và approval decision; (3) grounding test step trên **bằng chứng UI thật gắn với ý định requirement**; và (4) giới hạn repair theo **mức ảnh hưởng ngữ nghĩa với human approval bắt buộc**.

Do đó, khoảng trống mà đề tài hướng đến là **thiếu một pipeline Agentic AI bán tự động, traceable và human-governed để chuyển requirement tự nhiên thành Playwright Python E2E tests có UI grounding, đồng thời ngăn quá trình self-healing làm thay đổi test oracle hoặc ý nghĩa test case khi chưa được phê duyệt**.

## 6. Đóng góp dự kiến của đề tài

| Đóng góp | Nội dung | Nguồn tham chiếu / học hỏi |
|---|---|---|
| **C1 — Structured Requirement Representation + Ambiguity** | Schema chuẩn hóa use case/user story/acceptance criteria/functional requirement với định danh, nguồn gốc, precondition, action, expected outcome, constraints, **ambiguity flags** và approval status | Mở rộng SRC-004, SRC-007, SRC-011; lấp phần ambiguity còn thiếu ở mọi nguồn |
| **C2 — End-to-End Traceability Model** | Mô hình dữ liệu + ma trận truy vết liên kết requirement → scenario → test case → step → Playwright code → execution → repair → approval | Mượn cơ chế "trace là dependency" của SRC-009; mở rộng phạm vi tới execution/repair/approval |
| **C3 — Requirement-Aware UI Grounding** | Khảo sát DOM/accessibility, ưu tiên locator theo Playwright best practices, kiểm uniqueness, lưu UI evidence chứng minh locator **vừa tồn tại vừa phù hợp ý định** | Kết hợp SRC-002/006 (a11y-first), SRC-010 (lọc DOM), SRC-012 (đa thuộc tính) với ý định requirement |
| **C4 — Risk-Based Constrained Repair** | Repair policy phân biệt thay đổi kỹ thuật an toàn (locator tương đương, synchronization — tự động trong giới hạn) với thay đổi ngữ nghĩa (assertion, expected result, test step, test data, traceability — bắt buộc phê duyệt) | Hiện thực hóa 5 guideline của SRC-008; dùng repair xác định của SRC-006/012 làm allowlist |
| **C5 — Evaluation Protocol** | Thực nghiệm ~3 ứng dụng web, so sánh direct prompting với pipeline đề xuất, ablation cho structured requirements / UI grounding / constrained repair | Lấp GAP-06; tránh lỗi đánh giá isolated của các nguồn |

## 7. Ánh xạ research gap với câu hỏi nghiên cứu

| Research question | Gap liên quan | Thành phần được đánh giá | Chỉ số dự kiến |
|---|---|---|---|
| RQ1: Structured requirement có cải thiện test case không? | GAP-01, GAP-02 | Requirement Analysis, Test Design, Traceability | Test-case validity, requirement coverage, unsupported-test rate, ambiguity resolution rate, số chỉnh sửa thủ công |
| RQ2: DOM/accessibility grounding có cải thiện first-run execution không? | GAP-03 | UI Explorer/Grounder, Playwright Generator | Locator validity, locator uniqueness, first-run execution rate, element-not-found rate, tỷ lệ chạy đến assertion |
| RQ3: Constrained repair có giữ nguyên ý nghĩa test không? | GAP-04, GAP-05 | Failure Classifier, Repair Policy, Human Approval | Repair success rate, semantic preservation rate, assertion weakening rate, approval rate, số vòng repair |
| RQ4: Hệ thống giảm bao nhiêu công sức thủ công? | GAP-06 | Toàn bộ pipeline | Thời gian hoàn thành, số thao tác/chỉnh sửa, số approval, chi phí/token nếu áp dụng |

## 8. Phạm vi tuyên bố novelty

Đề tài không tuyên bố phát minh mới từng thành phần riêng lẻ: LLM-based test generation, Playwright locator generation, requirement structuring, traceability, self-healing và human approval đều đã tồn tại dưới các hình thức khác nhau (xem ma trận mục 3). Novelty dự kiến nằm ở **cách tích hợp và kiểm soát** các thành phần này trong một pipeline Playwright Python bán tự động, cùng mô hình traceability và repair policy có thể audit — đặc biệt là **ambiguity detection + approval trước generation** (không nguồn nào có) và **phạm vi traceability kéo dài tới repair/approval** (chưa nguồn nào bao phủ).

Đề tài cũng không đặt mục tiêu: suy luận hoàn toàn test oracle từ requirement mơ hồ; tự sửa source code của ứng dụng được kiểm thử; cho phép agent tự động xóa/skip/làm yếu assertion để đạt trạng thái pass; thay thế hoàn toàn kiểm thử viên; hoặc chứng minh hiệu quả trên mọi loại ứng dụng/kiểm thử.

## 9. Kết luận và việc còn lại

Research gap trung tâm không phải là thiếu công cụ sinh Playwright test, mà là thiếu cơ chế bảo đảm test được sinh **có căn cứ, có truy vết, có bằng chứng UI và được sửa trong giới hạn an toàn**. Bộ 12 nguồn **củng cố** cả sáu GAP: đặc biệt GAP-04/GAP-05 có bằng chứng công nghiệp mạnh (SRC-008) cho sự cần thiết của human approval và constrained repair, còn GAP-01 xác nhận **ambiguity detection là khoảng trống rõ nhất** (✗ trên toàn bộ 12 nguồn). Đề tài vì vậy nên được định vị là một hệ thống hỗ trợ kiểm thử viên ra quyết định, trong đó AI thực hiện phân tích, sinh và đề xuất; con người giữ quyền quyết định đối với requirement, test oracle và mọi repair làm thay đổi ý nghĩa kiểm thử.

**Việc còn lại trước khi đưa vào luận văn chính thức:**

1. Bổ sung nguồn **peer-reviewed chuyên về ambiguity/inconsistency detection trong requirements** — mảng hiện chưa có nguồn nào trong bộ 12 triển khai (SRC-009 là preprint chưa peer-review; các nguồn còn lại không đụng ambiguity).
2. Bổ sung nghiên cứu về **semantic-preserving repair** và **human–AI collaboration/approval workflow** ở mức peer-reviewed để củng cố C4.
3. Đối chiếu các con số dễ gây hiểu nhầm khi trích (đã ghi trong từng SRC note): ví dụ SRC-008 "70% vs strict 50%", SRC-010 "81% component-isolation ≠ 40% end-to-end", SRC-012 "98.8% ở config/benchmark cụ thể".
