# Kết quả RQ1 — chất lượng test case: pipeline có cấu trúc vs đưa thẳng tài liệu

15 tài liệu, 47 yêu cầu, 83 điều kiện gold (`datasets/reference/ambiguity_eval/test_conditions.json`); giám khảo LLM
(deepseek-chat), mẫu 20% để chấm tay: `datasets/reference/ambiguity_eval/judge_sample_v2.csv`.
Lệnh: `python evaluate_rq1.py --profile cloud --out rq1_results_v2.json`.

| Nhánh | Số TC | Độ phủ gold | Không căn cứ | Truy vết |
|---|---|---|---|---|
| direct v1 | 168 | 79/83 (95%) | 32% | 0% |
| pipeline v1 | 304 | 76/83 (92%) | 45% | 100% |
| direct v2 | 79 | 62/83 (75%) | 3% | 0% |
| pipeline v2 | 106 | 67/83 (81%) | 9% | 100% |
| pipeline v2 + AG-01 (bỏ yêu cầu bị gắn cờ) | 72 | 43/83 (52%) | 4% | 100% |

v2 = thêm quy tắc chỉ sinh negative/error_guessing/alternative_flow khi tài liệu nêu phản ứng của hệ thống (cả hai
nhánh) + ca BVA mang ngữ cảnh hành động. McNemar theo điều kiện: v1 p = 0,38; v2 p = 0,23 → độ phủ không khác có ý nghĩa.
Pipeline v1: 34% test không căn cứ ở UC sạch, 58% ở UC có khuyết tật chèn sẵn.

Phát hiện mơ hồ trên 47 yêu cầu (deepseek-chat): micro-P 0,44, micro-R 0,90, micro-F1 0,59; over-flag 5/23.
