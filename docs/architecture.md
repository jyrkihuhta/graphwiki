# MeshWiki Architecture

This document describes the architecture of MeshWiki and its deployment infrastructure.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
│              (HTMX + D3.js graph visualization)                  │
└──────────┬──────────────────────────────┬───────────────────────┘
           │ HTTP/HTMX                    │ WebSocket
           ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Application                        │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Routes   │  │  Parser  │  │ Graph Wrapper │  │ WS Manager │  │
│  │ (main.py) │  │(parser.py│  │  (graph.py)   │  │(ws_manager)│  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  └─────┬──────┘  │
│       │              │               │                │          │
│       ▼              │               ▼                │          │
│  ┌──────────┐        │        ┌─────────────┐        │          │
│  │ Storage   │        │        │ graph_core  │        │          │
│  │(storage.py│◄───────┘        │ (Rust/PyO3) │◄───────┘          │
│  └────┬─────┘                  └──────┬──────┘                   │
│       │                               │                          │
└───────┼───────────────────────────────┼──────────────────────────┘
        │                               │
        ▼                               ▼
  ┌───────────┐                  ┌─────────────┐
  │ Markdown  │                  │  petgraph   │
  │   Files   │◄─── watches ────│  WikiGraph  │
  │ data/pages│                  │ (in-memory) │
  └───────────┘                  └─────────────┘
```

## Application Layer

### FastAPI Application

**Source:** `src/meshwiki/`

```
meshwiki/
├── main.py             # FastAPI app, routes, WebSocket endpoint
├── config.py           # pydantic-settings configuration
├── core/
│   ├── storage.py      # Storage abstraction + FileStorage
│   ├── parser.py       # Markdown + wiki links + MetaTable macro
│   ├── graph.py        # Rust engine wrapper (optional import)
│   ├── ws_manager.py   # WebSocket connection manager + event fanout
│   └── models.py       # Page model
├── templates/
│   ├── base.html       # Base layout
│   ├── graph.html      # Graph visualization page
│   └── page/
│       ├── view.html   # Page view with backlinks panel
│       ├── edit.html   # Page editing
│       └── list.html   # Page listing
└── static/
    ├── css/style.css   # Styles
    └── js/graph.js     # D3.js force-directed graph
```

### Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Page listing |
| GET | `/page/{name}` | View page (redirects to edit if missing) |
| GET | `/page/{name}/edit` | Edit form |
| POST | `/page/{name}` | Save page (HTMX-aware) |
| GET | `/page/{name}/raw` | Raw markdown (JSON) |
| POST | `/page/{name}/delete` | Delete page |
| GET | `/graph` | Graph visualization page |
| GET | `/api/graph` | Graph data as JSON (nodes + links) |
| WS | `/ws/graph` | WebSocket for real-time graph events |

### Storage Architecture

Abstract storage layer for future extensibility:

```python
class Storage(ABC):
    """Base class for page storage backends."""
    async def get_page(name: str) -> Page | None
    async def save_page(name: str, content: str) -> Page
    async def delete_page(name: str) -> bool
    async def list_pages() -> list[str]
    async def page_exists(name: str) -> bool
```

Current implementation: `FileStorage`
- Pages stored as `{data_dir}/{PageName}.md`
- YAML frontmatter supported for metadata
- Filename sanitization (spaces to underscores)

### Parser Architecture

Markdown processing pipeline with custom extensions:

1. **Preprocessors:**
   - `MetaTablePreprocessor` — expands `<<MetaTable(...)>>` macros into HTML tables by querying the graph engine

2. **Inline processors:**
   - `WikiLinkExtension` — `[[PageName]]` and `[[PageName|Text]]` to HTML links
   - `StrikethroughExtension` — `~~text~~` to `<del>` tags

3. **Third-party extensions:**
   - `extra` — tables, fenced code, footnotes
   - `sane_lists` — better list parsing
   - `smarty` — smart quotes and dashes
   - `toc` — table of contents
   - `pymdownx.tasklist` — checkbox task lists

Wiki links check page existence (via graph engine or filesystem fallback) to apply different CSS classes for existing vs missing pages.

### Graph Engine

The Rust graph engine (`graph-core/`) provides fast graph operations exposed to Python via PyO3.

**Architecture:**
- `WikiGraph` built on `petgraph::DiGraph` — directed graph of pages and links
- YAML frontmatter parsed for metadata (via `serde_yaml`)
- Wiki links extracted from Markdown (via `pulldown-cmark`)
- File watcher (`notify-debouncer-mini`) for live updates with 500ms debounce
- Thread-safe graph access via `Arc<Mutex<WikiGraph>>`
- Event queue (`GraphEvent` enum) for change notifications

**Rust modules:**

| Module | Purpose |
|--------|---------|
| `lib.rs` | PyO3 entry point, `GraphEngine` class |
| `graph.rs` | `WikiGraph` using petgraph |
| `parser.rs` | Frontmatter + wiki link extraction |
| `models.rs` | `PageNode`, `WikiLink` structs |
| `query.rs` | `Filter` enum, `query()`, `metatable()` |
| `events.rs` | `GraphEvent` enum, `EventQueue` |
| `watcher.rs` | `FileWatcher` with notify crate |

**Python wrapper** (`core/graph.py`):
- Optional import — app works without `graph_core` installed
- Singleton `GraphEngine` initialized on FastAPI startup
- `init_engine()` / `shutdown_engine()` lifecycle management
- Falls back to filesystem for `page_exists()` when engine unavailable

### WebSocket and Real-time Updates

**Connection Manager** (`core/ws_manager.py`):
- Singleton `ConnectionManager` with per-client `asyncio.Queue` fanout
- Background task polls `graph_core.poll_events()` at 0.5s intervals
- Events broadcast to all connected clients as JSON
- Auto-cleanup on client disconnect

**Client** (`static/js/graph.js`):
- D3.js v7 force-directed graph
- WebSocket connection with auto-reconnect
- Live node/link additions and removals
- Click-to-navigate, drag, zoom/pan

## Infrastructure Layer

### Kubernetes (k3d)

Local Kubernetes cluster running in Docker containers:

- 1 server node (control plane)
- 2 agent nodes (workers)
- Traefik disabled (using Istio instead)
- Load balancer exposing ports 8080 (HTTP) and 8443 (HTTPS)

**Terraform:** `infra/local/main.tf`

### Istio Service Mesh

Provides ingress routing:

- `istio-base` — CRDs and cluster-wide resources
- `istiod` — Control plane
- `istio-ingress` — Gateway for external traffic

Routing configured via Gateway and VirtualService resources.

**Terraform:** `infra/local/istio.tf`

### Rancher

Cluster management UI accessible at https://rancher.localhost:8443

- Installed via Helm (rancher-latest repo)
- Uses cert-manager for TLS
- Single-cluster deployment

**Terraform:** `infra/local/rancher.tf`

### Flux GitOps

Continuous deployment from Git repository:

```
deploy/
├── flux/
│   └── flux-system/
│       ├── gotk-components.yaml  # Flux controllers
│       ├── gotk-sync.yaml        # Git repository source
│       ├── kustomization.yaml    # Flux system kustomization
│       └── apps.yaml             # Reference to apps/
└── apps/
    ├── kustomization.yaml        # All applications
    ├── test-app/                 # Test application
    └── meshwiki/                # MeshWiki application
```

Push to `main` branch triggers automatic deployment.

## Deployment

### Container

**Dockerfile:** `Dockerfile` (repo root, multi-stage build)

- **Stage 1 (`rust-builder`):** Installs Rust + Maturin, compiles `graph_core` wheel from `graph-core/`
- **Stage 2 (runtime):** Installs Python deps + graph_core wheel, copies application code

```bash
docker build -t meshwiki:latest .
```

### Kubernetes Resources

**Manifests:** `deploy/apps/meshwiki/`

| Resource | Description |
|----------|-------------|
| `namespace.yaml` | `meshwiki` namespace |
| `deployment.yaml` | Pod spec with volume mount |
| `service.yaml` | ClusterIP service on port 80 |
| `pvc.yaml` | PersistentVolumeClaim for wiki data |
| `virtualservice.yaml` | Istio routing for wiki.localhost |

### Build & Deploy Workflow

```bash
# Build image (from repo root)
docker build -t meshwiki:latest .

# Import to k3d
k3d image import meshwiki:latest -c meshwiki

# Restart deployment (picks up new image)
kubectl rollout restart deployment/meshwiki -n meshwiki
```

Or push to Git and let Flux handle it (requires image registry).

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MESHWIKI_DATA_DIR` | `data/pages` | Storage directory |
| `MESHWIKI_DEBUG` | `false` | Debug mode |
| `MESHWIKI_APP_TITLE` | `MeshWiki` | App title |
| `MESHWIKI_GRAPH_WATCH` | `true` | Enable file watching for live updates |

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| k3d Terraform | `null_resource` + CLI | Provider unreliable ([ADR-001](adr/001-k3d-terraform-approach.md)) |
| Istio CRDs | `kubectl apply` via null_resource | Terraform CRD validation issues |
| Storage | Abstract class + FileStorage | Prepare for future database backend |
| Frontend | HTMX + Jinja2 + D3.js | Server-rendered, D3 for graph visualization |
| Graph engine | Rust + PyO3 | Performance for graph operations, optional dependency |
| Real-time | WebSocket + asyncio fanout | Per-client queue, 0.5s poll interval |

## URLs

| URL | Service |
|-----|---------|
| http://wiki.localhost:8080 | MeshWiki |
| https://rancher.localhost:8443 | Rancher |
| http://test.localhost:8080 | Test application |

## Future Considerations

### Search

Options:
- SQLite FTS for simple full-text search
- Meilisearch for advanced features

### Authentication

Options:
- OAuth2 (GitHub, Google)
- Simple username/password with sessions

### Graph Persistence

Serialize the in-memory graph to disk for fast startup instead of rebuilding from files on every launch.
