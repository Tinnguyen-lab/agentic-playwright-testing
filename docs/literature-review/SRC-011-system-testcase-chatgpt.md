# Source Reading Notes — System Test Case Design from SRS (ChatGPT)

## Thông tin nguồn

- Tiêu đề: System Test Case Design from Requirements Specifications: Insights and Challenges of Using ChatGPT
- Tác giả/tổ chức: Shreya Bhatia, Tarushi Gandhi, Dhruv Kumar, Pankaj Jalote (IIIT Delhi)
- Năm: 2024
- Loại nguồn: Research paper (ACM conference format)
- Mã DOI/arXiv/tài liệu: [arXiv:2412.03693v1](https://arxiv.org/abs/2412.03693) [cs.SE], 4 Dec 2024
- Ngày đọc: 2026-07-19
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Sinh **system test case designs** từ Software Requirements Specification (SRS) thủ công tốn công, dễ sót và dễ thừa. Bài đánh giá hiệu quả của LLM (ChatGPT) trong việc sinh test case design trực tiếp từ SRS, và khả năng LLM **phát hiện test case trùng lặp (redundancy)**, có đối chiếu với đánh giá của chính developer.

## Các phần đã đọc

- **Abstract/tóm tắt:** 5 SRS (functional + non-functional), ChatGPT-4o Turbo, prompt-chaining (context-setting → sinh test cho từng use case). ~87% test case sinh ra valid; 13% còn lại không áp dụng được hoặc trùng; đáng chú ý 15% valid test case là loại developer **chưa từng nghĩ tới**. ChatGPT cũng được giao nhiệm vụ phát hiện redundancy, được developer validate để lọc false positive.
- **Introduction:** SRS mô tả functional (dạng use case) + non-functional. Test case design = xác định scenario, input, expected output. 3 RQ: (RQ1) LLM sinh test case valid/toàn diện từ SRS hiệu quả ra sao; (RQ2) tỉ lệ test valid nhưng bị developer bỏ sót & giá trị bổ sung; (RQ3) LLM phát hiện redundancy chính xác đến đâu.
- **Architecture/phương pháp (Sec 2):** So sánh single-prompt vs prompt-chaining → chaining tốt hơn (~9–11 vs 2–3 test/use case). Quy trình 2 giai đoạn: Familiarization (đọc SRS) → Test Case Generation cho từng use case, **format bảng 4 cột** (functionality/condition, input action/values, expected output/behaviour, comments), specification-based technique. Union-of-attempts đến khi hội tụ.
- **Evaluation:** Đánh giá định tính bằng feedback từ chính **developer tác giả SRS**, 5 nhãn: Valid (đã implement), Not-implemented-but-valid, Not applicable, Redundant, Missed. RQ3: ChatGPT tự flag redundancy → developer validate (overlap / new / false positive).
- **Conclusion/Limitations:** Dataset nhỏ (5 SRS student project), có thể không generalize; ChatGPT hiểu system behavior hạn chế chỉ từ SRS → sót & false positive; chưa dùng độc lập được.

## Phương pháp

Prompt-chaining 2 giai đoạn (Familiarization + per-use-case generation), ChatGPT-4o Turbo, default temperature, GPT-4 Turbo, chạy nhiều lần rồi lấy **union** test set đến khi không tăng thêm. Output bảng chuẩn hóa 4 cột (gồm cột **expected output/behaviour** — oracle mô tả). Đánh giá bằng developer review từng test case (human-in-the-loop trung tâm). Redundancy: prompt ChatGPT flag + developer đối chiếu.

## Dữ liệu hoặc ứng dụng thực nghiệm

5 SRS document từ project kỹ thuật sinh viên làm cho khách hàng thật: SMP Portal, Medical Leave Portal, Student Clubs Event Platform, Ph.D. Management Portal, Changemaking Website. 7,000–12,000 LOC, team 3–4, 11–29 use case, 3–4 user type mỗi SRS. Stack: React/HTML frontend, Django/NodeJS backend, PostgreSQL/MySQL/MongoDB.

## Tiêu chí đánh giá

% Valid (đã implement) + % Not-implemented-but-valid + % Not applicable + % Redundant + số Missed test/SRS; với redundancy: tỉ lệ overlap với developer / new valid / false positive.

## Kết quả chính

- **~87.7% valid** = 72.5% valid & implemented + **15.2% not-implemented-but-valid** (mới, hợp lệ, developer chưa nghĩ tới — UX, accessibility, security).
- 9.7% not applicable; 2.6% redundant; ~2.2 missed test/SRS (ChatGPT hiểu system hạn chế nên sót).
- **RQ2:** 15.2% test valid nhưng bị developer bỏ sót → bổ sung coverage cho edge case/UX/a11y/security.
- **RQ3:** ChatGPT flag 12.82% redundant (vs developer 8.3%); trong số ChatGPT flag: **47.19% trùng với developer, 22.65% mới & hợp lệ, 30.16% false positive** (thực ra cần thiết cho coverage, vd cùng chức năng nhưng khác actor).

## Hạn chế

- Dataset nhỏ (5 SRS student project) → khó generalize; requirement thật khó thu thập vì tính bảo mật.
- ChatGPT hiểu system behavior/implementation hạn chế chỉ từ SRS → sót 2–3 test/SRS.
- **Redundancy false-positive cao (30.16%)** — nếu tự động xóa sẽ giảm coverage; không dùng độc lập được.
- Dừng ở **test case design (bảng NL)**, không thực thi/không code; oracle chỉ là mô tả expected output, không validate tự động.

## Liên quan đến đề tài

- Structured requirements: **Có** — input là SRS formal (functional + non-functional, use case); output test case theo **format bảng chuẩn hóa** (condition/input/expected/comments).
- Traceability: **Một phần** — test case sinh **per use case** (use-case → test mapping ngầm); không có ID traceability formal.
- DOM grounding: **Không** — test case design mức NL, không UI.
- Oracle validation: **Một phần** — mỗi test có cột **"expected output/behaviour"** (oracle mô tả rõ), nhưng **không validation/execution tự động**.
- Human approval: **Có, mạnh (ở evaluation)** — developer review & phân loại từng test (5 nhãn), gồm validate redundancy/false-positive; human-in-the-loop là trung tâm (dù ở đánh giá, chưa phải pipeline gate).
- Constrained repair: **Không**.
- Playwright support: **Không** — dừng ở bảng test case design.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Đánh giá ChatGPT sinh system test case design từ SRS + phát hiện redundancy.
2. **Đầu vào là gì?** SRS document (functional/non-functional, use case).
3. **Đầu ra là gì?** Test case designs dạng bảng 4 cột (condition, input, expected output, comments) theo từng use case.
4. **Có chuẩn hóa requirement không?** Input SRS formal + output bảng chuẩn; không normalize requirement thêm.
5. **Có phát hiện ambiguity không?** Không; ChatGPT hiểu hạn chế → sót test.
6. **Có traceability không?** Per-use-case mapping ngầm; không ID formal.
7. **Có grounding trên UI không?** Không.
8. **Có xác định test oracle không?** Cột "expected output/behaviour" (oracle mô tả NL); không execution/validation tự động.
9. **Có human approval không?** Có — developer đánh giá & phân loại từng test (trung tâm phương pháp), gồm validate redundancy/false-positive.
10. **Có kiểm soát repair không?** Không.
11. **Đánh giá trên dữ liệu nào?** 5 SRS student project; 87.7% valid, 15.2% overlooked-but-valid, redundancy FP 30%.
12. **Hạn chế là gì?** Dataset nhỏ, hiểu system hạn chế (sót test), redundancy false-positive cao, không thực thi.

## Trích dẫn hoặc ý cần kiểm tra lại

- "87 percent valid" = 72.5% + 15.2% = 87.7% (Table IV: valid&implemented 72.49 + not-impl-but-valid 15.18) — nhất quán.
- "13% not applicable or redundant": 9.68% NA + 2.65% redundant ≈ 12.3% (làm tròn ~13%) — ổn.
- RQ3: chú ý **redundancy false-positive 30.16%** khi diễn giải "LLM phát hiện redundancy" — không nên tự động xóa.
- Dataset là **student project**, không phải industrial thực → generalizability hạn chế.

## Nhận xét của nhóm

Nguồn requirement(SRS)→system-test-design rất liên quan cho phần **structured requirements + expected-output (oracle mô tả) + human review** của đề tài. **Format bảng 4 cột** (condition/input/expected/comments) là mẫu tốt cho test case artifact của đề tài. Điểm mạnh: human-in-the-loop đánh giá 5 nhãn + phát hiện overlooked tests (15.2%) tăng coverage. Khoảng trống để đề tài lấp: NL/không thực thi, oracle không tự động, redundancy FP cao, dataset nhỏ. Cùng hướng với [[SRC-005-llm-testcase-scenario-gen]], [[SRC-007-ghl-llm-test-cases]]; đề tài nối tiếp bằng DOM grounding + oracle execution + Playwright + human approval gate ([[SRC-008-autonomous-test-repair-limits]]).
