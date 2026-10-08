# Kết quả đánh giá — phát hiện mơ hồ (Requirement Agent)

Ground truth: nhãn chèn có chủ đích trong `datasets/reference/ambiguity_eval`. Đơn vị so khớp: cặp (requirement, loại mơ hồ). Căn predicted↔gold theo thứ tự UC.

## Tổng hợp

| Model | Micro-P | Micro-R | Micro-F1 | Macro-F1 | Over-flag* | Lệch số req |
|---|---|---|---|---|---|---|
| deepseek-chat | 0.44 | 0.90 | 0.59 | 0.60 | 0.22 | 1 |
| gemma-4-12b (trước: chưa nắn prompt) | 0.06 | 0.08 | 0.07 | 0.17 | 0.00 | 0 |
| google/gemma-4-12b | 0.71 | 0.83 | 0.77 | 0.69 | 0.00 | 0 |

*Over-flag = tỉ lệ requirement SẠCH bị gắn cờ nhầm (thấp là tốt).

## F1 theo từng loại mơ hồ

| Loại | deepseek-chat | gemma-4-12b (trước: chưa nắn prompt) | google/gemma-4-12b |
|---|---|---|---|
| conflict | 1.00 | 1.00 | 1.00 |
| missing_actor | 0.67 | 0.00 | 1.00 |
| missing_expected_outcome | 0.60 | 0.00 | 0.67 |
| missing_precondition | 0.18 | 0.00 | 0.00 |
| underspecified_action | 0.14 | 0.00 | 0.50 |
| vague_quantifier | 1.00 | 0.00 | 1.00 |
