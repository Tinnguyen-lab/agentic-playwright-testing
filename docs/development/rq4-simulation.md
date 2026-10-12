# RQ4-S — mô phỏng kiểm soát cổng xác nhận

## Mục đích và ranh giới

RQ4 đánh giá quy trình **human-in-the-loop**, không đánh giá AI như công cụ
thay thế kiểm thử viên. RQ4-S là một ablation kỹ thuật nhỏ: nó kiểm tra trực
tiếp hậu quả của việc bỏ qua bước xác nhận oracle/expected result. Không có dữ
liệu người dùng, thời gian hoàn thành, SUS, hay kết luận “nhanh hơn con người”.

Hai nhánh dùng cùng sáu yêu cầu trong `datasets/reference/rq4/task_A.md` và
`task_B.md`:

| Nhánh | Nội dung |
|---|---|
| `system_only` | Sáu script fixture chạy được. Hai script cố ý thiếu assertion expected result: lỗi mật khẩu sai (A/UC-2) và kiểm tra First name (B/UC-2). |
| `reviewed` | Giữ nguyên action/locator, chỉ bổ sung hai assertion bị thiếu như một reviewer oracle lý tưởng. |

Mỗi script chạy trên ShopLab `v0`, sau đó trên mutation semantic đúng với UC.
Một test chỉ hợp lệ nếu pass trên `v0` và fail trên mutation. Đây là cùng tiêu
chí kiểm chứng được dùng trong RQ4, không phải nhận định chủ quan của LLM.

## Chạy

```powershell
python tools/rq4/simulate.py
```

Kết quả và script fixture được ghi riêng tại `artifacts/rq4_simulation/`; không
đụng vào `artifacts/rq4/` của thí nghiệm người dùng. Tệp chính là
`rq4_simulation_results.json`.

## Cách đọc kết quả

- `runnable_tests`: số UC có script pass ở bản đúng. Chỉ số này có thể cao dù
  assertion rỗng hoặc quá yếu.
- `semantically_valid_tests`: số UC pass ở bản đúng **và** phát hiện mutation
  phá hành vi yêu cầu.
- `semantic_precision_pct` và `semantic_coverage_pct`: trong fixture một test
  cho một UC nên cùng mẫu số là 6. Chúng biểu diễn chất lượng oracle có thể
  kiểm chứng, không phải precision/recall tổng quát của mô hình.

Kết quả mong đợi từ fixture là `system_only` chạy được 6/6 nhưng hợp lệ 4/6,
trong khi `reviewed` hợp lệ 6/6 sau hai chỉnh sửa. Điều đó chỉ chứng minh rằng
cổng review có thể phát hiện và sửa những expected result bị thiếu trong kịch
bản này; nó **không** chứng minh một reviewer thực tế luôn chính xác, cũng
không đo năng suất.

## Cách trình bày trong báo cáo

Gọi đây là “mô phỏng/ablation kỹ thuật RQ4-S”, không gọi nó là phiên review
người thật. Có thể viết: “Pipeline tự động có thể hoàn thành action để test
chạy xanh, nhưng hai trong sáu oracle fixture không đủ mạnh để phát hiện
mutation semantic. Bước xác nhận oracle được mô phỏng đã khôi phục hai
assertion này. Kết quả minh hoạ nhu cầu human-in-the-loop; hiệu quả thời gian
chỉ là lợi ích thiết kế dự kiến, không phải chỉ số đã đo.”
