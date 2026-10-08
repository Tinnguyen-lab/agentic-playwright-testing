# Source Reading Notes — ReqToCode (Requirements Traceability as Structural Property)

## Thông tin nguồn

- Tiêu đề: ReqToCode: Embedding Requirements Traceability as a Structural Property of the Codebase
- Tác giả/tổ chức: Thorsten Schlathölter (Independent Researcher; công cụ Ariadne)
- Năm: 2026
- Loại nguồn: Preprint (approach/position paper, **not peer-reviewed**)
- Mã DOI/arXiv/tài liệu: [arXiv:2603.13999v1](https://arxiv.org/abs/2603.13999) [cs.SE], 14 Mar 2026
- Ngày đọc: 2026-07-19
- Người đọc: Nhóm đồ án

## Bài toán nguồn giải quyết

Trong phần mềm safety-critical (ISO 26262, IEC 62304, DO-178C, ASPICE), requirements traceability là bắt buộc nhưng thường duy trì bằng artifact **external** (spreadsheet, traceability matrix, ALM: Jira/DOORS/Polarion/Codebeamer) tách rời code. Khi requirement/code/test tiến hóa độc lập, trace **suy giảm âm thầm** ("traceability debt") và lộ ra đau đớn lúc audit. Các cách LLM-based traceability recovery chỉ khôi phục link **sau khi đã hỏng** (retrospective). ReqToCode **ngăn suy giảm** bằng cách embed phần tử traceable trực tiếp vào codebase → traceability thành thuộc tính **verify được lúc compile** ("broken trace = broken build").

## Các phần đã đọc

- **Abstract/tóm tắt:** Giới thiệu **Traceable** — code element language-native, generated, đại diện 1 requirement và mang metadata. Developer reference Traceable trong impl & test code tạo hard bidirectional links, validate tự động lúc build. Requirement đổi → graduated lifecycle (deprecation warning → build failure).
- **Introduction:** Traceability external phân kỳ với hệ thống khi tiến hóa; AI code generation càng nới rộng khoảng cách. Recovery-based (LLM) là retrospective, output xác suất, không đảm bảo completeness.
- **Architecture/phương pháp (Sec 3):** Traceable (generated, language-native, metadata-carrying, referenceable, lifecycle-aware). RequirementSets (nhóm scope → module riêng). Pipeline: source sync (ALM) → Traceable generation → codebase integration (commit + review) → reference & verification (compiler) → **bidirectional change detection**. Graduated lifecycle Active → Deprecated → Removed. Branch-scoped traceability. Coverage analysis at any revision (static analysis).
- **Example (Sec 4):** Automotive sensor validation (SWR-101/102/103): generation, impl reference `trace(SWR_101)`, test `verifiesRequirement(SWR_101)`, deprecation, removal→compile error, change detection bằng so timestamp ALM vs Git commit, branch-scoped, coverage report.
- **Discussion/Limitations (Sec 5) + Appendix Java:** Properties + limitations; realization Java (enum + `@TracesSWR`/`@VerifiesSWR`, source-retention). Self-application: **Ariadne** dùng ReqToCode để trace chính nó (Java/C/C++, Jira/Codebeamer/Markdown).

## Phương pháp

Đảo ngược mô hình traceability truyền thống: thay vì metadata external mô tả hệ thống, sinh artifact language-native từ requirement source (single source of truth) và embed vào codebase như phần tử type-system. Link trace trở thành code dependency → compiler/linker/build kiểm. Bidirectional change detection: so requirement last-modified (ALM) vs Git commit của code reference. Graduated lifecycle: deprecation (@Deprecated) trước khi removal (build failure) — "signal proportional to urgency". Không có LLM trong lõi (nhưng đề xuất LLM làm lớp "plausibility assessment" cho suspect traces — chưa triển khai).

## Dữ liệu hoặc ứng dụng thực nghiệm

**Không có empirical evaluation định lượng.** Chỉ có: (1) illustrative example (automotive, tool/language-agnostic); (2) **self-application** — công cụ Ariadne dùng ReqToCode để trace requirement của chính nó, sinh artifact Java/C/C++, kết nối Jira/Codebeamer + Markdown as-code. Là approach/position paper.

## Tiêu chí đánh giá

Không có metric định lượng. Trình bày **properties** (structural traceability, graduated lifecycle, immediate failure on removal, bidirectional change visibility, developer-native workflow, audit-readiness, branch-scoped, on-demand coverage) và **limitations** định tính.

## Kết quả chính

- Đề xuất khái niệm Traceable + RequirementSet + graduated lifecycle + branch-scoped traceability + coverage-at-any-revision.
- "Broken trace = broken build": vi phạm traceability biểu hiện thành compile error, không phải cảnh báo âm thầm.
- Audit-native: có thể tái dựng trạng thái traceability tại bất kỳ revision nào từ Git history.
- Self-application (Ariadne) chứng minh khả thi trong điều kiện thật (chưa phải đánh giá đối chứng).

## Hạn chế

- **Trace granularity:** chỉ đảm bảo requirement **được reference**, KHÔNG verify implementation đúng/đủ — "structural presence, not semantic correctness". Developer có thể `trace(SWR_101)` trong code không thực sự làm range validation.
- **Adoption dependency:** dựa developer tự thêm reference; quên → hệ thống không phát hiện.
- Generation latency (sync định kỳ); cần language hỗ trợ compile-time verifiable named constants; cần ALM expose lifecycle transitions.
- **Không có empirical evaluation** (preprint chưa peer-review).

## Liên quan đến đề tài

- Structured requirements: **Có** — requirement từ ALM/Markdown-as-code → mỗi requirement thành Traceable typed element có metadata (id/title/status/version). Rất liên quan cho requirement representation.
- Traceability: **Đóng góp chính / mạnh nhất trong bộ đọc** — hard, compile-time verifiable, **bidirectional** requirement↔code↔test; branch-scoped; coverage at any revision.
- DOM grounding: **Không** — về code/build, không UI.
- Oracle validation: **Không** — chỉ structural link; `verifiesRequirement` chỉ đánh dấu test verify requirement nào, **không phải oracle** kiểm hành vi.
- Human approval: **Một phần** — Traceable generated commit qua PR/review; deprecation lifecycle cho team thời gian phản hồi; nhưng không phải approval gate cho test/oracle.
- Constrained repair: **Không** — nhưng **graduated lifecycle (deprecation→removal, signal proportional)** là mô hình đáng học cho quản lý thay đổi/repair.
- Playwright support: **Không**.

## Trả lời 12 câu hỏi đối chiếu

1. **Nguồn giải quyết vấn đề gì?** Ngăn suy giảm traceability bằng cách embed requirement thành code element verify lúc compile (thay vì recovery sau khi hỏng).
2. **Đầu vào là gì?** Requirement từ ALM tool / structured Markdown (single source of truth).
3. **Đầu ra là gì?** Traceable (enum/typed element) + RequirementSet module + coverage report + change-detection signals.
4. **Có chuẩn hóa requirement không?** Có — mỗi requirement → Traceable typed element có metadata (id, title, status, version).
5. **Có phát hiện ambiguity không?** Không (không phát hiện ambiguity ngữ nghĩa).
6. **Có traceability không?** **Có, đóng góp chính** — hard compile-time bidirectional requirement↔code↔test, branch-scoped, coverage-at-revision.
7. **Có grounding trên UI không?** Không — về codebase/build.
8. **Có xác định test oracle không?** Không — chỉ structural presence, không verify implementation đúng.
9. **Có human approval không?** Một phần — generated Traceable qua PR review + deprecation warning; không approval gate test.
10. **Có kiểm soát repair không?** Không; nhưng graduated lifecycle (deprecation→build failure) là mô hình signal proportional đáng học.
11. **Đánh giá trên dữ liệu nào?** Không empirical; illustrative example + self-application (Ariadne, Java/C/C++, Jira/Codebeamer).
12. **Hạn chế là gì?** Chỉ structural (không semantic), adoption dependency, generation latency, language/ALM support, không empirical evaluation.

## Trích dẫn hoặc ý cần kiểm tra lại

- Là **preprint chưa peer-review**, **không có evaluation định lượng** → khi trích phải nói rõ đây là approach/position paper, không phải bằng chứng empirical.
- "Structural presence, not semantic correctness" (Sec 5.2) rất quan trọng: ReqToCode **không** đảm bảo test/impl đúng; ý dùng LLM đánh giá "plausibility" của trace là đề xuất **chưa triển khai**.
- Số liệu accuracy trong related work (vd TVR 98.87%) là của nguồn khác, không phải kết quả ReqToCode.

## Nhận xét của nhóm

Nguồn **traceability mạnh nhất** trong bộ đọc; cung cấp mô hình requirement→code→test link **cứng, bidirectional, coverage-at-revision, audit-native** — rất phù hợp tiêu chí "traceability" + "structured requirements" của đề tài. Ý "trace là build dependency, broken trace = broken build" và graduated lifecycle đáng áp dụng cho **test artifact** của đề tài (gắn requirement ID vào Playwright test — traceability artifact-level mà [[SRC-004-webtestpilot]] còn thiếu). Nhưng dừng ở structural, không grounding/oracle/execution → bổ trợ chứ không thay [[SRC-004-webtestpilot]]/[[SRC-008-autonomous-test-repair-limits]]. Dùng làm **design reference** cho traceability, không phải nguồn số liệu.
