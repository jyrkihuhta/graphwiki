"""Tests for inline MetaTable cell editing.

Covers the storage layer update_frontmatter_field() method and
the PATCH /api/page/{name}/metadata API endpoint.
"""

import importlib
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from meshwiki.core.storage import FileStorage

# ============================================================
# Storage layer tests
# ============================================================


@pytest.fixture
def storage(tmp_path):
    return FileStorage(tmp_path)


class TestUpdateFrontmatterField:
    @pytest.mark.asyncio
    async def test_update_scalar_field(self, storage):
        await storage.save_page("TestPage", "---\nstatus: draft\n---\n\n# Body")
        page = await storage.update_frontmatter_field("TestPage", "status", "active")
        assert page is not None
        raw = await storage.get_raw_content("TestPage")
        assert "status: active" in raw
        assert "# Body" in raw

    @pytest.mark.asyncio
    async def test_update_title_field(self, storage):
        await storage.save_page("TestPage", "---\ntitle: Old\n---\n\n# Body")
        page = await storage.update_frontmatter_field("TestPage", "title", "New Title")
        assert page is not None
        assert page.metadata.title == "New Title"

    @pytest.mark.asyncio
    async def test_update_tags_field(self, storage):
        await storage.save_page("TestPage", "---\ntags:\n  - old\n---\n\n# Body")
        page = await storage.update_frontmatter_field(
            "TestPage", "tags", "new, updated"
        )
        assert page is not None
        assert page.metadata.tags == ["new", "updated"]

    @pytest.mark.asyncio
    async def test_nonexistent_page_returns_none(self, storage):
        result = await storage.update_frontmatter_field("Missing", "status", "active")
        assert result is None

    @pytest.mark.asyncio
    async def test_adds_new_field(self, storage):
        await storage.save_page("TestPage", "---\ntitle: Test\n---\n\n# Body")
        page = await storage.update_frontmatter_field("TestPage", "priority", "high")
        assert page is not None
        raw = await storage.get_raw_content("TestPage")
        assert "priority: high" in raw

    @pytest.mark.asyncio
    async def test_preserves_body(self, storage):
        await storage.save_page(
            "TestPage", "---\nstatus: draft\n---\n\n# My Body\n\nSome content here."
        )
        await storage.update_frontmatter_field("TestPage", "status", "active")
        raw = await storage.get_raw_content("TestPage")
        assert "# My Body" in raw
        assert "Some content here." in raw

    @pytest.mark.asyncio
    async def test_empty_value_removes_extra_field(self, storage):
        await storage.save_page(
            "TestPage", "---\nstatus: draft\ntitle: Test\n---\n\n# Body"
        )
        await storage.update_frontmatter_field("TestPage", "status", "")
        raw = await storage.get_raw_content("TestPage")
        assert "status" not in raw
        assert "title: Test" in raw

    @pytest.mark.asyncio
    async def test_updates_modified_timestamp(self, storage):
        page1 = await storage.save_page("TestPage", "---\nstatus: draft\n---\n\n# Body")
        modified1 = page1.metadata.modified
        page2 = await storage.update_frontmatter_field("TestPage", "status", "active")
        assert page2.metadata.modified >= modified1

    @pytest.mark.asyncio
    async def test_page_without_frontmatter(self, storage):
        await storage.save_page("TestPage", "# No frontmatter")
        page = await storage.update_frontmatter_field("TestPage", "status", "new")
        assert page is not None
        raw = await storage.get_raw_content("TestPage")
        assert "status: new" in raw
        assert "# No frontmatter" in raw


# ============================================================
# API endpoint tests
# ============================================================


@pytest.fixture()
def wiki_app(tmp_path):
    os.environ["MESHWIKI_DATA_DIR"] = str(tmp_path)
    import meshwiki.config

    importlib.reload(meshwiki.config)
    import meshwiki.main

    importlib.reload(meshwiki.main)
    yield meshwiki.main.app
    os.environ.pop("MESHWIKI_DATA_DIR", None)


@pytest_asyncio.fixture()
async def client(wiki_app):
    transport = ASGITransport(app=wiki_app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as c:
        yield c


class TestMetadataEndpoint:
    @pytest.mark.asyncio
    async def test_update_field(self, client):
        await client.post(
            "/page/TestPage",
            data={"content": "---\nstatus: draft\n---\n\n# Body"},
        )
        resp = await client.patch(
            "/api/page/TestPage/metadata",
            data={"field": "status", "value": "active"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["field"] == "status"
        assert data["value"] == "active"

    @pytest.mark.asyncio
    async def test_nonexistent_page(self, client):
        resp = await client.patch(
            "/api/page/Missing/metadata",
            data={"field": "status", "value": "active"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_protected_field_rejected(self, client):
        await client.post("/page/TestPage", data={"content": "# Body"})
        resp = await client.patch(
            "/api/page/TestPage/metadata",
            data={"field": "created", "value": "2020-01-01"},
        )
        assert resp.status_code == 400
        assert "cannot be edited" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_name_field_rejected(self, client):
        await client.post("/page/TestPage", data={"content": "# Body"})
        resp = await client.patch(
            "/api/page/TestPage/metadata",
            data={"field": "name", "value": "NewName"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_field_name_rejected(self, client):
        await client.post("/page/TestPage", data={"content": "# Body"})
        resp = await client.patch(
            "/api/page/TestPage/metadata",
            data={"field": "../etc/passwd", "value": "bad"},
        )
        assert resp.status_code == 400
        assert "Invalid field name" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_path_traversal_rejected(self, client):
        resp = await client.patch(
            "/api/page/..%2Fetc%2Fpasswd/metadata",
            data={"field": "status", "value": "hacked"},
        )
        assert resp.status_code in (400, 404, 422)

    @pytest.mark.asyncio
    async def test_value_persists_on_read(self, client):
        await client.post(
            "/page/TestPage",
            data={"content": "---\nstatus: draft\n---\n\n# Body"},
        )
        await client.patch(
            "/api/page/TestPage/metadata",
            data={"field": "status", "value": "published"},
        )
        resp = await client.get("/page/TestPage/raw")
        assert resp.status_code == 200
