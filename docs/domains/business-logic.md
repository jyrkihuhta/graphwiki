# Domain: Business Logic

**Owner:** TBD
**Status:** MVP + graph integration complete
**Language:** Python

## Scope

Core wiki functionality in the Python/FastAPI layer:
- Page CRUD operations
- Markdown rendering
- Wiki link processing
- Template rendering
- HTMX interactions

**Not in scope:** Graph queries (graph-engine), auth (authentication), deployment (infrastructure)

## Current State

MVP is complete with:
- [x] View, create, edit, delete pages
- [x] Markdown rendering with extensions
- [x] Wiki links (`[[Page]]` and `[[Page|Text]]`)
- [x] Missing page detection and styling
- [x] Task lists, tables, code blocks, strikethrough
- [x] HTMX-powered interactions

## Architecture

```
src/graphwiki/
├── main.py           # FastAPI routes + WebSocket endpoint
├── config.py         # Settings (pydantic-settings)
├── core/
│   ├── storage.py    # Abstract Storage + FileStorage
│   ├── parser.py     # Markdown + WikiLink + MetaTable extensions
│   ├── models.py     # Page model
│   ├── graph.py      # Graph engine wrapper (optional import)
│   └── ws_manager.py # WebSocket connection manager + event fanout
├── templates/        # Jinja2 templates (incl. graph.html)
├── static/css/       # CSS
├── static/js/        # graph.js (D3.js visualization)
└── tests/            # Integration tests (34 tests)
```

## Design Patterns

### Storage Abstraction
```python
class Storage(ABC):
    async def get_page(name: str) -> Page | None
    async def save_page(name: str, content: str) -> Page
    async def delete_page(name: str) -> bool
    async def list_pages() -> list[str]
    async def page_exists(name: str) -> bool
```

Current implementation: `FileStorage` (files on disk)
Future: May delegate existence checks to graph engine

### Parser Pipeline
```
Raw Markdown → [Extensions] → HTML
                    ↓
         - extra (tables, code)
         - sane_lists
         - smarty (typography)
         - toc
         - pymdownx.tasklist
         - WikiLinkExtension (custom)
         - StrikethroughExtension (custom)
```

### HTMX Integration
- Check `HX-Request` header for partial responses
- Return fragments for dynamic updates
- Full page for direct navigation

## Completed Enhancements

### Backlinks Panel ✅
Displays pages linking to current page in `view.html`:
```python
# In view_page route
backlinks = sorted(engine.get_backlinks(name))
```

### MetaTable Macro ✅
Query pages by metadata, rendered as inline HTML table:
```markdown
<<MetaTable(status=draft, ||name||status||author||)>>
```
Filter operators: `key=value` (equals), `key~=sub` (contains), `key/=regex` (matches).
Implemented as Markdown `Preprocessor` in `parser.py`.

### Graph Visualization ✅
Interactive D3.js force graph at `/graph` with WebSocket live updates.

## Planned Enhancements

### Search
Full-text search across page content:
- Simple: grep-style search
- Advanced: integrate with graph engine metadata

### Frontmatter Display
Show parsed YAML frontmatter in page view:
```yaml
---
status: published
author: jhuhta
---
```

## Integration Points

| Component | Status | Implementation |
|-----------|--------|----------------|
| Page existence | ✅ Done | `graph_engine.page_exists()` with filesystem fallback |
| Backlinks | ✅ Done | `graph_engine.get_backlinks()` in view route |
| MetaTable | ✅ Done | `graph_engine.metatable()` via MetaTablePreprocessor |
| Visualization | ✅ Done | `/api/graph` + `/ws/graph` + D3.js |
| Search | Not implemented | graph_engine.query() |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAPHWIKI_DATA_DIR` | `data/pages` | Page storage directory |
| `GRAPHWIKI_DEBUG` | `false` | Debug mode |
| `GRAPHWIKI_APP_TITLE` | `GraphWiki` | Application title |
| `GRAPHWIKI_GRAPH_WATCH` | `true` | Enable file watching for graph engine |

## Code Conventions

- Async/await for all I/O operations
- Type hints on all function signatures
- Google-style docstrings for public functions
- HTTPException with appropriate status codes
- Jinja2 auto-escaping (careful with `| safe`)

## Testing Strategy

- Unit tests for parser, storage operations
- Integration tests for API routes (httpx TestClient)
- Test wiki link rendering (existing vs missing pages)
- Test HTMX partial responses
