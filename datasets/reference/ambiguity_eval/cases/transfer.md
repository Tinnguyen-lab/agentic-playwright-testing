# Tài liệu yêu cầu — Chuyển tiền

## UC-1: Chuyển tiền nội bộ
Khách hàng đã đăng nhập chuyển từ 10.000 đến 50.000.000 đồng mỗi giao dịch. Số tiền ngoài khoảng này bị từ chối với thông báo "Số tiền không hợp lệ".

## UC-2: Xác thực OTP
Trước khi chuyển, hệ thống gửi mã OTP gồm 6 chữ số. Khách hàng nhập đúng OTP thì giao dịch được thực hiện; nhập sai 3 lần thì giao dịch bị huỷ.

## UC-3: Hạn mức ngày
Tổng số tiền chuyển trong một ngày của khách hàng không vượt quá 100.000.000 đồng.
