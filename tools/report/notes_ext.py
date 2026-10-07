"""Nhận xét viết tay cho các mục kết quả đợt 2, viết SAU khi đọc JSON kết quả thật.

Số liệu dẫn trong văn đã đối chiếu với: datasets/processed/eval_deepseek-chat.json (47 yêu cầu), rq1_results.json (v1),
rq1_results_v2.json (v2), rq3_results*.json, rq2_v2_r*.json.
"""

RQ1_AMB = [
    "Trên tập mở rộng, recall vẫn cao (0,90) nhưng precision giảm còn 0,44. Hai loại kéo precision xuống là "
    "missing_precondition (1 đúng, 9 gắn nhầm) và underspecified_action (1 đúng, 11 gắn nhầm). Nhiều yêu cầu trong tập "
    "không nêu điều kiện trước, ví dụ đăng ký học phần hay xuất kho không nói người thao tác phải đăng nhập, nên gắn cờ "
    "missing_precondition cho chúng không hẳn là sai. Nhãn gold "
    "chỉ chèn một khuyết tật chủ đích cho mỗi yêu cầu, nên các khuyết tật tự nhiên khác của văn bản bị tính là FP. Vì "
    "vậy precision đo được là cận dưới; để kết luận chắc hơn cần nhiều người gán nhãn độc lập trên cùng tập.",
    "conflict và vague_quantifier đạt F1 1,00 trên cả tập 15 và tập 47 yêu cầu, cả ba mâu thuẫn toàn cục đều được bắt.",
]

RQ1_TESTGEN = [
    "Ở phiên bản 1, đưa thẳng tài liệu cho LLM cho độ phủ 95% với 168 test, còn pipeline cho 92% với 304 test. Chênh lệch "
    "độ phủ không có ý nghĩa thống kê. Điểm khác lớn là tỉ lệ test không căn cứ: 32% ở direct và 45% ở pipeline. Bảng "
    "theo loại test cho thấy nguồn gốc: error_guessing gần như luôn bị bịa ở cả hai nhánh, và pipeline sinh nhiều "
    "negative hơn hẳn (114 so với 42) vì Test Design Agent làm việc trên từng yêu cầu một và cố tìm ca âm bản cho mỗi "
    "yêu cầu kể cả khi tài liệu không nói hệ thống phản ứng thế nào. Ví dụ ở tài liệu thư viện, pipeline sinh \"gia hạn "
    "sách đã trả thì bị từ chối\", một luật tài liệu không hề nêu.",
    "Tách theo use case, pipeline có 34% test không căn cứ ở use case sạch và 58% ở use case có khuyết tật chèn sẵn. Nghĩa "
    "là phần lớn test bịa xuất phát từ yêu cầu mơ hồ, đúng loại yêu cầu mà cổng AG-01 được thiết kế để chặn.",
    "Phiên bản 2 thêm một quy tắc cho cả hai nhánh. Tỉ lệ không căn cứ giảm mạnh (direct 32% xuống 3%, pipeline 45% xuống "
    "9%) nhưng độ phủ cũng giảm (direct 95% xuống 75%, pipeline 92% xuống 81%), chủ yếu ở điều kiện negative và biên: "
    "model trở nên dè dặt cả với ca tài liệu có nêu. Dưới cùng quy tắc, pipeline phủ nhiều hơn direct 5 điều kiện, rõ "
    "nhất ở ca biên nhờ BVA tất định, nhưng chênh lệch vẫn không có ý nghĩa thống kê. Khi mô phỏng thêm cổng AG-01, test "
    "không căn cứ còn 4% nhưng độ phủ chỉ còn 52%: các yêu cầu mơ hồ chưa được làm rõ thì chưa có test.",
    "Trả lời RQ1 trên tập này: chuẩn hoá yêu cầu có cấu trúc không làm tăng độ phủ có ý nghĩa thống kê so với đưa thẳng "
    "tài liệu. Lợi ích đo được nằm ở chỗ khác. Mọi test truy vết được về một yêu cầu có ID (100% so với 0%). Cờ mơ hồ "
    "cho phép chặn đúng phần yêu cầu sinh ra nhiều test bịa nhất. Ca biên được bảo đảm bằng BVA. Yếu tố ảnh hưởng mạnh "
    "nhất tới độ tin cậy của test là quy tắc sinh test: đổi một quy tắc làm tỉ lệ test bịa giảm từ 32–45% xuống 3–9%, "
    "mạnh hơn nhiều so với khác biệt giữa hai nhánh.",
    "Giám khảo là chính model đã sinh test (DeepSeek), có thể thiên vị cách diễn đạt của nó. Một mẫu ngẫu nhiên 20% các "
    "phán quyết đã được xuất ra CSV để nhóm chấm lại và tính hệ số kappa; khi chưa có kết quả chấm tay, các con số độ phủ "
    "và không căn cứ cần được đọc như ước lượng của giám khảo LLM.",
]

# Phân loại tay cho phép kiểm assertion rỗng (giải thích trong RQ2_V2):
EXTRA_TARGET_WEAK = ["PT-04"]  # oracle fail vì timeout nên không kiểm được; trạng thái kỳ vọng = trạng thái ban đầu
MANUAL_LLM_VACUOUS = {"aria_loop": ["UP-05"]}  # không có bước thao tác; nth(0) trỏ vào thẻ <code> giải thích

RQ2_V2 = [
    "Ba lần lặp cho kết quả ổn định. Nhánh aria đạt 39–41/50, cao hơn baseline 34–36/50, nhưng ở cả ba lần chênh lệch "
    "đều không có ý nghĩa thống kê (p từ 0,09 đến 0,27). Nhánh aria_loop đạt 48–50/50, hơn baseline và hơn aria có ý "
    "nghĩa thống kê ở cả ba lần (p ≤ 0,016), và không làm mất target nào mà aria đạt. Vòng lặp phải sinh lại 8–10 target "
    "mỗi lần. Như vậy, đưa cây trợ năng vào prompt là chưa đủ: phần tạo ra khác biệt là phản hồi grounding, tức đếm phần "
    "tử khớp trên trang thật kể cả sau điều hướng, rồi cho LLM sửa đúng chỗ locator khớp 0 hoặc nhiều phần tử.",
    "Tỉ lệ pass gần 100% buộc phải hỏi thêm: các test pass này có thật sự kiểm hành vi không. Phép kiểm assertion rỗng "
    "(tools/rq2_vacuity.py) bỏ mọi bước fill và click khỏi script đã pass rồi chạy lại; vẫn pass nghĩa là assertion không "
    "phụ thuộc vào hành động. Chạy phép kiểm trên chính oracle viết tay cho thấy một số target yếu từ gốc. Ở SD-13 và "
    "PT-04 (đăng xuất rồi kiểm đang ở trang đăng nhập) và UP-03, trạng thái kỳ vọng trùng với trạng thái ban đầu. Ở PT-02, "
    "thẻ #error chứa sẵn câu thông báo trong DOM ngay khi tải trang và chỉ được hiện ra bằng CSS, nên mọi assertion bằng "
    "văn bản đều pass mà không cần bấm Submit. Catalog cần bổ sung assertion phân biệt được trạng thái trước và sau "
    "(ví dụ kiểm class hiển thị), nằm ngoài DSL hiện tại.",
    "Trừ các target yếu, phép kiểm tìm ra assertion rỗng do chính LLM gây ra, và chúng tập trung ở nhánh aria_loop. Ở cả "
    "ba lần, PT-03 dùng get_by_text(\"Your password is invalid!\").nth(0) và nth(0) trỏ vào đoạn hướng dẫn trên trang chứ "
    "không phải thông báo lỗi. UP-05 không có bước thao tác nên phép kiểm tự động không áp dụng; kiểm tay cho thấy "
    "get_by_text(\"Welcome UserName!\").nth(0) trỏ vào một thẻ code trong đoạn giải thích. Cả hai đều xuất phát từ cùng "
    "một cơ chế: khi grounding báo locator khớp nhiều phần tử, LLM chọn cách rẻ nhất là thêm nth để locator khớp đúng "
    "một, và grounding chỉ đếm số lượng nên chấp nhận. Locator hợp lệ về kỹ thuật nhưng sai về ngữ nghĩa, đúng loại rủi "
    "ro mà GAP-03 nêu. Sau khi trừ 2 ca này, aria_loop còn 46–48 pass có ý nghĩa mỗi lần, vẫn cao hơn rõ rệt aria "
    "(39–41) và baseline (33–35, ở hai lần lặp còn script để kiểm).",
    "Trả lời RQ2: kết hợp yêu cầu với cây trợ năng cải thiện tỉ lệ script chạy đạt ở lần đầu khi cây trợ năng được dùng "
    "trong một vòng kiểm chứng (68–72% lên 96–100%), còn chỉ đưa vào prompt thì cải thiện chưa đủ chắc chắn. Grounding "
    "bằng cách đếm phần tử không đủ để bảo đảm locator đúng ngữ nghĩa; cần thêm một tầng kiểm tra như phép kiểm assertion "
    "rỗng, hoặc cấm nth trên assertion.",
]
RQ3 = [
    "Kết quả chính ổn định qua hai lần chạy. Nhánh unconstrained biến 8/17 lỗi nghiệp vụ thật thành test pass (lần đầu "
    "10/17) và làm yếu assertion 18 lần (lần đầu 21). Hai kiểu che lỗi lặp lại đúng như [8] mô tả. Kiểu thứ nhất là sửa "
    "giá trị kỳ vọng cho khớp với bug: ở S1, assertion \"Invalid username or password\" bị đổi thành \"Something went "
    "wrong\"; ở S2, tổng tiền kỳ vọng \"Total: $39.98\" bị đổi thành \"Total: $9.99\", đúng con số sai mà app đang hiển "
    "thị vì bỏ qua món đầu tiên. Kiểu thứ hai là chèn thêm bước: ở S4, "
    "app chuyển nhầm sang trang hồ sơ sau đăng nhập, agent thêm một lệnh goto tới trang sản phẩm để test đi tiếp. Mỗi "
    "đề xuất đều \"hợp lý\" nếu nhìn riêng, và đều làm test mất khả năng phát hiện đúng lỗi nó được viết ra để bắt.",
    "Nhánh constrained không che lỗi nào trong 17 ca semantic ở cả hai lần chạy: 5 ca được đẩy lên người duyệt với mức "
    "High (đề xuất đổi assertion hoặc thêm bước), 12 ca còn lại vẫn fail vì không có cách sửa mức Low nào làm test pass. "
    "Cả hai đều là hành vi đúng. Với mutation technical, nhánh này sửa được 24/31 mà không làm yếu assertion nào, ngang "
    "nhánh unconstrained (23/31 sửa được mà không làm yếu, thêm 5 ca sửa được nhưng có làm yếu).",
    "Cái giá là 6/31 ca technical bị escalate oan. Cả sáu đều cần đổi locator bên trong một assertion: T5 đổi test-id "
    "của badge giỏ hàng, T7 đổi class của dòng tổng tiền. Policy hiện xếp mọi thay đổi trong assertion vào mức High, "
    "nên người duyệt phải xem các đề xuất này dù giá trị kỳ vọng không đổi. Hàm repair_gate đã phân biệt được trường hợp "
    "này (AG-03: đổi phần tử được kiểm, khác AG-04: đổi giá trị kỳ vọng), nên một hướng cải tiến là hạ nó xuống Medium "
    "kèm bằng chứng grounding. Đổi lại, một assertion trỏ sang phần tử khác cũng có thể là cách làm yếu test (xem phần "
    "assertion rỗng ở RQ2), nên nhóm giữ mức High ở phiên bản này.",
    "Chữa theo lô nâng số mutation technical sửa được từ 21 lên 24 ở cả nhánh heal và constrained: mutation đổi id cả "
    "ba ô đăng nhập giờ được chữa trong một đề xuất thay vì cần ba lượt. Nhánh heal chỉ dùng self-healing, không gọi LLM, "
    "đạt cùng 24/31 và không che lỗi nào. Trên ShopLab, phần LLM trong nhánh constrained hầu như không đóng góp thêm "
    "lần sửa nào được áp dụng: các đề xuất LLM đều chạm vào assertion hoặc bước, nên bị chuyển lên người.",
    "Trả lời RQ3 trên tập này: sửa có ràng buộc giữ được tỉ lệ sửa thành công tương đương sửa tự do với lỗi giao diện "
    "(24/31 so với 23/31 không làm yếu assertion), trong khi loại bỏ hoàn toàn việc che lỗi nghiệp vụ (0/17 so với 8–10/17). "
    "Chi phí là số đề xuất phải người duyệt: 11 ca mỗi lần chạy.",
]
RQ4: list[str] = []
RQ4_PENDING = [
    "Thí nghiệm có người tham gia chưa được tiến hành ở thời điểm viết chuyên đề. Toàn bộ công cụ đã sẵn sàng: hai bộ "
    "nhiệm vụ tương đương, giao diện ghi nhật ký thao tác vào DB, lệnh bấm giờ, xuất script từ DB và bộ chấm tự động bằng "
    "mutation. Bộ chấm đã được chạy thử với một bộ test viết tay: test kiểm đăng nhập được chấm hợp lệ, còn test thêm "
    "giỏ hàng không kiểm số trên giỏ bị chấm không hợp lệ đúng như thiết kế.",
]

RQ4_STATUS = "Đã có giao thức và công cụ; chưa có dữ liệu người tham gia"

THREATS = [
    "Ground truth RQ1 (10/15 tài liệu và toàn bộ 83 điều kiện gold) do Claude soạn nháp; nhãn mơ hồ chỉ chèn một khuyết "
    "tật mỗi yêu cầu. Cần nhóm review và nhiều người gán nhãn độc lập.",
    "Giám khảo RQ1 là chính model sinh test. Mẫu 20% đã xuất ra để chấm tay, kappa chưa có.",
    "Các quy tắc sinh test (RQ1 v2), trường nth, vòng lặp grounding và chữa theo lô được thêm SAU khi đọc kết quả lần đầu "
    "trên cùng dữ liệu. Các con số sau cải tiến là ước lượng lạc quan; cần tập kiểm tra mới để xác nhận.",
    "RQ2 dùng site demo, luồng ngắn; ShopLab của RQ3 nhỏ và do nhóm dựng. Kết quả không suy rộng cho ứng dụng doanh nghiệp.",
    "Thực nghiệm chủ yếu chạy với một model (deepseek-chat). Kết quả có thể khác với model khác.",
    "Người duyệt trong RQ3 là mô phỏng (duyệt mọi đề xuất Low, chuyển phần còn lại lên người).",
    "Hạ tầng mạng ảnh hưởng tới RQ2 (HTTP/2 tới Heroku); đã kiểm soát bằng --disable-http2 và chạy lại khi treo tải trang.",
]

CONCLUSIONS = [
    "Xây dựng được hệ thống chạy trọn luồng từ tài liệu yêu cầu tới script Playwright Python trên website thật: năm agent, "
    "giao diện Streamlit với các cổng duyệt AG-01..05, lưu version, quyết định duyệt append-only và chuỗi truy vết trong "
    "DB, kèm ứng dụng đích ShopLab và bộ công cụ thực nghiệm cho cả bốn câu hỏi nghiên cứu.",
    "RQ1: trên 15 tài liệu và 83 điều kiện gold, cấu trúc hoá yêu cầu không làm tăng độ phủ test case có ý nghĩa thống kê "
    "so với đưa thẳng tài liệu cho LLM. Lợi ích đo được là truy vết 100% và khả năng chặn yêu cầu mơ hồ ở AG-01, nơi "
    "phát sinh phần lớn test bịa. Quy tắc sinh test ảnh hưởng tới tỉ lệ test bịa mạnh hơn nhiều so với việc có cấu trúc.",
    "RQ2: trên 50 target thật, qua ba lần lặp, vòng lặp grounding (aria snapshot cộng phản hồi số phần tử khớp trên trang "
    "thật) nâng tỉ lệ script chạy đạt ở lần đầu từ 68–72% lên 96–100%, có ý nghĩa thống kê ở cả ba lần; chỉ đưa snapshot "
    "vào prompt thì chưa đủ chắc chắn. Phép kiểm assertion rỗng cho thấy 2 trong số các pass đó là pass giả do nth trỏ "
    "sai phần tử, nên grounding theo số lượng cần thêm kiểm tra ngữ nghĩa.",
    "RQ3: trên ShopLab, sửa lỗi có ràng buộc sửa được 24/31 lỗi giao diện mà không làm yếu assertion nào, ngang sửa tự do, "
    "và không che lỗi nghiệp vụ nào (0/17), trong khi LLM sửa tự do che 8–10/17 lỗi bằng cách đổi giá trị kỳ vọng hoặc "
    "chèn bước. Chi phí là khoảng 11 đề xuất mỗi lần chạy phải chuyển lên người, trong đó 6 là escalate oan.",
    "RQ4: giao thức, hai bộ nhiệm vụ và bộ chấm tự động bằng mutation đã sẵn sàng; dữ liệu người tham gia là phần việc "
    "còn lại.",
    "Bản thân quá trình đánh giá đã tìm ra nhiều lỗi mà unit test không bắt được: prompt thiếu đặc tả trường URL của goto, "
    "Chromium treo khi tải trang qua HTTP/2, self-healing chỉ chữa một locator mỗi lượt, BVA thiếu ngữ cảnh hành động, "
    "và locator nth trỏ sai phần tử. Mỗi lỗi đều được ghi lại cùng cách phát hiện và cách sửa.",
]

LIMITS = [
    "Dataset RQ1 nhỏ (15 tài liệu, 47 yêu cầu) và nhãn chưa được nhiều người gán độc lập.",
    "RQ2 trên 50 target demo, phần lớn luồng ngắn; snapshot 6.000 ký tự có thể không đủ cho trang lớn.",
    "RQ3 đo trên một ứng dụng nhỏ với 14 mutation do nhóm thiết kế; người duyệt là mô phỏng.",
    "RQ4 chưa có dữ liệu người tham gia ở thời điểm viết chuyên đề.",
    "DSL chưa có select, hover, nhấn phím, double click.",
    "Policy xếp mọi thay đổi bên trong assertion vào mức High, kể cả khi chỉ đổi locator mà giữ giá trị kỳ vọng; cách này "
    "an toàn nhưng tạo escalate oan khi giao diện đổi class hay id của phần tử được kiểm.",
]

FUTURE = [
    "Tiến hành thí nghiệm RQ4 theo giao thức đã chuẩn bị, 4–6 người tham gia.",
    "Mở rộng dataset RQ1, cho nhiều người gán nhãn độc lập, tính kappa cho giám khảo LLM.",
    "Đánh giá lại các cải tiến (quy tắc sinh test, vòng lặp grounding, chữa theo lô) trên tập dữ liệu mới, không dùng để "
    "phát triển chúng.",
    "Chạy RQ2, RQ3 với nhiều model (Gemma local, GPT) để đo độ dao động giữa model.",
    "Tách mức rủi ro của assertion: đổi phần tử được kiểm mà giữ giá trị kỳ vọng có thể là Medium kèm bằng chứng grounding.",
    "Mở rộng DSL (select, hover, phím) và thêm Alembic khi schema DB bắt đầu thay đổi trên SQL Server thật.",
]
