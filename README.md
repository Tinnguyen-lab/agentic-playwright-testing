# Agentic Playwright Testing

**Tên đề tài:** Nghiên cứu và xây dựng hệ thống Agentic AI bán tự động sinh và kiểm chứng kiểm thử đầu-cuối dựa trên Playwright.

## Mục tiêu

Xây dựng hệ thống hỗ trợ chuyển đổi tài liệu yêu cầu thành:

1. Yêu cầu có cấu trúc.
2. Test scenario và test case có truy vết.
3. Mã Playwright Python được grounding trên giao diện thật.
4. Kết quả thực thi và đề xuất sửa kiểm thử có kiểm soát.
5. Quy trình phê duyệt human-in-the-loop.

## Cài đặt

```
pip install -r requirements.txt
python -m playwright install chromium
```

LLM cấu hình trong `.env` (local, ví dụ LM Studio) và `.env.cloud` (DeepSeek/OpenAI), xem `.env.example`.
Hai file này không được commit. DB mặc định là SQLite `artifacts/app.db`; dùng SQL Server bằng `DATABASE_URL`
(xem `src/database/__init__.py`).

## Chạy

| Việc | Lệnh |
|---|---|
| Unit test (offline) | `python -m pytest tests/unit -q` |
| Giao diện | `streamlit run src/ui/app.py` |
| App đích ShopLab | `python apps/shoplab/app.py --variant v0 --port 5100` |
| Pipeline demo trên SauceDemo | `python run_full_pipeline.py` |

## Tái lập thực nghiệm

| RQ | Lệnh | Kết quả |
|---|---|---|
| RQ1 phát hiện mơ hồ | `python evaluate_agent.py --profile cloud` | `datasets/processed/eval_<model>.json` |
| RQ1 chất lượng test case | `python evaluate_rq1.py --profile cloud --out rq1_results_v2.json` | JSON + mẫu chấm tay CSV |
| RQ1 kappa (sau khi chấm tay) | `python evaluate_rq1.py --kappa rq1_judge_sample_v2.csv` | in kappa |
| RQ2 kiểm catalog | `python run_rq2.py --context oracle` | kỳ vọng 49–50/50 |
| RQ2 ba nhánh | `python run_rq2.py --profile cloud --context all --out rq2_v2_r1.json` | JSON |
| RQ3 kiểm suite + mutation | `python run_rq3.py --check` | 20/20 trên v0, mỗi mutation gãy ≥ 1 test |
| RQ3 ba nhánh sửa | `python run_rq3.py --profile cloud --out rq3_results_v2.json` | JSON |
| RQ4 | xem `docs/development/rq4-protocol.md` | `artifacts/rq4/rq4_results.json` |
| Báo cáo chuyên đề | `cd tools/report && python build_report.py ../../rq2_results_both.json ../../rq2_results_both_v1.json <out.docx>` | .docx |

Kết quả và nhận xét: `docs/development/eval-results.md`, `docs/development/eval-rq2.md`,
`docs/bao-cao-chuyen-de/`.

## Cấu trúc

- `src/agents/` — năm agent (Requirement, Test Design, Playwright Generation, Execution, Repair)
- `src/services/` — dịch vụ tất định: LLM client, BVA, locator policy, self-healing, repair policy, truy vết, tác vụ trình duyệt
- `src/database/`, `src/repositories/` — lưu trữ SQLAlchemy và repository
- `src/ui/` — giao diện Streamlit
- `apps/shoplab/` — ứng dụng đích có mutation cho RQ3/RQ4
- `datasets/reference/` — ground truth RQ1, catalog RQ2, nhiệm vụ RQ4
- `tools/` — công cụ RQ4 và bộ dựng báo cáo
