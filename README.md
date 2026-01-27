# GraphWiki

A modern wiki and collaboration platform inspired by MoinMoin, Graphingwiki, and Obsidian.

## Features

- **Wiki pages** - Markdown content with full formatting support
- **Wiki links** - `[[PageName]]` and `[[PageName|Display Text]]` syntax
- **Modern UI** - Clean, responsive interface with HTMX interactions
- **Kubernetes-native** - Deployed via GitOps with Flux
- **File-based storage** - Pages stored as Markdown files, easy to backup and version

## Quick Start

**Local development:**

```bash
cd src
pip install -e .
mkdir -p data/pages
uvicorn graphwiki.main:app --reload
```

Access at http://localhost:8000

**Kubernetes deployment:** See [Getting Started](docs/getting-started.md)

## Project Structure

```
graphwiki/
├── docs/                    # Documentation
│   ├── prd/                 # Product requirements
│   ├── adr/                 # Architecture decisions
│   └── research/            # Background research
├── infra/local/             # Terraform (k3d + Rancher + Istio)
├── src/graphwiki/           # Python application
├── deploy/
│   ├── flux/                # Flux GitOps config
│   └── apps/                # Kubernetes manifests
└── data/pages/              # Wiki content (gitignored)
```

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Setup guide for local dev and k8s |
| [Architecture](docs/architecture.md) | System design and components |
| [PRD: Infrastructure](docs/prd/001-infrastructure.md) | Infrastructure requirements |
| [PRD: GraphWiki MVP](docs/prd/002-graphwiki-mvp.md) | Application requirements |
| [ADR-001: k3d Approach](docs/adr/001-k3d-terraform-approach.md) | k3d Terraform decision |

## Current Status

**Phase 1: Infrastructure** - Complete
- k3d Kubernetes cluster via Terraform
- Rancher cluster management
- Istio service mesh
- Flux GitOps deployment

**Phase 2: GraphWiki MVP** - Complete
- Wiki page CRUD operations
- Markdown rendering with full syntax support
- Wiki links with missing page detection
- Task lists, tables, code blocks, strikethrough
- Kubernetes deployment

**Phase 3: Enhanced Features** - Planned
- Metatables (structured data queries)
- Search
- Graph visualization
- Version history

## Tech Stack

- **Backend:** FastAPI (Python 3.12+)
- **Frontend:** Jinja2 templates + HTMX
- **Storage:** Markdown files on disk
- **Infrastructure:** k3d, Istio, Rancher, Flux, Terraform

## URLs (local k8s)

| URL | Service |
|-----|---------|
| http://wiki.localhost:8080 | GraphWiki |
| https://rancher.localhost:8443 | Rancher |

## License

MIT
