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

## Development Standards

### Python Style
- **PEP 8** - Follow standard Python style guide
- **Type hints** - Required for all function signatures
- **Docstrings** - Google style for public functions/classes
- **Line length** - 88 characters (Black default)
- **Imports** - Use `isort` ordering (stdlib, third-party, local)
- **Formatting** - Use `black` for consistent formatting
- **Linting** - Use `ruff` for fast linting

### Naming Conventions
- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Prefix private methods/attributes with `_`

### Error Handling
- Use specific exception types, not bare `except:`
- Raise `HTTPException` with appropriate status codes in routes
- Log errors with context before re-raising

### Testing Requirements
- **Write tests for all new features** - No feature is complete without tests
- **Test file naming** - `test_<module>.py` in `tests/` directory
- **Use pytest** - With pytest-asyncio for async code
- **Test coverage** - Aim for >80% on new code
- **Test types:**
  - Unit tests for core logic (storage, parser)
  - Integration tests for API routes (use httpx TestClient)
  - Edge cases and error conditions

Example test structure:
```python
# tests/test_storage.py
import pytest
from graphwiki.core.storage import FileStorage

@pytest.fixture
def storage(tmp_path):
    return FileStorage(tmp_path)

@pytest.mark.asyncio
async def test_save_and_get_page(storage):
    await storage.save_page("TestPage", "# Hello")
    page = await storage.get_page("TestPage")
    assert page is not None
    assert page.content == "# Hello"
```

### Code Quality Checklist
Before committing:
- [ ] Code follows PEP 8 style
- [ ] Type hints added
- [ ] Tests written and passing
- [ ] No hardcoded secrets or credentials
- [ ] Error handling is appropriate
- [ ] Docstrings for public APIs

### Git Commits
- Write clear, concise commit messages
- Use imperative mood ("Add feature" not "Added feature")
- Reference issues if applicable
- Keep commits focused and atomic

### Dependencies
- Add to `pyproject.toml` under `[project.dependencies]`
- Pin minimum versions (`>=X.Y`), not exact versions
- Dev dependencies go in `[project.optional-dependencies.dev]`

## Code Conventions

### Python Application
- Use async/await for all storage operations
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

## Security Practices

- **No secrets in code** - Use environment variables or k8s secrets
- **Validate user input** - Sanitize page names, prevent path traversal
- **No SQL injection** - Use parameterized queries (when DB is added)
- **XSS prevention** - Jinja2 auto-escapes; be careful with `| safe`
- **CSRF protection** - Use tokens for state-changing operations (future)
- **Dependencies** - Keep updated, check for vulnerabilities

## Documentation Practices

- **Update docs with code** - If behavior changes, update relevant docs
- **ADRs for decisions** - Document significant technical decisions in `docs/adr/`
- **PRDs for features** - New features should have requirements in `docs/prd/`
- **Code comments** - Explain "why", not "what" (code shows what)
- **README updates** - Keep root README current with project status

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
pytest --cov=graphwiki          # With coverage
pytest -x                        # Stop on first failure
pytest -k "test_storage"         # Run specific tests
```

Tests use pytest + pytest-asyncio + httpx for async API testing.

## Recommended Tools

```bash
# Install dev tools
pip install black ruff isort pytest pytest-asyncio pytest-cov httpx

# Format code
black src/
isort src/

# Lint
ruff check src/

# Type checking (optional)
pip install mypy
mypy src/graphwiki/
```

Add to `pyproject.toml` for consistent configuration:
```toml
[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```
