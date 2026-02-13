---
title: Python Development
tags:
  - development
  - python
  - tutorial
status: active
author: alice
priority: medium
---

# Python Development

Guide for local development of the GraphWiki Python application.

## Setup

```bash
# With Rust engine (recommended)
./dev.sh

# Without Rust engine
cd src
pip install -e ".[dev]"
uvicorn graphwiki.main:app --reload
```

The app runs at **http://localhost:8000**.

## Project Structure

```
src/graphwiki/
├── main.py          # FastAPI routes, WebSocket
├── config.py        # Settings (GRAPHWIKI_* env vars)
├── core/
│   ├── storage.py   # FileStorage implementation
│   ├── parser.py    # Markdown extensions
│   ├── graph.py     # Rust engine wrapper
│   ├── ws_manager.py # WebSocket manager
│   └── models.py    # Pydantic models
├── templates/       # Jinja2 templates
└── static/          # CSS, JS
```

## Running Tests

```bash
cd src
pytest                          # All tests
pytest --cov=graphwiki          # With coverage
pytest -x                       # Stop on first failure
pytest -k "test_storage"        # Run specific tests
pytest tests/test_parser.py -v  # Single file, verbose
```

## Code Style

| Tool | Purpose | Command |
|------|---------|---------|
| black | Formatting | `black src/` |
| isort | Import sorting | `isort src/` |
| ruff | Linting | `ruff check src/` |
| mypy | Type checking | `mypy src/graphwiki/` |

## Key Patterns

### Async Storage

All storage operations are `async`:

```python
page = await storage.get_page("PageName")
await storage.save_page("PageName", content)
```

### Settings

Environment variables with `GRAPHWIKI_` prefix:

```python
from graphwiki.config import settings
data_dir = settings.data_dir  # GRAPHWIKI_DATA_DIR
```

### Optional Graph Engine

The Rust engine is imported with a try/except:

```python
from graphwiki.core.graph import get_engine
engine = get_engine()  # Returns None if not available
```

## Related

- [[Architecture Overview]] - System design
- [[Rust Graph Engine]] - Graph engine details
- [[Getting Started]] - User-facing guide
