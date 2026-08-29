# Source Reading Notes — LLM Test Case Scenario Generation Tool

## Thông tin nguồn

- Tiêu đề: A Tool for Test Case Scenarios Generation Using Large Language Models
- Tác giả/tổ chức: Abdul Malik Sami, Zeeshan Rasheed, Muhammad Waseem, Zheying Zhang, Tomas Herda, Pekka Abrahamsson (Tampere University, Jyväskylä University, Austrian Postal Service)
- Năm: 2024
- Loại nguồn: Preprint (arXiv, proof-of-concept / early report)
- Mã DOI/arXiv/tài liệu: [arXiv:2406.07021v1](https://arxiv.org/abs/2406.07021) [cs.SE], 11 Jun 2024
- Ngày đọc: 2026-07-19
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Bài báo giải quyết việc tự động hóa sinh **test case scenarios** từ user requirements. Vấn đề đặt ra: viết test script/tự động hóa test cần tài liệu test suite bao phủ đầy đủ functional requirements trong phạm vi và thời gian hạn chế, trong khi requirement liên tục thay đổi. Nhóm mở rộng một công cụ web sẵn có (SLR-GPT, Sami et al. 2024): lấy các user story đã được ưu tiên hóa làm đầu vào, rồi dùng LLM agent + prompt engineering để sinh test case scenarios cho từng requirement, xuất ra CSV để tích hợp với các công cụ quản lý test.

## Các phần đã đọc

- **Abstract/tóm tắt:** LLM được dùng rộng rãi trong SE (sinh code, tài liệu, review, viết test script). Bài tập trung sinh requirement dạng epic + high-level user story và crafting test case scenarios từ các story đó. Giới thiệu công cụ web dùng LLM-based agent + prompt engineering để tự động sinh test case scenarios đối chiếu với user requirements.
- **Introduction / Problem statement:** Chuyển user requirement thành technical spec chính xác là thách thức; testing xác nhận requirement được đáp ứng theo acceptance criteria và cần duy trì traceability. Bài đặt 2 RQ (Bảng 1): (1) LLM có thể áp dụng thế nào để sinh test case scenarios/suites; (2) hạn chế và cơ hội của việc dùng LLM cho test suite generation. Bốn hướng cải tiến: nhận đầu ra prioritized stories làm input, dùng OpenAI agent-style API + prompt engineering để sinh scenario, cho tải test suite dạng CSV, và phân tích performance + content.
- **Architecture/phương pháp (Section 3):** Công cụ web tích hợp React + Flask + OpenAI. Ba bước: Tool Development (mở rộng công cụ sẵn có), Test Case Scenarios Generation (user nhập requirement hoặc upload user story → LLM sinh test case & scenario cho từng requirement), Evaluation & Output (phân tích performance + content, verify conformance).
- **Evaluation (Section 4):** Kiến trúc: React/CSS/JS + ANT Design (frontend), Flask (backend), API tương tác GPT-3.5. Bước 1 sinh scenario dạng JSON (ví dụ user story của "researcher" trong hệ SLR-GPT, Test Case 1/Test Case 5). Bước 2 export CSV để tích hợp JIRA, Azure DevOps, RE tools. Content analysis gọi agent API và parse NL bằng regular expressions; chỉnh temperature để đạt độ chính xác.
- **Limitations (Section 5) & Future Work:** Hallucination, cần tự động hóa content analysis, chi phí OpenAI API. Tương lai: benchmarking framework, khảo sát open-source LLM, sinh **test case code** (Python/Node.js), và co-pilot dùng RAG + LangChain.

## Phương pháp

Pipeline khái niệm: `prioritized user stories (input) → LLM agent + prompt engineering (GPT-3.5) → test case scenarios per requirement (JSON) → export CSV`. Frontend React (ANT Design), backend Flask cung cấp API gọi GPT-3.5. Không có mô tả prompt template chi tiết, không có DSL/schema oracle, không có tương tác với UI/DOM của hệ under test. Việc "kiểm chứng" đầu ra dựa trên content analysis: gọi agent API, dùng regex để bóc tách phản hồi NL và điều chỉnh tham số (temperature) qua nhiều vòng chạy cho tới khi khớp hành vi kỳ vọng — mang tính thủ công/định tính.

## Dữ liệu hoặc ứng dụng thực nghiệm

- Bối cảnh minh họa là hệ **SLR-GPT** (systematic literature review). User story ví dụ: "As a researcher, I aim to formulate questions that align with my research objectives...".
- Ví dụ Test Case 1 (researcher cung cấp keyword rõ ràng) và Test Case 5 (mục tiêu có ràng buộc, ví dụ "ethical considerations in AI applications under GDPR").
- Không có dataset chuẩn/benchmark, không có tập requirement quy mô lớn, không có bộ bug để đo bug detection. Đây là **proof of concept / preliminary study** (7 trang).

## Tiêu chí đánh giá

- **Performance:** thời gian sinh scenario trung bình ~2 giây cho mỗi prioritized requirement.
- **Content analysis:** parse phản hồi NL bằng regex, chỉnh temperature, chạy nhiều vòng để kết quả khớp hành vi kỳ vọng; "verify conformance".
- Đánh giá dựa trên user feedback, mang tính định tính. Không có metric định lượng (precision/recall/coverage/accuracy).

## Kết quả chính

- Công cụ sinh được test case scenarios cho từng prioritized requirement, trung bình ~2 giây/requirement.
- Đầu ra dạng JSON, thân thiện, tải xuống được dưới dạng CSV để dùng với JIRA/Azure DevOps/RE tools.
- Cho thấy GPT-3.5 có thể diễn giải ngữ cảnh từ user story và tạo test suite bao phủ nhiều edge case/kịch bản người dùng.
- Là bằng chứng khái niệm (proof of concept) cho việc tích hợp LLM vào vòng đời testing/documentation, không kèm số liệu đo lường chặt chẽ.

## Hạn chế

- **Nghiên cứu sơ bộ:** proof of concept, không có evaluation định lượng, không benchmark, phạm vi minh họa hẹp (một hệ SLR-GPT).
- **Hallucination:** LLM sinh nội dung không khớp input; đề xuất RAG/fine-tuning để giảm nhưng chưa triển khai.
- **Content analysis thủ công:** phụ thuộc regex + chỉnh temperature nhiều vòng; chưa tự động hóa/đảm bảo độ chính xác ở quy mô.
- **Chi phí:** phụ thuộc OpenAI API, có thể không khả thi tài chính cho mọi tổ chức.
- **Chỉ sinh scenario mức cao (NL/JSON), không sinh test code thực thi**, không grounding trên UI, không oracle tự động, không traceability triển khai thực tế. Sinh test code là future work.
- Chỉ dùng GPT-3.5; chưa so sánh model hay open-source LLM.

## Liên quan đến đề tài

- Structured requirements: **Một phần yếu** — dùng prioritized user story/epic (NL bán cấu trúc) làm input; không có schema chuẩn hóa requirement hay resolve ambiguity.
- Traceability: **Không triển khai** — Introduction nhấn mạnh tầm quan trọng của traceability nhưng công cụ không có liên kết requirement→test cụ thể.
- DOM grounding: **Không** — đầu ra là scenario NL/JSON mức cao, không tương tác/định vị trên UI/DOM.
- Oracle validation: **Rất yếu** — scenario có mô tả "expectation"/expected output dạng NL nhưng không có oracle formal hay validation tự động.
- Human approval: **Một phần** — có human-in-the-loop (user nhập requirement, review đầu ra, feedback) nhưng không có approval gate/quy trình phê duyệt rõ ràng.
- Constrained repair: **Không** — không có cơ chế self-healing/repair.
- Playwright support: **Không** — xuất CSV/JSON cho công cụ quản lý test; sinh code test (Python/Node.js) chỉ là future work, không nhắc Playwright.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Tự động sinh test case scenarios từ user requirements/prioritized user stories bằng LLM agent + prompt engineering.
2. **Đầu vào là gì?** User requirements / prioritized user stories (epic, high-level story) dạng NL; có thể upload user story định sẵn.
3. **Đầu ra là gì?** Test case scenarios cho từng requirement dạng JSON, tải xuống CSV; là scenario mức cao, không phải test code thực thi.
4. **Có chuẩn hóa requirement không?** Không chuẩn hóa formal; chỉ dùng user story đã ưu tiên hóa từ công cụ trước (có sinh epic + story nhưng không có schema/standardization).
5. **Có phát hiện ambiguity không?** Không — không đề cập detector/clarification cho requirement mơ hồ.
6. **Có traceability không?** Không triển khai; chỉ nêu tầm quan trọng ở phần lý thuyết.
7. **Có grounding trên UI không?** Không — không có DOM/screenshot/UI grounding.
8. **Có xác định test oracle không?** Chỉ mô tả expected output dạng NL trong scenario; không có oracle validation tự động.
9. **Có human approval không?** Human-in-the-loop qua input + review + feedback, nhưng không có approval gate formal.
10. **Có kiểm soát repair không?** Không có cơ chế repair/self-healing.
11. **Đánh giá trên dữ liệu nào?** Đánh giá sơ bộ định tính trên bối cảnh SLR-GPT (sinh research question); ~2s/requirement, content analysis bằng regex; không có dataset/benchmark chuẩn.
12. **Hạn chế là gì?** Hallucination, content analysis thủ công chưa scale, chi phí API; nghiên cứu proof-of-concept, không benchmark, chưa sinh test code/grounding/oracle/traceability.

## Trích dẫn hoặc ý cần kiểm tra lại

- Con số "trung bình ~2 giây/requirement" (Section 4.3) không kèm mô tả phương pháp đo/khối lượng mẫu — cần thận trọng khi trích, không nên diễn giải thành hiệu năng đã được benchmark.
- Tuyên bố "verify the conformance" / "results match the expected behavior" là định tính, dựa trên regex + chỉnh temperature qua nhiều vòng; không có metric precision/recall/coverage kèm theo.
- Chỉ dùng GPT-3.5; kết quả có thể khác đáng kể với model mới hơn — không suy rộng cho LLM hiện tại.
- Một số câu trong PDF có lỗi diễn đạt/chính tả (OCR/preprint); khi trích dẫn nguyên văn nên đối chiếu bản arXiv.

## Nhận xét của nhóm

Đây là nguồn **early/proof-of-concept mức nhẹ**, giá trị chính là làm **baseline và động lực (motivation)** hơn là phương pháp để so sánh trực tiếp. Nó minh họa hướng "LLM sinh test scenario từ requirement" nhưng dừng ở scenario NL/JSON: không grounding UI/DOM, không oracle validation tự động, không traceability, không repair, không sinh test thực thi (Playwright). Chính những khoảng trống này trùng khớp với đóng góp đề tài — dùng để định vị rõ điểm mới của nhóm so với thế hệ công cụ LLM-to-test-scenario thời kỳ đầu. So sánh gần với [[SRC-004-webtestpilot]] (agentic, có oracle + DOM grounding) và [[SRC-003-rbtg-survey]] (khảo sát requirements-based test generation) cho thấy rõ mức độ trưởng thành khác nhau của các hướng.
