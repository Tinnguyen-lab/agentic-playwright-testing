# Source Reading Notes — WebTestPilot

## Thông tin nguồn

- Tiêu đề: WebTestPilot: Agentic End-to-End Web Testing against Natural Language Specification by Inferring Oracles with Symbolized GUI Elements
- Tác giả/tổ chức: Xiwen Teoh, Yun Lin, Duc-Minh Nguyen, Ruofei Ren, Wenjie Zhang, Jin Song Dong
- Năm: 2026
- Loại nguồn: Research paper (FSE 2026)
- Mã DOI/arXiv/tài liệu: [arXiv:2602.11724v3](https://arxiv.org/abs/2602.11724), DOI: 10.1145/3797115
- Ngày đọc: 2026-07-15
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

WebTestPilot giải quyết việc kiểm thử E2E từ natural-language specification khi agent vừa phải hành động vừa tự làm oracle. Trọng tâm là phân biệt inconsistency do bug thật với phán đoán thiếu ổn định/hallucination của LLM, đặc biệt với expectation ngầm phụ thuộc dữ liệu, nhân quả và lịch sử nhiều state.

## Các phần đã đọc

- **Abstract/tóm tắt:** Phương pháp neurosymbolic trừu tượng hóa GUI thành symbol và ràng buộc assertion bằng DSL. Báo cáo task completion 99%, bug-detection precision/recall 96%/96% và phát hiện 8 bug trong deployment no-code.
- **Introduction:** Existing navigation agents thiếu oracle; PinATA có assertion nhưng memory dạng text bị mất dữ liệu, mất dependency và bị giới hạn theo thời gian. LLM tự do còn tạo verdict không ổn định giữa các lần chạy.
- **Architecture/phương pháp:** `NL requirement → (condition, action, expectation) steps → oracle inference → symbols + Pythonic DSL pre/postconditions → action execution → pre/postcondition execution → retry/report bug`. Hệ thống duy trì Session/State/Element history, page reidentification và symbolization theo nhu cầu.
- **Evaluation:** 100 requirements trên BookStack (27), Indico (25), InvoiceNinja (25), PrestaShop (23), mỗi requirement có một bug nhân tạo; so với LaVague, NaviQAte và PinATA. Có thêm 23 bug GitHub được tái tạo, input transformations, model ablation và maintainability study.
- **Limitations:** Benchmark chỉ gồm bốn web app và có thể chưa phản ánh thực tế; metric có thể phạt đường đi hợp lệ khác; giả định requirement tự chứa, đầy đủ condition/action/expectation và đúng thứ tự.

## Phương pháp

Input parser dùng LLM tạo JSON steps; có cấu hình tự suy ra step thiếu. Oracle inference dùng trace để tìm data/causal/temporal dependencies, định nghĩa custom symbols bằng Pydantic và sinh predicate trong Python-extended DSL. Mỗi bước kiểm tra precondition, thực thi action rồi kiểm tra postcondition. Action grounding kết hợp UI-Venus-7B để dự đoán vùng thô với Set-of-Mark trên screenshot crop để chọn chính xác action/element. DOM tree edit distance cùng LLM screenshot comparison dùng để nhận diện lại page. Assertion thất bại có thể được sinh lại và retry tối đa `n`; thí nghiệm dùng `n=1`.

## Dữ liệu hoặc ứng dụng thực nghiệm

- 4 ứng dụng open-source có trên 5.000 GitHub stars, hoạt động/mature và có user documentation.
- 100 natural-language happy-path requirements dựa trên tài liệu và CRUD, theo ISTQB CTFL 4.0.
- 100 bug nhân tạo thuộc missing UI, data inconsistency, no-op action và navigation failure, thiết kế từ phân tích GitHub issues.
- 23 bug thật được tái tạo; deployment trên nền tảng no-code phát hiện 8 bug.

## Tiêu chí đánh giá

Task Completion (TC), Correct Trace (CT), bug-detection precision/recall, thời gian/token mỗi step, resilience khi UI thay đổi, robustness trước dropout/noise/summarize/restyle và ảnh hưởng model scale.

## Kết quả chính

WebTestPilot đạt TC và CT tổng 0,99; precision và recall phát hiện bug đều 0,96, cao hơn PinATA lần lượt 0,70 và 0,27 tuyệt đối. Nó phát hiện 22/23 bug thật so với 15/23 của PinATA. Median là 29 giây và 10k token/step. Trong study UI evolution, nó nhận diện lại widget đúng 39/40 so với Playwright script 29/40. Hiệu năng giảm đáng kể với model nhỏ; 7B được xem là ngưỡng khả dụng tối thiểu về chi phí, còn 72B đáng tin cậy hơn về hiệu năng.

## Hạn chế

- Requirement completeness là giả định mạnh; implementation hiện tại không có approval/clarification gate cho ambiguity dù Discussion đề xuất agent nên hỏi lại người dùng.
- Chỉ bốn ứng dụng và 100 happy-path requirements; loại crash và lỗi thuần cosmetic khỏi benchmark.
- Bug injection ổn định và reproducible nhưng không đại diện đầy đủ phân bố bug sản xuất.
- Evaluation có manual verification semantic correctness của assertions, nên chưa hoàn toàn tự động và có nguy cơ reviewer subjectivity.
- Retry assertion/action có thể giảm hallucination nhưng cũng cần kiểm soát để không che lỗi thật; paper không nghiên cứu approval cho thay đổi oracle.
- Chi phí 10k token/step còn cao; page reidentification là bottleneck chính.
- Hệ thống tạo/executed actions và DSL predicates, không tập trung sinh file Playwright test duy trì lâu dài như mục tiêu đồ án.

## Liên quan đến đề tài

- Structured requirements: **Có** — chuẩn hóa thành `(condition, action, expectation)` theo từng step.
- Traceability: **Có một phần mạnh** — step liên kết với precondition/action/postcondition và trace state; chưa có requirement ID/audit matrix như đề tài có thể bổ sung.
- DOM grounding: **Có, hybrid** — full-page screenshot, GUI grounding, Set-of-Mark và DOM tree/page reidentification.
- Oracle validation: **Có, đóng góp chính** — symbolized pre/postconditions và cross-state DSL.
- Human approval: **Không trong runtime**; con người tham gia tạo ground truth và manual semantic verification ở evaluation.
- Constrained repair: **Một phần** — retry giới hạn `n` khi assertion thất bại; đây không phải code-healing có patch approval.
- Playwright support: **Có trong benchmark/ground-truth scripts**, nhưng runtime approach không được trình bày như Playwright test generator.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Reliable oracle inference và bug detection cho agentic NL-to-E2E web testing.
2. **Đầu vào là gì?** Natural-language test requirement và các state/screenshot của ứng dụng web.
3. **Đầu ra là gì?** Structured steps, executable actions, DSL pre/postconditions và inconsistency/bug report.
4. **Có chuẩn hóa requirement không?** Có, thành condition–action–expectation; có thể cấu hình điền phần thiếu.
5. **Có phát hiện ambiguity không?** Chưa có detector/clarification workflow trong implementation; paper nêu đây là hướng cần làm.
6. **Có traceability không?** Có ở cấp step–predicate–state trace, nhưng chưa đầy đủ ở cấp requirement artifact/version.
7. **Có grounding trên UI không?** Có, bằng visual GUI grounding + Set-of-Mark và hỗ trợ DOM cho page/state representation.
8. **Có xác định test oracle không?** Có, bằng symbols và DSL cho explicit/implicit pre/postconditions.
9. **Có human approval không?** Không có approval gate runtime.
10. **Có kiểm soát repair không?** Có retry hữu hạn (`n=1` trong evaluation), nhưng không có policy phê duyệt sửa oracle/code.
11. **Đánh giá trên dữ liệu nào?** 100 requirements/100 injected bugs trên 4 app, 23 replicated real bugs, input perturbations, model scales và một deployment no-code.
12. **Hạn chế là gì?** Benchmark hẹp, complete-requirement assumption, manual verification, chi phí và thiếu ambiguity/human approval.

## Trích dẫn hoặc ý cần kiểm tra lại

- Công thức mô tả bug ở một đoạn PDF có dấu hiệu lỗi ký hiệu (`p(s)=⊤` cạnh `s` không thỏa predicate); khi trích công thức cần đối chiếu bản camera-ready/source.
- Kết quả 39/40 so với “Playwright 29/40” là study re-identification widget dưới UI changes, không nên diễn giải thành WebTestPilot tốt hơn Playwright trên mọi loại test maintenance.

## Nhận xét của nhóm

WebTestPilot là nguồn gần đề tài nhất cho oracle validation và bug-injected evaluation. Khoảng trống rõ để đồ án đóng góp là ambiguity detection + human approval trước khi cố định oracle, traceability artifact-level và constrained repair có audit log/budget. Khi so sánh, cần giữ cùng requirement, app version, model và retry budget để tránh lợi thế do pipeline khác nhau.
