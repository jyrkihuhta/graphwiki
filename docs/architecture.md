# GraphWiki Architecture

This document describes the current architecture of GraphWiki and its deployment infrastructure.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    k3d Load Balancer                             │
│                   (localhost:8080/8443)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Istio Ingress Gateway                           │
│            (Gateway + VirtualService routing)                    │
├─────────────────────────────────────────────────────────────────┤
│  wiki.localhost:8080  →  graphwiki service                       │
│  rancher.localhost:8443  →  rancher service                      │
│  test.localhost:8080  →  test-app service                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  GraphWiki  │  │   Rancher   │  │  Test App   │
│   (Pod)     │  │   (Pods)    │  │   (Pod)     │
└──────┬──────┘  └─────────────┘  └─────────────┘
       │
       ▼
┌─────────────┐
│     PVC     │
│ (wiki data) │
└─────────────┘
```

## Infrastructure Layer

### Kubernetes (k3d)

Local Kubernetes cluster running in Docker containers:

- 1 server node (control plane)
- 2 agent nodes (workers)
- Traefik disabled (using Istio instead)
- Load balancer exposing ports 8080 (HTTP) and 8443 (HTTPS)

**Terraform:** `infra/local/main.tf`

### Istio Service Mesh

Provides ingress routing and future observability:

- `istio-base` - CRDs and cluster-wide resources
- `istiod` - Control plane
- `istio-ingress` - Gateway for external traffic

Routing configured via Gateway and VirtualService resources.

**Terraform:** `infra/local/istio.tf`

### Rancher

Cluster management UI accessible at https://rancher.localhost:8443

- Installed via Helm (rancher-latest repo)
- Uses cert-manager for TLS
- Single-cluster deployment (Rancher on workload cluster)

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
    └── graphwiki/                # GraphWiki application
```

Push to `main` branch triggers automatic deployment.

## Application Layer

### GraphWiki Application

**Stack:**
- FastAPI (Python 3.12+) - async web framework
- Jinja2 - server-side templates
- HTMX - dynamic updates without heavy JavaScript
- Markdown + pymdown-extensions - content parsing

**Source:** `src/graphwiki/`

```
graphwiki/
├── main.py         # FastAPI app, routes
├── config.py       # pydantic-settings configuration
├── core/
│   ├── storage.py  # Storage abstraction + FileStorage
│   ├── parser.py   # Markdown + wiki link parsing
│   └── models.py   # Page model
├── templates/      # Jinja2 HTML templates
└── static/         # CSS, JS assets
```

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
- Filename sanitization (spaces → underscores)

### Parser Architecture

Markdown processing pipeline:

1. **Input:** Raw Markdown with wiki links
2. **Extensions:**
   - `extra` - tables, fenced code, footnotes
   - `sane_lists` - better list parsing
   - `smarty` - typography (quotes, dashes)
   - `toc` - table of contents
   - `pymdownx.tasklist` - checkbox lists
   - `WikiLinkExtension` - `[[PageName]]` → HTML links
   - `StrikethroughExtension` - `~~text~~` → `<del>`
3. **Output:** HTML string

Wiki links check page existence to apply different CSS classes.

## Deployment

### Container

**Dockerfile:** `src/Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY graphwiki/ ./graphwiki/
RUN mkdir -p /data/pages
CMD ["uvicorn", "graphwiki.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Resources

**Manifests:** `deploy/apps/graphwiki/`

| Resource | Description |
|----------|-------------|
| `namespace.yaml` | `graphwiki` namespace |
| `deployment.yaml` | Pod spec with volume mount |
| `service.yaml` | ClusterIP service on port 80 |
| `pvc.yaml` | PersistentVolumeClaim for wiki data |
| `virtualservice.yaml` | Istio routing for wiki.localhost |

### Build & Deploy Workflow

```bash
# Build image
cd src && docker build -t graphwiki:latest .

# Import to k3d
k3d image import graphwiki:latest -c graphwiki

# Restart deployment (picks up new image)
kubectl rollout restart deployment/graphwiki -n graphwiki
```

Or push to Git and let Flux handle it (requires image registry).

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAPHWIKI_DATA_DIR` | `data/pages` | Storage directory |
| `GRAPHWIKI_DEBUG` | `false` | Debug mode |
| `GRAPHWIKI_APP_TITLE` | `GraphWiki` | App title |

### Kubernetes ConfigMap (future)

Currently using environment variables in Deployment spec.

## URLs

| URL | Service |
|-----|---------|
| http://wiki.localhost:8080 | GraphWiki |
| https://rancher.localhost:8443 | Rancher |
| http://test.localhost:8080 | Test application |

## Future Considerations

### Metatables

Will require:
- YAML frontmatter parsing (already supported in storage)
- Query language for metadata
- Table rendering component

### Search

Options:
- SQLite FTS for simple full-text search
- Elasticsearch/Meilisearch for advanced features

### Authentication

Options:
- Rancher authentication integration
- OAuth2 (GitHub, Google)
- Simple username/password with sessions
