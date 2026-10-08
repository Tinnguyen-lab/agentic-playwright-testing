"""Test multi-step grounding (offline, FakePage có trạng thái điều hướng).

Chứng minh: phần tử chỉ xuất hiện SAU khi login được ground đúng nhờ đi theo luồng,
trong khi grounding trên một ảnh chụp tĩnh (ground_actions) báo sai là không khớp.
"""
from src.agents.playwright_generation_agent import ground_actions, ground_flow, live_count_fn
from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction


class FakeLocator:
    def __init__(self, page, key):
        self.page = page
        self.key = key

    @property
    def first(self):
        return self

    def wait_for(self, state=None, timeout=None):
        pass

    def count(self):
        return 1 if self.key in self.page.here else 0

    def fill(self, value):
        pass

    def click(self):
        if self.key == ("role", "button", "Login"):
            self.page.here = set(self.page.inventory)


class FakePage:
    """Login page -> click Login -> Inventory page (phần tử khác nhau ở mỗi trang)."""

    def __init__(self):
        self.login = {("placeholder", "Username"), ("placeholder", "Password"), ("role", "button", "Login")}
        self.inventory = {("css", ".inventory_list")}
        self.here = set()

    def goto(self, url):
        self.here = set(self.login)

    def get_by_placeholder(self, v):
        return FakeLocator(self, ("placeholder", v))

    def get_by_role(self, role, name=""):
        return FakeLocator(self, ("role", role, name))

    def get_by_label(self, v):
        return FakeLocator(self, ("label", v))

    def get_by_text(self, v):
        return FakeLocator(self, ("text", v))

    def get_by_test_id(self, v):
        return FakeLocator(self, ("test_id", v))

    def locator(self, v):
        return FakeLocator(self, ("css", v))


def _flow():
    return [
        PlaywrightAction(type=ActionType.GOTO, arg="https://x/"),
        PlaywrightAction(type=ActionType.FILL, strategy=LocatorStrategy.PLACEHOLDER, value="Username", arg="u"),
        PlaywrightAction(type=ActionType.CLICK, strategy=LocatorStrategy.ROLE, value="button", role_name="Login"),
        PlaywrightAction(type=ActionType.EXPECT_VISIBLE, strategy=LocatorStrategy.CSS, value=".inventory_list"),
    ]


def test_flow_grounds_post_login_element():
    recs = {r.action_index: r for r in ground_flow(FakePage(), _flow())}
    assert recs[1].ok is True   # Username có trên trang login
    assert recs[2].ok is True   # nút Login có trên trang login
    assert recs[3].ok is True   # .inventory_list CHỈ có sau khi click Login -> multi-step bắt đúng


def test_static_grounding_misses_post_login_element():
    page = FakePage()
    page.goto("x")  # dừng ở trang login, không đi tiếp
    recs = ground_actions(_flow(), live_count_fn(page))
    inv = [r for r in recs if r.value == ".inventory_list"][0]
    assert inv.ok is False  # ảnh chụp tĩnh không thấy phần tử sau-login
