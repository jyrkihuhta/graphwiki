# GraphWiki Phase 3: Graph Engine MVP

## Overview

Phase 3 introduces the Rust-based graph engine for metadata queries and visualization.

**Goal:** Build a working MetaTable feature powered by a Rust graph backend.

## Development Approach

This project uses a **domain-based subagent architecture**:

- **This level (main conversation):** Architecture decisions, coordination, progress tracking
- **Subagents:** Focused implementation work on specific domains

### Domain Documentation

Each domain has a dedicated doc in `docs/domains/` that subagents read for context:

| Domain | Doc | Description |
|--------|-----|-------------|
| Graph Engine | `graph-engine.md` | Rust core, petgraph, PyO3 bindings |
| Business Logic | `business-logic.md` | Python wiki functionality |
| Authentication | `authentication.md` | User auth (planned) |
| Infrastructure | `infrastructure.md` | k8s, deployment |
| Observability | `observability.md` | Logging, metrics, tracing |
| Testing | `testing.md` | Test strategy, CI/CD |

### Spawning Subagents

To work on a domain, spawn a subagent with:
```
Task(subagent_type="general-purpose", prompt="Read docs/domains/<domain>.md and implement <task>")
```

The agent reads the domain doc for context and works autonomously.

## Milestones

### Milestone 1: Rust Foundation ✅ COMPLETE
Set up the Rust project structure and basic PyO3 integration.

- [x] Initialize `graph-core/` with Maturin
- [x] Set up Cargo.toml with dependencies (pyo3, petgraph, pulldown-cmark)
- [x] Create basic PyO3 module that Python can import
- [x] Add Rust build to development workflow
- [x] Document Rust development setup in getting-started.md

**Build commands:**
```bash
cd graph-core
source ~/.cargo/env
source .venv/bin/activate
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop
```

Note: Python 3.14 requires `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1`

### Milestone 2: Graph Core ✅ COMPLETE
Implement the core graph data structure and page parsing.

- [x] Define `PageNode` and `WikiLink` structs (`src/models.rs`)
- [x] Implement `WikiGraph` using petgraph (`src/graph.rs`)
- [x] Parse markdown files to extract frontmatter (YAML) (`src/parser.rs`)
- [x] Parse markdown to extract wiki links (`[[Page]]` syntax)
- [x] Build graph from directory of markdown files
- [x] Implement `list_pages()`, `get_page()`, `page_exists()`
- [x] Implement `get_backlinks()`, `get_outlinks()`
- [x] Write Python integration tests (13 tests passing)

**Verified working:**
```python
from graph_core import GraphEngine
engine = GraphEngine('/path/to/pages')
engine.rebuild()
engine.get_backlinks("SomePage")  # Returns pages linking to SomePage
```

### Milestone 3: Query Engine ✅ COMPLETE
Implement MetaTable-style queries on metadata.

- [x] Define `Filter` enum (Equals, HasKey, Contains, Matches, LinksTo, LinkedFrom)
- [x] Implement `query(filters)` - filter pages by metadata
- [x] Implement `metatable(filters, columns)` - query with column selection
- [x] Expose query API to Python via PyO3 (PyFilter wrapper class)
- [x] Write tests for query functionality (39 query tests)

**Verified working:**
```python
from graph_core import GraphEngine, PyFilter
engine = GraphEngine('/path/to/wiki')
engine.rebuild()

# Query with filters
results = engine.query([PyFilter.equals("status", "draft")])

# MetaTable with columns
table = engine.metatable([PyFilter.has_key("tags")], ["name", "status", "tags"])
for row in table:
    print(row.get("name"), row.get("tags"))
```

### Milestone 4: File Watching ✅ COMPLETE
Add live updates when files change.

- [x] Integrate `notify-debouncer-mini` crate (500ms debounce)
- [x] Update graph incrementally on file create/modify/delete
- [x] Define `GraphEvent` enum (PageCreated, PageUpdated, PageDeleted, LinkCreated, LinkRemoved)
- [x] Thread-safe graph with Arc<Mutex<WikiGraph>>
- [x] Expose `start_watching()`, `stop_watching()`, `poll_events()` to Python
- [x] Write tests for file watching behavior (18 watcher tests)

**Verified working:**
```python
from graph_core import GraphEngine
engine = GraphEngine('/path/to/wiki')
engine.rebuild()
engine.start_watching()

# Poll for events (non-blocking)
events = engine.poll_events()
for event in events:
    print(f"{event.event_type()}: {event.page_name()}")

engine.stop_watching()
```

### Milestone 5: Python Integration ✅ COMPLETE
Integrate the Rust engine with the FastAPI application.

- [x] Import graph-core module in graphwiki (`core/graph.py` with optional import)
- [x] Initialize GraphEngine on app startup (FastAPI lifespan)
- [x] Replace `page_exists()` calls to use graph engine (falls back to filesystem)
- [x] Add backlinks panel to page view template
- [x] Implement `<<MetaTable(...)>>` macro in parser (Markdown preprocessor)
- [x] Add configuration for graph engine data directory (`GRAPHWIKI_GRAPH_WATCH`)

**Key files:**
- `src/graphwiki/core/graph.py` - Engine wrapper (optional import, singleton, init/shutdown)
- `src/graphwiki/core/parser.py` - MetaTablePreprocessor + MetaTableExtension
- `src/tests/test_graph_integration.py` - 21 tests

**MetaTable syntax:**
```markdown
<<MetaTable(status=draft, ||name||status||author||)>>
```
Filter operators: `key=value` (equals), `key~=sub` (contains), `key/=regex` (matches)

### Milestone 6: Real-time Visualization ✅ COMPLETE
Push graph updates to the browser for live visualization.

- [x] Add WebSocket endpoint for graph events (`/ws/graph`)
- [x] Add JSON API for graph snapshot (`/api/graph`)
- [x] Create D3.js force-directed graph visualization
- [x] Add dedicated `/graph` page with full-width layout
- [x] WebSocket connection manager with per-client event fanout
- [x] Live node/link additions and removals
- [x] Click-to-navigate, drag, zoom/pan
- [x] Auto-reconnect on WebSocket disconnect

**Key files:**
- `src/graphwiki/core/ws_manager.py` - ConnectionManager with asyncio.Queue fanout
- `src/graphwiki/static/js/graph.js` - D3.js v7 force graph
- `src/graphwiki/templates/graph.html` - Graph page template
- `src/tests/test_graph_visualization.py` - 13 tests

## Domain Tasks

### Graph Engine
See Milestones 1-4 above.

### Business Logic
- [x] Add backlinks panel to page view
- [x] Implement MetaTable macro parsing
- [ ] Display frontmatter metadata in page view
- [x] Update wiki link rendering to use graph engine

### Authentication
- [ ] Design auth approach (session vs JWT vs OAuth)
- [ ] Implement user model and storage
- [ ] Add login/logout routes
- [ ] Protect edit/delete routes
- [ ] Add user info to templates

### Infrastructure
- [ ] Add Rust build stage to Dockerfile
- [ ] Update CI/CD for Rust tests
- [ ] Consider multi-stage build optimization

### Observability
- [ ] Add structured logging (structlog)
- [ ] Add basic metrics endpoint
- [ ] Document logging conventions

### Testing
- [x] Set up Rust test infrastructure (graph-core)
- [x] Add PyO3 integration tests (70 tests total: 13 engine + 39 query + 18 watcher)
- [x] Add Python integration tests (34 tests: 21 Milestone 5 + 13 Milestone 6)
- [x] Add end-to-end smoke tests (25 tests: full CRUD lifecycle, wiki links, frontmatter, HTMX, graph routes)
- [ ] Achieve 80% coverage on business logic
- [ ] Set up CI pipeline (GitHub Actions)

## Priority Order

1. ~~**Rust Foundation** (Milestone 1)~~ ✅ Complete
2. ~~**Graph Core** (Milestone 2)~~ ✅ Complete
3. ~~**Query Engine** (Milestone 3)~~ ✅ Complete - MetaTable queries working
4. ~~**File Watching** (Milestone 4)~~ ✅ Complete - Live graph updates
5. ~~**Python Integration** (Milestone 5)~~ ✅ Complete - Backlinks, MetaTable macro, graph-backed page_exists
6. ~~**Visualization** (Milestone 6)~~ ✅ Complete - D3.js force graph, WebSocket, live updates

## Success Criteria

MVP is complete when:
- [x] Rust graph engine builds and imports in Python
- [x] Backlinks panel shows pages linking to current page
- [x] MetaTable query API + macro integration complete
- [x] Graph updates when files change (file watching complete)
- [x] Real-time graph visualization with WebSocket
- [x] All tests pass (129 tests: 70 graph-core + 59 integration)

## Notes

- Start with in-memory graph, add persistence later
- Manual rebuild is acceptable for MVP; file watching is enhancement
- Focus on correctness over performance initially
- Keep Python as the primary interface; Rust is an implementation detail
- Python 3.14 requires ABI3 forward compatibility flag for PyO3
