"""Tests for graph node tooltips (Milestone 10)."""

import os
import time
from unittest.mock import patch

import pytest

from meshwiki.core.graph import (
    GRAPH_ENGINE_AVAILABLE,
    init_engine,
    shutdown_engine,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def wiki_dir(tmp_path):
    """Create a temporary wiki directory with test pages."""
    pages = {
        "HomePage.md": (
            "---\nstatus: published\ntags:\n  - main\n  - wiki\n---\n"
            "# Home\n\nWelcome to [[About]] and [[Contact]].\n"
        ),
        "About.md": (
            "---\nstatus: draft\ntags:\n  - info\n---\n# About\n\nSee [[HomePage]].\n"
        ),
        "Contact.md": "# Contact\n\nReturn to [[HomePage]].\n",
    }
    for name, content in pages.items():
        (tmp_path / name).write_text(content)
    return tmp_path


@pytest.fixture(autouse=True)
def cleanup_engine():
    """Ensure engine is shut down after each test."""
    yield
    shutdown_engine()


# ============================================================
# Tooltip API tests
# ============================================================


class TestGraphTooltipAPI:
    @pytest.mark.skipif(not GRAPH_ENGINE_AVAILABLE, reason="graph_core not installed")
    @pytest.mark.asyncio
    async def test_api_graph_returns_node_metadata(self, wiki_dir):
        """API should return tags, backlinks_count, and modified for each node."""
        import importlib

        os.environ["MESHWIKI_DATA_DIR"] = str(wiki_dir)
        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        init_engine(wiki_dir, watch=False)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/graph")
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "links" in data

            node_map = {n["id"]: n for n in data["nodes"]}

            assert "HomePage" in node_map
            home = node_map["HomePage"]
            assert "tags" in home
            assert "main" in home["tags"]
            assert "wiki" in home["tags"]
            assert "backlinks_count" in home
            assert home["backlinks_count"] == 2
            assert "modified" in home
            assert isinstance(home["modified"], int)

            assert "About" in node_map
            about = node_map["About"]
            assert about["backlinks_count"] == 1

            assert "Contact" in node_map
            contact = node_map["Contact"]
            assert contact["backlinks_count"] == 1

    @pytest.mark.skipif(not GRAPH_ENGINE_AVAILABLE, reason="graph_core not installed")
    @pytest.mark.asyncio
    async def test_api_graph_tags_from_frontmatter(self, wiki_dir):
        """Tags should be extracted from page frontmatter."""
        import importlib

        os.environ["MESHWIKI_DATA_DIR"] = str(wiki_dir)
        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        init_engine(wiki_dir, watch=False)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/graph")
            data = response.json()
            node_map = {n["id"]: n for n in data["nodes"]}

            assert node_map["HomePage"]["tags"] == ["main", "wiki"]
            assert node_map["About"]["tags"] == ["info"]
            assert node_map["Contact"]["tags"] == []

    @pytest.mark.skipif(not GRAPH_ENGINE_AVAILABLE, reason="graph_core not installed")
    @pytest.mark.asyncio
    async def test_api_graph_modified_is_valid_timestamp(self, wiki_dir):
        """Modified field should be a valid Unix timestamp."""
        import importlib

        os.environ["MESHWIKI_DATA_DIR"] = str(wiki_dir)
        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        init_engine(wiki_dir, watch=False)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/graph")
            data = response.json()
            for node in data["nodes"]:
                assert "modified" in node
                assert node["modified"] > 0
                ts = node["modified"]
                date = time.gmtime(ts)
                assert date.tm_year >= 2020

    @pytest.mark.asyncio
    async def test_api_graph_without_engine_returns_empty(self):
        """Without engine, API should return empty nodes list."""
        import importlib

        os.environ["MESHWIKI_DATA_DIR"] = "/tmp/nonexistent"
        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        with patch("meshwiki.main.get_engine", return_value=None):
            from httpx import ASGITransport, AsyncClient

            transport = ASGITransport(app=meshwiki.main.app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.get("/api/graph")
                assert response.status_code == 200
                data = response.json()
                assert data == {"nodes": [], "links": []}


# ============================================================
# Tooltip CSS tests
# ============================================================


class TestTooltipCSS:
    def test_tooltip_css_classes_exist(self):
        """Tooltip CSS classes should be defined in style.css."""
        import os

        style_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "meshwiki",
            "static",
            "css",
            "style.css",
        )
        with open(style_path, "r") as f:
            css = f.read()

        assert ".graph-tooltip" in css
        assert ".graph-tooltip.visible" in css
        assert ".graph-tooltip.fade-out" in css
        assert ".graph-tooltip-title" in css
        assert ".graph-tooltip-row" in css
        assert ".graph-tooltip-tags" in css
        assert ".graph-tooltip-tag" in css

    def test_tooltip_uses_css_variables(self):
        """Tooltip should use CSS variables for theming."""
        import os

        style_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "meshwiki",
            "static",
            "css",
            "style.css",
        )
        with open(style_path, "r") as f:
            css = f.read()

        tooltip_section = css[
            css.find(".graph-tooltip") : css.find(
                ".graph-tooltip", css.find(".graph-tooltip-tag") + 10
            )
        ]
        assert "var(--color-bg)" in tooltip_section
        assert "var(--color-border)" in tooltip_section
        assert "var(--color-text)" in tooltip_section
        assert "var(--color-shadow)" in tooltip_section

    def test_tooltip_has_transition(self):
        """Tooltip should have fade transition."""
        import os

        style_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "meshwiki",
            "static",
            "css",
            "style.css",
        )
        with open(style_path, "r") as f:
            css = f.read()

        assert "transition: opacity" in css
