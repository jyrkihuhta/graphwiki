# graph-core

Rust-based graph engine for GraphWiki.

Provides fast graph operations for wiki pages using petgraph, exposed to Python via PyO3.

## Features

- Markdown file parsing with link extraction
- YAML frontmatter metadata parsing
- petgraph-based wiki graph
- File watching for live updates
- MetaTable-style queries

## Development

```bash
# Create venv and install maturin
python3 -m venv .venv
source .venv/bin/activate
pip install maturin

# Build and install in development mode
maturin develop

# Run tests
cargo test
```

## Usage

```python
from graph_core import GraphEngine

engine = GraphEngine("/path/to/pages")
pages = engine.list_pages()
backlinks = engine.get_backlinks("SomePage")
```
