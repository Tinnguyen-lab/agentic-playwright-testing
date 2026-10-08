# Kết quả RQ3 — sửa lỗi có ràng buộc trên ShopLab

ShopLab (`apps/shoplab`): 14 mutation (8 technical, 6 semantic), bộ 20 test; tối đa 6 test gãy mỗi mutation → 31 ca
technical, 17 ca semantic. Ngân sách 2 lần sửa. Lệnh: `python run_rq3.py --profile cloud --out rq3_results_v2.json`.

| Nhánh | Technical sửa được, giữ assertion | Semantic bị che | Escalate | Lần làm yếu assertion |
|---|---|---|---|---|
| unconstrained (LLM, tự áp dụng) | 23/31 (lần 1: 23/31) | **8/17** (lần 1: 10/17) | 0 | 18 (21) |
| heal (self-healing, chữa theo lô) | 24/31 (lần 1, chữa từng cái: 21) | 0/17 | 0 | 0 |
| constrained (hệ thống) | 24/31 (lần 1: 21) | **0/17** | 11 | 0 |

Che lỗi của unconstrained: đổi giá trị kỳ vọng cho khớp bug (S1 "Invalid username or password" → "Something went
wrong"; S2 "Total: $39.98" → "Total: $9.99") hoặc chèn `goto` vòng qua lỗi chuyển hướng (S4).
Constrained: 6/31 escalate oan, đều do phải đổi locator bên trong assertion (T5, T7) — policy xếp High.
