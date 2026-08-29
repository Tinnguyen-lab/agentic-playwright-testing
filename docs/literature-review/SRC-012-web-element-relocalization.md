# Source Reading Notes — Web Element Relocalization (Similo / VON Similo / HybridSimilo)

## Thông tin nguồn

- Tiêu đề: Web Element Relocalization in Evolving Web Applications: A Comparative Analysis and Extension Study
- Tác giả/tổ chức: Anton Kluge, Andrea Stocco (Technical University of Munich; fortiss GmbH)
- Năm: 2025
- Loại nguồn: Research paper (replication + extension study, bản thảo EMSE)
- Mã DOI/arXiv/tài liệu: [arXiv:2505.16424v1](https://arxiv.org/abs/2505.16424) [cs.SE], 22 May 2025; replication package công khai [27]
- Ngày đọc: 2026-07-19
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Web test dễ vỡ chủ yếu do **locator breakage** khi web app tiến hóa. Hướng giải quyết: **web-element re-identification (relocalization)** — dùng similarity scoring trên nhiều property để định vị lại element trên phiên bản mới. Bài **replicate** Similo và VON Similo (+ LLM VON Similo), **xem xét lại threats to validity** của nghiên cứu gốc, rồi **mở rộng**: benchmark lớn hơn (23×), tối ưu tham số bằng genetic algorithm, và đề xuất **HybridSimilo** — kết quả locate **98.8%** element có broken locator trong kịch bản thực tế.

## Các phần đã đọc

- **Abstract/tóm tắt:** Replicate Similo & VON Similo; phát hiện VON Similo tạo nhiều false positive hơn Similo; cải thiện Similo +5.62% trên benchmark gốc bằng tối ưu; đề xuất benchmark lớn 23× và HybridSimilo (kết hợp Similo + VON Similo) đạt 98.8% element có broken locator.
- **Introduction:** Locator là nguyên nhân chính gây fragility; Similo là SOTA cho repair broken web test. Nêu 3 threats: (T2/T3) benchmark cách nhau 12–60 tháng không phản ánh CI; benchmark bị đổi giữa nghiên cứu gốc và extension; fixed properties/weights.
- **Motivating example (Zoom.us):** 3 loại breakage — Element Not Found, False Positive (locator trả element khác), Misclassification (đổi tag → nhầm element gần đó).
- **Approaches (Sec 3):** Similo (single element), VON Similo (visually overlapping groups), LLM VON Similo (LLM chọn từ candidate pre-selected). Similarity score đa property → chọn candidate điểm cao nhất.
- **RQs & Benchmarks & Extensions (Sec 4):** RQ0 replication, RQ1 comparison, RQ2 improvements, RQ3 hybrid. Similo++/VON Similo++/HybridSimilo; genetic algorithm tối ưu weights + similarity functions.
- **Results (Sec 5) + Threats + Conclusion:** Số liệu M1–M6 trên 4 benchmark; threats external validity (front pages, overfit weights); kêu gọi benchmark chuẩn hóa.

## Phương pháp

Similarity scoring giữa element cũ (target, property từ phiên bản baseline) và **mọi candidate** trên phiên bản mới, dựa các property: tag, class, name, id, href, alt, type, aria-label, abs-xpath, id-xpath, location, dimension, visible text, neighbor text, attributes. **Similo++**: thêm property (type, aria-label), thêm similarity functions (Jaccard, Jaro-Winkler, String Set...), **tối ưu weights bằng genetic algorithm**. **HybridSimilo**: VON Similo++ pre-select top-10 candidate (mạnh ở visual overlap) → Similo++ chọn concrete element. Cung cấp **library cho Selenium** wrap locator: nếu locator gốc fail → dùng extended Similo relocate.

## Dữ liệu hoặc ứng dụng thực nghiệm

- **4 benchmark**: Similo gốc (809 pairs, 48 sites, 12–60 tháng), VON Similo (441/1163 pairs, 33 sites), LLM VON Similo (804 pairs).
- **Extended benchmark**: 30 web app phổ biến, span cố định 4 tháng, 16 version (Sep 2018–Sep 2023), 933 element ban đầu → **10,376 element pairs (2,012 broken locators)**; 3 tháng manual mapping; nguồn Web Archive/Wayback.

## Tiêu chí đánh giá

Nhiều metric: M1 (Similo top-1), M2 (VON classification match/non-match), M3 (visual/textual overlap), M4 (exact match), M5 (lower-case exact), M6 (fitness); % element located; false positive/negative rate.

## Kết quả chính

- **Replication thành công**: Similo 88.99% (gốc 88.64%), VON 91.65% (gốc 91.29%).
- **VON Similo KHÔNG vượt Similo** khi locate concrete element (ngược báo cáo gốc của Nass et al.); chỉ tốt hơn ở **visual overlap (M3)**.
- Tối ưu (genetic algorithm) cải thiện Similo: M4 87.54%→91.78%, M3 91.65%→95.64%; +5.62% trên benchmark gốc.
- **Extended benchmark (10,376 pairs)**: Similo++ (Ext, M6) đạt **99.8% (M1)** và **98.8% (M5, broken-locator)**; HybridSimilo tương đương Similo++.
- Property quan trọng (weight cao ổn định): name, type, aria-label, location, visible text, neighbor text, attributes; class và is-button thường bị hạ/loại.

## Hạn chế

- Chỉ dùng **front pages** → không đại diện selects/tables/table items ở trang sâu hơn.
- Số website hạn chế → generalizability; weights tối ưu **tailored to dataset** (nguy cơ overfit dù cross-validation).
- Wayback snapshots có thể không đầy đủ/chính xác; cross-browser/country gây sai lệch dataset.
- **Library cho Selenium (không Playwright)** — thuật toán transferable nhưng chưa có bản Playwright.

## Liên quan đến đề tài

- Structured requirements: **Không** — hoàn toàn về locator robustness, không requirement.
- Traceability: **Không**.
- DOM grounding: **Có, đóng góp chính** — dùng đa property DOM (tag/class/id/xpath/aria-label/text/location/dimension/neighbor) để relocate element; **property-based, không screenshot vision** (bài này còn cho thấy locator-based robust hơn visual).
- Oracle validation: **Không** — về relocalization element, không oracle.
- Human approval: **Không**.
- Constrained repair: **Có, rất liên quan** — đây chính là **self-healing/repair broken locator** bằng similarity relocalization deterministic (genetic-optimized weights); library wrap: locator gốc fail → relocate. Đúng loại constrained repair cấp locator đề tài cần.
- Playwright support: **Không trực tiếp** — library cho Selenium; thuật toán/property có thể port sang Playwright.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Relocate web element khi locator vỡ do web app tiến hóa, bằng similarity scoring đa property; replicate + extend Similo/VON Similo, đề xuất HybridSimilo.
2. **Đầu vào là gì?** Target element (property từ phiên bản cũ) + toàn bộ candidate element trên phiên bản mới.
3. **Đầu ra là gì?** Element khớp nhất (relocated) trên phiên bản mới; thư viện wrap locator Selenium.
4. **Có chuẩn hóa requirement không?** Không.
5. **Có phát hiện ambiguity không?** Không (nhưng xử lý false positive/misclassification của locator).
6. **Có traceability không?** Không.
7. **Có grounding trên UI không?** Có — đa property DOM (tag/class/id/xpath/aria-label/text/location/dimension/neighbor); property-based, không vision.
8. **Có xác định test oracle không?** Không.
9. **Có human approval không?** Không.
10. **Có kiểm soát repair không?** Có, trực tiếp — self-healing locator bằng relocalization deterministic (genetic-optimized), library fallback khi locator gốc fail.
11. **Đánh giá trên dữ liệu nào?** 4 benchmark (Similo 809 / VON 441 / LLM 804 / Extended 10,376 pairs, 30 sites, 5 năm); replication + genetic optimization.
12. **Hạn chế là gì?** Chỉ front pages, số site hạn chế, overfit weights (dù cross-val), Wayback snapshot inaccuracy, Selenium (không Playwright).

## Trích dẫn hoặc ý cần kiểm tra lại

- "98.8% element có broken locator" (abstract) là **M5 trên extended benchmark của Similo++ (Ext, M6)** — nêu rõ config + benchmark, không trích rời.
- Phát hiện quan trọng: **VON Similo KHÔNG vượt Similo** (ngược nghiên cứu gốc) do benchmark khác nhau; VON chỉ tốt hơn ở **visual overlap (M3)**.
- Weights optimized **tailored to dataset** → nguy cơ overfit; "hiệu quả hơn cho tập site nhỏ/cụ thể hơn" là giả định của tác giả.
- Library là cho **Selenium, không phải Playwright** — quan trọng khi đề tài muốn tái sử dụng.
- Bảng 2 (M1–M6) bị xáo dòng khi trích PDF (nhiều dòng con/benchmark) — đọc lại bản gốc khi cần số chính xác.

## Nhận xét của nhóm

Nguồn **academic vững nhất** (EMSE, replication + benchmark lớn + genetic optimization) về **constrained/deterministic locator repair**. Rất liên quan cho phần self-healing/constrained repair cấp locator của đề tài: đa property + weighted similarity + genetic-optimized. Bổ trợ [[SRC-006-zero-cost-self-healing-dom]] (cũng deterministic self-healing nhưng dùng a11y priority hierarchy; SRC-012 dùng multi-property similarity scoring) và đối lập [[SRC-008-autonomous-test-repair-limits]] (repair bằng LLM). Khoảng trống cho đề tài: là Selenium (cần port Playwright), thuần locator (không oracle/requirement/traceability), chỉ front pages. Đề tài có thể dùng relocalization này làm **constrained repair có kiểm soát** cho Playwright test, kết hợp requirement→test + oracle + human approval.
