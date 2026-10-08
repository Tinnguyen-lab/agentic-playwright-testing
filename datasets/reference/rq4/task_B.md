# Tài liệu yêu cầu — ShopLab (bộ nhiệm vụ B)

Ứng dụng: ShopLab, http://127.0.0.1:5100/login. Tài khoản hợp lệ: alice / secret123; tài khoản bị khoá: bob / secret123.

## UC-1: Tổng tiền giỏ hàng
Người dùng đã đăng nhập thêm "Sauce Backpack" ($29.99) và "Bike Light" ($9.99) vào giỏ, mở giỏ hàng thì thấy "Total: $39.98".

## UC-2: Checkout thiếu tên
Ở bước checkout, người dùng bỏ trống First name, nhập Last name và Zip code rồi bấm Continue thì thấy lỗi "First name is required".

## UC-3: Tài khoản bị khoá
Người dùng đăng nhập bằng bob / secret123 thì không vào được và thấy thông báo "Account is locked".
