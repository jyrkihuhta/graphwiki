"""Playwright E2E test fixtures for MeshWiki."""

import os
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 15.0) -> None:
    import httpx

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                return
        except httpx.ConnectError:
            pass
        time.sleep(0.2)
    raise TimeoutError(f"Server at {url} did not start within {timeout}s")


@pytest.fixture(scope="session")
def e2e_server(tmp_path_factory):
    """Start a MeshWiki server for the E2E test session."""
    data_dir = tmp_path_factory.mktemp("wiki_data")
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = {
        **os.environ,
        "MESHWIKI_DATA_DIR": str(data_dir),
        "MESHWIKI_DEBUG": "true",
        "MESHWIKI_GRAPH_WATCH": "false",
    }

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "meshwiki.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(Path(__file__).resolve().parent.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _wait_for_server(base_url)
        yield {"url": base_url, "data_dir": data_dir, "port": port}
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def base_url(e2e_server) -> str:
    return e2e_server["url"]


@pytest.fixture(scope="session")
def data_dir(e2e_server) -> Path:
    return e2e_server["data_dir"]


@pytest.fixture(autouse=True)
def clean_wiki(e2e_server):
    """Remove all .md files before each test for isolation."""
    dd = e2e_server["data_dir"]
    for f in dd.glob("*.md"):
        f.unlink()
    yield
    for f in dd.glob("*.md"):
        f.unlink()


@pytest.fixture()
def create_page(e2e_server):
    """Factory fixture to create wiki pages by writing files directly."""
    dd = e2e_server["data_dir"]

    def _create(name: str, content: str) -> None:
        filename = name.replace(" ", "_") + ".md"
        now = datetime.now(timezone.utc).isoformat()
        full = f"---\ncreated: {now}\nmodified: {now}\n---\n\n{content}"
        (dd / filename).write_text(full, encoding="utf-8")

    return _create
