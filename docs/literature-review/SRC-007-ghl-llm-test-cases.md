# Source Reading Notes — Generating High-Level Test Cases from Requirements (GHL)

## Thông tin nguồn

- Tiêu đề: Generating High-Level Test Cases from Requirements using LLM: An Industry Study
- Tác giả/tổ chức: Satoshi Masuda (Tokyo City University); Satoshi Kouzawa, Kyousuke Sezai, Hidetoshi Suhara, Yasuaki Hiruta, Kunihiro Kudou (VeriServe Corporation, Tokyo)
- Năm: 2025
- Loại nguồn: Research paper (industry study)
- Mã DOI/arXiv/tài liệu: [arXiv:2510.03641v1](https://arxiv.org/abs/2510.03641) [cs.SE], 4 Oct 2025
- Ngày đọc: 2026-07-19
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Sinh **high-level (HL) test cases** dạng natural language từ requirement documents hiện làm thủ công, phụ thuộc kỹ năng engineer → dễ sót. RAG giúp tăng độ chính xác nhưng phải chuẩn bị theo từng domain/nghiệp vụ, rất tốn công và độ chính xác bất ổn. Bài đề xuất phương pháp **chỉ dùng prompt (không RAG)** để tổng quát hóa cho nhiều loại requirement document khác nhau.

## Các phần đã đọc

- **Abstract/tóm tắt:** Phương pháp GHL: (1) input requirement doc → LLM sinh test design techniques tương ứng; (2) sinh HL test cases cho từng technique. Đánh giá bằng semantic similarity. Thực nghiệm trên Bluetooth & Mozilla đạt macro-recall 0.81 và 0.37; khả thi thực tế mà không cần RAG.
- **Introduction:** HL test case = mô tả tổng quan bằng NL (vd "Verify that several bookmarks are deleted at one time"). 3 RQ: (RQ1) prompt nào hiệu quả để sinh HL test case chỉ bằng prompt; (RQ2) đánh giá tính đúng của HL test case sinh ra thế nào; (RQ3) hiện trạng & thách thức thực tế.
- **Architecture/phương pháp (Sec III):** Step 1 — input requirement doc **+ test strategy** → LLM sinh/chọn test design techniques theo ISO/IEC/IEEE 29119-4 (EP, BVA, decision table, state transition, use case testing...). Step 2 — với mỗi technique → sinh HL test cases (normal + abnormal). Biến thể **GHL-F** thêm tổ hợp functions.
- **Evaluation (Sec IV–V):** Dataset Bluetooth (AVRCP/BAP/HFP/VDP) + Mozilla (Bookmarks/Themes/Password Manager/Browser History). GPT-4o, temp=0, seed cố định; embedding text-embedding-3-small, cosine similarity, threshold 0.7 = match. So sánh zero-shot vs GHL vs GHL-F qua macro precision/recall/F1, generation rate, thời gian.
- **Limitations/Discussion:** Precision thấp (nhiều test thừa), recall Mozilla thấp; expected result khi execution chưa được xác định (future); chỉ 2 dataset.

## Phương pháp

Step-by-step prompting: Step 1 trích test design techniques (dùng ISO 29119-4 làm khung, có fallback "phổ biến" nếu không trích được), Step 2 sinh test cases cho từng technique. Novelty so với step-by-step thông thường: thêm bước **extract test design techniques**. GHL-F bổ sung sinh tổ hợp function. Đánh giá tự động bằng vector hóa (LLM embedding) + cosine similarity với truth test cases; ngưỡng 0.7 (dựa [31]–[33]); có xác nhận thêm bằng expert evaluation.

## Dữ liệu hoặc ứng dụng thực nghiệm

- **Bluetooth**: AVRCP, BAP, HFP, VDP — requirement spec công khai + truth test cases (118/119/83/38... truth).
- **Mozilla (Firefox)**: Bookmarks, Themes, Password Manager, Browser History — wiki requirements + archived test cases.
- Mỗi phương pháp chạy lặp 3 lần; đo cả thời gian sinh.

## Tiêu chí đánh giá

Macro precision (matched gen / gen), macro recall (matched truth / truth), F1, generation rate (gen/truth), duration; so khớp bằng semantic similarity (cosine ≥ 0.7). Xác nhận ngưỡng bằng expert evaluation.

## Kết quả chính

- Macro-recall trung bình **0.84 (Bluetooth)** và **0.37 (Mozilla)** (abstract ghi 0.81/0.37) → HL test case sinh được với độ chính xác nhất định mà không cần RAG.
- **GHL-F** cho recall cao nhất: Bluetooth recall 0.80, precision 0.62; Mozilla recall 0.37, precision 0.17.
- Precision giảm khi generation rate tăng, nhưng tác giả **ưu tiên recall** (giả định execution tự động sau sẽ bù các test thừa).
- Thời gian: ~20 phút cho ~100 case bằng LLM vs ~500 phút thủ công (5 phút/case).

## Hạn chế

- Precision thấp → nhiều test thừa/không đúng; recall Mozilla thấp (0.37).
- Đánh giá dựa semantic similarity threshold 0.7 — nhạy cảm với ngưỡng, có yếu tố chủ quan (dù có expert confirm).
- **Expected result khi execution chưa được xác định** — chính tác giả nêu là future work (điểm oracle còn thiếu).
- Chỉ 2 dataset; HL test case dạng NL, **không thực thi**; chưa nối sang execution/Playwright.

## Liên quan đến đề tài

- Structured requirements: **Một phần** — input requirement doc + test strategy; không chuẩn hóa thành schema, nhưng dùng **ISO/IEC/IEEE 29119-4 test design techniques** làm khung sinh test.
- Traceability: **Yếu** — test cases sinh theo từng requirement doc/technique nhưng không có ID → test traceability; đánh giá bằng similarity với truth.
- DOM grounding: **Không** — HL test case NL, không UI.
- Oracle validation: **Yếu** — HL test case mô tả expected behavior dạng NL; oracle/expected-result execution là **future work**; đánh giá bằng semantic similarity chứ không phải oracle execution.
- Human approval: **Một phần** — expert evaluation xác nhận ngưỡng 0.7; không có approval gate trong pipeline.
- Constrained repair: **Không**.
- Playwright support: **Không** — dừng ở HL test case; execution automation là future work.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Sinh HL test cases từ requirement doc **chỉ bằng prompt (không RAG)**, tổng quát cho nhiều spec.
2. **Đầu vào là gì?** Requirement document (NL) + test strategy.
3. **Đầu ra là gì?** Test design techniques + HL test cases NL (normal/abnormal) theo từng technique.
4. **Có chuẩn hóa requirement không?** Không có schema formal; dùng ISO 29119-4 test design techniques làm khung.
5. **Có phát hiện ambiguity không?** Không.
6. **Có traceability không?** Yếu; không ID mapping, chỉ so similarity với truth.
7. **Có grounding trên UI không?** Không.
8. **Có xác định test oracle không?** Mô tả expected behavior NL; không oracle execution; expected result là future work.
9. **Có human approval không?** Expert evaluation ngoài pipeline; không approval gate.
10. **Có kiểm soát repair không?** Không.
11. **Đánh giá trên dữ liệu nào?** Bluetooth (4 profile) + Mozilla (4 feature), GPT-4o; macro-recall 0.81–0.84 / 0.37.
12. **Hạn chế là gì?** Precision thấp, recall Mozilla thấp, 2 dataset, HL NL không thực thi, chưa xác định expected result cho execution.

## Trích dẫn hoặc ý cần kiểm tra lại

- Recall abstract (0.81/0.37) vs discussion (0.84/0.37) hơi khác (macro average khác cách tính) — đối chiếu bản gốc.
- Bảng IV/V/VI bị xáo cột khi trích PDF (layout) — số precision/recall chi tiết cần đọc lại bản gốc, không trích máy móc.
- Ngưỡng similarity 0.7 = "identical" dựa [31]–[33]; ảnh hưởng lớn tới precision/recall → cẩn trọng khi so sánh cross-paper.

## Nhận xét của nhóm

Nguồn requirement→HL-test rất liên quan cho phần **structured requirements + test design techniques theo ISO 29119-4** của đề tài; cách để LLM tự chọn technique theo chuẩn rồi sinh test là ý đáng học. Khoảng trống: dừng ở NL, **oracle/expected-result chưa giải quyết**, không thực thi/Playwright, không traceability artifact-level. Cùng hướng với [[SRC-005-llm-testcase-scenario-gen]] và [[SRC-011-system-testcase-chatgpt]]. Đề tài có thể nối tiếp: HL test case → grounding + oracle + Playwright execution + human approval.
