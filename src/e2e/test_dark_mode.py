"""E2E tests for dark mode toggle and persistence."""

from playwright.sync_api import Page, expect


class TestDarkMode:
    def test_toggle_switches_theme(self, page: Page, base_url: str):
        page.goto(base_url)
        page.evaluate("localStorage.removeItem('meshwiki-theme')")
        page.reload()
        page.locator("#theme-toggle").click()
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")

    def test_dark_mode_persists(self, page: Page, base_url: str):
        page.goto(base_url)
        page.evaluate("localStorage.setItem('meshwiki-theme', 'dark')")
        page.reload()
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")

    def test_toggle_back_to_light(self, page: Page, base_url: str):
        page.goto(base_url)
        page.evaluate("localStorage.setItem('meshwiki-theme', 'dark')")
        page.reload()
        page.locator("#theme-toggle").click()
        theme = page.evaluate("localStorage.getItem('meshwiki-theme')")
        assert theme == "light"

    def test_light_mode_default(self, page: Page, base_url: str):
        page.goto(base_url)
        page.evaluate("localStorage.removeItem('meshwiki-theme')")
        page.reload()
        # Should not have dark theme
        attr = page.locator("html").get_attribute("data-theme")
        assert attr is None or attr == "light"
