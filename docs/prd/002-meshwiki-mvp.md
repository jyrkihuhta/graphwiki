# PRD: MeshWiki MVP

**Status:** Complete
**Date:** 2026-01-27

## Problem

Existing wiki platforms either lack modern UX (MoinMoin), require cloud subscriptions (Notion, Confluence), or focus purely on personal use (Obsidian). We need a self-hosted wiki that combines:

- Plaintext-first editing (like Obsidian)
- Wiki linking for knowledge graphs
- Metatables for structured data queries (from Graphingwiki)
- Modern, fast user experience

## Goals

Build an MVP wiki platform with:

- Markdown pages stored as files on disk
- Wiki links with `[[PageName]]` syntax
- Clean, responsive web interface
- HTMX for snappy interactions without heavy JavaScript
- Kubernetes-native deployment

## Non-Goals (for MVP)

- User authentication and access control
- Version history / page revisions
- Full-text search
- ~~Metatables~~ — implemented in Phase 3 (Milestone 3 + 5)
- ~~Graph visualization~~ — implemented in Phase 3 (Milestone 6)
- Real-time collaboration

## Architecture

### Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Backend | FastAPI (Python 3.12+) | Async, fast, good ecosystem |
| Frontend | Jinja2 + HTMX | Server-rendered, minimal JS |
| Storage | Markdown files | Simple, portable, git-friendly |
| Styling | Custom CSS | Keep it simple, no framework bloat |
| Deployment | Docker + Kubernetes | Matches infrastructure goals |

### Project Structure

```
src/meshwiki/
├── __init__.py
├── main.py              # FastAPI app and routes
├── config.py            # Settings via pydantic-settings
├── core/
│   ├── storage.py       # Abstract storage + FileStorage
│   ├── parser.py        # Markdown + wiki link parsing
│   └── models.py        # Pydantic models
├── templates/
│   ├── base.html        # Base layout
│   └── page/
│       ├── view.html    # Page viewing
│       ├── edit.html    # Page editing
│       └── list.html    # Page listing
└── static/css/
    └── style.css        # Styles
```

### Storage Layer

Abstract `Storage` base class allows future backends (database, S3):

```python
class Storage(ABC):
    async def get_page(name: str) -> Page | None
    async def save_page(name: str, content: str) -> Page
    async def delete_page(name: str) -> bool
    async def list_pages() -> list[str]
    async def page_exists(name: str) -> bool
```

`FileStorage` implementation:
- Pages stored as `data/pages/{PageName}.md`
- Spaces in names converted to underscores in filenames
- Optional YAML frontmatter for metadata (future Metatables support)

### Markdown Parser

Uses Python `markdown` library with extensions:

- `extra` - tables, fenced code, footnotes, etc.
- `sane_lists` - better list handling
- `smarty` - smart quotes and dashes
- `toc` - table of contents generation
- `pymdownx.tasklist` - checkbox task lists
- Custom `WikiLinkExtension` - `[[PageName]]` and `[[PageName|Display Text]]`
- Custom `StrikethroughExtension` - `~~strikethrough~~`

Wiki links render with different styles for existing vs missing pages.

### Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Page listing |
| GET | `/page/{name}` | View page (redirects to edit if missing) |
| GET | `/page/{name}/edit` | Edit form |
| POST | `/page/{name}` | Save page (HTMX-aware) |
| GET | `/page/{name}/raw` | Raw markdown (JSON) |
| POST | `/page/{name}/delete` | Delete page |

### Configuration

Environment variables with `MESHWIKI_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `MESHWIKI_DATA_DIR` | `data/pages` | Page storage directory |
| `MESHWIKI_DEBUG` | `false` | Debug mode |
| `MESHWIKI_APP_TITLE` | `MeshWiki` | Application title |
| `MESHWIKI_GRAPH_WATCH` | `true` | Enable file watching for live graph updates |

## Requirements

### Implemented

- [x] View wiki pages rendered as HTML
- [x] Edit pages with plaintext Markdown editor
- [x] Create new pages (from edit or clicking missing links)
- [x] Delete pages
- [x] Wiki links: `[[PageName]]` and `[[PageName|Display Text]]`
- [x] Missing page links styled differently
- [x] Full Markdown support (tables, code blocks, lists, etc.)
- [x] Task lists with checkboxes
- [x] Strikethrough text
- [x] Page listing / navigation
- [x] Docker containerization
- [x] Kubernetes deployment via Flux

### Future Enhancements

- [ ] YAML frontmatter metadata display
- [x] Backlinks panel (pages linking to current page) — Phase 3 Milestone 5
- [ ] Search functionality
- [x] MetaTable queries — Phase 3 Milestone 3 + 5
- [x] Graph visualization — Phase 3 Milestone 6
- [ ] Version history
- [ ] User accounts

## Success Criteria

- [x] Can create, view, edit, and delete wiki pages
- [x] Wiki links work and distinguish existing/missing pages
- [x] Markdown renders correctly including tables, code, lists
- [x] Application deploys to Kubernetes via GitOps
- [x] Accessible via Istio ingress at wiki.localhost:8080

## Dependencies

```toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "jinja2>=3.1",
    "markdown>=3.5",
    "pymdown-extensions>=10.0",
    "pydantic-settings>=2.0",
    "python-multipart>=0.0.9",
    "pyyaml>=6.0",
]
```
