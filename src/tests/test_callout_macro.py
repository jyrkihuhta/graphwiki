"""Unit and integration tests for the CalloutBlockPreprocessor feature.

This module tests the rendering of fenced code blocks with callout-type
language tags (```info, ```warning, etc.) as styled callout boxes.

Depends on: TASK001 (CalloutBlockPreprocessor implementation).
"""

from pathlib import Path

import pytest

from meshwiki.core.parser import parse_wiki_content

# Icon emoji for each callout type
CALLOUT_ICONS: dict[str, str] = {
    "info": "ℹ️",
    "warning": "⚠️",
    "tip": "💡",
    "error": "❌",
    "note": "📝",
}

CALLOUT_TYPES = list(CALLOUT_ICONS.keys())


# ============================================================
# Helper
# ============================================================


def render(text: str) -> str:
    """Render text through the wiki parser."""
    return parse_wiki_content(text)


# ============================================================
# Unit tests — each callout type
# ============================================================


class TestCalloutBlockTypes:
    """Test that each callout type renders with correct class and icon."""

    @pytest.mark.parametrize("callout_type", CALLOUT_TYPES)
    def test_callout_class_present(self, callout_type: str):
        """Fenced block with type language tag produces callout--{type} class."""
        content = f"```{callout_type}\nWatch out!\n```"
        html = render(content)
        assert (
            f"callout--{callout_type}" in html
        ), f"Expected callout--{callout_type} in output for type '{callout_type}'"

    @pytest.mark.parametrize("callout_type", CALLOUT_TYPES)
    def test_callout_icon_present(self, callout_type: str):
        """Each callout type renders with its correct emoji icon."""
        content = f"```{callout_type}\nBody text here.\n```"
        html = render(content)
        icon = CALLOUT_ICONS[callout_type]
        assert icon in html, f"Expected emoji {icon} for type '{callout_type}'"

    @pytest.mark.parametrize("callout_type", CALLOUT_TYPES)
    def test_callout_body_text_present(self, callout_type: str):
        """Callout body text appears inside the rendered output."""
        body = "This is the warning message."
        content = f"```{callout_type}\n{body}\n```"
        html = render(content)
        assert body in html

    @pytest.mark.parametrize("callout_type", CALLOUT_TYPES)
    def test_callout_wrapper_class_present(self, callout_type: str):
        """Output contains the outer callout CSS class."""
        content = f"```{callout_type}\nSome content.\n```"
        html = render(content)
        assert 'class="callout ' in html or 'class="callout"' in html


# ============================================================
# Regular code block not affected
# ============================================================


class TestRegularCodeBlock:
    """Regular fenced code blocks (non-callout) must not become callouts."""

    def test_python_code_block_not_callout(self):
        """```python ...``` is rendered as a normal code block, not a callout."""
        content = '```python\nprint("hello")\n```'
        html = render(content)
        assert "callout" not in html
        assert "<code" in html or "<pre" in html

    def test_javascript_code_block_not_callout(self):
        """```javascript ...``` is rendered as a normal code block."""
        content = "```javascript\nconst x = 1;\n```"
        html = render(content)
        assert "callout" not in html

    def test_plain_fenced_block_not_callout(self):
        """Unlabelled ```...``` is rendered as a normal code block."""
        content = "```\nsome plain text\n```"
        html = render(content)
        assert "callout" not in html


# ============================================================
# Multiple callouts on one page
# ============================================================


class TestMultipleCallouts:
    """Two or more callout blocks of different types on one page."""

    def test_multiple_callout_types_order(self):
        """Info and warning callouts both render, in correct order."""
        content = "```info\nInfo message.\n```\n\n```warning\nWarning message.\n```"
        html = render(content)
        assert "callout--info" in html
        assert "callout--warning" in html
        assert html.index("callout--info") < html.index("callout--warning")

    def test_all_five_types_on_one_page(self):
        """All five callout types can coexist on one page."""
        parts = [f"```{t}\n{t.capitalize()} body.\n```" for t in CALLOUT_TYPES]
        content = "\n\n".join(parts)
        html = render(content)
        for callout_type in CALLOUT_TYPES:
            assert f"callout--{callout_type}" in html, f"Missing {callout_type}"
        for icon in CALLOUT_ICONS.values():
            assert icon in html, f"Missing icon {icon}"


# ============================================================
# HTML-escaping of callout body
# ============================================================


class TestCalloutHtmlEscaping:
    """Callout body content must be HTML-escaped to prevent XSS."""

    @pytest.mark.parametrize("callout_type", CALLOUT_TYPES)
    def test_script_tag_escaped(self, callout_type: str):
        """<script>alert(1)</script> in callout body is escaped."""
        content = f"```{callout_type}\n<script>alert(1)</script>\n```"
        html = render(content)
        assert "&lt;script&gt;" in html or "&lt;script " in html
        assert "<script>alert(1)</script>" not in html

    def test_html_tags_escaped_in_warning(self):
        """HTML tags are escaped inside a warning callout."""
        content = "```warning\n<b>bold</b> and <em>italic</em>\n```"
        html = render(content)
        assert "&lt;b&gt;" in html
        assert "&lt;em&gt;" in html
        assert "<b>bold</b>" not in html


# ============================================================
# Tilde fence style
# ============================================================


class TestTildeFenceStyle:
    """Callout blocks using ~~~ fence style are also rendered."""

    @pytest.mark.parametrize("callout_type", CALLOUT_TYPES)
    def test_tilde_fence_renders_callout(self, callout_type: str):
        """~~~{type} ... ~~~ produces a callout block."""
        content = f"~~~\n{callout_type}\nWatch out!\n~~~"
        html = render(content)
        assert f"callout--{callout_type}" in html

    def test_tilde_fence_warning_callout(self):
        """~~~warning with body renders correct icon and class."""
        content = "~~~warning\nBe careful here.\n~~~"
        html = render(content)
        assert "callout--warning" in html
        assert "⚠️" in html


# ============================================================
# CSS presence test
# ============================================================


class TestCalloutCssPresence:
    """Verify callout CSS is present in style.css."""

    def test_dark_mode_support_present(self):
        """style.css contains [data-theme="dark"] for dark mode."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert '[data-theme="dark"]' in css_content

    @pytest.mark.parametrize("callout_type", CALLOUT_TYPES)
    def test_callout_css_variable_defined(self, callout_type: str):
        """style.css defines --callout-{type}-bg for each type."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert (
            f"--callout-{callout_type}-bg" in css_content
        ), f"Missing --callout-{callout_type}-bg in style.css"

    @pytest.mark.parametrize("callout_type", CALLOUT_TYPES)
    def test_callout_css_class_defined(self, callout_type: str):
        """style.css defines .callout--{type} class for each type."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert (
            f".callout--{callout_type}" in css_content
        ), f"Missing .callout--{callout_type} in style.css"

    def test_callout_info_bg_defined(self):
        """--callout-info-bg custom property is present."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-info-bg" in css_content

    def test_callout_warning_bg_defined(self):
        """--callout-warning-bg custom property is present."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-warning-bg" in css_content

    def test_callout_tip_bg_defined(self):
        """--callout-tip-bg custom property is present."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-tip-bg" in css_content

    def test_callout_error_bg_defined(self):
        """--callout-error-bg custom property is present."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-error-bg" in css_content

    def test_callout_note_bg_defined(self):
        """--callout-note-bg custom property is present."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-note-bg" in css_content


# ============================================================
# Integration test — HTTP route
# ============================================================


class TestCalloutViaHttpRoute:
    """Render a page with a warning callout block via the FastAPI route."""

    @pytest.mark.asyncio
    async def test_warning_callout_via_page_route(self, tmp_path):
        """A wiki page with a warning callout renders callout--warning in HTML."""
        import meshwiki.main

        meshwiki.main.storage.base_path = tmp_path
        content = """\
---
title: Callout Test Page
---

```warning
This is a warning message.
```
"""
        await meshwiki.main.storage.save_page("CalloutTest", content)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/page/CalloutTest")

        assert resp.status_code == 200
        assert "callout--warning" in resp.text
        assert "⚠️" in resp.text
