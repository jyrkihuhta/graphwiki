"""Unit tests for application configuration."""

from pathlib import Path
from unittest.mock import patch

from graphwiki.config import Settings


class TestSettings:
    def test_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            s = Settings()
            assert s.data_dir == Path("data/pages")
            assert s.debug is False
            assert s.app_title == "GraphWiki"
            assert s.graph_watch is True

    def test_from_env(self):
        env = {
            "GRAPHWIKI_DATA_DIR": "/tmp/wiki",
            "GRAPHWIKI_DEBUG": "true",
            "GRAPHWIKI_APP_TITLE": "MyWiki",
            "GRAPHWIKI_GRAPH_WATCH": "false",
        }
        with patch.dict("os.environ", env, clear=True):
            s = Settings()
            assert s.data_dir == Path("/tmp/wiki")
            assert s.debug is True
            assert s.app_title == "MyWiki"
            assert s.graph_watch is False

    def test_debug_false_values(self):
        with patch.dict("os.environ", {"GRAPHWIKI_DEBUG": "false"}, clear=True):
            s = Settings()
            assert s.debug is False

    def test_graph_watch_true_default(self):
        with patch.dict("os.environ", {}, clear=True):
            s = Settings()
            assert s.graph_watch is True
