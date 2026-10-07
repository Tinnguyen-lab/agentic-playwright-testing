"""Nhận xét viết sau khi đọc kết quả thật: rq2_results_both.json (v2) và rq2_results_both_v1.json (v1).

Số liệu dẫn ở đây đã đối chiếu với JSON: v2 none 32/50, aria 35/50, cặp (29, 6, 3, 12); v1 none 21/50, aria 38/50,
cặp aria_only 19 / none_only 2; nguyên nhân v2 none {timeout 13, strict 5}, aria {strict 9, timeout 5, hạ tầng 1};
oracle 50/50.
"""
UNIT_TESTS = 83
ORACLE_PASS = 50

RQ2_DISCUSSION = [
    "Sau khi sửa đặc tả goto, nhánh aria đạt 35/50 so với 32/50 của baseline, hơn 3 target. Có 6 target chỉ aria đạt và 3 "
    "target chỉ baseline đạt, McNemar cho p ≈ 0,51. Với 50 target và một lần chạy, nhóm chưa có bằng chứng thống kê rằng "
    "aria snapshot của trang đầu cải thiện first-run pass rate tổng thể.",

    "Phân tích theo nguyên nhân cho thấy rõ hơn ngữ cảnh DOM đã làm gì. Nhóm lỗi \"không tìm thấy phần tử để thao tác\" giảm "
    "từ 13 xuống 5. Ví dụ điển hình là UI Testing Playground (2/8 lên 6/8) và OrangeHRM (0/3 lên 2/3). Không có snapshot, "
    "LLM đoán get_by_label(\"Password\"), nhưng ô mật khẩu của Sample App không có nhãn, chỉ có placeholder \"********\", còn "
    "nhãn của OrangeHRM không gắn với ô nhập. Snapshot cho LLM thấy tên truy cập thật (textbox \"********\", textbox "
    "\"Username\") nên nó viết get_by_role với đúng tên đó. Đây chính là loại lỗi mà grounding nhắm tới: locator trỏ tới "
    "một phần tử không tồn tại.",

    "Nhóm lỗi \"locator khớp nhiều phần tử\" lại tăng từ 5 lên 9. Khi có snapshot, LLM dùng đúng tên nó thấy, ví dụ button "
    "\"Add to cart\", trong khi trang sản phẩm của SauceDemo có sáu nút cùng tên. Practice Test Automation in nguyên văn "
    "thông báo lỗi trong phần hướng dẫn trên trang, nên get_by_text(\"Your username is invalid!\") khớp hai phần tử. Snapshot "
    "cho biết phần tử có tồn tại nhưng không cho biết locator có duy nhất hay không. DSL hiện tại cũng chưa có cách thu hẹp "
    "phạm vi (lọc theo khung sản phẩm, chọn phần tử thứ n). Ngữ cảnh DOM vì thế đổi loại lỗi từ \"không tồn tại\" sang "
    "\"không duy nhất\". Đây đúng là chỗ phân biệt locator validity với tính duy nhất trong GAP-03. Bước grounding đếm số "
    "phần tử khớp (mục 3.5.2) phát hiện được loại lỗi này trước khi chạy, nên hướng hợp lý là ghép hai cơ chế: snapshot cho "
    "LLM, grounding kiểm tính duy nhất, rồi trả kết quả đếm về cho LLM sinh lại.",

    "Snapshot chỉ chụp trang đầu nên không giúp với phần tử xuất hiện sau điều hướng. Ở TI-15 và PT-04, nút đăng xuất chỉ có "
    "sau khi đăng nhập. Baseline đoán role link và đạt; nhánh aria đoán role button và trượt. Ba target chỉ baseline đạt đều "
    "rơi vào trường hợp này hoặc lỗi hạ tầng: TI-08 của nhánh aria trượt vì The Internet không tải được cả sau lần chạy lại. "
    "Snapshot theo từng bước, dựa trên ground_flow, là cải tiến trực tiếp cho điểm yếu này.",

    "Bài học phương pháp từ lần đo thứ nhất đáng ghi lại. Lần đó cho 42% so với 76%, với 19 target chỉ aria đạt và 2 target "
    "chỉ baseline đạt (p < 0,001). Nhìn con số tổng, kết luận \"ngữ cảnh DOM gần như gấp đôi tỉ lệ đạt\" rất hấp dẫn, nhưng "
    "nó sai: phần lớn khoảng cách đến từ một dòng thiếu trong prompt. Hai việc giúp bắt được lỗi này là đọc từng script trượt "
    "thay vì chỉ đọc tỉ lệ, và có oracle chứng minh mọi target đều làm được, nên lỗi phải nằm ở phía sinh mã.",
]

CONCLUSIONS = [
    "Xây dựng được pipeline năm agent chạy từ tài liệu yêu cầu tới script Playwright Python trên website thật, với các cổng "
    "duyệt AG-01, AG-02 trên giao diện Streamlit, truy vết từ yêu cầu tới đề xuất sửa, và 83 unit test chạy offline.",
    "RQ1 (sơ bộ, 15 yêu cầu): sau khi siết prompt, Gemma 4 12B chạy local đạt micro-F1 0,77 và không gắn cờ nhầm yêu cầu "
    "sạch nào; DeepSeek đạt micro-F1 0,67 với recall 1,00. Loại missing_precondition vẫn khó nhất.",
    "RQ2: catalog 50 target trên 6 website, oracle viết tay đạt 50/50. Với deepseek-chat, aria snapshot trang đầu cho 35/50 "
    "so với 32/50 của baseline, khác biệt chưa có ý nghĩa thống kê (p ≈ 0,51). Ngữ cảnh DOM giảm lỗi phần tử không tồn tại "
    "(13 xuống 5) nhưng làm tăng lỗi locator không duy nhất (5 lên 9).",
    "Phát hiện và xử lý hai nguồn sai lệch trong phép đo: Chromium treo khi tải The Internet qua HTTP/2, và prompt thiếu đặc "
    "tả trường URL của goto. Lỗi thứ hai từng làm lần đo đầu thổi phồng hiệu ứng của ngữ cảnh DOM (42% so với 76%).",
    "Cơ chế sửa có ràng buộc hoạt động đúng thiết kế trên kịch bản demo: locator sai được chữa từ DOM sống, policy xếp mức "
    "rủi ro Low, đề xuất chờ người duyệt và không được tự áp dụng.",
]
