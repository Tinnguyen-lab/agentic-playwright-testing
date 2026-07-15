# Kế hoạch Tuần 1

## Mục tiêu tuần

1. Hiểu và thống nhất bài toán nghiên cứu.
2. Chốt phạm vi và giới hạn đề tài.
3. Xác định research gap ban đầu.
4. Khởi tạo repository và quy trình làm việc nhóm.
5. Tạo ma trận khảo sát tài liệu.
6. Chuẩn bị đầu vào cho tuần 2.

## Ngày 1 — Khởi tạo dự án

- Tạo GitHub repository.
- Tạo nhánh `develop`.
- Tạo cấu trúc thư mục.
- Thêm thành viên còn lại.
- Commit bộ tài liệu nền tảng.

**Đầu ra:** repository hoạt động và cả hai thành viên clone được.

## Ngày 2 — Phân tích đề tài

- Review `problem_statement.md`.
- Review `scope.md`.
- Review `research_questions.md`.
- Đánh dấu điểm chưa rõ cần hỏi giảng viên.
- Chốt thuật ngữ sử dụng thống nhất.

**Đầu ra:** ba tài liệu được hai thành viên đồng thuận.

## Ngày 3 — Khảo sát giải pháp hiện có

Đọc và ghi chú tối thiểu:

- Playwright Test Agents.
- Playwright locator/code generation.
- Requirements-Based Test Generation survey.
- WebTestPilot.
- Các bài báo khác trong đề xuất.

**Đầu ra:** ít nhất 5 dòng trong literature review matrix.

## Ngày 4 — Xác định research gap

So sánh giải pháp theo các tiêu chí:

- Structured requirement representation.
- Ambiguity detection.
- Requirement–test traceability.
- DOM/accessibility grounding.
- Test oracle validation.
- Human approval.
- Constrained repair.
- Evaluation metrics.
- Support for Playwright Python.

**Đầu ra:** bảng research gap phiên bản 0.1.

## Ngày 5 — Chốt MVP

Xác định chức năng tối thiểu:

1. Upload tài liệu.
2. Trích xuất yêu cầu thành JSON.
3. Người dùng review yêu cầu.
4. Sinh test case có requirement ID.
5. Người dùng duyệt test case.
6. Khảo sát website và sinh Playwright Python.
7. Chạy test và lưu kết quả.
8. Đề xuất sửa locator hoặc synchronization.
9. Yêu cầu phê duyệt với thay đổi có ảnh hưởng ngữ nghĩa.
10. Hiển thị traceability matrix.

**Đầu ra:** MVP scope và danh sách chức năng ưu tiên.

## Ngày 6 — Lập kiến trúc sơ bộ

- Vẽ context diagram.
- Vẽ component diagram.
- Xác định input/output của từng agent.
- Xác định dữ liệu cần lưu trong SQL Server.
- Xác định các điểm human approval.

**Đầu ra:** `architecture_v0.1.md` hoặc sơ đồ draw.io.

## Ngày 7 — Review và báo cáo tuần

- Review deliverable.
- Ghi vấn đề tồn đọng.
- Ghi quyết định kỹ thuật.
- Chuẩn bị backlog tuần 2.
- Commit và tạo pull request.

**Đầu ra:** báo cáo tuần 1 và kế hoạch tuần 2.
