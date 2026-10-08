"""Bộ 20 test (test case + plan) viết cho ShopLab v0 — đầu vào của RQ3.

Locator trộn chiến lược (css id, placeholder, label, role, test id, class) như một bộ test thật, để mỗi mutation
kỹ thuật làm gãy một tập test khác nhau. URL dùng "{BASE}", thay bằng gốc của server lúc chạy.
"""
from __future__ import annotations

from src.models.playwright_artifacts import PlaywrightAction, PlaywrightPlan
from src.models.test_case import TestCase, TestStep, TestType


def A(type, strategy=None, value="", role_name="", arg=""):
    return PlaywrightAction(type=type, strategy=strategy, value=value, role_name=role_name, arg=arg)


def login_css(user="alice", pw="secret123"):
    return [A("goto", arg="{BASE}/login"), A("fill", "css", "#username", arg=user), A("fill", "css", "#password", arg=pw),
            A("click", "css", "#login-button")]


def login_ph(user="alice", pw="secret123"):
    return [A("goto", arg="{BASE}/login"), A("fill", "placeholder", "Username", arg=user),
            A("fill", "placeholder", "Password", arg=pw), A("click", "role", "button", "Login")]


def login_label(user="alice", pw="secret123"):
    return [A("goto", arg="{BASE}/login"), A("fill", "label", "Username", arg=user),
            A("fill", "label", "Password", arg=pw), A("click", "role", "button", "Login")]


ADD = lambda slug: A("click", "test_id", f"add-{slug}")  # noqa: E731
TO_CART = A("click", "role", "link", "Cart")
TO_CHECKOUT = A("click", "role", "button", "Checkout")
LOGIN_STEP = "Đăng nhập bằng alice / secret123"

# id, loại, tiêu đề, các bước, kết quả mong đợi, plan
SUITE = [
    ("R01", "positive", "Đăng nhập hợp lệ", [LOGIN_STEP], "Vào trang Products, URL là /products",
     login_ph() + [A("expect_url", arg="{BASE}/products"), A("expect_visible", "role", "heading", "Products")]),
    ("R02", "negative", "Sai mật khẩu", ["Đăng nhập alice với mật khẩu 'wrong'"],
     "Hiện lỗi 'Invalid username or password'",
     login_label(pw="wrong") + [A("expect_text", "css", "#error", arg="Invalid username or password")]),
    ("R03", "negative", "Bỏ trống username", ["Bấm Login khi chưa nhập gì"], "Hiện lỗi 'Username is required'",
     [A("goto", arg="{BASE}/login"), A("click", "role", "button", "Login"),
      A("expect_text", "css", "#error", arg="Username is required")]),
    ("R04", "negative", "Tài khoản bị khoá", ["Đăng nhập bob / secret123"], "Hiện lỗi 'Account is locked'",
     login_css(user="bob") + [A("expect_text", "css", "#error", arg="Account is locked")]),
    ("R05", "positive", "Đăng xuất", [LOGIN_STEP, "Bấm Logout"], "Về trang đăng nhập, hiện 'You have been logged out'",
     login_ph() + [A("click", "role", "link", "Logout"), A("expect_text", "css", "#flash", arg="You have been logged out")]),
    ("R06", "positive", "Thêm 1 sản phẩm", [LOGIN_STEP, "Thêm Sauce Backpack vào giỏ"], "Badge giỏ hàng hiện 1",
     login_ph() + [ADD("backpack"), A("expect_text", "test_id", "cart-count", arg="1")]),
    ("R07", "positive", "Thêm 2 sản phẩm", [LOGIN_STEP, "Thêm Sauce Backpack và Bike Light"], "Badge giỏ hàng hiện 2",
     login_label() + [ADD("backpack"), ADD("bike-light"), A("expect_text", "test_id", "cart-count", arg="2")]),
    ("R08", "positive", "Tổng tiền 2 món", [LOGIN_STEP, "Thêm Sauce Backpack và Bike Light", "Mở giỏ hàng"],
     "Tổng tiền là $39.98",
     login_ph() + [ADD("backpack"), ADD("bike-light"), TO_CART, A("expect_text", "css", ".cart-total", arg="Total: $39.98")]),
    ("R09", "positive", "Giỏ hàng có món đã thêm", [LOGIN_STEP, "Thêm Bolt T-Shirt", "Mở giỏ hàng"],
     "Giỏ hàng có 'Bolt T-Shirt'",
     login_ph() + [ADD("t-shirt"), TO_CART, A("expect_text", "css", ".cart-item", arg="Bolt T-Shirt")]),
    ("R10", "positive", "Giá sản phẩm đầu tiên", [LOGIN_STEP], "Sản phẩm đầu có giá $29.99",
     login_css() + [A("expect_text", "css", "div.card:first-of-type .price", arg="$29.99")]),
    ("R11", "positive", "Checkout thành công",
     [LOGIN_STEP, "Thêm Sauce Backpack", "Mở giỏ, bấm Checkout", "Nhập First name An, Last name Nguyen, Zip 70000",
      "Bấm Continue"], "Hiện 'Thank you for your order!'",
     login_ph() + [ADD("backpack"), TO_CART, TO_CHECKOUT, A("fill", "label", "First name", arg="An"),
                   A("fill", "label", "Last name", arg="Nguyen"), A("fill", "label", "Zip code", arg="70000"),
                   A("click", "role", "button", "Continue"),
                   A("expect_visible", "role", "heading", "Thank you for your order!")]),
    ("R12", "negative", "Checkout thiếu First name",
     [LOGIN_STEP, "Thêm Sauce Backpack", "Mở giỏ, bấm Checkout", "Bỏ trống First name, nhập Last name và Zip",
      "Bấm Continue"], "Hiện lỗi 'First name is required'",
     login_ph() + [ADD("backpack"), TO_CART, TO_CHECKOUT, A("fill", "label", "Last name", arg="Nguyen"),
                   A("fill", "label", "Zip code", arg="70000"), A("click", "role", "button", "Continue"),
                   A("expect_text", "css", "#error", arg="First name is required")]),
    ("R13", "positive", "Tổng tiền 3 món", [LOGIN_STEP, "Thêm cả 3 sản phẩm", "Mở giỏ hàng"], "Tổng tiền là $55.97",
     login_label() + [ADD("backpack"), ADD("bike-light"), ADD("t-shirt"), TO_CART,
                      A("expect_text", "css", ".cart-total", arg="Total: $55.97")]),
    ("R14", "positive", "Lưu hồ sơ", [LOGIN_STEP, "Mở Profile", "Đổi Display name thành 'Alice A'", "Bấm Save"],
     "Hiện 'Profile saved'",
     login_ph() + [A("click", "role", "link", "Profile"), A("fill", "label", "Display name", arg="Alice A"),
                   A("click", "role", "button", "Save"), A("expect_text", "css", "#message", arg="Profile saved")]),
    ("R15", "positive", "Chuyển hướng sau đăng nhập", [LOGIN_STEP], "URL là /products",
     login_css() + [A("expect_url", arg="{BASE}/products")]),
    ("R16", "positive", "Giỏ hàng trống", [LOGIN_STEP, "Mở giỏ hàng"], "Hiện 'Cart is empty'",
     login_ph() + [TO_CART, A("expect_visible", "text", "Cart is empty")]),
    ("R17", "positive", "Danh sách sản phẩm có nút thêm giỏ", [LOGIN_STEP], "Thấy nút thêm Sauce Backpack",
     login_ph() + [A("expect_visible", "test_id", "add-backpack")]),
    ("R18", "positive", "Giỏ có nút Checkout", [LOGIN_STEP, "Thêm Sauce Backpack", "Mở giỏ hàng"], "Thấy nút Checkout",
     login_ph() + [ADD("backpack"), TO_CART, A("expect_visible", "role", "button", "Checkout")]),
    ("R19", "negative", "Người dùng không tồn tại", ["Đăng nhập mallory / secret123"],
     "Hiện lỗi 'Invalid username or password'",
     login_ph(user="mallory") + [A("expect_text", "css", "#error", arg="Invalid username or password")]),
    ("R20", "positive", "Đăng xuất về trang có nút Login", [LOGIN_STEP, "Bấm Logout"], "Thấy nút Login",
     login_label() + [A("click", "role", "link", "Logout"), A("expect_visible", "role", "button", "Login")]),
]


def load_suite():
    """[(TestCase, PlaywrightPlan)] với URL còn chứa {BASE}."""
    out = []
    for tid, kind, title, steps, expected, actions in SUITE:
        tc = TestCase(id=tid, title=title, type=TestType(kind), steps=[TestStep(action=s) for s in steps],
                      expected_result=expected)
        out.append((tc, PlaywrightPlan(test_case_id=tid, actions=actions)))
    return out


def with_base(plan: PlaywrightPlan, base: str) -> PlaywrightPlan:
    acts = [a.model_copy(update={"arg": a.arg.replace("{BASE}", base)}) for a in plan.actions]
    return plan.model_copy(update={"actions": acts, "target_url": base})
