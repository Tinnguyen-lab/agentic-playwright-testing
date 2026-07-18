# Source Reading Notes — Requirements-Based Test Generation Survey

## Thông tin nguồn

- Tiêu đề: Requirements-Based Test Generation: A Comprehensive Survey
- Tác giả/tổ chức: Zhenzhen Yang, Rubing Huang, Chenhui Cui, Nan Niu, Dave Towey
- Năm: 2025
- Loại nguồn: Systematic literature review/survey
- Mã DOI/arXiv/tài liệu: [arXiv:2505.02015v2](https://arxiv.org/abs/2505.02015)
- Ngày đọc: 2026-07-15
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Bài báo khắc phục thiếu hụt một khảo sát cập nhật bao quát toàn bộ RBTG. Nó phân loại loại requirement, kỹ thuật sinh test, biểu diễn đầu ra, công cụ, evaluation, miền ứng dụng và thách thức mở. Giá trị của nguồn là khung phân loại và bằng chứng tổng hợp, không phải một kiến trúc agent có thể chạy trực tiếp.

## Các phần đã đọc

- **Abstract/tóm tắt:** RBTG tạo test từ requirement mà không cần source code và giúp bám nhu cầu người dùng. Survey tổng hợp approaches, tools, evaluation, applications và future work.
- **Introduction:** RBTG có thể tìm inconsistency/ambiguity sớm, nhưng natural language thường mơ hồ; nghiên cứu dùng natural, semi-formal và formal requirements. Survey bao quát 267 bài đến hết năm 2024.
- **Architecture/phương pháp:** Đây là kiến trúc nghiên cứu SLR, không phải kiến trúc phần mềm. Các tác giả định nghĩa 8 RQ, tìm trên 5 thư viện số, bổ sung snowballing, sàng lọc và trích dữ liệu theo từng RQ. Khung RBTG tổng quát là `requirement → kỹ thuật/biểu diễn trung gian → abstract/concrete test → execution/evaluation`.
- **Evaluation:** 493 kết quả ban đầu, 179 sau de-duplication và title/abstract review, 368 sau snowballing, 267 sau exclusion. Trong các nghiên cứu được khảo sát: 36% dùng example, 36% empirical case study, 17% real-world case study, 11% discussion; chỉ 12% có controlled comparative experiment.
- **Limitations:** Tác giả thừa nhận có thể không tìm được mọi bài liên quan. Corpus chỉ đến thời điểm tìm kiếm tháng 1/2025 và loại nghiên cứu không tiếng Anh, thiếu full text, survey, luận văn, sách/technical report và bài dưới 5 trang.

## Phương pháp

Search string yêu cầu title liên quan test case/suite/scenario và generate/create/requirement, còn abstract liên quan requirement/specification/user stories. Nguồn gồm ACM, ScienceDirect, IEEE Xplore, Springer và Wiley; Google Scholar được dùng trong snowballing. Dữ liệu trích xuất được kiểm tra trong và sau quá trình extraction.

## Dữ liệu hoặc ứng dụng thực nghiệm

267 công trình RBTG xuất bản từ 1994 đến 2024. Đơn vị phân tích là bài nghiên cứu, không phải requirement/test case riêng lẻ.

## Tiêu chí đánh giá

Survey thống kê loại evaluation, metric, domain, tool và test representation của các nghiên cứu. Các metric thường gặp gồm requirement coverage, code/model coverage, fault detection và quality/accuracy, nhưng bài báo nhận xét chúng chưa đo đầy đủ mức test bám requirement, đặc biệt với non-functional requirements.

## Kết quả chính

RBTG dịch chuyển từ formal/semi-formal model-based approaches sang natural language/NLP. Nhiều phương pháp vẫn tạo abstract test chưa chạy được. Lĩnh vực thiếu benchmark chuẩn, evaluation nghiêm ngặt, bằng chứng công nghiệp và cách chuyển tổng quát từ abstract sang concrete executable tests. Requirement quality là nút thắt đầu tiên.

## Hạn chế

- Coverage của SLR không tuyệt đối; tiêu chí tìm kiếm và exclusion có thể gây publication/language/selection bias.
- Các nghiên cứu dị thể nên số lượng theo category không tự động phản ánh chất lượng bằng chứng.
- Survey nói ambiguity, traceability, oracle và human involvement ở mức toàn lĩnh vực; không cung cấp một implementation giải quyết chúng.
- Dữ liệu dừng ở 2024 nên không bao phủ đầy đủ làn sóng agentic testing mới từ 2025–2026.

## Liên quan đến đề tài

- Structured requirements: **Có ở mức taxonomy** — natural, semi-formal, formal và model-based; không có module chuẩn hóa riêng.
- Traceability: **Có liên quan nhưng không phải capability của survey**.
- DOM grounding: **Không phải trọng tâm**; GUI/web chỉ là một phần trong corpus rộng.
- Oracle validation: **Được nhận diện là thành phần khó**, thường phải tạo thủ công/ngẫu nhiên trong các nghiên cứu; survey không triển khai oracle.
- Human approval: **Được thống kê**; 16% nghiên cứu dùng human-involvement evaluation, nhưng không định nghĩa approval gate.
- Constrained repair: **Không phải trọng tâm**.
- Playwright support: **Không cụ thể**.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Hệ thống hóa toàn bộ nghiên cứu RBTG và xác định khoảng trống.
2. **Đầu vào là gì?** Với survey: các công trình RBTG; với khung lĩnh vực: requirement tự nhiên, semi-formal, formal hoặc model.
3. **Đầu ra là gì?** Taxonomy, thống kê, danh mục tool/evaluation/domain và research challenges.
4. **Có chuẩn hóa requirement không?** Survey phân loại và tổng hợp cách biến đổi, nhưng không tự chuẩn hóa requirement.
5. **Có phát hiện ambiguity không?** Nhận diện ambiguity là thách thức; không cung cấp detector.
6. **Có traceability không?** Được đề cập trong lĩnh vực nhưng không có cơ chế traceability do survey triển khai.
7. **Có grounding trên UI không?** Không như một thành phần chung của survey.
8. **Có xác định test oracle không?** Phân tích oracle/test data trong corpus; không cung cấp oracle engine.
9. **Có human approval không?** Không có workflow; chỉ thống kê human involvement.
10. **Có kiểm soát repair không?** Không.
11. **Đánh giá trên dữ liệu nào?** 267 bài được chọn từ 493 kết quả ban đầu và snowballing.
12. **Hạn chế là gì?** Selection coverage, corpus chỉ đến 2024, dị thể nghiên cứu và thiếu benchmark/evaluation chuẩn của chính lĩnh vực.

## Trích dẫn hoặc ý cần kiểm tra lại

- Bản arXiv v2 vẫn hiển thị metadata template của journal ở một số footer; khi trích dẫn chính thức cần kiểm tra trạng thái xuất bản/DOI mới nhất.
- Các tỷ lệ evaluation có category khác nhau; không cộng lẫn “evaluation context” với “evaluation method”.

## Nhận xét của nhóm

Survey biện minh trực tiếp cho kiến trúc đề tài: requirement normalization/ambiguity trước generation, traceability đến test executable và benchmark bug-injected để đánh giá. Tuy nhiên, không nên ghi “survey hỗ trợ ambiguity detection”; kết luận đúng là survey chứng minh đây là khoảng trống cần giải quyết.
