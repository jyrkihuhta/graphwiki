"""Unit tests for the <<PageList>> macro."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from meshwiki.core.models import Page, PageMetadata
from meshwiki.core.parser import create_parser


def make_page(
    name: str,
    title: str | None = None,
    status: str | None = None,
    tags: list[str] | None = None,
    created_minutes_ago: int = 60,
    modified_minutes_ago: int = 60,
) -> Page:
    """Create a mock page matching the shape returned by the graph engine.

    Args:
        name: Page name.
        title: Optional title (falls back to name-derived title).
        status: Optional status string stored in page metadata via model_construct.
        tags: Optional list of tag strings.
        created_minutes_ago: Age of created timestamp.
        modified_minutes_ago: Age of modified timestamp.

    Returns:
        Page object with metadata.
    """
    created = datetime.now() - timedelta(minutes=created_minutes_ago)
    modified = datetime.now() - timedelta(minutes=modified_minutes_ago)
    metadata_kwargs = {
        "title": title,
        "tags": tags or [],
        "created": created,
        "modified": modified,
    }
    if status is not None:
        metadata = PageMetadata.model_construct(**metadata_kwargs, status=status)
    else:
        metadata = PageMetadata(**metadata_kwargs)
    return Page(
        name=name,
        content="# " + name,
        metadata=metadata,
        exists=True,
    )


def render(text: str, pages: list[Page] | None = None) -> str:
    """Render text through the parser with a mocked graph engine.

    Patches get_engine() to return a mock whose query() returns the
    supplied pages list, then calls create_parser() and converts the text.

    Args:
        text: Markdown text to render.
        pages: List of Page objects to return from mock engine query.

    Returns:
        Rendered HTML string.
    """
    mock_engine = MagicMock()
    mock_engine.query.return_value = pages or []
    with patch("meshwiki.core.graph.get_engine", return_value=mock_engine):
        md = create_parser(all_pages=pages or [])
        return md.convert(text)


class TestPageListBasic:
    """Basic rendering tests."""

    def test_pagelist_all_pages(self) -> None:
        """<<PageList()>> with 3 pages → all 3 appear in output."""
        pages = [
            make_page("PageA"),
            make_page("PageB"),
            make_page("PageC"),
        ]
        html = render("<<PageList()>>", pages=pages)
        assert "PageA" in html
        assert "PageB" in html
        assert "PageC" in html

    def test_pagelist_ul_structure(self) -> None:
        """Verify <ul class=\"page-list\"> wraps the list items."""
        pages = [make_page("TestPage")]
        html = render("<<PageList>>", pages=pages)
        assert '<ul class="page-list">' in html

    def test_pagelist_anchor_links(self) -> None:
        """Each <li> contains <a href=\"/page/{name}\"> with correct href."""
        pages = [make_page("MyTestPage")]
        html = render("<<PageList>>", pages=pages)
        assert 'href="/page/MyTestPage"' in html

    def test_pagelist_title_fallback(self) -> None:
        """Page with no title → page name used as link text."""
        pages = [make_page("NoTitlePage")]
        html = render("<<PageList>>", pages=pages)
        assert ">NoTitlePage</a>" in html

    def test_pagelist_empty_call(self) -> None:
        """<<PageList()>> with zero pages in engine → No pages found. message."""
        html = render("<<PageList()>>", pages=[])
        assert "No pages found" in html
        assert "<ul" not in html


class TestPageListFiltering:
    """Tests for tag, parent/prefix, and limit filtering."""

    def test_pagelist_filter_tag(self) -> None:
        """<<PageList(tag=\"factory\")>> → only pages tagged factory appear."""
        pages = [
            make_page("Factory/Task1", tags=["factory"]),
            make_page("OtherPage", tags=["other"]),
            make_page("Factory/Task2", tags=["factory", "docs"]),
        ]
        html = render("<<PageList(tag=factory)>>", pages=pages)
        assert "Factory/Task1" in html
        assert "Factory/Task2" in html
        assert "OtherPage" not in html

    @pytest.mark.xfail(reason="PageList does not yet implement status filtering")
    def test_pagelist_filter_status(self) -> None:
        """<<PageList(status=\"planned\")>> → only planned pages appear."""
        pages = [
            make_page("PlannedPage", status="planned"),
            make_page("InProgressPage", status="in_progress"),
            make_page("DonePage", status="done"),
        ]
        html = render("<<PageList(status=planned)>>", pages=pages)
        assert "PlannedPage" in html
        assert "InProgressPage" not in html
        assert "DonePage" not in html

    @pytest.mark.xfail(reason="PageList does not yet implement parent= filtering")
    def test_pagelist_filter_parent(self) -> None:
        """<<PageList(parent=\"Factory\")>> → only pages whose name starts with Factory/ appear."""
        pages = [
            make_page("Factory/Task1"),
            make_page("Factory/Task2"),
            make_page("Other/Task"),
        ]
        html = render("<<PageList(parent=Factory)>>", pages=pages)
        assert "Factory/Task1" in html
        assert "Factory/Task2" in html
        assert "Other/Task" not in html

    def test_pagelist_limit(self) -> None:
        """<<PageList(limit=2)>> with 4 pages → exactly 2 <li> items in output."""
        pages = [make_page(f"Page{i}") for i in range(4)]
        html = render("<<PageList(limit=2)>>", pages=pages)
        count = html.count("<li")
        assert count == 2

    @pytest.mark.xfail(reason="PageList does not yet implement status filtering")
    def test_pagelist_combined_filters(self) -> None:
        """<<PageList(tag=\"docs\", status=\"planned\")>> → only pages matching both filters."""
        pages = [
            make_page("Docs/Planned", tags=["docs"], status="planned"),
            make_page("Docs/InProgress", tags=["docs"], status="in_progress"),
            make_page("Other/Planned", tags=["other"], status="planned"),
        ]
        html = render("<<PageList(tag=docs, status=planned)>>", pages=pages)
        assert "Docs/Planned" in html
        assert "Docs/InProgress" not in html
        assert "Other/Planned" not in html

    def test_pagelist_no_match(self) -> None:
        """No pages match → output contains No pages found. and no <ul>."""
        pages = [
            make_page("Unmatched", tags=["other"], status="done"),
        ]
        html = render("<<PageList(tag=nonexistent)>>", pages=pages)
        assert "No pages found" in html
        assert "<ul" not in html


class TestPageListStatusBadge:
    """Tests for status badge rendering."""

    @pytest.mark.xfail(reason="PageList does not yet render status badges")
    def test_pagelist_status_badge(self) -> None:
        """Page with status=\"in_progress\" → output contains a <span class=\"badge element."""
        pages = [make_page("ActivePage", status="in_progress")]
        html = render("<<PageList>>", pages=pages)
        assert '<span class="badge' in html

    @pytest.mark.xfail(reason="PageList does not yet render status badges")
    def test_pagelist_status_badge_fallback(self) -> None:
        """Page with unknown status → badge uses badge-secondary class."""
        pages = [make_page("UnknownPage", status="some_weird_status")]
        html = render("<<PageList>>", pages=pages)
        assert "badge-secondary" in html


class TestPageListEdgeCases:
    """Edge case handling tests."""

    def test_pagelist_in_fenced_block(self) -> None:
        """Macro inside a ```...``` block → raw macro text appears, not rendered HTML."""
        content = "```\n<<PageList>>\n```"
        html = render(content, pages=[make_page("Test")])
        assert "page-list" not in html
        assert "&lt;&lt;PageList&gt;&gt;" in html or "<<PageList>>" in html

    def test_pagelist_in_tilde_block(self) -> None:
        """Macro inside a ~~~...~~~ block → raw macro text appears, not rendered HTML."""
        content = "~~~\n<<PageList>>\n~~~"
        html = render(content, pages=[make_page("Test")])
        assert "page-list" not in html
