# Báo cáo: Slice 2 — Parser tài liệu + Đánh giá định lượng

> Mở rộng Requirement Agent thành khối lượng ~2 tuần, tạo **kết quả nghiên cứu định lượng** (RQ1). Cập nhật: 2026-07-29.

---

## 1. Mục tiêu
Slice 1 mới là lõi (text → structured requirements + ambiguity). Slice 2 bổ sung 2 hướng đã chốt:
1. **Parser DOCX/PDF** — nhận tài liệu Word/PDF thật (kiến trúc mục 241 xem parsing là đầu vào agent).
2. **Bộ đánh giá định lượng** — đo precision/recall/F1 khả năng phát hiện mơ hồ, so sánh model.

Không làm slice này: Streamlit + AG-01, lưu SQL Server.

## 2. File mới & chức năng

| File | Chức năng |
|------|-----------|
| `src/services/document_loader.py` | `load_document()` — đọc DOCX (python-docx) / PDF (pymupdf, chèn mốc `[trang N]`) / TXT / MD về text thuần; đuôi lạ → lỗi rõ ràng. |
| `src/evaluation/metrics.py` | Đếm TP/FP/FN theo cặp (requirement, loại) → precision/recall/F1 theo loại + micro/macro. Thuần hàm. |
| `src/evaluation/dataset.py` | `load_dataset()` đọc `labels.json` + tài liệu → danh sách `Case` (text + nhãn gold). |
| `src/evaluation/evaluator.py` | Chạy agent trên dataset, căn predicted↔gold theo thứ tự UC, tổng hợp `EvalReport`. |
| `evaluate_agent.py` | CLI: `--profile` (local/cloud), chạy toàn dataset → in bảng + ghi `eval_<model>.json` + gộp thành `eval-results.md`. |
| `datasets/reference/ambiguity_eval/` | Dataset gán nhãn: 5 tài liệu, **15 yêu cầu**, chèn khuyết tật chủ đích đủ 6 loại + 5 yêu cầu sạch + 1 conflict. |
| `docs/development/design-notes.md` | Rationale thiết kế (tách khỏi code). |

Test: +9 (parser/metrics/evaluator) → tổng **29 test xanh**.

## 3. Phương pháp đánh giá
- **Ground truth = chèn khuyết tật có chủ đích**: mỗi UC gán trước loại mơ hồ + vài UC sạch (đo over-flag).
- **Đơn vị so khớp:** cặp *(requirement, loại mơ hồ)*. Căn predicted↔gold theo **thứ tự UC** (agent đánh REQ-001.. cùng thứ tự). Lệch số requirement → `count_mismatches`.
- **Metrics:** P/R/F1 theo loại, micro (gộp), macro (trung bình loại), tỉ lệ over-flag trên requirement sạch. `conflict` xử lý như một loại ở `global_ambiguities`.

## 4. Kết quả chính — Ablation "chỉ dẫn đặt ambiguity" (Gemma-4-12B local)

| Model | Micro-P | Micro-R | Micro-F1 | Macro-F1 | Over-flag |
|---|---|---|---|---|---|
| Trước (chưa nắn prompt) | 0.06 | 0.08 | **0.07** | 0.17 | 0.00 |
| Sau (thêm 1 dòng đặt ambiguity per-requirement) | 0.57 | 1.00 | **0.73** | 0.78 | 0.40 |

**F1 theo loại (sau):** conflict 1.00 · missing_actor 1.00 · vague_quantifier 1.00 · missing_expected_outcome 0.75 · underspecified_action 0.67 · missing_precondition 0.25.

### Diễn giải (cho luận văn)
- **Chỉ dẫn đặt ambiguity là then chốt:** trước khi thêm, Gemma dồn hết ambiguity vào `global_ambiguities` → per-type F1 ≈ 0 dù *có phát hiện đúng loại*. Chỉ 1 dòng prompt kéo micro-F1 **0.07 → 0.73** (×10). Bộ eval **định lượng hoá** được hiệu ứng này.
- **Recall = 1.00** sau khi sửa → Gemma-12B **bắt hết** khuyết tật chèn vào.
- **Điểm mạnh:** `missing_actor`, `vague_quantifier`, `conflict` đạt F1 = 1.00.
- **Điểm yếu (precision):** `missing_precondition` (P=0.14) và `missing_expected_outcome` (P=0.60) bị **over-flag**. Một phần vì model quá nhạy, một phần vì gold chỉ gán **1 khuyết tật/requirement** (nhãn có thể chưa vét hết mọi chiều) → precision nhạy với cách gán nhãn.

## 5. Việc kế tiếp
- **So cloud:** dán key vào `.env.cloud` → `python evaluate_agent.py --profile cloud` (DeepSeek) → bảng tự thêm cột.
- **Review nhãn gold** (người dùng sở hữu ground truth) — nhất là các chiều precondition/outcome.
- Tinh chỉnh precision (prompt/calibration) hoặc dựa **human-in-the-loop AG-01** để lọc false positive — slice sau.

## 6. Cách chạy lại
```powershell
python -m pytest tests/unit -q                 # 29 passed (offline)
python run_requirement_agent.py --file tai_lieu.docx   # parser DOCX/PDF
python evaluate_agent.py                        # eval Gemma local -> eval-results.md
```
