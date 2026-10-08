# Source Reading Notes — Playwright Codegen và Locator Policy

## Thông tin nguồn

- Tiêu đề: Test generator; Best Practices
- Tác giả/tổ chức: Microsoft Playwright
- Năm: 2026 (tài liệu được cập nhật liên tục)
- Loại nguồn: Tài liệu sản phẩm chính thức
- Mã tài liệu: [Codegen](https://playwright.dev/docs/codegen), [Best Practices](https://playwright.dev/docs/best-practices)
- Ngày đọc: 2026-07-15
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Codegen giảm công sức viết test và locator thủ công bằng cách ghi lại thao tác người dùng trên trình duyệt. Locator policy hướng đến test bền vững trước thay đổi DOM bằng cách ưu tiên thuộc tính người dùng nhìn thấy và explicit contract thay vì CSS/XPath phụ thuộc cấu trúc.

## Các phần đã đọc

- **Abstract/tóm tắt:** Không có abstract. Phần giới thiệu nói generator quan sát trang, ưu tiên role, text và test ID, rồi tinh chỉnh khi locator khớp nhiều phần tử để chọn duy nhất mục tiêu.
- **Introduction:** Người dùng thao tác trong browser; VS Code extension hoặc Playwright Inspector tạo mã hành động, assertion và locator.
- **Architecture/phương pháp:** `browser interaction → recorder/inspector → locator selection → Playwright code`. Có thể dùng Pick Locator, chỉnh locator và xem highlight trực tiếp. Codegen hỗ trợ viewport/device/color scheme/geolocation/language/timezone và lưu/nạp authentication state.
- **Evaluation:** Không có benchmark hoặc metric về độ ổn định locator; tài liệu cung cấp hướng dẫn và ví dụ sử dụng.
- **Limitations:** Codegen ghi lại hành vi, không hiểu requirement, không phát hiện ambiguity và chỉ sinh ba loại assertion trực tiếp là visibility, text, value.

## Phương pháp

Playwright ưu tiên locator gần với cách người dùng nhận biết UI: role và accessible name, text, hoặc test ID. Khi locator chưa duy nhất, generator thêm thông tin để thu hẹp. Best Practices khuyến cáo locator có auto-wait/retry, chaining/filtering khi cần, và tránh CSS/XPath gắn chặt với DOM. Test ID ổn định nhưng là contract do đội phát triển chủ động đưa vào mã.

## Dữ liệu hoặc ứng dụng thực nghiệm

Các trang web do người dùng mở trong phiên ghi. Không có corpus hoặc tập ứng dụng chuẩn được công bố để đánh giá locator policy.

## Tiêu chí đánh giá

Tài liệu nêu các mục tiêu định tính: locator duy nhất, resilient, dựa trên user-facing behavior, có auto-wait và retry. Không có số liệu fault rate, flakiness hay độ bền qua các phiên bản UI.

## Kết quả chính

Codegen cung cấp baseline thực dụng cho DOM/accessibility grounding. Policy phù hợp cho đề tài là ưu tiên `getByRole`, sau đó text hoặc explicit test ID; dùng filter/chaining để phân giải nhiều kết quả; chỉ dùng CSS/XPath như phương án cuối có lý do. Tuy nhiên, “locator duy nhất” không đồng nghĩa “locator đúng với requirement”.

## Hạn chế

- Không nhận đặc tả ngôn ngữ tự nhiên và không tạo trace requirement–test.
- Không đánh giá semantic correctness của hành động được người dùng ghi.
- Oracle giới hạn ở assertion người dùng chủ động chọn; không suy ra quan hệ dữ liệu, nhân quả hoặc xuyên trạng thái.
- Text/accessible name có thể đổi theo nội dung hoặc localization; test ID ổn định hơn nhưng cần sửa ứng dụng.
- Lưu authentication state tạo dữ liệu nhạy cảm; tài liệu yêu cầu giữ local và ignore/delete file.
- Không có repair loop hoặc chính sách phê duyệt thay đổi tự động.

## Liên quan đến đề tài

- Structured requirements: **Không**.
- Traceability: **Không** ở cấp requirement; chỉ giữ thứ tự thao tác ghi được.
- DOM grounding: **Có, mạnh** — role/accessibility, text, test ID, chaining/filtering và kiểm tra highlight live.
- Oracle validation: **Hạn chế** — visibility, text, value do người dùng chọn.
- Human approval: **Có trong luồng tương tác** — người dùng thực hiện thao tác, chọn/chỉnh/copy locator và được khuyên kiểm tra mã.
- Constrained repair: **Không**.
- Playwright support: **Có, native**.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Sinh nhanh Playwright code và locator bền hơn từ thao tác browser.
2. **Đầu vào là gì?** URL, thao tác người dùng, phần tử được chọn và tùy chọn emulation/authentication.
3. **Đầu ra là gì?** Playwright actions, locators và assertions visibility/text/value.
4. **Có chuẩn hóa requirement không?** Không.
5. **Có phát hiện ambiguity không?** Chỉ phát hiện locator khớp nhiều element và tinh chỉnh; đây không phải ambiguity của requirement.
6. **Có traceability không?** Không có traceability từ requirement.
7. **Có grounding trên UI không?** Có; đây là đóng góp trực tiếp nhất của nguồn.
8. **Có xác định test oracle không?** Chỉ oracle tường minh do người dùng chọn, không suy luận oracle.
9. **Có human approval không?** Có tính tương tác và review thủ công, dù không phải approval workflow chính thức.
10. **Có kiểm soát repair không?** Không có repair.
11. **Đánh giá trên dữ liệu nào?** Không có evaluation dataset hoặc kết quả định lượng.
12. **Hạn chế là gì?** Không hiểu requirement/oracle, thiếu traceability/evaluation và phụ thuộc độ ổn định thuộc tính UI.

## Trích dẫn hoặc ý cần kiểm tra lại

- Cần kiểm thử thực nghiệm thứ tự ưu tiên locator trên phiên bản Playwright khóa cho đồ án; tài liệu mô tả policy ở mức định tính.
- Phân biệt “DOM grounding” với “semantic grounding”: locator có thể chỉ đúng element nhưng hành động vẫn sai ý định requirement.

## Nhận xét của nhóm

Nguồn này nên được dùng để thiết kế locator policy và baseline locator, không nên dùng làm baseline requirements-based generation. Đề tài có thể chấm riêng locator validity (hợp lệ), uniqueness (duy nhất) và resilience (khả năng bị thay đổi); chấm test pass thôi sẽ không cho biết locator có bền hoặc có đúng ngữ nghĩa hay không.
