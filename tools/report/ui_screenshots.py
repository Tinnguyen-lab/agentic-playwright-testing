"""Đi hết luồng UI (mock backend) + chụp ảnh cho báo cáo."""
import json
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).parent / "ui_shots"
OUT.mkdir(exist_ok=True)
APP = "http://localhost:8599"
BASE = "http://127.0.0.1:5200/login"
BROKEN = {"actions": [{"type": "goto", "arg": BASE},
                      {"type": "fill", "strategy": "placeholder", "value": "Usernamex", "arg": "alice"},
                      {"type": "expect_visible", "strategy": "role", "value": "heading", "role_name": "ShopLab"}]}


def key(page, k):
    return page.locator(f".st-key-{k} button")


def wait_idle(page):
    page.wait_for_timeout(800)
    expect(page.locator("[data-testid='stStatusWidget']")).to_have_count(0, timeout=120_000)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1400, "height": 1000})
    page.goto(APP)
    expect(page.get_by_text("Agentic Playwright").first).to_be_visible(timeout=60_000)
    url = page.get_by_label("URL ứng dụng đích")
    url.fill(BASE)
    url.press("Enter")
    wait_idle(page)
    page.get_by_role("button", name="① Phân tích yêu cầu").click()
    wait_idle(page)
    expect(page.get_by_text("① Yêu cầu")).to_be_visible()
    page.screenshot(path=str(OUT / "1_requirements.png"), full_page=True)
    req_ids = [c.split("st-key-ap_")[1].split()[0] for c in
               page.locator("[class*='st-key-ap_']").evaluate_all("els => els.map(e => e.className)")]
    print("requirements:", req_ids)
    key(page, f"ap_{req_ids[0]}").click()
    wait_idle(page)
    page.get_by_role("button", name="Thiết kế test cho các yêu cầu đã duyệt").click()
    wait_idle(page)
    tc_ids = [c.split("st-key-aptc_")[1].split()[0] for c in
              page.locator("[class*='st-key-aptc_']").evaluate_all("els => els.map(e => e.className)")]
    print("test cases:", tc_ids)
    tc = tc_ids[0]
    key(page, f"aptc_{tc}").click()
    wait_idle(page)
    page.screenshot(path=str(OUT / "2_test_cases.png"), full_page=True)
    key(page, f"g_{tc}").click()
    wait_idle(page)
    key(page, f"x_{tc}").click()
    wait_idle(page)
    expect(page.get_by_text("passed").first).to_be_visible()
    print("run 1: passed")
    # cố ý làm hỏng plan rồi chạy lại -> đề xuất sửa
    page.get_by_text("Plan, grounding và mã").first.click()
    area = page.get_by_label("Plan (JSON, sửa được)").first
    area.fill(json.dumps(BROKEN))
    area.press("Control+Enter")
    wait_idle(page)
    key(page, f"sp_{tc}").click()
    wait_idle(page)
    key(page, f"x_{tc}").click()
    wait_idle(page)
    expect(page.get_by_text("failed").first).to_be_visible()
    print("run 2 (plan hỏng): failed")
    page.get_by_role("button", name=f"Đề xuất sửa cho {tc}").click()
    wait_idle(page)
    expect(page.get_by_text("Đề xuất #").first).to_be_visible()
    page.get_by_text("Đề xuất #").first.scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / "3_repair.png"), full_page=True)
    print("proposal:", page.get_by_text("Đề xuất #").first.inner_text())
    page.get_by_role("button", name="Duyệt và chạy lại").first.click()
    wait_idle(page)
    expect(page.get_by_text("passed").first).to_be_visible()
    print("run 3 (sau sửa): passed")
    page.get_by_role("tab", name="Lịch sử & truy vết").click()
    wait_idle(page)
    page.screenshot(path=str(OUT / "4_history.png"), full_page=True)
    print("history metrics:", page.locator("[data-testid='stMetricValue']").all_inner_texts())
    b.close()
