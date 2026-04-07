"""Unit and integration tests for CalloutBlockPreprocessor."""

import pytest

from meshwiki.core.parser import parse_wiki_content


class TestCalloutBlockPreprocessor:
    """Test CalloutBlockPreprocessor with fenced code blocks."""

    @pytest.mark.parametrize(
        "callout_type,expected_class,expected_icon",
        [
            ("info", "callout--info", "ℹ️"),
            ("warning", "callout--warning", "⚠️"),
            ("tip", "callout--tip", "💡"),
            ("error", "callout--error", "❌"),
            ("note", "callout--note", "📝"),
        ],
    )
    def test_callout_renders_correct_class_and_icon(
        self, callout_type: str, expected_class: str, expected_icon: str
    ):
        content = f"```{callout_type}\nThis is a {callout_type} callout.\n```"
        html = parse_wiki_content(content)
        assert expected_class in html
        assert expected_icon in html
        assert "callout__icon" in html
        assert "callout__body" in html

    def test_callout_with_multiple_lines(self):
        content = """```info
Line one
Line two
Line three
```"""
        html = parse_wiki_content(content)
        assert "callout--info" in html
        assert "Line one" in html
        assert "Line two" in html
        assert "Line three" in html

    def test_regular_code_block_not_affected(self):
        content = "```python\nprint('hello')\n```"
        html = parse_wiki_content(content)
        assert "callout" not in html
        assert "print" in html

    def test_tilde_fence_callout(self):
        content = """~~~tip
This is a tip.
~~~"""
        html = parse_wiki_content(content)
        assert "callout--tip" in html
        assert "This is a tip." in html

    def test_multiple_callouts_on_same_page(self):
        content = """```info
First info callout
```
Some text in between.
```warning
Warning callout here
```
More text.
```tip
A tip callout
```"""
        html = parse_wiki_content(content)
        assert html.count("callout--info") == 1
        assert html.count("callout--warning") == 1
        assert html.count("callout--tip") == 1
        assert "First info callout" in html
        assert "Warning callout here" in html
        assert "A tip callout" in html

    def test_mixed_callouts_and_code_blocks(self):
        content = """```python
def hello():
    print("world")
```
```info
This is info
```
```tip
And a tip
```"""
        html = parse_wiki_content(content)
        assert "callout--info" in html
        assert "callout--tip" in html
        assert "def hello" in html

    def test_callout_content_is_html_escaped(self):
        content = """```error
<script>alert('xss')</script>
```"""
        html = parse_wiki_content(content)
        assert "callout--error" in html
        assert "&lt;script&gt;" in html
        assert "<script>" not in html

    def test_unclosed_callout_passes_through(self):
        content = """```info
This callout has no closing fence
just some text"""
        html = parse_wiki_content(content)
        assert "callout--info" not in html
        assert "This callout has no closing fence" in html

    def test_callout_type_not_case_sensitive(self):
        content = "```INFO\nShould not match\n```"
        html = parse_wiki_content(content)
        assert "callout--INFO" not in html
        assert "callout--info" not in html


class TestCalloutCSS:
    """Test that callout CSS is present in style.css."""

    def test_callout_css_variables_present(self):
        import meshwiki

        css_path = meshwiki.__file__.rsplit("/", 1)[0] + "/static/css/style.css"
        with open(css_path) as f:
            css_content = f.read()

        assert "--callout-info-bg" in css_content
        assert "--callout-warning-bg" in css_content
        assert "--callout-tip-bg" in css_content
        assert "--callout-error-bg" in css_content
        assert "--callout-note-bg" in css_content

    def test_dark_mode_callout_variables_present(self):
        import meshwiki

        css_path = meshwiki.__file__.rsplit("/", 1)[0] + "/static/css/style.css"
        with open(css_path) as f:
            css_content = f.read()

        assert '[data-theme="dark"] .callout--info' in css_content
        assert '[data-theme="dark"] .callout--warning' in css_content
        assert '[data-theme="dark"] .callout--tip' in css_content
        assert '[data-theme="dark"] .callout--error' in css_content
        assert '[data-theme="dark"] .callout--note' in css_content


class TestCalloutViaHTTP:
    """Integration tests for callouts via HTTP route."""

    @pytest.mark.asyncio
    async def test_callout_via_http_route(self, tmp_path):
        from httpx import ASGITransport, AsyncClient

        import meshwiki.main

        meshwiki.main.storage.base_path = tmp_path
        await meshwiki.main.storage.save_page(
            "CalloutTest", "```info\nThis is an info callout.\n```"
        )

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/page/CalloutTest")

        assert resp.status_code == 200
        assert "callout--info" in resp.text
        assert "ℹ️" in resp.text

    @pytest.mark.asyncio
    async def test_multiple_callouts_via_http(self, tmp_path):
        from httpx import ASGITransport, AsyncClient

        import meshwiki.main

        meshwiki.main.storage.base_path = tmp_path
        content = """```info
First info
```
```warning
A warning
```
```tip
And a tip
```"""
        await meshwiki.main.storage.save_page("MultiCalloutTest", content)

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/page/MultiCalloutTest")

        assert resp.status_code == 200
        assert "callout--info" in resp.text
        assert "callout--warning" in resp.text
        assert "callout--tip" in resp.text
        assert "ℹ️" in resp.text
        assert "⚠️" in resp.text
        assert "💡" in resp.text
