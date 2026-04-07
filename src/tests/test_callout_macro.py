"""Unit and integration tests for CalloutBlockPreprocessor."""

import asyncio
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from meshwiki.core.parser import create_parser


@pytest.fixture(scope="module")
def css_content() -> str:
    """Read style.css once for the entire test module."""
    css_path = (
        Path(__file__).parent.parent / "meshwiki" / "static" / "css" / "style.css"
    )
    return css_path.read_text()


# ============================================================
# Unit tests for callout rendering
# ============================================================


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
    html = create_parser().convert("```tip\nThis is a tip.\n```")
    assert 'class="callout callout--tip"' in html
    assert "💡" in html
    assert "This is a tip" in html


def test_error_callout_renders() -> None:
    """```error\\n...``` renders as a callout with error styling."""
    html = create_parser().convert("```error\nThis is an error.\n```")
    assert 'class="callout callout--error"' in html
    assert "❌" in html
    assert "This is an error" in html


def test_note_callout_renders() -> None:
    """```note\\n...``` renders as a callout with note styling."""
    html = create_parser().convert("```note\nThis is a note.\n```")
    assert 'class="callout callout--note"' in html
    assert "📝" in html
    assert "This is a note" in html


def test_python_code_block_not_affected() -> None:
    """Regular ```python\\n...``` code blocks are NOT treated as callouts."""
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
```"""
    html = create_parser().convert(content)
    assert html.count("callout--info") == 1
    assert html.count("callout--warning") == 1
    assert html.count("callout--tip") == 1
    assert "First info callout" in html
    assert "Warning callout here" in html
    assert "A tip callout" in html
    info_pos = html.find("callout--info")
    warning_pos = html.find("callout--warning")
    tip_pos = html.find("callout--tip")
    assert info_pos < warning_pos < tip_pos, "Callouts should appear in source order"


def test_callout_content_is_html_escaped() -> None:
    """Callout body content is HTML-escaped to prevent XSS."""
    html = create_parser().convert("```warning\n<script>alert(1)</script>\n```")
    assert "callout--warning" in html
    assert "&lt;script&gt;" in html
    assert "<script>" not in html


def test_tilde_fence_style() -> None:
    """Callout blocks also work with ~~~ fence style."""
    html = create_parser().convert("~~~warning\nWatch out!\n~~~")
    assert 'class="callout callout--warning"' in html
    assert "⚠️" in html
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
    """Regular code blocks and callouts can coexist on the same page."""
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
    html = create_parser().convert(content)
    assert "callout--info" in html
    assert "callout--tip" in html
    assert "def hello" in html


def test_unclosed_callout_passes_through() -> None:
    """Unclosed callout blocks are not rendered as callouts."""
    content = """```info
This callout has no closing fence
just some text"""
    html = create_parser().convert(content)
    assert "callout--info" not in html
    assert "This callout has no closing fence" in html


def test_callout_type_not_case_sensitive() -> None:
    """Callout type must be lowercase to be recognized."""
    html = create_parser().convert("```INFO\nShould not match\n```")
    assert "callout--INFO" not in html
    assert "callout--info" not in html


# ============================================================
# Integration tests via HTTP
# ============================================================


def test_warning_callout_via_http(tmp_path) -> None:
    """A wiki page with a warning callout renders the callout styling via HTTP."""
    import os

    import meshwiki.config
    import meshwiki.main

    importlib = __import__("importlib")

    os.environ["MESHWIKI_DATA_DIR"] = str(tmp_path)
    importlib.reload(meshwiki.config)
    importlib.reload(meshwiki.main)

    asyncio.run(
        meshwiki.main.storage.save_page(
            "CalloutTestPage", "```warning\nThis is a warning message.\n```"
        )
    )

    with TestClient(meshwiki.main.app) as client:
        resp = client.get("/page/CalloutTestPage")
        assert resp.status_code == 200
        assert "callout--warning" in resp.text
        assert "⚠️" in resp.text

    os.environ.pop("MESHWIKI_DATA_DIR", None)


def test_info_callout_via_http(tmp_path) -> None:
    """A wiki page with an info callout renders correctly via HTTP."""
    import os

    import meshwiki.config
    import meshwiki.main

    importlib = __import__("importlib")

    os.environ["MESHWIKI_DATA_DIR"] = str(tmp_path)
    importlib.reload(meshwiki.config)
    importlib.reload(meshwiki.main)

    asyncio.run(
        meshwiki.main.storage.save_page(
            "InfoCalloutPage", "```info\nThis is an info message.\n```"
        )
    )

    with TestClient(meshwiki.main.app) as client:
        resp = client.get("/page/InfoCalloutPage")
        assert resp.status_code == 200
        assert "callout--info" in resp.text
        assert "ℹ️" in resp.text

    os.environ.pop("MESHWIKI_DATA_DIR", None)


def test_multiple_callouts_via_http(tmp_path) -> None:
    """Multiple callouts on one page render correctly via HTTP."""
    import os

    import meshwiki.config
    import meshwiki.main

    importlib = __import__("importlib")

    os.environ["MESHWIKI_DATA_DIR"] = str(tmp_path)
    importlib.reload(meshwiki.config)
    importlib.reload(meshwiki.main)

    content = """```info
First info
```
```warning
A warning
```
```tip
And a tip
```"""
    asyncio.run(meshwiki.main.storage.save_page("MultiCalloutPage", content))

    with TestClient(meshwiki.main.app) as client:
        resp = client.get("/page/MultiCalloutPage")
        assert resp.status_code == 200
        assert "callout--info" in resp.text
        assert "callout--warning" in resp.text
        assert "callout--tip" in resp.text
        assert "ℹ️" in resp.text
        assert "⚠️" in resp.text
        assert "💡" in resp.text

    os.environ.pop("MESHWIKI_DATA_DIR", None)


# ============================================================
# CSS presence tests
# ============================================================


def test_dark_mode_support(css_content: str) -> None:
    """CSS contains dark mode support for callouts."""
    assert '[data-theme="dark"]' in css_content


def test_callout_css_variables_present(css_content: str) -> None:
    """CSS contains callout background color variables."""
    assert "--callout-info-bg" in css_content
    assert "--callout-warning-bg" in css_content
    assert "--callout-tip-bg" in css_content
    assert "--callout-error-bg" in css_content
    assert "--callout-note-bg" in css_content


def test_callout_dark_mode_variables(css_content: str) -> None:
    """CSS contains dark mode callout color overrides."""
    assert '[data-theme="dark"] .callout--info' in css_content
    assert '[data-theme="dark"] .callout--warning' in css_content
    assert '[data-theme="dark"] .callout--tip' in css_content
    assert '[data-theme="dark"] .callout--error' in css_content
    assert '[data-theme="dark"] .callout--note' in css_content


def test_callout_info_class(css_content: str) -> None:
    """CSS contains .callout--info class."""
    assert ".callout--info" in css_content


def test_callout_warning_class(css_content: str) -> None:
    """CSS contains .callout--warning class."""
    assert ".callout--warning" in css_content


def test_callout_tip_class(css_content: str) -> None:
    """CSS contains .callout--tip class."""
    assert ".callout--tip" in css_content


def test_callout_error_class(css_content: str) -> None:
    """CSS contains .callout--error class."""
    assert ".callout--error" in css_content


def test_callout_note_class(css_content: str) -> None:
    """CSS contains .callout--note class."""
    assert ".callout--note" in css_content
