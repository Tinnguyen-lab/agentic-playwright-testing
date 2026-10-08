# Source Reading Notes — Playwright Test Agents

## Thông tin nguồn

- Tiêu đề: Playwright Test Agents; Playwright release notes, version 1.56
- Tác giả/tổ chức: Microsoft Playwright
- Năm: 2025–2026
- Loại nguồn: Tài liệu sản phẩm chính thức
- Mã tài liệu: [Test Agents](https://playwright.dev/docs/test-agents), [Release notes](https://playwright.dev/docs/release-notes)
- Ngày đọc: 2026-07-15
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Tài liệu mô tả cách dùng LLM để hỗ trợ toàn bộ chu trình tạo Playwright test thay vì chỉ ghi lại thao tác. Ba agent tách trách nhiệm thành lập kế hoạch, sinh mã và sửa test thất bại. Đây là baseline sản phẩm trực tiếp cho đề tài vì đầu ra cuối cùng cũng là Playwright test và quy trình cũng dựa trên tương tác thật với ứng dụng.

## Các phần đã đọc

- **Abstract/tóm tắt:** Không có abstract theo cấu trúc bài báo. Phần giới thiệu nêu ba agent có thể chạy độc lập, tuần tự hoặc trong một agentic loop.
- **Introduction:** Planner khảo sát ứng dụng và sinh Markdown test plan; Generator biến plan thành Playwright Test; Healer chạy và tự động sửa test thất bại.
- **Architecture/phương pháp:** Pipeline chính là `yêu cầu + seed test + PRD tùy chọn → Planner → specs/*.md → Generator → tests/*.spec.ts → Healer`. Agent definitions là tập lệnh và MCP tools. `specs/`, `tests/`, seed test và comment liên kết spec là các artifact có thể kiểm tra.
- **Evaluation:** Không có benchmark, tập dữ liệu, baseline so sánh hoặc metric. Tài liệu chỉ minh họa bằng TodoMVC và ví dụ “Add valid todo”.
- **Limitations:** Tài liệu không định nghĩa phương pháp phát hiện yêu cầu mơ hồ, không công bố độ chính xác sinh test/sửa test, và không mô tả chi tiết guardrail của vòng lặp healer.

## Phương pháp

Planner chạy seed test để có đúng fixtures/hooks và trực tiếp khám phá ứng dụng. Plan chứa scenario, step, expected result và test data. Generator thực thi scenario để kiểm tra selector và assertion trên UI thật trước khi ghi test. Khi test thất bại, Healer phát lại bước lỗi, quan sát UI hiện tại, đề xuất thay đổi locator/wait/data, chạy lại cho đến khi test pass hoặc guardrail dừng; nếu cho rằng chức năng hỏng, nó có thể skip test.

## Dữ liệu hoặc ứng dụng thực nghiệm

Chỉ có ví dụ tài liệu trên TodoMVC. Đây là demonstration, không phải thực nghiệm có thiết kế.

## Tiêu chí đánh giá

Không được công bố. Có thể quan sát các tiêu chí vận hành là plan đọc được, test chạy được, selector/assertion được kiểm tra trực tiếp, và test sau healing pass hoặc bị skip; tài liệu không lượng hóa các tiêu chí này.

## Kết quả chính

Playwright cung cấp một baseline ba giai đoạn có artifact trung gian rõ ràng. Điểm đáng kế thừa là tách plan khỏi code, dùng seed test (Test mẫu có sẵn trong project) để giữ context dự án và kiểm chứng locator/assertion trực tiếp. Điểm đề tài cần vượt lên là chuẩn hóa requirement, phát hiện ambiguity (sự mơ hồ), traceability cấp requirement và kiểm soát repair minh bạch hơn (Ghi lại đầy đủ AI đã sửa gì, vì sao sửa và bằng chứng để người dùng xem xét).

## Hạn chế

- Không phải nghiên cứu thực nghiệm nên không thể kết luận độ hiệu quả tương đối.
- PRD chỉ là context tùy chọn; không có schema requirement bắt buộc hoặc bước xác nhận ambiguity.
- Traceability mới ở mức file/comment và ánh xạ spec–test “wherever feasible”, chưa phải ma trận requirement–scenario–step–assertion.
- Healer có thể biến test thành pass hoặc skip nhưng tài liệu không nêu ngân sách sửa, loại sửa được phép, approval gate hay cách ngăn sửa sai oracle.
- Không công bố cách phân biệt lỗi test với regression thật của ứng dụng.

## Liên quan đến đề tài

- Structured requirements: **Một phần** — Markdown plan có steps và expected results, nhưng không có schema/validation requirement chính thức.
- Traceability: **Một phần** — spec và seed được ghi trong test; có mục tiêu ánh xạ một-một giữa spec và test.
- DOM grounding: **Có** — khám phá UI, kiểm chứng selector/assertion trực tiếp và quan sát UI khi healing.
- Oracle validation: **Một phần** — expected results thành assertions và được kiểm chứng live, nhưng không có mô hình oracle độc lập.
- Human approval: **Không bắt buộc** — artifact dễ đọc và healer “suggests a patch”, nhưng quy trình được mô tả là có thể tự động.
- Constrained repair: **Một phần** — có guardrail và dừng/skip, nhưng guardrail không được đặc tả.
- Playwright support: **Có, native**.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Tự động hóa lập kế hoạch, sinh và sửa Playwright E2E tests bằng LLM agents.
2. **Đầu vào là gì?** Planner nhận yêu cầu, seed test và PRD tùy chọn; Generator nhận Markdown plan; Healer nhận tên test thất bại.
3. **Đầu ra là gì?** Markdown test plan, Playwright test suite và test đã pass hoặc bị skip.
4. **Có chuẩn hóa requirement không?** Một phần; Planner tạo plan có cấu trúc nhưng không chuẩn hóa requirement thành schema được kiểm tra.
5. **Có phát hiện ambiguity không?** Không được tài liệu mô tả.
6. **Có traceability không?** Một phần qua file spec, comment `spec`/`seed` và mục tiêu ánh xạ spec–test.
7. **Có grounding trên UI không?** Có, thông qua khám phá và xác minh live.
8. **Có xác định test oracle không?** Một phần qua expected results/assertions; không có oracle inference/validation riêng.
9. **Có human approval không?** Không có approval gate bắt buộc được mô tả.
10. **Có kiểm soát repair không?** Có đề cập guardrail và điều kiện dừng, nhưng thiếu chi tiết đủ để audit. (Guardrail là các quy tắc giới hạn những gì AI được phép làm và không được phép làm.)
11. **Đánh giá trên dữ liệu nào?** Không có evaluation dataset; chỉ có ví dụ TodoMVC.
12. **Hạn chế là gì?** Thiếu evaluation, ambiguity handling, traceability chi tiết và đặc tả repair safety.

## Trích dẫn hoặc ý cần kiểm tra lại

- Test Agents được giới thiệu trong Playwright 1.56.
- Khi dùng làm baseline thực nghiệm, cần khóa phiên bản agent definitions vì tài liệu yêu cầu tái sinh definitions sau mỗi lần nâng Playwright.
- Cần kiểm tra mã agent definition thực tế trước khi thiết kế protocol baseline; trang tài liệu chỉ mô tả hành vi cấp cao.

## Nhận xét của nhóm

Baseline này mạnh về tích hợp Playwright và khả năng tạo test chạy được, nhưng chưa trực tiếp giải quyết bài toán “requirement đáng tin cậy”. So sánh công bằng nên tách ít nhất ba metric: chất lượng plan, chất lượng test trước healing và chất lượng sau healing; nếu chỉ đo tỷ lệ pass cuối cùng, Healer có thể che khuất lỗi oracle hoặc lỗi generator.
