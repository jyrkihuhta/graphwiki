"""Unit and integration tests for CalloutBlockPreprocessor."""

import importlib
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from meshwiki.core.parser import create_parser


@pytest.fixture(scope="module")
def css_content() -> str:
    """Read style.css once for the entire test module."""
    css_path = Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
    return css_path.read_text()


@pytest.fixture()
def wiki_app(tmp_path):
    """Create a fresh app instance pointing at a temp directory."""
    import os

    import meshwiki.config
    import meshwiki.main

    os.environ["MESHWIKI_DATA_DIR"] = str(tmp_path)

    importlib.reload(meshwiki.config)
    importlib.reload(meshwiki.main)

    yield meshwiki.main.app

    os.environ.pop("MESHWIKI_DATA_DIR", None)


@pytest_asyncio.fixture()
async def client(wiki_app):
    """Async HTTP client wired to the app."""
    transport = ASGITransport(app=wiki_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True,
    ) as c:
        yield c


def test_info_callout_renders() -> None:
    """```info\\n...``` renders as a callout with info styling."""
    html = create_parser().convert("```info\nThis is an info message.\n```")
    assert 'class="callout callout--info"' in html
    assert "ℹ️" in html
    assert "This is an info message" in html


def test_warning_callout_renders() -> None:
    """```warning\\n...``` renders as a callout with warning styling."""
    html = create_parser().convert("```warning\nThis is a warning message.\n```")
    assert 'class="callout callout--warning"' in html
    assert "⚠️" in html
    assert "This is a warning message" in html


def test_tip_callout_renders() -> None:
    """```tip\\n...``` renders as a callout with tip styling."""
    html = create_parser().convert("```tip\nThis is a tip message.\n```")
    assert 'class="callout callout--tip"' in html
    assert "💡" in html
    assert "This is a tip message" in html


def test_error_callout_renders() -> None:
    """```error\\n...``` renders as a callout with error styling."""
    html = create_parser().convert("```error\nThis is an error message.\n```")
    assert 'class="callout callout--error"' in html
    assert "❌" in html
    assert "This is an error message" in html


def test_note_callout_renders() -> None:
    """```note\\n...``` renders as a callout with note styling."""
    html = create_parser().convert("```note\nThis is a note message.\n```")
    assert 'class="callout callout--note"' in html
    assert "📝" in html
    assert "This is a note message" in html


def test_python_code_block_not_affected() -> None:
    """Regular ```python\\n...``` code blocks are not treated as callouts."""
    html = create_parser().convert('```python\nprint("hello")\n```')
    assert 'class="callout"' not in html
    assert "<code" in html


def test_multiple_callouts_on_same_page() -> None:
    """Multiple callout blocks of different types render in order."""
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
```
"""
    html = create_parser().convert(content)
    assert html.count("callout--info") == 1
    assert html.count("callout--warning") == 1
    assert html.count("callout--tip") == 1
    assert "First info callout" in html
    assert "Warning callout here" in html
    assert "A tip callout" in html
    assert html.index("callout--info") < html.index("callout--warning")
    assert html.index("callout--warning") < html.index("callout--tip")


def test_callout_body_html_escaped() -> None:
    """Callout body content is HTML-escaped to prevent XSS."""
    html = create_parser().convert(
        "```error\n<script>alert(1)</script>\n```"
    )
    assert "&lt;script&gt;" in html
    assert "<script>" not in html


def test_tilde_fence_callout() -> None:
    """Callout blocks also work with ~~~ fence style."""
    html = create_parser().convert("~~~warning\nWatch out!\n~~~")
    assert 'class="callout callout--warning"' in html
    assert "Watch out!" in html


def test_callout_with_multiple_lines() -> None:
    """Callout body can span multiple lines."""
    content = """```info
Line one
Line two
Line three
```"""
    html = create_parser().convert(content)
    assert "callout--info" in html
    assert "Line one" in html
    assert "Line two" in html
    assert "Line three" in html


def test_mixed_callouts_and_code_blocks() -> None:
    """Code blocks and callouts can coexist on the same page."""
    content = """```python
def hello():
    print("world")
```
```info
This is info
```
```tip
And a tip
```
"""
    html = create_parser().convert(content)
    assert "callout--info" in html
    assert "callout--tip" in html
    assert "def hello" in html


def test_unclosed_fence_passes_through() -> None:
    """Unclosed fence does not render as a callout."""
    content = """```info
This callout has no closing fence
just some text"""
    html = create_parser().convert(content)
    assert "callout--info" not in html
    assert "This callout has no closing fence" in html


def test_unknown_callout_type_not_special() -> None:
    """Fenced block with unknown type is not treated as a callout."""
    content = "```UNKNOWN\nSome text\n```"
    html = create_parser().convert(content)
    assert "callout" not in html


def test_dark_mode_support(css_content: str) -> None:
    """CSS contains dark mode support for callouts."""
    assert '[data-theme="dark"]' in css_content


def test_callout_css_variables_present(css_content: str) -> None:
    """CSS contains callout background variables for all types."""
    assert "--callout-info-bg" in css_content
    assert "--callout-warning-bg" in css_content
    assert "--callout-tip-bg" in css_content
    assert "--callout-error-bg" in css_content
    assert "--callout-note-bg" in css_content


def test_callout_css_classes_present(css_content: str) -> None:
    """CSS contains callout class styles for all types."""
    assert ".callout--info" in css_content
    assert ".callout--warning" in css_content
    assert ".callout--tip" in css_content
    assert ".callout--error" in css_content
    assert ".callout--note" in css_content


def test_dark_mode_callout_classes_present(css_content: str) -> None:
    """CSS contains dark mode variants for all callout types."""
    assert '[data-theme="dark"] .callout--info' in css_content
    assert '[data-theme="dark"] .callout--warning' in css_content
    assert '[data-theme="dark"] .callout--tip' in css_content
    assert '[data-theme="dark"] .callout--error' in css_content
    assert '[data-theme="dark"] .callout--note' in css_content


@pytest.mark.asyncio
async def test_warning_callout_via_http(client) -> None:
    """A wiki page with a warning callout renders the callout styling."""
    content = "```warning\nThis is a warning message.\n```"
    resp = await client.post("/page/CalloutTestPage", data={"content": content})
    assert resp.status_code == 200

    resp = await client.get("/page/CalloutTestPage")
    assert resp.status_code == 200
    assert "callout--warning" in resp.text
    assert "⚠️" in resp.text


@pytest.mark.asyncio
async def test_multiple_callouts_via_http(client) -> None:
    """Multiple callout types render correctly via HTTP."""
    content = """```info
First info
```
```warning
A warning
```
```tip
And a tip
```
"""
    resp = await client.post("/page/MultiCalloutTest", data={"content": content})
    assert resp.status_code == 200

    resp = await client.get("/page/MultiCalloutTest")
    assert resp.status_code == 200
    assert "callout--info" in resp.text
    assert "callout--warning" in resp.text
    assert "callout--tip" in resp.text
    assert "ℹ️" in resp.text
    assert "⚠️" in resp.text
    assert "💡" in resp.text
