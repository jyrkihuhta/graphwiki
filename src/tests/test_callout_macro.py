"""Unit tests for the CalloutBlockPreprocessor feature.

Tests fenced code blocks with callout language tags (```info, ```warning, etc.)
are rendered as styled callout boxes with appropriate icons.

Depends on: TASK001 (CalloutBlockPreprocessor implementation)
"""

from pathlib import Path

import pytest

from meshwiki.core.parser import parse_wiki_content

# ============================================================
# Callout type mapping
# ============================================================

CALLOUT_TYPES = {
    "info": "ℹ️",
    "warning": "⚠️",
    "tip": "💡",
    "error": "❌",
    "note": "📝",
}


# ============================================================
# Individual callout type tests
# ============================================================


class TestCalloutInfo:
    """Tests for ```info callout blocks."""

    def test_info_callout_renders(self):
        """```info\n...``` renders as a callout with info styling."""
        html = parse_wiki_content("```info\nThis is an info message.\n```")
        assert 'class="callout callout--info"' in html
        assert "ℹ️" in html
        assert "This is an info message" in html


class TestCalloutWarning:
    """Tests for ```warning callout blocks."""

    def test_warning_callout_renders(self):
        """```warning\n...``` renders as a callout with warning styling."""
        html = parse_wiki_content("```warning\nWatch out!\n```")
        assert 'class="callout callout--warning"' in html
        assert "⚠️" in html
        assert "Watch out" in html


class TestCalloutTip:
    """Tests for ```tip callout blocks."""

    def test_tip_callout_renders(self):
        """```tip\n...``` renders as a callout with tip styling."""
        html = parse_wiki_content("```tip\nPro tip: use the force.\n```")
        assert 'class="callout callout--tip"' in html
        assert "💡" in html
        assert "Pro tip: use the force" in html


class TestCalloutError:
    """Tests for ```error callout blocks."""

    def test_error_callout_renders(self):
        """```error\n...``` renders as a callout with error styling."""
        html = parse_wiki_content("```error\nSomething went wrong.\n```")
        assert 'class="callout callout--error"' in html
        assert "❌" in html
        assert "Something went wrong" in html


class TestCalloutNote:
    """Tests for ```note callout blocks."""

    def test_note_callout_renders(self):
        """```note\n...``` renders as a callout with note styling."""
        html = parse_wiki_content("```note\nRemember this.\n```")
        assert 'class="callout callout--note"' in html
        assert "📝" in html
        assert "Remember this" in html


# ============================================================
# Regular code block tests
# ============================================================


class TestRegularCodeBlock:
    """Tests that regular fenced code blocks are not affected by callout rendering."""

    def test_python_code_block_not_affected(self):
        """```python\n...``` renders as a normal code block, not a callout."""
        html = parse_wiki_content('```python\nprint("hello")\n```')
        assert 'class="callout"' not in html
        assert "<code" in html or "print" in html

    def test_javascript_code_block_not_affected(self):
        """```javascript\n...``` renders as a normal code block."""
        html = parse_wiki_content("```javascript\nconst x = 1;\n```")
        assert 'class="callout"' not in html
        assert "<code" in html or "const x" in html

    def test_generic_fence_not_affected(self):
        """```text\n...``` renders as a normal code block."""
        html = parse_wiki_content("```text\nSome text content.\n```")
        assert 'class="callout"' not in html
        assert "Some text content" in html


# ============================================================
# Multiple callouts tests
# ============================================================


class TestMultipleCallouts:
    """Tests for pages with multiple callout blocks."""

    def test_multiple_different_callout_types(self):
        """Multiple callout blocks of different types appear in correct order."""
        content = "\n\n".join(
            [
                "```info\nFirst info.\n```",
                "```warning\nThen warning.\n```",
                "```tip\nFinally tip.\n```",
            ]
        )
        html = parse_wiki_content(content)

        info_pos = html.find("callout--info")
        warning_pos = html.find("callout--warning")
        tip_pos = html.find("callout--tip")

        assert info_pos != -1, "Info callout not found"
        assert warning_pos != -1, "Warning callout not found"
        assert tip_pos != -1, "Tip callout not found"
        assert info_pos < warning_pos < tip_pos, "Callouts not in correct order"

    def test_multiple_same_callout_type(self):
        """Multiple callout blocks of the same type both render."""
        content = "\n\n".join(
            [
                "```info\nFirst info message.\n```",
                "```info\nSecond info message.\n```",
            ]
        )
        html = parse_wiki_content(content)
        assert html.count("callout--info") == 2
        assert "First info message" in html
        assert "Second info message" in html


# ============================================================
# HTML escaping tests
# ============================================================


class TestCalloutHtmlEscaping:
    """Tests that HTML/script content inside callouts is properly escaped."""

    def test_script_tag_escaped(self):
        """<script>alert(1)</script> in callout body is HTML-escaped."""
        html = parse_wiki_content("```warning\n<script>alert(1)</script>\n```")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_html_tags_escaped(self):
        """Raw HTML tags in callout body are escaped."""
        html = parse_wiki_content("```error\n<div>hello</div>\n```")
        assert "<div>hello</div>" not in html
        assert "&lt;div&gt;hello&lt;/div&gt;" in html


# ============================================================
# Tilde fence style tests
# ============================================================


class TestTildeCalloutFence:
    """Tests for ~~~style callout blocks (tilde fence alternative)."""

    def test_tilde_warning_callout(self):
        """~~~warning\n...~~~ renders as a callout."""
        html = parse_wiki_content("~~~warning\nWatch out!\n~~~")
        assert 'class="callout callout--warning"' in html
        assert "⚠️" in html
        assert "Watch out" in html

    def test_tilde_info_callout(self):
        """~~~info\n...~~~ renders as a callout."""
        html = parse_wiki_content("~~~info\nInfo message.\n~~~")
        assert 'class="callout callout--info"' in html
        assert "ℹ️" in html

    def test_tilde_tip_callout(self):
        """~~~tip\n...~~~ renders as a callout."""
        html = parse_wiki_content("~~~tip\nPro tip.\n~~~")
        assert 'class="callout callout--tip"' in html
        assert "💡" in html


# ============================================================
# CSS presence tests
# ============================================================


class TestCalloutCssPresent:
    """Tests that CSS styles for callouts are present in style.css."""

    def test_dark_mode_support(self):
        """style.css contains [data-theme="dark"] for dark mode."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert '[data-theme="dark"]' in css_content

    def test_callout_info_bg_css_variable(self):
        """style.css contains --callout-info-bg custom property."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-info-bg" in css_content

    def test_callout_warning_bg_css_variable(self):
        """style.css contains --callout-warning-bg custom property."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-warning-bg" in css_content

    def test_callout_tip_bg_css_variable(self):
        """style.css contains --callout-tip-bg custom property."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-tip-bg" in css_content

    def test_callout_error_bg_css_variable(self):
        """style.css contains --callout-error-bg custom property."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-error-bg" in css_content

    def test_callout_note_bg_css_variable(self):
        """style.css contains --callout-note-bg custom property."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert "--callout-note-bg" in css_content

    def test_callout_info_css_class(self):
        """style.css contains .callout--info class."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert ".callout--info" in css_content

    def test_callout_warning_css_class(self):
        """style.css contains .callout--warning class."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert ".callout--warning" in css_content

    def test_callout_tip_css_class(self):
        """style.css contains .callout--tip class."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert ".callout--tip" in css_content

    def test_callout_error_css_class(self):
        """style.css contains .callout--error class."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert ".callout--error" in css_content

    def test_callout_note_css_class(self):
        """style.css contains .callout--note class."""
        css_path = (
            Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
        )
        css_content = css_path.read_text()
        assert ".callout--note" in css_content


# ============================================================
# Integration tests (HTTP route)
# ============================================================


class TestCalloutIntegration:
    """Integration tests for callout blocks via HTTP route."""

    @pytest.mark.asyncio
    async def test_warning_callout_via_http(self, client):
        """A wiki page with a warning callout renders the callout styling."""
        content = "```warning\nThis is a warning message.\n```"
        await client.post("/page/CalloutTestPage", data={"content": content})

        resp = await client.get("/page/CalloutTestPage")
        assert resp.status_code == 200
        assert "callout--warning" in resp.text

    @pytest.mark.asyncio
    async def test_multiple_callouts_via_http(self, client):
        """Multiple callout types render correctly via HTTP."""
        content = "\n\n".join(
            [
                "```info\nInfo message.\n```",
                "```error\nError message.\n```",
                "```tip\nTip message.\n```",
            ]
        )
        await client.post("/page/MultiCalloutPage", data={"content": content})

        resp = await client.get("/page/MultiCalloutPage")
        assert resp.status_code == 200
        assert "callout--info" in resp.text
        assert "callout--error" in resp.text
        assert "callout--tip" in resp.text

    @pytest.mark.asyncio
    async def test_callout_with_markdown_inside(self, client):
        """Callout body can contain markdown formatting."""
        content = "```note\n**Bold** and *italic* text.\n```"
        await client.post("/page/FormattedCallout", data={"content": content})

        resp = await client.get("/page/FormattedCallout")
        assert resp.status_code == 200
        assert "callout--note" in resp.text
        assert "<strong>Bold</strong>" in resp.text
        assert "<em>italic</em>" in resp.text
