# Tài liệu yêu cầu — ShopLab (bộ nhiệm vụ A)

Ứng dụng: ShopLab, http://127.0.0.1:5100/login. Tài khoản hợp lệ: alice / secret123.

## UC-1: Đăng nhập hợp lệ
Người dùng nhập username "alice" và password "secret123" rồi bấm Login thì được chuyển tới trang sản phẩm (URL /products), trang có tiêu đề "Products".

## UC-2: Đăng nhập sai mật khẩu
Người dùng nhập username "alice" và password sai rồi bấm Login thì ở lại trang đăng nhập và thấy thông báo lỗi "Invalid username or password".

## UC-3: Thêm sản phẩm vào giỏ
Người dùng đã đăng nhập bấm "Add to cart" ở sản phẩm "Sauce Backpack" thì số trên biểu tượng giỏ hàng (Cart) tăng thành 1.
