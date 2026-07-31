# Kết quả đánh giá — phát hiện mơ hồ (Requirement Agent)

Ground truth: nhãn chèn có chủ đích trong `datasets/reference/ambiguity_eval`. Đơn vị so khớp: cặp (requirement, loại mơ hồ). Căn predicted↔gold theo thứ tự UC.

## Tổng hợp

| Model | Micro-P | Micro-R | Micro-F1 | Macro-F1 | Over-flag* | Lệch số req |
|---|---|---|---|---|---|---|
| gemma-4-12b (trước: chưa nắn prompt) | 0.06 | 0.08 | 0.07 | 0.17 | 0.00 | 0 |
| google/gemma-4-12b | 0.57 | 1.00 | 0.73 | 0.78 | 0.40 | 0 |

*Over-flag = tỉ lệ requirement SẠCH bị gắn cờ nhầm (thấp là tốt).

## F1 theo từng loại mơ hồ

| Loại | gemma-4-12b (trước: chưa nắn prompt) | google/gemma-4-12b |
|---|---|---|
| conflict | 1.00 | 1.00 |
| missing_actor | 0.00 | 1.00 |
| missing_expected_outcome | 0.00 | 0.75 |
| missing_precondition | 0.00 | 0.25 |
| underspecified_action | 0.00 | 0.67 |
| vague_quantifier | 0.00 | 1.00 |
