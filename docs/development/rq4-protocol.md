# Giao thức thí nghiệm RQ4 — công sức thủ công: tự viết test so với dùng hệ thống

**RQ4:** Hệ thống giảm được bao nhiêu thời gian và thao tác chỉnh sửa thủ công so với quy trình viết test case và mã
Playwright truyền thống?

Tài liệu này dành cho người điều phối buổi thí nghiệm. Mọi lệnh chạy ở thư mục gốc dự án.

## 1. Thiết kế

- **Trong-đối-tượng (within-subject):** mỗi người tham gia làm cả hai điều kiện, mỗi điều kiện một bộ nhiệm vụ khác nhau.
- **Hai điều kiện:**
  - `manual`: tự viết test Playwright Python. Được dùng VS Code, `playwright codegen`, tài liệu Playwright và tìm kiếm
    web. Không dùng trợ lý AI.
  - `system`: dùng giao diện Streamlit của hệ thống: phân tích yêu cầu → duyệt → sinh test case → duyệt → sinh script →
    chạy → (nếu lỗi) duyệt đề xuất sửa. Được sửa test case và plan trên giao diện.
- **Hai bộ nhiệm vụ tương đương** trên ShopLab: [task_A.md](../../datasets/reference/rq4/task_A.md) và
  [task_B.md](../../datasets/reference/rq4/task_B.md), mỗi bộ 3 yêu cầu (UC-1..3), độ khó tương tự.
- **Đảo cân bằng** thứ tự điều kiện và bộ nhiệm vụ:

| Người tham gia | Phiên 1 | Phiên 2 |
|---|---|---|
| P1, P5 | manual + A | system + B |
| P2, P6 | system + A | manual + B |
| P3 | manual + B | system + A |
| P4 | system + B | manual + A |

- **Giới hạn thời gian:** 30 phút mỗi phiên. Hết giờ thì dừng và chấm phần đã làm.

## 2. Người tham gia

4–6 người: thành viên nhóm và sinh viên CNTT đã biết Python cơ bản. Ghi lại mức kinh nghiệm Playwright (chưa dùng /
đã dùng / thành thạo). Người tham gia đồng ý bằng lời trước khi bắt đầu; không thu thông tin cá nhân ngoài mã P1..P6.

## 3. Chuẩn bị máy (một lần)

```
pip install -r requirements.txt
python -m playwright install chromium
python apps/shoplab/app.py --variant v0 --port 5100      # để chạy suốt buổi, cửa sổ riêng
streamlit run src/ui/app.py                               # cửa sổ riêng, cho điều kiện system
```

Điều kiện `system` dùng backend `cloud (.env.cloud)` trên giao diện. Ở ô "Người dùng / mã người tham gia" nhập mã
P1..P6. Ở ô "Dự án" nhập `rq4-<mã>-<bộ>`, ví dụ `rq4-P1-B`. Ở ô "URL ứng dụng đích" nhập `http://127.0.0.1:5100/login`.

## 4. Quy trình một phiên

1. Đưa người tham gia tài liệu nhiệm vụ (A hoặc B). Cho 2 phút đọc, chưa tính giờ.
2. Hướng dẫn quy ước nộp bài: **mỗi yêu cầu một file**, tên bắt đầu bằng `uc1_`, `uc2_`, `uc3_`. File có hàm
   `test_...` sẽ chạy bằng pytest (fixture `page` của pytest-playwright); file không có thì chạy bằng `python` và phải
   thoát mã 0 khi đạt.
3. Bấm giờ bắt đầu:
   `python tools/rq4/rq4.py timer start --participant P1 --condition manual --task A`
4. Người tham gia làm việc. Người điều phối không gợi ý về nội dung, chỉ trả lời câu hỏi về công cụ.
5. Khi người tham gia báo xong (hoặc hết 30 phút), bấm giờ kết thúc:
   `python tools/rq4/rq4.py timer stop --participant P1 --condition manual --task A`
6. Với điều kiện `system`, xuất script hệ thống đã sinh ra từ DB:
   `python tools/rq4/rq4.py export --project rq4-P1-B --out artifacts/rq4/P1_system`
   Với điều kiện `manual`, chép các file `uc*.py` của người tham gia vào `artifacts/rq4/P1_manual`.
7. Chấm tự động:
   `python tools/rq4/rq4.py check --participant P1 --condition manual --task A --tests artifacts/rq4/P1_manual`
   (Tắt ShopLab ở cổng 5100 trước khi chấm; lệnh check tự bật các phiên bản cần thiết trên cổng này.)
8. Người tham gia điền phiếu SUS (mục 6) cho điều kiện vừa làm.

## 5. Số đo

| Số đo | Cách lấy | Ghi chú |
|---|---|---|
| Thời gian hoàn thành (phút) | `timer start/stop` | Tối đa 30 |
| Số yêu cầu có test **hợp lệ** (0–3) | `check` | Hợp lệ = có test PASS trên ShopLab v0 **và** FAIL trên mutation ngữ nghĩa phá đúng hành vi của yêu cầu đó (A: S4_redirect, S1_error_msg, S6_add_noop; B: S2_total, S3_validation, S5_locked). Test chạy được nhưng không kiểm gì sẽ bị loại. |
| Số lần sửa tay (system) | bảng `ui_event` (sự kiện `edit_test_case`, `edit_plan`) | Lấy theo mã người tham gia |
| Điểm SUS (0–100) | phiếu mục 6 → `artifacts/rq4/sus.csv` | |

Tổng hợp: `python tools/rq4/rq4.py analyze` → `artifacts/rq4/rq4_results.json` (từng người + trung vị theo điều kiện).
Với 4–6 người, báo cáo dạng mô tả (trung vị, từng cặp), không kết luận thống kê mạnh.

## 6. Phiếu SUS (System Usability Scale)

Thang 1 (hoàn toàn không đồng ý) đến 5 (hoàn toàn đồng ý). Người điều phối nhập vào `artifacts/rq4/sus.csv` với cột
`participant,condition,q1,...,q10`.

1. Tôi nghĩ mình sẽ muốn dùng cách làm này thường xuyên.
2. Tôi thấy cách làm này phức tạp không cần thiết.
3. Tôi thấy cách làm này dễ dùng.
4. Tôi nghĩ mình cần người hỗ trợ kỹ thuật mới dùng được cách làm này.
5. Tôi thấy các chức năng được kết hợp tốt với nhau.
6. Tôi thấy có quá nhiều điểm không nhất quán.
7. Tôi nghĩ hầu hết mọi người sẽ học được cách làm này rất nhanh.
8. Tôi thấy cách làm này rất cồng kềnh.
9. Tôi thấy tự tin khi dùng cách làm này.
10. Tôi phải học nhiều thứ trước khi dùng được cách làm này.

## 7. Mối đe dọa tính hợp lệ cần ghi trong báo cáo

- Cỡ mẫu nhỏ và người tham gia gần nhóm nghiên cứu (có thể thiên vị điều kiện `system`).
- Hiệu ứng học: phiên 2 dễ hơn vì đã quen ShopLab. Đảo cân bằng giảm nhưng không loại bỏ hoàn toàn.
- Nhiệm vụ ngắn, ứng dụng nhỏ; kết quả không suy rộng cho bộ test lớn.
- Bộ chấm chỉ kiểm hành vi chính của từng yêu cầu bằng một mutation; test có thể đúng ở khía cạnh khác mà không được ghi
  nhận.
