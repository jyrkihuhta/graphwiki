"""E2E tests for responsive design and mobile viewport."""

from playwright.sync_api import Page, expect


class TestMobileNav:
    def test_hamburger_visible_on_mobile(self, page: Page, base_url: str):
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(base_url)
        expect(page.locator(".nav-toggle")).to_be_visible()

    def test_hamburger_opens_nav(self, page: Page, base_url: str):
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(base_url)
        page.locator(".nav-toggle").click()
        expect(page.locator(".nav--open, nav.open")).to_be_visible()

    def test_hamburger_hidden_on_desktop(self, page: Page, base_url: str):
        page.set_viewport_size({"width": 1280, "height": 800})
        page.goto(base_url)
        expect(page.locator(".nav-toggle")).not_to_be_visible()


class TestMobileEditor:
    def test_editor_accessible_on_mobile(self, page: Page, base_url: str):
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{base_url}/page/MobileEdit/edit")
        expect(page.locator("#content")).to_be_visible()
        expect(page.locator("#editor-toolbar")).to_be_visible()
