"""Tests for the graph_core Python module."""

import os
import tempfile
import pytest
from graph_core import GraphEngine, PageInfo


@pytest.fixture
def temp_wiki_dir():
    """Create a temporary directory with test wiki files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test markdown files
        files = {
            "HomePage.md": """---
status: published
tags:
  - main
  - index
---
# Welcome

This links to [[About]] and [[Contact]].
""",
            "About.md": """---
status: draft
author: testuser
---
# About

Return to [[HomePage]].
""",
            "Contact.md": """---
status: published
---
# Contact

See [[HomePage]] for more.
""",
        }

        for filename, content in files.items():
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, "w") as f:
                f.write(content)

        yield tmpdir


class TestGraphEngine:
    """Tests for GraphEngine class."""

    def test_create_engine(self):
        """Test creating a new GraphEngine."""
        engine = GraphEngine("/tmp/test")
        assert engine.get_data_dir() == "/tmp/test"
        assert engine.page_count() == 0
        assert engine.link_count() == 0

    def test_empty_engine(self):
        """Test operations on an empty engine."""
        engine = GraphEngine("/tmp/test")
        assert engine.list_pages() == []
        assert engine.get_page("NonExistent") is None
        assert engine.page_exists("NonExistent") is False
        assert engine.get_backlinks("SomePage") == []
        assert engine.get_outlinks("SomePage") == []

    def test_rebuild_with_files(self, temp_wiki_dir):
        """Test rebuilding the graph from files."""
        engine = GraphEngine(temp_wiki_dir)
        engine.rebuild()

        # Should have 3 real pages + stub pages for any broken links
        assert engine.page_count() >= 3
        assert engine.page_exists("HomePage")
        assert engine.page_exists("About")
        assert engine.page_exists("Contact")

    def test_get_page(self, temp_wiki_dir):
        """Test getting a specific page."""
        engine = GraphEngine(temp_wiki_dir)
        engine.rebuild()

        page = engine.get_page("HomePage")
        assert page is not None
        assert page.name == "HomePage"
        assert page.file_path == "HomePage.md"
        assert "status" in page.metadata
        assert page.metadata["status"] == ["published"]
        assert page.metadata["tags"] == ["main", "index"]

    def test_get_metadata(self, temp_wiki_dir):
        """Test getting page metadata."""
        engine = GraphEngine(temp_wiki_dir)
        engine.rebuild()

        metadata = engine.get_metadata("About")
        assert metadata is not None
        assert metadata["status"] == ["draft"]
        assert metadata["author"] == ["testuser"]

        # Non-existent page
        assert engine.get_metadata("NonExistent") is None

    def test_backlinks(self, temp_wiki_dir):
        """Test getting backlinks (pages linking TO a page)."""
        engine = GraphEngine(temp_wiki_dir)
        engine.rebuild()

        # About and Contact link to HomePage
        backlinks = engine.get_backlinks("HomePage")
        assert len(backlinks) == 2
        assert "About" in backlinks
        assert "Contact" in backlinks

        # HomePage links to About
        backlinks = engine.get_backlinks("About")
        assert "HomePage" in backlinks

    def test_outlinks(self, temp_wiki_dir):
        """Test getting outlinks (pages a page links TO)."""
        engine = GraphEngine(temp_wiki_dir)
        engine.rebuild()

        # HomePage links to About and Contact
        outlinks = engine.get_outlinks("HomePage")
        assert len(outlinks) == 2
        assert "About" in outlinks
        assert "Contact" in outlinks

        # About links to HomePage
        outlinks = engine.get_outlinks("About")
        assert "HomePage" in outlinks

    def test_link_count(self, temp_wiki_dir):
        """Test counting total links."""
        engine = GraphEngine(temp_wiki_dir)
        engine.rebuild()

        # HomePage -> About, Contact (2 links)
        # About -> HomePage (1 link)
        # Contact -> HomePage (1 link)
        # Total: 4 links
        assert engine.link_count() == 4

    def test_rebuild_clears_graph(self, temp_wiki_dir):
        """Test that rebuild clears and rebuilds the graph."""
        engine = GraphEngine(temp_wiki_dir)
        engine.rebuild()

        initial_count = engine.page_count()
        assert initial_count >= 3

        # Rebuild again
        engine.rebuild()
        assert engine.page_count() == initial_count

    def test_repr(self, temp_wiki_dir):
        """Test string representation of engine."""
        engine = GraphEngine(temp_wiki_dir)
        repr_str = repr(engine)
        assert "GraphEngine" in repr_str
        assert temp_wiki_dir in repr_str


class TestPageInfo:
    """Tests for PageInfo class."""

    def test_create_page_info(self):
        """Test creating a PageInfo."""
        page = PageInfo("TestPage", "TestPage.md")
        assert page.name == "TestPage"
        assert page.file_path == "TestPage.md"
        assert page.metadata == {}

    def test_page_info_with_metadata(self):
        """Test creating a PageInfo with metadata."""
        metadata = {"status": ["draft"], "tags": ["rust", "wiki"]}
        page = PageInfo.with_metadata("TestPage", "TestPage.md", metadata)
        assert page.name == "TestPage"
        assert page.metadata == metadata

    def test_page_info_repr(self):
        """Test string representation of PageInfo."""
        page = PageInfo("TestPage", "TestPage.md")
        repr_str = repr(page)
        assert "PageInfo" in repr_str
        assert "TestPage" in repr_str
