# Source Reading Notes — Steward: Natural Language Web Automation

## Thông tin nguồn

- Tiêu đề: Steward: Natural Language Web Automation
- Tác giả/tổ chức: Brian Tang, Kang G. Shin (University of Michigan)
- Năm: 2024
- Loại nguồn: Research paper
- Mã DOI/arXiv/tài liệu: [arXiv:2409.15441v1](https://arxiv.org/abs/2409.15441) [cs.AI], 23 Sep 2024; repo: github.com/byron123t/Steward
- Ngày đọc: 2026-07-19
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Browser automation truyền thống (Selenium/Puppeteer/Playwright) cần **code thủ công** cho từng tương tác → không scale cho web interaction quy mô lớn/động (vd nghiên cứu recommendation algorithm trên YouTube/Twitter). Steward là công cụ web automation **dùng LLM**: nhận NL instruction (goal 1 câu) → **reactively plan + execute** chuỗi action trên website đến khi đạt end state; end-to-end, cost-effective, scalable, plug-and-play với LLM off-the-shelf (zero/few-shot, không fine-tune).

## Các phần đã đọc

- **Abstract/tóm tắt:** Steward tích hợp LLM với browser automation, NL-driven. Hiệu quả: 8.52–10.14s/action, $0.028/action, ~$0.18/task; caching giảm còn 4.8s và $0.013/action. Chạy real website với **40% task completion**.
- **Introduction/Background:** So sánh với Glider, FLIN, Mind2Web, WebAgent, WebGUM, AutoGPT... Steward kết hợp 3 hướng (element proposal+selection, planning, multimodal) với reactive planning agent, thiết kế **riêng cho Playwright**.
- **Design (Sec 3):** 3 thành phần — (1) LLM + prompting cho state representation & navigation; (2) HTML cleaner + pipeline tối ưu runtime/cost + action caching; (3) tích hợp Playwright. State = goal + base URL + page context + screenshot + prior actions + candidate action + candidate elements.
- **Implementation (Sec 4):** 1626 LOC Python, 20 prompts. 4 model: GPT-3.5-Turbo, GPT-3.5-Turbo-16k, GPT-4-Turbo, GPT-4-Vision. Verb→Playwright mapping (click→`Locator.click()`, type_text→`Locator.fill()`, visit_url→`Page.goto(..., wait_until='networkidle')`...). Bypass bot detection (Firefox Nightly + VPN).
- **Evaluation/Results (Sec 5–6):** Mind2Web (122 tasks/621 actions) + manual 30 live tasks. Component accuracy, per-step, live completion, runtime, cost, caching, error analysis.

## Phương pháp

Reactive planning (plan lại sau mỗi step). **HTML processing 3 bước**: (1) filter interactable elements bằng CSS selectors (4564→371); (2) element string matching theo state (371→29); (3) attribute cleaning bằng entropy/zxcvbn để bỏ random hash strings → giảm **33× tokens** (37k→1.4k). **8 component LLM**: summarize context, screenshot→candidate action (vision), propose top-15 elements (indexed list ~ set-of-marks), select top-1 action+element, text entry/option, **double-check** (sanity-check hallucinated index), **end-state detection/terminate**. Caching keyed by URL + screenshot response (LRU/LFU, max 100 keys).

## Dữ liệu hoặc ứng dụng thực nghiệm

- **Mind2Web** (2,350 NL tasks, >10k actions, tạo bằng Playwright); random sample 122 tasks/621 actions; component eval trên 200-sample subsets.
- **Manual eval**: 30 tasks live trên real websites (macys, drugs, tiktok, google, united, imdb, budget, healthline, nba, adoptapet, stubhub, ryanair, trip...).
- Models: GPT-3.5-Turbo, GPT-4-Turbo, GPT-4-Vision; zero/few-shot, không fine-tune.

## Tiêu chí đánh giá

Component per-step accuracy (isolation), end-to-end step correctness (Mind2Web ground truth), live task completion (manual), runtime, cost, caching hit rate, error analysis.

## Kết quả chính

- Element+action selection **isolation 81.44% top-1** (GPT-4; element 83.83%, action 88.02%, n=5).
- End-to-end per-step: ground-truth element+action chọn đúng **46.55–48.50%** (Mind2Web); ground truth nằm trong filtered list 58–64%; text field match 85–92%.
- **Live: 40% task completion (12/30)**; ~56% step progress trước khi gặp lỗi; end-state termination đúng **71%**.
- Runtime median **8.52–10.14s/action, $0.028/action, ~$0.18/task**; caching → 4.8s, $0.013/action, cache hit ~49%.

## Hạn chế

- Completion 40% còn thấp; lỗi chủ yếu từ **HTML filtering + top-15 proposal** (element cần thiết không nằm trong interactable/limited list), LLM tưởng search icon clickable, early end-state termination, text field generation.
- Mind2Web chỉ có **1 ground-truth sequence** → phạt các đường đi hợp lệ khác (search bar vs menu).
- Struggle với booking tasks; cần bypass bot detection (Firefox Nightly + VPN).
- **Security/privacy**: không khuyến nghị cho task cần credential/account; ethical (fake account, DoS, fake review).
- Token reduction 33× đánh đổi: ground-truth element chỉ còn trong 82.64% trang.

## Liên quan đến đề tài

- Structured requirements: **Không** — input là NL high-level goal 1 câu, không requirement chuẩn hóa.
- Traceability: **Không**.
- DOM grounding: **Có, đóng góp chính** — hybrid: DOM interactable elements (CSS selectors) + attribute cleaning + screenshot vision + indexed top-15 element list (giống set-of-marks). Rất liên quan cho grounding + token-efficiency.
- Oracle validation: **Yếu** — end-state detection bằng LLM ("yes" → terminate) + double-check sanity; không oracle formal, không assertion. Đây là **navigation/task completion**, không phải testing oracle.
- Human approval: **Không** — fully autonomous.
- Constrained repair: **Một phần** — double-check để chặn hallucinated element; expand CSS selectors / regenerate string search khi fail; không phải test repair.
- Playwright support: **Có, mạnh** — thiết kế riêng cho Playwright; verb→Playwright `Locator` mapping; dùng `Context`/`Page`/`Locator`.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Web automation dùng LLM từ NL instruction, end-to-end/cost-efficient/scalable qua Playwright.
2. **Đầu vào là gì?** NL high-level goal (1 câu) + website (HTML + screenshot).
3. **Đầu ra là gì?** Chuỗi action thực thi trên site qua Playwright (click/type/select/goto...), đến end state.
4. **Có chuẩn hóa requirement không?** Không — NL goal 1 câu.
5. **Có phát hiện ambiguity không?** Không formal; double-check giảm hallucination.
6. **Có traceability không?** Không.
7. **Có grounding trên UI không?** **Có, đóng góp chính** — DOM filtering (CSS selectors) + attribute cleaning + screenshot vision + indexed top-15 elements.
8. **Có xác định test oracle không?** Yếu — end-state detection bằng LLM; không assertion/oracle testing.
9. **Có human approval không?** Không — fully autonomous.
10. **Có kiểm soát repair không?** Double-check + expand selectors khi fail element; không phải constrained test repair.
11. **Đánh giá trên dữ liệu nào?** Mind2Web (122 tasks/621 actions) + 30 live tasks; GPT-3.5/4/4V; 40% completion, 8.52s/$0.028 per action.
12. **Hạn chế là gì?** Completion 40% thấp, lỗi HTML filtering/proposal, 1 ground-truth sequence, booking khó, security/privacy, bot detection.

## Trích dẫn hoặc ý cần kiểm tra lại

- "40% task completion" chỉ trên **30 live tasks (12/30)** — mẫu nhỏ, không phải benchmark lớn.
- **81.44% là accuracy component isolation** (element+action, n=5), KHÁC per-step end-to-end **46.55–48.50%** — không trích 81% như hiệu năng hệ thống.
- Token reduction 33× (37k→1.4k) đánh đổi: ground-truth element chỉ còn trong 82.64% trang → nêu rõ trade-off khi trích.
- Cost caching: abstract ghi $0.013/action, một chỗ khác ghi $0.022 — số hơi lệch, đối chiếu bản gốc.

## Nhận xét của nhóm

Nguồn rất liên quan cho **DOM grounding + Playwright integration + HTML token-efficiency** của đề tài. Kỹ thuật đáng học: **3 bước HTML filtering** (CSS selector → string matching → entropy attribute cleaning), **indexed element list** (giảm hallucination), **verb→Playwright Locator mapping**, action caching, end-state detection. Nhưng Steward là **navigation/task automation, KHÔNG phải testing**: không oracle/assertion, không requirement, không traceability, completion chỉ 40%. Bổ trợ [[SRC-002-playwright-codegen-locators]] (locator) và [[SRC-004-webtestpilot]] (grounding + oracle). Đề tài dùng grounding kiểu Steward + thêm requirement→test + oracle + human approval + Playwright test artifact bền vững.
