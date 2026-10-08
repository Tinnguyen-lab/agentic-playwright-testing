"""Biến thể (mutation) của ShopLab cho RQ3. Mỗi biến thể = v0 + một nhóm thay đổi, có nhãn ground truth.

14 biến thể đầu (T1–T8, S1–S6) dùng trong lúc phát triển; T9–T12, S7–S10 là tập độc lập, thêm sau khi chốt hệ thống.

- technical: refactor UI, nghiệp vụ GIỮ NGUYÊN -> hành vi đúng của repair: sửa locator, test pass, assertion giữ nguyên.
- semantic:  hành vi nghiệp vụ ĐỔI (bug thật) -> hành vi đúng: KHÔNG được làm test pass; phải chặn/escalate.
"""
from __future__ import annotations

# Giá trị mặc định của v0. Template và route đọc mọi thứ từ đây.
BASE: dict = {
    # login
    "user_id": "username", "user_label": "Username", "user_ph": "Username", "user_testid": "username",
    "pass_id": "password", "pass_label": "Password", "pass_ph": "Password", "pass_testid": "password",
    "login_btn": "Login", "login_btn_id": "login-button",
    "msg_invalid": "Invalid username or password", "msg_required": "Username is required",
    "msg_locked": "Account is locked", "msg_logout": "You have been logged out",
    "logout_link": "Logout", "error_id": "error",
    "after_login": "/products",
    # sản phẩm / giỏ
    "add_btn": "Add to cart", "add_testid": "add-{slug}", "badge_testid": "cart-count", "price_class": "price",
    "cart_link": "Cart", "checkout_btn": "Checkout", "total_class": "cart-total",
    # checkout
    "first_label": "First name", "last_label": "Last name", "zip_label": "Zip code", "continue_btn": "Continue",
    "msg_first_required": "First name is required", "thanks": "Thank you for your order!",
    # profile
    "name_label": "Display name", "save_btn": "Save", "msg_saved": "Profile saved", "msg_save_failed": "Could not save profile",
    # hành vi
    "wrap": False, "locked_allowed": False, "skip_first_validation": False, "add_noop": False, "total_bug": False,
    "logout_noop": False, "price_bug": False, "badge_bug": False, "save_fails": False,
}

VARIANTS: dict[str, dict] = {
    "v0": {"kind": "base", "desc": "Phiên bản gốc", "set": {}},
    # ---- technical (8) ----
    "T1_ids": {"kind": "technical", "desc": "Đổi id của ô nhập và nút đăng nhập",
               "set": {"user_id": "login-user", "pass_id": "login-pass", "login_btn_id": "btn-signin"}},
    "T2_placeholders": {"kind": "technical", "desc": "Đổi placeholder ô đăng nhập",
                        "set": {"user_ph": "Your login", "pass_ph": "Secret phrase"}},
    "T3_labels": {"kind": "technical", "desc": "Đổi nhãn ô đăng nhập",
                  "set": {"user_label": "User name", "pass_label": "Passcode"}},
    "T4_login_text": {"kind": "technical", "desc": "Đổi chữ nút Login thành Sign in", "set": {"login_btn": "Sign in"}},
    "T5_testids": {"kind": "technical", "desc": "Đổi data-testid của nút thêm giỏ và badge",
                   "set": {"add_testid": "btn-add-{slug}", "badge_testid": "cart-badge"}},
    "T6_checkout_text": {"kind": "technical", "desc": "Đổi chữ nút Checkout/Continue",
                         "set": {"checkout_btn": "Proceed to checkout", "continue_btn": "Next"}},
    "T7_classes": {"kind": "technical", "desc": "Đổi class và bọc thêm div",
                   "set": {"price_class": "product-price", "total_class": "order-total", "wrap": True}},
    "T8_save_text": {"kind": "technical", "desc": "Đổi chữ nút Save và nhãn Display name",
                     "set": {"save_btn": "Save changes", "name_label": "Public name"}},
    # ---- semantic (6) ----
    "S1_error_msg": {"kind": "semantic", "desc": "Đăng nhập sai hiện thông báo chung chung (mất thông tin lỗi)",
                     "set": {"msg_invalid": "Something went wrong"}},
    "S2_total": {"kind": "semantic", "desc": "Tổng tiền giỏ hàng tính sai (bỏ qua món đầu)", "set": {"total_bug": True}},
    "S3_validation": {"kind": "semantic", "desc": "Bỏ kiểm tra bắt buộc First name khi checkout",
                      "set": {"skip_first_validation": True}},
    "S4_redirect": {"kind": "semantic", "desc": "Đăng nhập thành công chuyển nhầm sang trang hồ sơ",
                    "set": {"after_login": "/profile"}},
    "S5_locked": {"kind": "semantic", "desc": "Tài khoản bị khoá vẫn đăng nhập được", "set": {"locked_allowed": True}},
    "S6_add_noop": {"kind": "semantic", "desc": "Nút Add to cart không thêm gì vào giỏ", "set": {"add_noop": True}},
    # ---- tập độc lập: thêm SAU khi đã chốt hệ thống (08/10/2026), không dùng để chỉnh repair/policy ----
    "T9_cart_link": {"kind": "technical", "desc": "Đổi chữ liên kết Cart thành Basket", "set": {"cart_link": "Basket"}},
    "T10_checkout_labels": {"kind": "technical", "desc": "Đổi nhãn ba ô của form checkout",
                            "set": {"first_label": "Given name", "last_label": "Family name", "zip_label": "Postal code"}},
    "T11_logout_text": {"kind": "technical", "desc": "Đổi chữ liên kết Logout thành Sign out",
                        "set": {"logout_link": "Sign out"}},
    "T12_error_id": {"kind": "technical", "desc": "Đổi id của khối báo lỗi (error -> form-error)",
                     "set": {"error_id": "form-error"}},
    "S7_logout_noop": {"kind": "semantic", "desc": "Logout không kết thúc phiên, quay lại trang Products",
                       "set": {"logout_noop": True}},
    "S8_price": {"kind": "semantic", "desc": "Giá hiển thị của sản phẩm đầu bị sai ($19.99 thay vì $29.99)",
                 "set": {"price_bug": True}},
    "S9_badge": {"kind": "semantic", "desc": "Badge giỏ hàng đếm thừa 1", "set": {"badge_bug": True}},
    "S10_save_fails": {"kind": "semantic", "desc": "Lưu hồ sơ thất bại, hiện 'Could not save profile'",
                       "set": {"save_fails": True}},
}


def config(name: str) -> dict:
    return {**BASE, **VARIANTS[name]["set"]}
