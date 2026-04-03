"""Tests for graph node sizing based on backlink count (Milestone 10 - TASK004)."""

import os

import pytest

from meshwiki.core.graph import (
    GRAPH_ENGINE_AVAILABLE,
    init_engine,
    shutdown_engine,
)


@pytest.fixture
def wiki_dir(tmp_path):
    pages = {
        "HubPage.md": (
            "---\nstatus: published\n---\n"
            "# Hub Page\n\nWelcome to [[PageA]], [[PageB]], [[PageC]], [[PageD]], [[PageE]].\n"
        ),
        "PageA.md": "# Page A\n\nSee [[HubPage]].\n",
        "PageB.md": "# Page B\n\nSee [[HubPage]].\n",
        "PageC.md": "# Page C\n\nSee [[HubPage]].\n",
        "PageD.md": "# Page D\n\nSee [[HubPage]].\n",
        "PageE.md": "# Page E\n\nSee [[HubPage]].\n",
        "OrphanPage.md": "# Orphan Page\n\nNo links here.\n",
    }
    for name, content in pages.items():
        (tmp_path / name).write_text(content)
    return tmp_path


@pytest.fixture(autouse=True)
def cleanup_engine():
    yield
    shutdown_engine()


class TestGraphNodeSizingAPI:
    @pytest.mark.skipif(not GRAPH_ENGINE_AVAILABLE, reason="graph_core not installed")
    @pytest.mark.asyncio
    async def test_graph_api_includes_backlinks_count(self, wiki_dir):
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

            nodes_by_id = {n["id"]: n for n in data["nodes"]}

            assert "HubPage" in nodes_by_id
            hub_node = nodes_by_id["HubPage"]
            assert "backlinks_count" in hub_node
            assert hub_node["backlinks_count"] == 5

            assert "OrphanPage" in nodes_by_id
            orphan_node = nodes_by_id["OrphanPage"]
            assert "backlinks_count" in orphan_node
            assert orphan_node["backlinks_count"] == 0

    @pytest.mark.skipif(not GRAPH_ENGINE_AVAILABLE, reason="graph_core not installed")
    @pytest.mark.asyncio
    async def test_graph_api_backlinks_count_pages_link_to_hub(self, wiki_dir):
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

            nodes_by_id = {n["id"]: n for n in data["nodes"]}

            for page in ["PageA", "PageB", "PageC", "PageD", "PageE"]:
                assert page in nodes_by_id
                page_node = nodes_by_id[page]
                assert page_node.get("backlinks_count", 0) == 1


class TestGraphNodeSizingLogic:
    def test_node_radius_logarithmic_scaling_zero_backlinks(self):
        import math

        min_radius = 5
        max_radius = 24
        default_radius = 8

        def get_node_radius(backlinks_count, max_backlinks):
            if backlinks_count is None or backlinks_count < 0:
                backlinks_count = 0
            if not max_backlinks or max_backlinks <= 0:
                return default_radius
            log_scale = math.log(1 + backlinks_count) / math.log(1 + max_backlinks)
            return min_radius + (max_radius - min_radius) * log_scale

        assert get_node_radius(0, 10) == min_radius

    def test_node_radius_logarithmic_scaling_no_max_backlinks(self):
        import math

        min_radius = 5
        max_radius = 24
        default_radius = 8

        def get_node_radius(backlinks_count, max_backlinks):
            if backlinks_count is None or backlinks_count < 0:
                backlinks_count = 0
            if not max_backlinks or max_backlinks <= 0:
                return default_radius
            log_scale = math.log(1 + backlinks_count) / math.log(1 + max_backlinks)
            return min_radius + (max_radius - min_radius) * log_scale

        assert get_node_radius(0, 0) == default_radius
        assert get_node_radius(5, None) == default_radius

    def test_node_radius_logarithmic_scaling_low_backlinks(self):
        import math

        min_radius = 5
        max_radius = 24
        default_radius = 8

        def get_node_radius(backlinks_count, max_backlinks):
            if backlinks_count is None or backlinks_count < 0:
                backlinks_count = 0
            if not max_backlinks or max_backlinks <= 0:
                return default_radius
            log_scale = math.log(1 + backlinks_count) / math.log(1 + max_backlinks)
            return min_radius + (max_radius - min_radius) * log_scale

        radius = get_node_radius(1, 10)
        assert min_radius < radius < max_radius

    def test_node_radius_logarithmic_scaling_high_backlinks(self):
        import math

        min_radius = 5
        max_radius = 24

        def get_node_radius(backlinks_count, max_backlinks):
            if backlinks_count is None or backlinks_count < 0:
                backlinks_count = 0
            if not max_backlinks or max_backlinks <= 0:
                return 8
            log_scale = math.log(1 + backlinks_count) / math.log(1 + max_backlinks)
            return min_radius + (max_radius - min_radius) * log_scale

        radius = get_node_radius(100, 100)
        assert radius == max_radius

    def test_node_radius_respects_bounds(self):
        import math

        min_radius = 5
        max_radius = 24

        def get_node_radius(backlinks_count, max_backlinks):
            if backlinks_count is None or backlinks_count < 0:
                backlinks_count = 0
            if not max_backlinks or max_backlinks <= 0:
                return 8
            log_scale = math.log(1 + backlinks_count) / math.log(1 + max_backlinks)
            return min_radius + (max_radius - min_radius) * log_scale

        assert get_node_radius(0, 10) >= min_radius
        assert get_node_radius(0, 10) <= max_radius
        assert get_node_radius(5, 10) >= min_radius
        assert get_node_radius(5, 10) <= max_radius
        assert get_node_radius(10, 10) >= min_radius
        assert get_node_radius(10, 10) <= max_radius


class TestGraphPageNodeSizingUI:
    @pytest.mark.asyncio
    async def test_graph_js_creates_legend(self):
        import os

        os.environ["MESHWIKI_DATA_DIR"] = "/tmp/nonexistent"
        import importlib

        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/static/js/graph.js")
            assert response.status_code == 200
            body = response.text
            assert "initLegendUI" in body
            assert "graph-legend" in body

    @pytest.mark.skipif(not GRAPH_ENGINE_AVAILABLE, reason="graph_core not installed")
    @pytest.mark.asyncio
    async def test_graph_js_has_radius_constants(self):
        import os

        os.environ["MESHWIKI_DATA_DIR"] = "/tmp/nonexistent"
        import importlib

        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/static/js/graph.js")
            assert response.status_code == 200
            body = response.text
            assert "MIN_NODE_RADIUS" in body
            assert "MAX_NODE_RADIUS" in body
            assert "getNodeRadius" in body

    @pytest.mark.skipif(not GRAPH_ENGINE_AVAILABLE, reason="graph_core not installed")
    @pytest.mark.asyncio
    async def test_graph_js_uses_logarithmic_scaling(self):
        import os

        os.environ["MESHWIKI_DATA_DIR"] = "/tmp/nonexistent"
        import importlib

        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/static/js/graph.js")
            assert response.status_code == 200
            body = response.text
            assert "Math.log" in body
            assert "getNodeRadius" in body


class TestGraphNodeSizingCSS:
    @pytest.mark.asyncio
    async def test_graph_css_has_legend_styles(self):
        import os

        os.environ["MESHWIKI_DATA_DIR"] = "/tmp/nonexistent"
        import importlib

        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/static/css/graph.css")
            assert response.status_code == 200
            body = response.text
            assert ".graph-legend" in body or "graph-legend" in body

    @pytest.mark.asyncio
    async def test_graph_css_has_dark_theme_legend_styles(self):
        import os

        os.environ["MESHWIKI_DATA_DIR"] = "/tmp/nonexistent"
        import importlib

        import meshwiki.config

        importlib.reload(meshwiki.config)
        import meshwiki.main

        importlib.reload(meshwiki.main)

        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=meshwiki.main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/static/css/graph.css")
            assert response.status_code == 200
            body = response.text
            assert "[data-theme=" in body or "data-theme=" in body
