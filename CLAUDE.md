# Claude Code Guidelines for GraphWiki

## Project Overview

GraphWiki is a modern wiki platform inspired by MoinMoin, Graphingwiki, and Obsidian. It combines:
- File-based Markdown storage
- Wiki links (`[[PageName]]` syntax)
- Kubernetes-native deployment with GitOps

**Tech Stack:** FastAPI, Jinja2, HTMX, Python 3.12+, k3d, Istio, Rancher, Flux

## Key Documentation

Read these for full context:
- `docs/getting-started.md` - Setup and deployment guide
- `docs/architecture.md` - System design and components
- `docs/prd/002-graphwiki-mvp.md` - Application requirements and status
- `docs/prd/001-infrastructure.md` - Infrastructure requirements

## Project Structure

```
src/graphwiki/          # Python application
  main.py               # FastAPI routes
  config.py             # Settings (GRAPHWIKI_* env vars)
  core/storage.py       # FileStorage implementation
  core/parser.py        # Markdown + wiki link parsing
  templates/            # Jinja2 templates
  static/               # CSS

infra/local/            # Terraform for local k8s
  main.tf               # k3d cluster (uses null_resource, not provider)
  istio.tf              # Istio service mesh
  rancher.tf            # Rancher installation

deploy/apps/graphwiki/  # K8s manifests (Flux deploys these)
deploy/flux/            # Flux GitOps configuration
```

## Common Commands

```bash
# Local development (no k8s)
cd src && uvicorn graphwiki.main:app --reload

# Build and deploy to k8s
cd src && docker build -t graphwiki:latest .
k3d image import graphwiki:latest -c graphwiki
kubectl rollout restart deployment/graphwiki -n graphwiki

# Check deployment
kubectl get pods -n graphwiki
kubectl logs -f deployment/graphwiki -n graphwiki

# Terraform (infrastructure)
cd infra/local && terraform apply

# Flux (force sync)
flux reconcile kustomization apps --with-source
```

## URLs (local k8s)

- http://wiki.localhost:8080 - GraphWiki
- https://rancher.localhost:8443 - Rancher
- http://test.localhost:8080 - Test app

Requires `/etc/hosts` entries for `*.localhost` domains.

## Code Conventions

### Python
- Use async/await for all storage operations
- Type hints required
- Settings via pydantic-settings with `GRAPHWIKI_` prefix
- Storage layer is abstract - `FileStorage` implements `Storage` ABC

### Markdown Parser
- Extensions configured in `core/parser.py`
- Wiki links: `WikiLinkExtension` (custom)
- Task lists: `pymdownx.tasklist`
- Strikethrough: `StrikethroughExtension` (custom)

### Templates
- Base template: `templates/base.html`
- HTMX for dynamic updates (check `HX-Request` header)
- Minimal custom CSS, no framework

### Kubernetes
- All apps deployed via Flux from `deploy/apps/`
- Use Kustomize structure
- Istio VirtualService for routing

## Architecture Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| k3d Terraform | `null_resource` + CLI | Provider unreliable (ADR-001) |
| Istio CRDs | `kubectl apply` via null_resource | Terraform CRD validation issues |
| Storage | Abstract class + FileStorage | Prepare for future DB backend |
| Frontend | HTMX + Jinja2 | Server-rendered, minimal JS |

## Gotchas

1. **k3d image import required** - Local images must be imported to k3d cluster
2. **Traefik disabled** - Using Istio ingress instead
3. **Flux deploys from Git** - Local manifest changes need commit+push (or manual kubectl apply)
4. **Markdown parser groups** - `SimpleTagInlineProcessor` expects text in group(2), not group(1)

## Future Work (Phase 3)

- Metatables - Query pages by YAML frontmatter metadata
- Search - Full-text search
- Graph visualization - Page link visualization
- Version history - Track page changes
- Authentication - User accounts

## Testing

```bash
cd src
pip install -e ".[dev]"
pytest
```

Tests use pytest + pytest-asyncio + httpx for async API testing.
