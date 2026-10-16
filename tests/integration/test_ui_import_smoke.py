"""Opt-in browser regression for stale Streamlit module imports."""
import os

import pytest
from playwright.sync_api import sync_playwright


@pytest.mark.skipif(os.getenv("RUN_UI_SMOKE") != "1", reason="Requires local Streamlit on port 8501")
def test_streamlit_home_loads_without_import_error():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://127.0.0.1:8501", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=15000)
            page.get_by_text("Agentic Playwright", exact=False).first.wait_for(timeout=15000)
            assert page.get_by_text("ImportError", exact=False).count() == 0
        finally:
            browser.close()
