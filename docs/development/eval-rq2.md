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
