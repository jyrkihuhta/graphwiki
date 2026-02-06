# GraphWiki

A modern, self-hosted wiki platform inspired by [MoinMoin](https://moinmo.in/), [Graphingwiki](http://graphingwiki.python-hosting.com/), and [Obsidian](https://obsidian.md/). GraphWiki combines file-based Markdown storage with a Rust-powered graph engine for metadata queries, backlinks, and interactive graph visualization.

## Features

- **Markdown wiki pages** - Full Markdown support with tables, code blocks, task lists, strikethrough, and more
- **Wiki links** - `[[PageName]]` and `[[PageName|Display Text]]` syntax with missing-page detection
- **Backlinks** - Panel showing all pages that link to the current page
- **MetaTable queries** - Graphingwiki-style metadata queries via `<<MetaTable(...)>>` macro with YAML frontmatter
- **Graph visualization** - Interactive D3.js force-directed graph at `/graph` with real-time WebSocket updates
- **Rust graph engine** - Fast graph operations powered by [petgraph](https://github.com/petgraph/petgraph) + [PyO3](https://pyo3.rs/)
- **File-based storage** - Pages stored as plain Markdown files, easy to backup and version control
- **HTMX interactions** - Snappy server-rendered UI without heavy JavaScript
- **Kubernetes-native** - Deployed via GitOps with Flux, Istio ingress, and Rancher management

## Quick Start

### With Rust graph engine (recommended)

```bash
git clone https://github.com/jyrkihuhta/graphwiki.git
cd graphwiki
./dev.sh
```

This builds the Rust graph engine via [Maturin](https://www.maturin.rs/), installs Python dependencies, and starts the server at **http://localhost:8000**.

Options:
```bash
./dev.sh --skip-build    # Start server without rebuilding Rust
./dev.sh --build-only    # Build Rust engine only
```

### Without Rust engine

The app works without the graph engine — graph features (backlinks, MetaTable, visualization) gracefully degrade.

```bash
cd src
pip install -e .
uvicorn graphwiki.main:app --reload
```

### Prerequisites

- **Python 3.12+**
- **Rust** (install via [rustup](https://rustup.rs/)) — only needed for graph features
- **Maturin** — installed automatically by `dev.sh`, or `pip install maturin`

## Screenshots

<!-- TODO: Add screenshots of page view, graph visualization, MetaTable -->

## Usage

### Wiki Links

Link to other pages with double-bracket syntax:

```markdown
See [[OtherPage]] for details.
Check the [[Setup Guide|guide]] to get started.
```

Existing pages render as links; missing pages render with distinct styling and link to the editor.

### MetaTable Queries

Query page metadata using YAML frontmatter. Add frontmatter to your pages:

```yaml
---
status: draft
author: alice
tags: [python, wiki]
---
```

Then use the MetaTable macro to query across pages:

```markdown
<<MetaTable(status=draft, ||name||status||author||)>>
```

Filter operators: `key=value` (equals), `key~=substring` (contains), `key/=regex` (matches).

### Graph Visualization

Visit `/graph` for an interactive force-directed graph of all pages and their links. Nodes are clickable, draggable, and update in real-time as pages change.

## Running Tests

```bash
# Python integration tests (59 tests)
cd src
pip install -e ".[dev]"
pytest tests/ -v

# Rust graph engine tests (70 tests)
cd graph-core
source .venv/bin/activate
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop
python -m pytest tests/ -v
```

**129 total tests** across both test suites.

## Project Structure

```
graphwiki/
├── dev.sh                      # Development startup script
├── graph-core/                 # Rust graph engine
│   ├── Cargo.toml
│   ├── src/                    # Rust source (lib, graph, parser, models, query, events, watcher)
│   └── tests/                  # PyO3 integration tests (70 tests)
├── src/                        # Python application
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── graphwiki/
│   │   ├── main.py             # FastAPI routes + WebSocket endpoint
│   │   ├── config.py           # Settings (GRAPHWIKI_* env vars)
│   │   ├── core/
│   │   │   ├── storage.py      # Abstract storage + FileStorage
│   │   │   ├── parser.py       # Markdown + wiki links + MetaTable macro
│   │   │   ├── graph.py        # Rust engine wrapper (optional import)
│   │   │   ├── ws_manager.py   # WebSocket connection manager
│   │   │   └── models.py       # Pydantic models
│   │   ├── templates/          # Jinja2 templates (base, page views, graph)
│   │   └── static/             # CSS + D3.js graph visualization
│   └── tests/                  # Integration tests (59 tests)
├── docs/                       # Documentation
│   ├── architecture.md         # System design
│   ├── getting-started.md      # Setup and deployment guide
│   ├── prd/                    # Product requirements
│   ├── adr/                    # Architecture decision records
│   ├── domains/                # Domain-specific design docs
│   └── research/               # Background research
├── deploy/                     # Kubernetes deployment
│   ├── apps/graphwiki/         # K8s manifests (Deployment, Service, VirtualService)
│   └── flux/                   # Flux GitOps configuration
├── infra/local/                # Terraform for local k3d cluster
│   ├── main.tf                 # k3d cluster
│   ├── istio.tf                # Istio service mesh
│   └── rancher.tf              # Rancher management
└── data/pages/                 # Wiki content (gitignored)
```

## Configuration

Environment variables with `GRAPHWIKI_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAPHWIKI_DATA_DIR` | `data/pages` | Page storage directory |
| `GRAPHWIKI_DEBUG` | `false` | Debug mode |
| `GRAPHWIKI_APP_TITLE` | `GraphWiki` | Application title in header |
| `GRAPHWIKI_GRAPH_WATCH` | `true` | Enable file watcher for live graph updates |

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | FastAPI (Python 3.12+) | Async web framework |
| Graph Engine | Rust (petgraph + PyO3) | Fast graph operations and metadata queries |
| Frontend | Jinja2 + HTMX | Server-rendered templates with dynamic updates |
| Visualization | D3.js | Interactive force-directed graph |
| Real-time | WebSocket + asyncio | Live graph updates |
| Storage | Markdown files + YAML frontmatter | Plain-text, git-friendly |
| Infrastructure | k3d + Istio + Rancher + Flux | Kubernetes-native GitOps deployment |
| IaC | Terraform | Local cluster provisioning |

## Kubernetes Deployment

For deploying to a local k3d cluster with Istio and Flux GitOps, see the [Getting Started](docs/getting-started.md) guide.

```bash
# Quick overview
cd infra/local && terraform apply     # Create k3d cluster + Istio + Rancher
cd src && docker build -t graphwiki:latest .
k3d image import graphwiki:latest -c graphwiki
kubectl rollout restart deployment/graphwiki -n graphwiki
```

Access at **http://wiki.localhost:8080** (requires `/etc/hosts` entry).

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Setup guide for local dev and k8s deployment |
| [Architecture](docs/architecture.md) | System design and component overview |
| [TODO](TODO.md) | Current tasks and roadmap |
| [PRD: Infrastructure](docs/prd/001-infrastructure.md) | Infrastructure requirements |
| [PRD: GraphWiki MVP](docs/prd/002-graphwiki-mvp.md) | Application requirements |
| [ADR-001: k3d Approach](docs/adr/001-k3d-terraform-approach.md) | k3d Terraform decision |

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Infrastructure (k3d, Istio, Rancher, Flux) | Complete |
| Phase 2 | Wiki MVP (CRUD, Markdown, wiki links, k8s deploy) | Complete |
| Phase 3 | Graph Engine (Rust, MetaTable, backlinks, D3.js viz, WebSocket) | Complete |

See [TODO.md](TODO.md) for remaining tasks and future plans.

## License

[MIT](LICENSE)
