# Kết quả RQ2 — ngữ cảnh DOM (aria snapshot) và first-run pass rate

Catalog `datasets/reference/rq2_targets.json`: 50 target, 6 site; oracle viết tay đạt **50/50** (`python run_rq2.py --context oracle`). Model `deepseek-chat`, mỗi nhánh chạy 1 lần, script không qua repair. Lệnh: `python run_rq2.py --profile cloud --context both --out rq2_results_both.json`.

| Site | n | Baseline (none) | DOM-aware (aria) |
|---|---|---|---|
| The Internet (Heroku) | 16 | 16 (100%) | 14 (88%) |
| SauceDemo | 14 | 8 (57%) | 8 (57%) |
| UI Testing Playground | 8 | 2 (25%) | 6 (75%) |
| Practice Test Automation | 5 | 3 (60%) | 2 (40%) |
| DemoQA | 4 | 3 (75%) | 3 (75%) |
| OrangeHRM Demo | 3 | 0 (0%) | 2 (67%) |
| **Tổng** | 50 | **32 (64%)** | **35 (70%)** |

Theo cặp: cả hai đạt 29, chỉ aria đạt 6, chỉ baseline đạt 3, cả hai trượt 12. McNemar chính xác p = 0.508.

Kiểm soát nhiễu: Chromium chạy `--disable-http2` (HTTP/2 tới heroku treo ở mạng của nhóm), `expect` timeout 10s; script fail vì `Page.goto: Timeout` được chạy lại đúng script đó 1 lần (`infra_retry`).

Theo nguyên nhân (dòng lỗi cuối của stderr): "không tìm thấy phần tử để thao tác" 13 → 5; "locator khớp nhiều phần tử" 5 → 9.
Ngữ cảnh DOM chữa locator trỏ tới phần tử không tồn tại (ô nhập không gắn nhãn ở UI Testing Playground, OrangeHRM)
nhưng không kiểm tính duy nhất (6 nút "Add to cart" ở SauceDemo) và không thấy phần tử sau điều hướng (snapshot chỉ trang đầu).

**Lần đo 1 (bị loại):** baseline 21/50, aria 38/50 — 17 script baseline có `page.goto("")` vì SYSTEM_PROMPT không nói
goto đặt URL ở `arg`; DeepSeek đặt vào `value`. Đã sửa prompt (1 dòng) cho cả hai nhánh rồi đo lại (bảng trên).
Kết quả lần 1 lưu ở `rq2_results_both_v1.json` (không commit).

## Bản 2 — vòng lặp grounding, 3 lần lặp (deepseek-chat)

Lệnh: `python run_rq2.py --profile cloud --context all --out rq2_v2_r{1,2,3}.json`. Template mới: timeout thao tác 10s,
trường `nth`. Oracle 49/50 (PT-04 vượt timeout 10s).

| Nhánh | Lần 1 | Lần 2 | Lần 3 |
|---|---|---|---|
| none | 34 | 34 | 36 |
| aria (snapshot trang đầu) | 39 | 41 | 41 |
| aria_loop (+ phản hồi grounding, sinh lại 1 lần) | 49 | 48 | 50 |

McNemar: none→aria p = 0,27 / 0,09 / 0,18 (không có ý nghĩa); none→aria_loop p ≤ 0,0013; aria→aria_loop p ≤ 0,016;
aria_loop không làm mất target nào mà aria đạt.

**Assertion rỗng** (`tools/rq2_vacuity.py`: bỏ fill/click rồi chạy lại, vẫn pass = assertion không phụ thuộc hành động):
oracle rỗng ở 6 target + PT-04 → target yếu từ gốc. Rỗng do LLM chỉ ở aria_loop, cả 3 lần: PT-03 và UP-05 (kiểm tay),
đều do `nth(0)` trỏ vào đoạn văn hướng dẫn/giải thích thay vì phần tử thật. Pass có ý nghĩa của aria_loop: 47 / 46 / 48.
