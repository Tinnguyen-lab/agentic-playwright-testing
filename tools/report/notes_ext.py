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
    "Ground truth RQ1 (20/25 tài liệu và toàn bộ 158 điều kiện gold) do Claude soạn nháp; nhãn mơ hồ chỉ chèn một khuyết "
    "tật mỗi yêu cầu. Cần nhóm review và nhiều người gán nhãn độc lập.",
    "Giám khảo RQ1 là chính model sinh test. Hai mẫu 20% (37 và 25 phán quyết) đã xuất ra để chấm tay, kappa chưa có.",
    "Các quy tắc sinh test (RQ1 v2), trường nth, vòng lặp grounding và chữa theo lô được thêm SAU khi đọc kết quả lần đầu "
    "trên cùng dữ liệu. Để kiểm mức lạc quan này, nhóm đo lại trên ba tập độc lập soạn sau khi chốt hệ thống (10 tài "
    "liệu RQ1, 12 target RQ2 trên 4 site mới, 8 mutation RQ3). Vòng lặp grounding và việc không che lỗi giữ được trên "
    "tập độc lập; tỉ lệ sửa lỗi giao diện của RQ3 thì không (mục 5.3.1). Các tập độc lập nhỏ, và cũng do Claude soạn.",
    "RQ2 dùng site demo, luồng ngắn; ShopLab của RQ3 nhỏ và do nhóm dựng. Kết quả không suy rộng cho ứng dụng doanh nghiệp.",
    "RQ1 chỉ chạy với deepseek-chat. RQ2 và RQ3 có thêm Claude Sonnet 5 (và Gemma 4 12B cho RQ2) nhưng chỉ một lần "
    "chạy mỗi model; Claude không cho đặt temperature = 0 nên so sánh giữa model không hoàn toàn cùng điều kiện.",
    "Người duyệt trong RQ3 là mô phỏng (duyệt mọi đề xuất Low, chuyển phần còn lại lên người).",
    "Hạ tầng mạng ảnh hưởng tới RQ2 (HTTP/2 tới Heroku); đã kiểm soát bằng --disable-http2 và chạy lại khi treo tải trang.",
]

CONCLUSIONS = [
    "Xây dựng được hệ thống chạy trọn luồng từ tài liệu yêu cầu tới script Playwright Python trên website thật: năm agent, "
    "giao diện Streamlit với các cổng duyệt AG-01..05, lưu version, quyết định duyệt append-only và chuỗi truy vết trong "
    "DB, kèm ứng dụng đích ShopLab và bộ công cụ thực nghiệm cho cả bốn câu hỏi nghiên cứu.",
    "RQ1: trên tập phát triển (15 tài liệu, 83 điều kiện gold), cấu trúc hoá yêu cầu không làm tăng độ phủ test case có ý "
    "nghĩa thống kê; trên tập độc lập (10 tài liệu, 75 điều kiện) pipeline phủ 72% so với 61%, có ý nghĩa thống kê "
    "(p = 0,039). Lợi thế về độ phủ vì vậy nhỏ và chưa ổn định; lợi ích ổn định là truy vết 100% và tỉ lệ test bịa thấp "
    "khi có quy tắc sinh test phù hợp. Quy tắc đó lại chặn luôn các ca negative suy ra từ điều kiện trước.",
    "RQ2: vòng lặp grounding (aria snapshot cộng phản hồi số phần tử khớp trên trang thật) nâng tỉ lệ script chạy đạt ở "
    "lần đầu từ 68–72% lên 96–100% trên 50 target qua ba lần lặp, và từ 17–33% lên 92% trên 12 target độc lập thuộc 4 "
    "site mới, có ý nghĩa thống kê ở mọi lần chạy của DeepSeek. Với Claude Sonnet 5 xu hướng giống nhau ở mức thấp hơn. "
    "Chỉ đưa snapshot vào prompt thì chưa đủ chắc chắn. Grounding theo số lượng vẫn để lọt pass giả do nth trỏ sai phần "
    "tử, và không bắt được vi phạm quy ước DSL như URL dạng mẫu.",
    "RQ3: trên ShopLab, sửa lỗi có ràng buộc không che lỗi nghiệp vụ nào ở cả hai model và hai tập mutation (0/17 và "
    "0/6), trong khi LLM sửa tự do che 8–12/17 và 4/6, model mạnh hơn che nhiều hơn. Tỉ lệ sửa lỗi giao diện ngang sửa "
    "tự do trên tập phát triển (24/31) nhưng giảm mạnh trên mutation độc lập (4/15), do policy xếp mọi thay đổi trong "
    "assertion vào mức High và self-healing chép cả nội dung động vào tên phần tử.",
    "RQ4: giao thức, hai bộ nhiệm vụ và bộ chấm tự động bằng mutation đã sẵn sàng; dữ liệu người tham gia là phần việc "
    "còn lại.",
    "Bản thân quá trình đánh giá đã tìm ra nhiều lỗi mà unit test không bắt được: prompt thiếu đặc tả trường URL của goto, "
    "Chromium treo khi tải trang qua HTTP/2, self-healing chỉ chữa một locator mỗi lượt, BVA thiếu ngữ cảnh hành động, "
    "locator nth trỏ sai phần tử, template chèn thẳng chuỗi của LLM vào mã Python (lỗi cú pháp, nguy cơ chèn mã), và DB "
    "trên SQL Server làm mất dấu tiếng Việt do dùng VARCHAR. Mỗi lỗi đều được ghi lại cùng cách phát hiện và cách sửa.",
]

LIMITS = [
    "Dataset RQ1 nhỏ (25 tài liệu, 86 yêu cầu, 158 điều kiện) và nhãn chưa được nhiều người gán độc lập.",
    "RQ2 trên 62 target demo thuộc 10 site, phần lớn luồng ngắn; snapshot 6.000 ký tự có thể không đủ cho trang lớn.",
    "RQ3 đo trên một ứng dụng nhỏ với 22 mutation do nhóm thiết kế; người duyệt là mô phỏng.",
    "Self-healing lấy nguyên tên hiển thị của phần tử, kể cả phần nội dung động như số đếm trong \"Basket (3)\".",
    "RQ4 chưa có dữ liệu người tham gia ở thời điểm viết chuyên đề.",
    "DSL chưa có select, hover, nhấn phím, double click.",
    "Policy xếp mọi thay đổi bên trong assertion vào mức High, kể cả khi chỉ đổi locator mà giữ giá trị kỳ vọng; cách này "
    "an toàn nhưng tạo escalate oan khi giao diện đổi class hay id của phần tử được kiểm.",
]

FUTURE = [
    "Tiến hành thí nghiệm RQ4 theo giao thức đã chuẩn bị, 4 sinh viên ngoài nhóm tham gia.",
    "Cho nhiều người gán nhãn độc lập dataset RQ1, tính kappa cho giám khảo LLM.",
    "Cho phép sinh ca negative suy ra từ điều kiện trước của yêu cầu, vẫn giữ quy tắc chống bịa phản ứng của hệ thống.",
    "Kiểm hợp đồng của DSL bằng một bước tất định trước khi chạy (URL đầy đủ trong expect_url, không có dấu ngoặc trong "
    "locator), cấm nth trong assertion.",
    "Self-healing bỏ phần số và nội dung động khỏi tên phần tử, khớp theo chuỗi con.",
    "Lặp lại RQ2, RQ3 với nhiều lần chạy cho mỗi model để đo độ dao động giữa model.",
    "Tách mức rủi ro của assertion: đổi phần tử được kiểm mà giữ giá trị kỳ vọng có thể là Medium kèm bằng chứng grounding.",
    "Mở rộng DSL (select, hover, phím) và thêm Alembic khi schema DB bắt đầu thay đổi trên SQL Server thật.",
]

RQ1_HELDOUT = [
    "Phát hiện mơ hồ trên tập độc lập lặp lại gần đúng hình ảnh của tập phát triển: recall 0,94, precision 0,42. Cả hai "
    "mâu thuẫn toàn cục được bắt, vague_quantifier sót 1/4. Gắn cờ nhầm tăng từ 5/23 lên 9/27 yêu cầu sạch, và lại tập "
    "trung ở hai loại khó: underspecified_action (2 đúng, 9 nhầm) và missing_precondition (1 đúng, 4 nhầm). Prompt đã "
    "siết ở tập phát triển không làm giảm được hai loại này trên dữ liệu mới.",
    "Với sinh test case, pipeline phủ 54/75 điều kiện so với 46/75 của direct, và lần này chênh lệch có ý nghĩa thống kê "
    "(10 điều kiện chỉ pipeline phủ, 2 chỉ direct phủ, p = 0,039). Phần chênh nằm ở ca biên (19/30 so với 15/30) và "
    "positive (34/35 so với 31/35). Tỉ lệ test không căn cứ thấp ở cả hai nhánh (3% và 5%), xác nhận quy tắc phiên bản 2 "
    "giữ được tác dụng trên tài liệu mới.",
    "Điểm yếu lớn nhất lộ ra là điều kiện negative: direct phủ 0/10, pipeline 1/10. Các điều kiện này phần lớn suy ra từ "
    "điều kiện trước của yêu cầu (chưa đăng nhập thì không đặt lịch được, thẻ hết hạn thì không đặt lớp được), tức tài "
    "liệu có nêu điều kiện nhưng không nêu phản ứng của hệ thống. Quy tắc phiên bản 2 cấm sinh negative khi tài liệu "
    "không nêu phản ứng, nên chặn luôn cả các ca hợp lý này. Đây là cái giá của việc giảm test bịa: trên tập phát triển "
    "nó đã thấy ở độ phủ negative giảm, trên tập độc lập nó rõ hơn vì tỉ lệ negative suy ra từ điều kiện trước cao hơn.",
    "Mô phỏng cổng AG-01 trên tập độc lập chỉ giữ lại 31 test và phủ 22/75 điều kiện: Requirement Agent gắn cờ 24 trong "
    "38 yêu cầu có test, trong khi gold chỉ có 12 yêu cầu mơ hồ. Với độ chính xác gắn cờ hiện tại, cổng AG-01 giữ lại "
    "gấp đôi số yêu cầu cần làm rõ.",
    "Kết luận RQ1 sau hai tập: lợi thế về độ phủ của pipeline nhỏ và chỉ đạt ý nghĩa thống kê ở một trong hai tập, nên "
    "chưa đủ để khẳng định chắc. Lợi ích ổn định qua cả hai tập là truy vết 100% và tỉ lệ test bịa thấp khi có quy tắc "
    "sinh test phù hợp. Cả hai lần đo đều dùng một model (DeepSeek) và một giám khảo LLM chưa được đối chiếu với người "
    "chấm.",
]

RQ2_MODELS_HELDOUT = [
    "Trên tập độc lập, các site mới khó hơn hẳn với hai nhánh không có vòng lặp: none chỉ đạt 2–4/12, aria 4–6/12. "
    "Gần như mọi lần trượt là locator khớp nhiều phần tử (strict mode) hoặc không khớp phần tử nào. Ở expandtesting, các "
    "liên kết quảng cáo có aria-label chứa chữ \"Password\" nên get_by_label(\"Password\") khớp ba phần tử; ở "
    "automationexercise, trang đăng nhập có hai ô cùng placeholder \"Email Address\"; ở testpages.eviltester, nút "
    "submit có tên trùng với nút khác trên trang. Vòng lặp grounding giữ được mức cao: DeepSeek 11/12 ở cả ba "
    "lần, hơn none có ý nghĩa thống kê ở cả ba lần (p ≤ 0,016) và hơn aria ở cả ba lần (p ≤ 0,031). Đây là bằng chứng "
    "mạnh nhất trong chuyên đề rằng cải thiện của vòng lặp không đến từ việc chỉnh nó cho vừa tập phát triển.",
    "Với Claude Sonnet 5, xu hướng giống nhau nhưng mức thấp hơn: 30/36/44 trên 50 target và 4/6/9 trên 12 target "
    "độc lập. Trên 50 target, vòng lặp hơn none (p = 0,003) và hơn aria (p = 0,02) có ý nghĩa thống kê; trên 12 target thì "
    "chưa đủ mẫu (p = 0,125). Trên 50 target, Claude không đạt thêm target nào mà DeepSeek trượt. Bốn trong sáu lần trượt của Claude ở "
    "nhánh aria_loop trên 50 target là vi phạm quy ước của DSL chứ không phải tìm sai phần tử: ba lần viết URL dạng mẫu "
    "hoặc thiếu phần đầu (\"**/dashboard/index\", \"practicetestautomation.com/...\") trong khi expect_url so nguyên "
    "chuỗi, một lần đặt dấu ngoặc kép bên trong giá trị locator. Grounding chỉ kiểm locator nên không bắt được các lỗi "
    "này. DeepSeek trước đó cũng vi phạm một quy ước khác (bỏ URL của goto vào sai trường). Mỗi model vi phạm theo cách "
    "riêng, nên hợp đồng của DSL cần được kiểm bằng một bước tất định trước khi chạy, thay vì chỉ mô tả trong prompt.",
    "Lần trượt cuối cùng ở trên làm lộ một lỗi của template sinh mã: chuỗi do LLM sinh được chèn thẳng vào mã Python, "
    "nên một giá trị chứa dấu ngoặc kép làm script lỗi cú pháp, và về nguyên tắc cho phép chèn mã tuỳ ý vào script sẽ "
    "được chạy. Template đã được sửa để escape mọi chuỗi (json.dumps) và có unit test cho trường hợp chèn mã. Rà lại mọi "
    "script đã lưu cho thấy chỉ một script bị ảnh hưởng; chạy lại với template đã sửa script đó vẫn trượt, nên không số "
    "liệu nào thay đổi.",
    "Claude không cho đặt temperature = 0 (DeepSeek chạy ở 0), nên so sánh giữa hai model không hoàn toàn cùng điều "
    "kiện; mỗi model trên mỗi tập chỉ có một lần chạy, trừ DeepSeek.",
]

RQ3_MODELS_HELDOUT = [
    "Model mạnh hơn che lỗi nhiều hơn. Khi sửa tự do, Claude biến 12/17 lỗi nghiệp vụ của tập phát triển thành test "
    "pass, so với 8/17 của DeepSeek, và làm yếu assertion 23 lần. Ở S4 (đăng nhập chuyển nhầm trang), cả sáu test bị "
    "Claude sửa thành pass bằng cách thêm bước và đổi loại thao tác. Trên mutation độc lập, hai model che 4/6 lỗi nghiệp "
    "vụ. Rủi ro che lỗi vì vậy không giảm khi model tốt lên; nó tăng theo khả năng \"làm cho test pass\" của model.",
    "Nhánh có ràng buộc không che lỗi nghiệp vụ nào ở cả bốn tổ hợp (hai model, hai tập): 0/17 và 0/6. Đây là kết luận "
    "của RQ3 giữ nguyên qua model và qua dữ liệu mới. Với Claude, số đề xuất phải chuyển lên người tăng (19 so với 11 ở "
    "tập phát triển), chủ yếu là các lỗi nghiệp vụ thật được đẩy lên đúng chỗ (13 so với 5); số escalate oan không đổi.",
    "Phần không giữ được là tỉ lệ sửa lỗi giao diện: trên mutation độc lập, nhánh có ràng buộc chỉ sửa được 4/15, so với "
    "24/31 ở tập phát triển, trong khi sửa tự do vẫn đạt 10/15. Hai nguyên nhân chiếm 11 ca còn lại. T12 đổi id của khối "
    "báo lỗi, tức đổi locator bên trong assertion, nên cả 5 ca bị escalate oan theo đúng hạn chế đã nêu ở mục 5.3. T9 "
    "đổi chữ liên kết Cart thành Basket: self-healing tìm ra liên kết nhưng lấy cả tên hiển thị \"Basket (3)\", gồm số món "
    "trong giỏ lúc dò trang; khi chạy thật giỏ có số món khác nên locator vừa chữa không khớp. Tập phát triển không có "
    "mutation nào chạm vào phần tử có nội dung động, nên điểm yếu này bị che. Nhóm không sửa thuật toán sau khi thấy kết "
    "quả này, để tập độc lập giữ đúng vai trò; hướng sửa (bỏ phần số khỏi tên, khớp theo chuỗi con) được ghi ở chương 6.",
    "Trả lời RQ3 sau khi mở rộng: sửa có ràng buộc loại bỏ được việc che lỗi một cách ổn định, nhưng tỉ lệ sửa thành công "
    "tương đương sửa tự do chỉ đúng trên tập phát triển. Trên dữ liệu mới, self-healing tất định và policy xếp mọi thay "
    "đổi trong assertion vào mức High khiến hệ thống sửa ít hơn và chuyển nhiều hơn cho người duyệt.",
]
