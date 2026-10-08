# Source Reading Notes — Practical Limits of Autonomous Test Repair

## Thông tin nguồn

- Tiêu đề: Practical Limits of Autonomous Test Repair: A Multi-Agent Case Study with LLM-Driven Discovery and Self-Correction
- Tác giả/tổ chức: Hyukjoo Lee (Independent Researcher, Republic of Korea)
- Năm: 2026
- Loại nguồn: Preprint (industrial case study)
- Mã DOI/arXiv/tài liệu: [arXiv:2605.01471v1](https://arxiv.org/abs/2605.01471) [cs.SE], 2 May 2026; Zenodo: 10.5281/zenodo.19944395
- Ngày đọc: 2026-07-19
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Bảo trì UI test suite ở quy mô enterprise rất tốn kém. Agent LLM tự trị có thể tự **khám phá feature + sinh test + sửa test** không cần người, nhưng câu hỏi thực sự không phải "autonomy có tạo được execution pass hay không" mà là "dưới ràng buộc nào nó hoạt động ổn định và đáng tin". Bài là case study công nghiệp phân tích **failure modes** của một hệ multi-agent autonomous UI testing, rồi rút ra ràng buộc để vận hành tin cậy. Thông điệp trung tâm: **autonomy không ràng buộc → kết quả bất ổn/gây hiểu nhầm; autonomy có ràng buộc → khả dụng trong sản xuất.**

## Các phần đã đọc

- **Abstract/tóm tắt:** Hệ multi-agent (LLM + LangGraph + Playwright + RAG) tiến hóa từ AI-Assisted sang High-autonomy (tự discover >100 feature/10 screen, mở rộng 15–30 feature qua runtime DOM, tự repair). Phân tích 300 execution report / 636 test-case execution / 10 scenario family: convergence 70% (mean 4.4 iteration), nhưng chỉ 10% first-pass, 38% report không sinh được artifact thực thi, và ghi nhận **assertion weakening + test-case deletion** để giả hội tụ.
- **Introduction:** Không phủ nhận LLM; mục tiêu là chỉ ra **giới hạn của autonomy không ràng buộc** và các failure mode lặp lại. Nhấn mạnh failure trong repair loop **compound theo iteration** → bất ổn cấp hệ thống.
- **Architecture/phương pháp (Sec 3):** Pipeline 5 agent Explorer → Planner → Coder → Executor → Self-Correction với 2 vòng lặp; **inter-agent coupling chặt → uncertainty tích lũy**. Coder sinh Playwright TypeScript.
- **Evaluation (Sec 6):** 300 report liên tục / 126 ngày / môi trường enterprise ẩn danh. Đo convergence θ, iteration count, failure signature distribution, first-pass rate. Phân biệt convergence "naive 70%" vs "semantically strict 50%".
- **Limitations/Threats (Sec 10):** 1 môi trường/1 LLM version; nhãn do first-author (không multi-rater); metric convergence không đo semantic quality.

## Phương pháp

- **Explorer**: LLM-driven feature discovery qua multi-round RAG (tối đa 3 vòng) + runtime DOM analysis; feature tracker + skip list.
- **Planner**: feature → structured test scenario; quyết định reuse vs generate (Jaccard similarity, threshold 0.6, ~90% dedup).
- **Coder**: scenario → Playwright TypeScript (context được orchestration pre-collect để tránh misorder tool call).
- **Executor**: chạy script, thu pass/fail, log, DOM snapshot.
- **Self-Correction**: 14 tool (DOM parser, selector verifier single/batch, auth-state checker, RAG experience store) → sinh script sửa → trả lại Executor.

## Dữ liệu hoặc ứng dụng thực nghiệm

Prototype UI testing enterprise ẩn danh (vài trăm element động/màn hình), cấu hình "Improved workflow" (constrained self-correction, bounded retry, skip-list, RAG-grounded selector). 300 report liên tục / 126 ngày, 636 test-case execution, 10 scenario family, max retry depth 16.

## Tiêu chí đánh giá

Repair convergence θ (tỉ lệ family hội tụ trong retry budget), repair iteration count, failure signature distribution + co-occurrence, first-pass success rate. Phân biệt **naive vs semantically-strict** convergence.

## Kết quả chính

- Convergence **70%** family (mean ~3.4–4.4 iteration), nhưng:
  - Chỉ **10% first-pass** (1/10 family).
  - **38% report (113/300) không sinh được artifact thực thi** ("code-gen collapse" — 113 report liên tiếp).
  - **2/7 family hội tụ nhờ assertion weakening (`toBe(5)` → `toBeTruthy()`) hoặc test-case deletion** → naive 70% nhưng **semantically-strict chỉ 50%**.
- Failure signatures (không loại trừ nhau): method/contract mismatch 44%, nav/env timeout 40%, non-executable 38%, selector/readiness 32%, assertion mismatch 26%; **trung bình 2.3 signature đồng xuất hiện/report**. 6 hallucinated selector.
- **6 root causes**: non-determinism, thiếu runtime grounding, **thiếu correctness oracle**, error compounding, fragile inter-agent contract, weak environment-state modeling.
- **5 design guidelines (constrained autonomy)**: G1 bắt buộc runtime grounding (validate selector vs live DOM); G2 bounded iteration + **escalate lên người**; G3 coi test là behavioral spec — **mọi thay đổi assertion/scope phải human validation**; G4 tách environment failure khỏi test failure (skip-list); G5 explicit interface contract giữa agent.

## Hạn chế

- Một môi trường enterprise ẩn danh, một LLM version → external validity hạn chế (cần replicate với GPT-4/Gemini, domain khác).
- Nhãn failure/convergence do first-author, không có inter-rater agreement.
- Metric convergence không đo semantic test quality (chính lỗ hổng mà assertion-weakening/test-deletion phơi bày).
- Là phân tích failure/định hướng, không đề xuất hệ mới hoàn chỉnh.

## Liên quan đến đề tài

- Structured requirements: **Một phần** — Planner tạo structured scenario, nhưng feature do Explorer/LLM tự chọn (không từ requirement chuẩn hóa của người).
- Traceability: **Yếu** — feature registry + Jaccard dedup; không requirement → test traceability.
- DOM grounding: **Một phần / khuyến nghị bắt buộc** — có runtime DOM analysis + selector verifier, nhưng Coder **bỏ qua** khi generate → hallucinated selector; G1 yêu cầu bắt buộc grounding.
- Oracle validation: **Điểm mấu chốt (bằng phản chứng)** — **thiếu correctness oracle là root cause chính**; dẫn tới assertion weakening/test deletion để giả pass. Đề tài cần oracle + semantic preservation.
- Human approval: **Đóng góp chính** — G2/G3 yêu cầu **escalation lên người** + **human validation cho mọi thay đổi assertion/scope**. Bằng chứng công nghiệp mạnh cho "human approval gate".
- Constrained repair: **Đóng góp trung tâm** — bounded iteration (6–7 retry), skip-list environment, **phát hiện semantic drift** (`toBe`→`toBeTruthy`) và **test-count reduction** → route sang người. Chính là "constrained repair" đề tài hướng tới.
- Playwright support: **Có** — Coder sinh Playwright TypeScript, execute qua Playwright.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Chỉ ra giới hạn/failure của autonomous multi-agent LLM test repair ở quy mô enterprise và ràng buộc cần để tin cậy.
2. **Đầu vào là gì?** Feature documentation (qua RAG) + runtime DOM; ở High-autonomy **không có explicit test target**.
3. **Đầu ra là gì?** Playwright TS test script + script đã repair + execution report; và bộ failure modes + design guidelines.
4. **Có chuẩn hóa requirement không?** Planner tạo structured scenario, nhưng feature do LLM chọn; không chuẩn hóa requirement của người.
5. **Có phát hiện ambiguity không?** Không — ngược lại LLM hallucinate feature/selector.
6. **Có traceability không?** Feature registry/dedup, không requirement-level.
7. **Có grounding trên UI không?** Có tool (DOM parser, selector verifier) nhưng Coder bỏ qua → hallucination; G1 đề xuất bắt buộc.
8. **Có xác định test oracle không?** **KHÔNG** — thiếu correctness oracle là root cause chính; gây assertion weakening/test deletion.
9. **Có human approval không?** **KHÔNG trong hệ đang chạy**; nhưng paper kết luận **bắt buộc phải có** (G2/G3 escalation + validation).
10. **Có kiểm soát repair không?** Hệ hiện tại thiếu → khuyến nghị bounded iteration + semantic preservation + escalation (constrained autonomy).
11. **Đánh giá trên dữ liệu nào?** 300 report / 636 execution / 10 family / 126 ngày, prototype UI enterprise ẩn danh; convergence 70% (strict 50%).
12. **Hạn chế là gì?** 1 môi trường/1 LLM, first-author labeling, metric không đo semantic quality, external validity hẹp.

## Trích dẫn hoặc ý cần kiểm tra lại

- "Mean iterations to convergence": abstract ghi **4.4**, Table 3 & Conclusion ghi **3.4** — mâu thuẫn; bảng bị xáo khi trích PDF → đối chiếu bản gốc.
- "70% convergence" dễ gây hiểu nhầm; tác giả nhấn mạnh **"semantically strict 50%"** mới có ý nghĩa vận hành — **không trích 70% mà bỏ ngữ cảnh**.
- Bảng 2 (Corpus): "test cases passed 636 / failed 204 (32.1%)" và "distinct scenario families 42 (14%)" vs "10 families" ở chỗ khác — layout bảng bị lệch khi trích, cần đọc lại bản gốc.

## Nhận xét của nhóm

**Nguồn quan trọng nhất cho luận điểm đề tài về constrained repair + human approval + oracle.** Chứng minh bằng dữ liệu công nghiệp rằng autonomy không ràng buộc thất bại (assertion weakening `toBe→toBeTruthy`, test deletion, code-gen collapse), và đưa ra 5 guideline gần trùng đóng góp đề tài. Trực tiếp bổ trợ [[SRC-004-webtestpilot]] (oracle) và đối lập [[SRC-006-zero-cost-self-healing-dom]] (deterministic repair, không LLM). Đề tài nên trích để justify: (a) **human approval gate** cho thay đổi assertion/scope, (b) **bounded repair budget + audit log**, (c) **runtime DOM grounding bắt buộc**, (d) **semantic-drift detection**. Rất mạnh cho phần motivation + design của đề tài.
