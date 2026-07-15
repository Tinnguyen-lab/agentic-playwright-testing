# Problem Statement

## 1. Bối cảnh

Trong quy trình kiểm thử phần mềm, kiểm thử viên thường phải đọc tài liệu yêu cầu, phân tích luồng nghiệp vụ, thiết kế test case và viết mã kiểm thử tự động bằng phương pháp thủ công. Quá trình này tốn thời gian, phụ thuộc nhiều vào kinh nghiệm và có nguy cơ bỏ sót luồng thay thế, dữ liệu không hợp lệ hoặc điều kiện biên.

Mô hình ngôn ngữ lớn có thể hỗ trợ sinh test case và mã kiểm thử từ yêu cầu tự nhiên. Tuy nhiên, đầu ra có thể chứa test case không có căn cứ, expected result không chính xác, locator không tồn tại hoặc sửa test theo hướng làm yếu assertion.

## 2. Vấn đề nghiên cứu

Đề tài tập trung giải quyết ba vấn đề:

1. **Requirements traceability:** duy trì liên kết từ yêu cầu đến test scenario, test case, mã Playwright và kết quả thực thi.
2. **DOM grounding:** kết hợp tài liệu yêu cầu với DOM hoặc accessibility tree của website để hạn chế locator và thao tác không tồn tại.
3. **Constrained repair:** giới hạn khả năng tự sửa của agent và yêu cầu con người phê duyệt khi thay đổi assertion, expected result, bước kiểm thử hoặc liên kết truy vết.

## 3. Giải pháp đề xuất

Xây dựng hệ thống Agentic AI bán tự động gồm:

- Requirement Analysis Agent.
- Test Design Agent.
- Playwright Generation Agent.
- Execution and Repair Agent.
- Human Approval Service.
- Traceability Service.
- Giao diện Streamlit.
- Microsoft SQL Server để lưu dữ liệu dự án, kết quả và lịch sử phê duyệt.

## 4. Quan hệ truy vết cốt lõi

Requirement → Test Scenario → Playwright Script → Execution Result
