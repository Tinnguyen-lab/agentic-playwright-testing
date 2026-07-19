# Source Reading Notes — Zero-Cost Self-Healing (DOM Accessibility Tree)

## Thông tin nguồn

- Tiêu đề: Beyond LLM-Based Test Automation: A Zero-Cost Self-Healing Approach Using DOM Accessibility Tree Extraction
- Tác giả/tổ chức: Renjith Nelson Joseph (Independent Researcher / Ecommerce Program Manager)
- Năm: 2026
- Loại nguồn: Preprint (empirical case study)
- Mã DOI/arXiv/tài liệu: [arXiv:2603.20358v1](https://arxiv.org/abs/2603.20358) [cs.SE], 20 Mar 2026; repo: github.com/Renjithnj/zero-cost-self-healing-qa
- Ngày đọc: 2026-07-19
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Locator dựa trên CSS/XPath/visible text vốn dễ vỡ khi DOM/class/nội dung đổi qua nhiều locale, làm test suite fail ở quy mô lớn. Các cách self-healing dựa trên LLM giải quyết được nhưng phát sinh chi phí API mỗi lần chạy, quá đắt ở quy mô regression enterprise. Bài đề xuất framework self-healing **zero-cost**: thay việc dùng LLM để tìm element bằng thuật toán trích xuất accessibility tree có thứ tự ưu tiên, chỉ re-extract selector bị hỏng khi fail.

## Các phần đã đọc

- **Abstract/tóm tắt:** Framework 10 tầng locator ưu tiên (`get_by_role` → `data-testid` → ARIA label → CSS class fragment → visible text) khám phá selector bền, language-agnostic từ live DOM trong một lần chạy. Kiểm chứng trên automationexercise.com, 3 device profile, 10 workflow; đạt 31/31 (100%) pass, chạy song song 22s; self-healing phát hiện & phục hồi selector giả lập hỏng trong <1s, không cần người.
- **Introduction:** Component framework (React/Vue/Angular) sinh class name phi tất định + refactor DOM; visible text đổi theo locale → maintenance tuyến tính. Công cụ AI (Testim, Functionize, Mabl, Browser Use) resilient hơn nhưng tốn token mỗi run ($1,350–2,160/tháng ở quy mô 300 test/ngày). 6 đóng góp: thuật toán 10 tầng, self-healing chỉ re-extract selector hỏng, hierarchy L0/L1/L2, case study thực nghiệm, kiến trúc engine/functions/workflows, dashboard real-time.
- **Architecture/phương pháp:** 3 lớp — Engine (`dom_extractor.py`, `smart_find.py`, cache `global_locators.json`), Functions (`actions.py`), Workflows (test file L0/L1/L2). Cache locator dùng chung cho mọi device (discovery 1 lần trên Desktop Chrome). Multi-pass discovery (5 pass theo trạng thái app). Element pattern registry.
- **Evaluation:** Discovery 14/17 element (82.4%) ở cold cache; 3 element còn lại cần auth. 31/31 pass across 3 device. Self-healing: inject selector `.product-grid-item-stale` → SmartFind timeout → re-extract 10 tầng → phục hồi `.single-products`, <1s, tự động; ~3–5s/element vs 30–90s cho full LLM re-discovery.
- **Limitations:** Không discover element cần auth; tầng CSS class kém bền, phụ thuộc dev tuân thủ a11y; chưa hỗ trợ shadow DOM; một số feature phụ thuộc product cần URL ổn định.

## Phương pháp

Thuật toán selector 10 tầng theo độ bền: `get_by_role`+name (W3C) → `get_by_role` only → `data-testid` → HTML id → ARIA label (exact/contains) → href fragment → CSS class (exact/contains) → visible text (last resort). `SmartFind` bọc mọi tương tác: khi selector cache fail → invalidate → re-extract riêng element đó → ghi lại cache → retry; nếu không thấy → mark failed + chụp screenshot. Xử lý riêng WebKit mobile (dùng modal xác nhận add-to-cart làm success signal thay vì cart page). Dashboard HTML single-file poll `results.json` (atomic write + spin-lock cho pytest-xdist).

## Dữ liệu hoặc ứng dụng thực nghiệm

automationexercise.com (demo e-commerce công khai cho automation, không auth). 3 device (Desktop Chrome 1440×900, Desktop Safari/WebKit, iPhone 15). 2 L0 domain, 7 L1 process, 11 L2 feature (5 browse + 5 checkout + 1 self-healing demo) → 31 combination. Stack: Python 3.9.6, Playwright (pytest-playwright 0.7.1), pytest 8.4.2, pytest-xdist 3.8.0, macOS.

## Tiêu chí đánh giá

Element discovery coverage, pass rate, thời gian chạy song song, heal time, human intervention, chi phí (per-run/monthly/annual TCO), so sánh với LLM-based (Browser Use + Claude/GPT-4o) và SaaS (Testim, BrowserStack).

## Kết quả chính

- Discovery 82.4% (14/17) cold cache; 3 element chưa discover được là auth-gated (giới hạn kỳ vọng, không phải lỗi framework).
- Pass rate 31/31 (100%) trên 3 device, 22s chạy song song (10 worker).
- Self-healing: phát hiện + phục hồi selector giả lập hỏng <1s, zero human intervention; ~3–5s/element.
- Chi phí API $0 ở mọi quy mô vs $1,350–2,160/tháng LLM; lợi thế TCO 3–14× dù tính công bảo trì (4–12h/tháng).

## Hạn chế

- Không xử lý element cần auth (payment, order confirmation).
- Tầng CSS class kém bền; hiệu quả phụ thuộc dev tuân thủ ARIA/a11y — site thiếu ARIA rơi xuống text-based, giảm robustness đa locale.
- Chưa hỗ trợ shadow DOM (ngày càng phổ biến với web components).
- Kiểm chứng chỉ trên MỘT site demo; không có so sánh head-to-head thực nghiệm với LLM tool (chỉ so định tính/chi phí).
- Hoàn toàn **không requirement-driven** — test workflow do người viết thủ công.

## Liên quan đến đề tài

- Structured requirements: **Không** — không nhận requirement làm input; L0/L1/L2 là phân loại test cho stakeholder, không phải chuẩn hóa requirement.
- Traceability: **Một phần (business-level)** — L0/L1/L2 map test → business outcome; không phải requirement-ID → test artifact.
- DOM grounding: **Có, đóng góp chính** — accessibility tree extraction, ưu tiên `get_by_role`/ARIA/`data-testid`; nhưng **không dùng LLM**.
- Oracle validation: **Yếu** — assertion thủ công đơn giản (page load, title, visibility, item verify); WebKit dùng modal làm success signal; không oracle tự động.
- Human approval: **Không có gate runtime**; test do người viết.
- Constrained repair: **Có, đóng góp chính** — targeted re-extraction chỉ selector hỏng, deterministic, không LLM. Là self-healing cấp locator, không sửa logic/assertion.
- Playwright support: **Có, mạnh** — dùng Playwright (pytest-playwright) + `get_by_role`, pytest-xdist. Rất gần công cụ mục tiêu về locator/execution.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Self-healing locator discovery zero-cost cho web test automation (thay LLM bằng accessibility tree).
2. **Đầu vào là gì?** Live DOM của app + element pattern registry do người định nghĩa; không có requirement.
3. **Đầu ra là gì?** Selector bền language-agnostic (cache), kết quả pass/fail, dashboard; selector đã self-heal.
4. **Có chuẩn hóa requirement không?** Không.
5. **Có phát hiện ambiguity không?** Không.
6. **Có traceability không?** Business-level L0/L1/L2, không phải requirement-level.
7. **Có grounding trên UI không?** Có — accessibility tree/DOM extraction, `get_by_role`.
8. **Có xác định test oracle không?** Assertion đơn giản do người viết; không oracle tự động.
9. **Có human approval không?** Không có gate runtime; test do người viết.
10. **Có kiểm soát repair không?** Có — deterministic targeted re-extraction chỉ selector hỏng (không sửa code/assertion bằng LLM).
11. **Đánh giá trên dữ liệu nào?** automationexercise.com, 3 device, 31 combination, 100% pass, self-healing demo.
12. **Hạn chế là gì?** Auth-gated elements, CSS tier fragile, không shadow DOM, một site demo, không requirement-driven.

## Trích dẫn hoặc ý cần kiểm tra lại

- "82.4% discovery" nhưng "100% pass": 3 element không discover được là auth-gated nên không nằm trong 31 test — không mâu thuẫn nhưng dễ hiểu nhầm nếu trích rời.
- Bảng chi phí LLM ($1,350–2,160/tháng, TCO 3–14×) dựa trên giả định 4,500 execution/tháng — con số minh họa/ước lượng, không phải đo thực nghiệm.
- "Hamcrest et al. [3] — 73% locator failures": "Hamcrest" là tên một thư viện assertion, nhiều khả năng lỗi trích dẫn tác giả; cần kiểm nguồn gốc.
- Không có so sánh thực nghiệm trực tiếp với công cụ LLM — mọi so sánh ở mức chi phí/định tính.

## Nhận xét của nhóm

Nguồn thực dụng, gần đề tài ở **locator policy** (a11y-first `get_by_role`/ARIA, khớp [[SRC-002-playwright-codegen-locators]]) và **constrained repair** (deterministic, đối lập với repair-bằng-LLM trong [[SRC-008-autonomous-test-repair-limits]]). Điểm đáng học: cache locator + targeted re-extraction + a11y-first + tách environment-specific verification. Khoảng trống để đề tài lấp: hoàn toàn không requirement-driven, oracle yếu, một site demo, self-healing chỉ cấp locator (không xử lý semantic). Hướng kết hợp tự nhiên: nối requirement→test ([[SRC-005-llm-testcase-scenario-gen]], [[SRC-007-ghl-llm-test-cases]], [[SRC-011-system-testcase-chatgpt]]) với locator policy + constrained repair kiểu này.
