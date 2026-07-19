# Problem Statement

## 1. Bối cảnh

Trong quy trình phát triển phần mềm hiện đại, kiểm thử đầu-cuối (End-to-End Testing) là chốt chặn chất lượng quan trọng, nhưng việc chuyển thủ công tài liệu yêu cầu (SRS, use case, user story) thành kịch bản và mã kiểm thử rất tốn thời gian, dễ sai sót và khó bảo trì. Các Mô hình ngôn ngữ lớn (LLM) đã cho thấy tiềm năng tự động hóa quá trình này: nhiều nghiên cứu gần đây sinh được test case/scenario từ tài liệu yêu cầu (Sami và cộng sự, 2024; Masuda và cộng sự, 2025; Bhatia và cộng sự, 2024) và thao tác được trên web thật thông qua trình duyệt (Steward, 2024). Tuy nhiên, khi đưa vào môi trường thực tế, việc ứng dụng LLM để sinh và duy trì E2E test vấp phải **bốn thách thức cốt lõi** mà chưa một nghiên cứu hay công cụ đơn lẻ nào giải quyết trọn vẹn.

**Thứ nhất — Yêu cầu chưa được quản trị như một artifact có cấu trúc, và không có bước phát hiện mơ hồ.**
Các công cụ hiện tại thường nhận nguyên tài liệu/PRD làm ngữ cảnh rồi để LLM tự suy diễn. Ngay cả những phương pháp cấu trúc hóa tốt — biến requirement thành bộ ba condition–action–expectation (WebTestPilot, 2026) hay sinh test theo test design techniques của chuẩn ISO/IEC/IEEE 29119-4 (Masuda và cộng sự, 2025) — vẫn **giả định đầu vào tự chứa và đầy đủ**, thiếu cơ chế chuẩn hóa kèm định danh, nguồn gốc, và đặc biệt là **phát hiện yêu cầu thiếu/mơ hồ/mâu thuẫn** rồi chuyển cho con người xác nhận trước khi sinh test. Hệ quả là LLM dễ tạo ra test case hoặc expected result dựa trên giả định không được yêu cầu hỗ trợ; nghiên cứu trên SRS thực tế cũng cho thấy mô hình "hiểu hành vi hệ thống hạn chế chỉ từ tài liệu" nên bỏ sót test và sinh dư thừa (Bhatia và cộng sự, 2024).

**Thứ hai — Đứt gãy khả năng truy vết (Requirements Traceability).**
Trong quy trình truyền thống và cả các công cụ AI hiện tại, ma trận truy vết thường chỉ tồn tại dưới dạng tài liệu tĩnh (Excel, hệ thống ALM bên ngoài) tách biệt khỏi mã nguồn; khảo sát thực nghiệm cho thấy khoảng 80% người hành nghề coi chi phí bảo trì thủ công là rào cản chính khiến trace suy giảm âm thầm ("traceability debt") (Ruiz và cộng sự, dẫn trong ReqToCode, 2026). Hướng nhúng trace thành thuộc tính kiểm chứng lúc biên dịch (ReqToCode, 2026) rất mạnh cho mã viết tay nhưng chỉ đảm bảo **sự hiện diện cấu trúc (structural presence), không đảm bảo tính đúng ngữ nghĩa (semantic correctness)**, và không bao phủ chuỗi requirement → scenario → mã Playwright → kết quả thực thi → đề xuất sửa → quyết định phê duyệt. Khi LLM tự sinh test, thiếu liên kết hai chiều này khiến đội phát triển không xác định được đoạn mã nào phục vụ yêu cầu nào, yêu cầu nào chưa được kiểm thử, và một thay đổi khi tự sửa lỗi tác động tới artifact nào.

**Thứ ba — Neo giữ giao diện (DOM/UI Grounding) yếu, bộ định vị giòn và ảo giác.**
Ứng dụng web hiện đại (React, Vue) liên tục sinh tên lớp CSS động, khiến các locator truyền thống dễ gãy dù logic nghiệp vụ không đổi — một nghiên cứu công nghiệp quy tới 73% thất bại của test suite về lỗi locator chứ không phải lỗi chức năng thực sự (dẫn trong Beyond LLM, 2026). Khi dùng LLM để sinh hoặc tự sửa mã mà **không neo chặt vào DOM hoặc cây trợ năng (accessibility tree)**, mô hình rất dễ ảo giác — suy ra selector từ mẫu đồng xuất hiện trong dữ liệu huấn luyện thay vì DOM thật, sinh ra thao tác lên phần tử không tồn tại; một case study doanh nghiệp ghi nhận agent sinh mã bỏ qua công cụ kiểm chứng DOM và gây hàng loạt lỗi selector-timeout (Practical Limits, 2026). Ngược lại, các kỹ thuật grounding có tính xác định cao — ưu tiên `get_by_role`/ARIA/`data-testid` (Beyond LLM, 2026; Playwright best practices), lọc DOM và chỉ số hóa phần tử (Steward, 2024), hay định vị lại theo nhiều thuộc tính (Similo/HybridSimilo, 2025) — cho độ bền cao mà **không tốn chi phí API mỗi lần chạy**, nhưng chưa được kết hợp với ý định của requirement để chứng minh phần tử vừa **tồn tại vừa đúng ngữ nghĩa nghiệp vụ** của bước kiểm thử.

**Thứ tư — Rủi ro nghiêm trọng từ hệ thống tự sửa lỗi hoàn toàn tự chủ (Unrestricted Autonomous Repair).**
Để chống gãy test case, các công cụ tự động hóa được trang bị khả năng tự phục hồi (self-healing). Nhưng bằng chứng công nghiệp gần đây rất đáng lo ngại: trên 300 báo cáo thực thi tự trị, một hệ multi-agent chỉ hội tụ thật khoảng 50% (thay vì con số "bề mặt" 70%), 38% báo cáo không sinh nổi artifact chạy được, và — nghiêm trọng nhất — agent **âm thầm làm yếu lệnh kiểm chứng (assertion weakening)**, ví dụ đổi `expect(value).toBe(5)` thành `toBeTruthy()`, hoặc **xóa hẳn kịch bản kiểm thử đang lỗi (test-case deletion)** để đạt trạng thái "Pass" giả tạo (Practical Limits, 2026). Nguyên nhân gốc là **thiếu một test oracle đúng đắn** và thiếu ranh giới kiểm soát; chính nghiên cứu đó kết luận phải bắt buộc **giới hạn vòng lặp sửa lỗi, phát hiện trôi lệch ngữ nghĩa, và đưa mọi thay đổi assertion/scope cho con người phê duyệt**. Đây là ranh giới thiết kế mà các cơ chế repair xác định — định vị lại locator theo similarity (Similo, 2025), hay trích xuất lại chỉ selector hỏng (Beyond LLM, 2026) — có thể lấp phần "thay đổi kỹ thuật an toàn"; còn phần "thay đổi ngữ nghĩa" thì bắt buộc phải do con người quyết định.

**Tóm lại.**
Công nghệ AI tạo sinh cung cấp công cụ mạnh mẽ để tự động hóa kiểm thử, nhưng qua khảo sát 12 nguồn (tài liệu Playwright, khảo sát Requirements-Based Test Generation và các nghiên cứu 2024–2026 về requirement→test, grounding, traceability, oracle và self-healing), **chưa có một hệ thống thống nhất nào** giải quyết đồng thời: quản trị yêu cầu có cấu trúc kèm phát hiện mơ hồ, duy trì truy vết có thể kiểm toán từ yêu cầu đến mã và kết quả, neo giữ chính xác các thao tác trên cấu trúc DOM để chống ảo giác, và ngăn quá trình tự sửa lỗi làm sai lệch ý nghĩa nghiệp vụ. Do đó, việc nghiên cứu và xây dựng một **hệ thống Agentic AI bán tự động (semi-automated)** — kết hợp khả năng suy luận của LLM với các thuật toán xử lý DOM tĩnh (zero-cost) và áp dụng một "Khung tự chủ có kiểm soát" bắt buộc sự phê duyệt của con người (Human-in-the-loop) đối với các thay đổi logic cốt lõi — là một bài toán cấp thiết nhằm đảm bảo tính toàn vẹn, ổn định và hiệu quả của quá trình kiểm thử phần mềm.

## 2. Vấn đề nghiên cứu

Đề tài tập trung giải quyết bốn vấn đề, tương ứng với bốn câu hỏi nghiên cứu RQ1–RQ4:

1. **Structured requirement và ambiguity (RQ1):** chuẩn hóa tài liệu yêu cầu thành biểu diễn có cấu trúc (định danh, nguồn gốc, precondition, action, expected outcome, trạng thái duyệt) và phát hiện yêu cầu thiếu/mơ hồ/mâu thuẫn trước khi sinh test.
2. **Requirements traceability:** duy trì liên kết có thể kiểm toán từ yêu cầu đến test scenario, test case, mã Playwright, kết quả thực thi, đề xuất sửa và quyết định phê duyệt.
3. **DOM grounding (RQ2):** kết hợp tài liệu yêu cầu với DOM hoặc accessibility tree của website để hạn chế locator và thao tác không tồn tại, đồng thời phân biệt **locator validity** với **semantic correctness**.
4. **Constrained repair (RQ3):** giới hạn khả năng tự sửa của agent theo mức rủi ro và yêu cầu con người phê duyệt khi thay đổi assertion, expected result, bước kiểm thử hoặc liên kết truy vết; cùng với đó là đánh giá mức giảm công sức thủ công của toàn bộ pipeline (RQ4).

## 3. Giải pháp đề xuất

Xây dựng hệ thống Agentic AI bán tự động gồm:

- Requirement Analysis Agent — chuẩn hóa requirement thành schema có cấu trúc và gắn cờ mơ hồ.
- Test Design Agent — sinh test scenario/test case (positive, negative, boundary, alternative-flow) từ requirement đã duyệt.
- Playwright Generation Agent — sinh mã Playwright Python có neo giữ DOM/accessibility.
- Execution and Repair Agent — chạy test, phân loại lỗi và đề xuất sửa trong ràng buộc.
- Human Approval Service — cổng phê duyệt trước khi sinh test và trước mọi repair ảnh hưởng ngữ nghĩa.
- Traceability Service — duy trì liên kết artifact-level xuyên suốt pipeline.
- Giao diện Streamlit.
- Microsoft SQL Server để lưu dữ liệu dự án, kết quả và lịch sử phê duyệt.

## 4. Quan hệ truy vết cốt lõi

```text
Requirement
→ Test Scenario
→ Test Case
→ Test Step
→ Playwright Script
→ Execution Result
→ Repair Proposal
→ Approval Decision
```

## 5. Định vị đóng góp

Đề tài **không** tuyên bố phát minh mới từng thành phần riêng lẻ (sinh test bằng LLM, sinh locator Playwright, cấu trúc hóa requirement, traceability, self-healing, human approval đều đã tồn tại dưới nhiều hình thức). Novelty nằm ở **cách tích hợp và kiểm soát** các thành phần này trong một pipeline Playwright Python bán tự động: yêu cầu có cấu trúc + phát hiện mơ hồ, grounding DOM chống ảo giác, traceability kiểm toán được, và constrained repair theo mức rủi ro với human approval bắt buộc cho mọi thay đổi làm biến đổi ý nghĩa kiểm thử. Xem chi tiết khoảng trống và đối chiếu nguồn trong [research_gap](../literature-review/research_gap_v0.1.md).
