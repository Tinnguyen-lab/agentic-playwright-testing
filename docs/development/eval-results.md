# Kết quả đánh giá — phát hiện mơ hồ (Requirement Agent)

Ground truth: nhãn chèn có chủ đích trong `datasets/reference/ambiguity_eval`. Đơn vị so khớp: cặp (requirement, loại mơ hồ). Căn predicted↔gold theo thứ tự UC.

## Tổng hợp

| Model | Micro-P | Micro-R | Micro-F1 | Macro-F1 | Over-flag* | Lệch số req |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.50 | 1.00 | 0.67 | 0.71 | 0.20 | 0 |
| gemma-4-12b (trước: chưa nắn prompt) | 0.06 | 0.08 | 0.07 | 0.17 | 0.00 | 0 |
| google/gemma-4-12b | 0.71 | 0.83 | 0.77 | 0.69 | 0.00 | 0 |

*Over-flag = tỉ lệ requirement SẠCH bị gắn cờ nhầm (thấp là tốt).

## Ảnh hưởng của siết prompt (before → after)

Siết `SYSTEM_PROMPT` (thêm nguyên tắc độ chính xác: chỉ gắn cờ khi thực sự thiếu/mơ hồ rõ ràng,
ưu tiên KHÔNG gắn khi phân vân ở precondition/outcome), chạy lại cùng prompt trên cả hai backend:

| Model | Micro-F1 | Over-flag | Recall |
|---|---|---|---|
| gemma-4-12b (local) | 0.73 → **0.77** | 0.40 → **0.00** | 1.00 → 0.83 |
| deepseek-chat (cloud) | 0.51 → **0.67** | 0.80 → **0.20** | 1.00 → 1.00 |

Nhận xét (kết quả **sơ bộ**, dataset 5 tài liệu / 15 yêu cầu):
- Siết prompt **giảm mạnh gắn cờ nhầm** ở cả hai (over-flag Gemma 0.40→0.00, DeepSeek 0.80→0.20) và **nâng micro-F1** cả hai.
- Dưới CÙNG prompt: Gemma nhỉnh hơn về micro-F1/precision (0.77 vs 0.67), còn DeepSeek đầy đủ hơn (recall 1.00 và macro-F1 0.71 > 0.69).
- Trade-off: prompt chặt hơn khiến Gemma **hạ recall 1.00→0.83** (bỏ sót vài ca, rõ nhất `missing_precondition`); DeepSeek giữ recall 1.00.
- `missing_precondition` vẫn là loại khó nhất (nhãn gold chủ quan, chỉ 1 khuyết tật/yêu cầu) — cần nhóm mở rộng nhãn để kết luận vững.

## F1 theo từng loại mơ hồ

| Loại | deepseek-chat | gemma-4-12b (trước: chưa nắn prompt) | google/gemma-4-12b |
|---|---|---|---|
| conflict | 1.00 | 1.00 | 1.00 |
| missing_actor | 0.86 | 0.00 | 1.00 |
| missing_expected_outcome | 0.60 | 0.00 | 0.67 |
| missing_precondition | 0.50 | 0.00 | 0.00 |
| underspecified_action | 0.29 | 0.00 | 0.50 |
| vague_quantifier | 1.00 | 0.00 | 1.00 |

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
