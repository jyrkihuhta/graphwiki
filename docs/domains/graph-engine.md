# Domain: Graph Engine

**Owner:** TBD
**Status:** All 6 milestones complete (104 tests passing)
**Language:** Rust (PyO3/Maturin)

## Scope

The Rust-based graph engine responsible for:
- Reading and watching Markdown files
- Parsing files to extract links and frontmatter metadata
- Building and maintaining an in-memory graph (petgraph)
- Providing query APIs for MetaTable-style queries
- Pushing real-time updates for graph visualization

**Not in scope:** HTTP routing, HTML rendering, user authentication (handled by Python layer)

## Current Implementation Status

| Milestone | Status | Description |
|-----------|--------|-------------|
| 1. Rust Foundation | ✅ Complete | Maturin setup, PyO3 bindings, builds successfully |
| 2. Graph Core | ✅ Complete | petgraph, frontmatter/link parsing, backlinks/outlinks |
| 3. Query Engine | ✅ Complete | Filter enum, query(), metatable() - 39 tests |
| 4. File Watching | ✅ Complete | notify-debouncer-mini, GraphEvent, poll_events() - 18 tests |
| 5. Python Integration | ✅ Complete | `core/graph.py` wrapper, backlinks panel, MetaTable macro, 21 tests |
| 6. Visualization | ✅ Complete | WebSocket fanout, D3.js force graph, `/graph` page, 13 tests |

**Verified working:**
```python
from graph_core import GraphEngine, PyFilter
engine = GraphEngine('/path/to/wiki/pages')
engine.rebuild()

# Basic queries
print(engine.page_count())          # 4
print(engine.get_backlinks("Home")) # ['OtherPage']

# MetaTable queries
results = engine.query([PyFilter.equals("status", "draft")])
table = engine.metatable([PyFilter.has_key("tags")], ["name", "status"])

# File watching
engine.start_watching()
events = engine.poll_events()  # PageCreated, PageUpdated, etc.
engine.stop_watching()
```

## Architecture

```
┌─────────────────────────────────────┐
│         Python (FastAPI)            │
│   Web routes, templates, HTMX       │
└──────────────┬──────────────────────┘
               │ PyO3 bindings
               ▼
┌─────────────────────────────────────┐
│          Rust (graph-core)          │
│  - File reading/watching (notify)   │
│  - Markdown parsing (pulldown-cmark)│
│  - Graph storage (petgraph)         │
│  - Query engine                     │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Markdown Files              │
│   (source of truth)                 │
└─────────────────────────────────────┘
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Rust with PyO3 | Performance for graph operations, learning opportunity |
| Graph library | petgraph | Battle-tested, efficient traversals |
| Markdown parser | pulldown-cmark or comrak | 10-50x faster than Python markdown |
| File watching | notify crate | Cross-platform, reliable |
| Build tool | Maturin | Best PyO3 build experience |
| Persistence | In-memory first | Start simple, add serialization later |

## Data Model

### Graph Structure

```rust
// Nodes represent wiki pages
struct PageNode {
    name: String,
    file_path: PathBuf,
    metadata: HashMap<String, Vec<String>>,  // Frontmatter key-values
    last_modified: SystemTime,
}

// Edges represent wiki links
struct WikiLink {
    from: NodeIndex,
    to: NodeIndex,
    display_text: Option<String>,  // [[Page|Display Text]]
}

// The graph
type WikiGraph = petgraph::Graph<PageNode, WikiLink>;
```

### Metadata Extraction

Frontmatter YAML is parsed into node attributes:

```yaml
---
status: draft
tags:
  - rust
  - architecture
author: jhuhta
---
```

Becomes:
```rust
metadata: {
    "status": ["draft"],
    "tags": ["rust", "architecture"],
    "author": ["jhuhta"],
}
```

## Query API

Based on Graphingwiki MetaTable patterns:

### Core Queries

```rust
pub trait GraphQuery {
    /// Get all pages
    fn list_pages(&self) -> Vec<&PageNode>;

    /// Get a specific page
    fn get_page(&self, name: &str) -> Option<&PageNode>;

    /// Get pages linking to this page (backlinks)
    fn get_backlinks(&self, name: &str) -> Vec<&PageNode>;

    /// Get pages this page links to
    fn get_outlinks(&self, name: &str) -> Vec<&PageNode>;

    /// Check if a page exists
    fn page_exists(&self, name: &str) -> bool;

    /// Query pages by metadata filters
    fn query(&self, filters: Vec<Filter>) -> Vec<&PageNode>;

    /// MetaTable: query + select specific columns
    fn metatable(&self, filters: Vec<Filter>, columns: Vec<&str>) -> MetaTableResult;
}
```

### Filter Types

```rust
pub enum Filter {
    /// Exact match: status = "draft"
    Equals { key: String, value: String },

    /// Key exists (any value)
    HasKey { key: String },

    /// Value contains substring
    Contains { key: String, substring: String },

    /// Regex match
    Matches { key: String, pattern: String },

    /// Linked to specific page
    LinksTo { page: String },

    /// Has backlink from specific page
    LinkedFrom { page: String },
}
```

### Example Queries

```python
# Python side using the Rust bindings

# Get all draft pages
drafts = graph.query([Filter.equals("status", "draft")])

# Get backlinks for a page
backlinks = graph.get_backlinks("Architecture")

# MetaTable: show status and author for all pages tagged "rust"
table = graph.metatable(
    filters=[Filter.equals("tags", "rust")],
    columns=["name", "status", "author"]
)
```

## File Watching

### Behavior

1. **Startup:** Scan all `.md` files, build initial graph
2. **Runtime:** Watch for file changes via notify
3. **On change:** Re-parse affected file, update graph
4. **Manual rebuild:** API to force full rebuild

### Events

```rust
pub enum GraphEvent {
    PageCreated { name: String },
    PageUpdated { name: String },
    PageDeleted { name: String },
    LinkCreated { from: String, to: String },
    LinkRemoved { from: String, to: String },
}
```

Events are exposed to Python for real-time UI updates (WebSocket/SSE).

## Python Bindings (PyO3)

```rust
#[pyclass]
struct GraphEngine {
    graph: WikiGraph,
    watcher: FileWatcher,
}

#[pymethods]
impl GraphEngine {
    #[new]
    fn new(data_dir: &str) -> PyResult<Self>;

    fn list_pages(&self) -> Vec<PageInfo>;
    fn get_page(&self, name: &str) -> Option<PageInfo>;
    fn get_backlinks(&self, name: &str) -> Vec<String>;
    fn query(&self, filters: Vec<PyFilter>) -> Vec<PageInfo>;
    fn metatable(&self, filters: Vec<PyFilter>, columns: Vec<String>) -> PyMetaTable;
    fn rebuild(&mut self) -> PyResult<()>;

    // For real-time updates
    fn poll_events(&mut self) -> Vec<PyGraphEvent>;
}
```

## Project Structure

```
graph-core/
├── pyproject.toml        # Maturin config
├── Cargo.toml            # Rust dependencies
├── README.md             # Build instructions
├── .gitignore
├── .venv/                # Python virtual environment
├── src/
│   ├── lib.rs            # PyO3 entry point, Python bindings ✅
│   ├── graph.rs          # petgraph logic, WikiGraph ✅
│   ├── parser.rs         # Markdown parsing, link/frontmatter extraction ✅
│   ├── models.rs         # PageNode, WikiLink structs ✅
│   ├── query.rs          # Query engine, filters (Milestone 3)
│   ├── watcher.rs        # File watching (Milestone 4)
│   └── events.rs         # Graph change events (Milestone 4)
└── tests/
    ├── test_graph_engine.py  # Core engine tests (13 tests) ✅
    ├── test_query.py         # Query engine tests (39 tests) ✅
    └── test_file_watcher.py  # File watching tests (18 tests) ✅
```

### Implemented Modules

| Module | Status | Description |
|--------|--------|-------------|
| `lib.rs` | ✅ Complete | PyO3 bindings, GraphEngine class with Arc<Mutex> thread safety |
| `models.rs` | ✅ Complete | PageNode, WikiLink, ParsedPage structs |
| `parser.rs` | ✅ Complete | Frontmatter parsing, wiki link extraction |
| `graph.rs` | ✅ Complete | WikiGraph with petgraph, backlinks/outlinks, incremental updates |
| `query.rs` | ✅ Complete | Filter enum (Equals, HasKey, Contains, Matches, LinksTo, LinkedFrom), query(), metatable() |
| `events.rs` | ✅ Complete | GraphEvent enum, EventQueue with thread-safe VecDeque |
| `watcher.rs` | ✅ Complete | FileWatcher with notify-debouncer-mini (500ms debounce) |

## Dependencies (Cargo.toml)

```toml
[dependencies]
pyo3 = { version = "0.23", features = ["extension-module"] }
petgraph = "0.8"
pulldown-cmark = "0.12"
notify-debouncer-mini = "0.7"  # File watching with debouncing
serde = { version = "1.0", features = ["derive"] }
serde_yaml = "0.9"
regex = "1.11"  # For Matches filter

[dev-dependencies]
tempfile = "3.15"
```

**Note:** Use `notify-debouncer-mini` instead of `notify` directly - it handles debouncing and pulls the correct notify version.

## Build Commands

```bash
cd graph-core
source ~/.cargo/env
source .venv/bin/activate
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop

# Run all Python tests (70 tests)
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_query.py -v
python -m pytest tests/test_file_watcher.py -v
```

**Notes:**
- Python 3.14 requires `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` since PyO3 0.23 doesn't officially support it yet
- File watcher tests use timing helpers (`wait_for_events`, `start_watching_and_wait`) to handle FS event latency

## Future Enhancements

### Persistence (Phase 2)
- Serialize graph to disk (sled or SQLite)
- Fast startup from cache, rebuild only on hash mismatch

### Advanced Queries
- Graph traversal queries (N-hop neighbors)
- Path finding between pages
- Clustering/community detection

### Visualization Support
- Export to DOT format for Graphviz
- JSON graph format for D3.js/Cytoscape
- Incremental updates for live visualization

## Integration Points

| Component | Integration |
|-----------|-------------|
| Python storage | Graph engine becomes source of truth for page existence |
| Templates | Backlinks panel calls `get_backlinks()` |
| MetaTable macro | Calls `metatable()` query |
| Graph visualization | Consumes `poll_events()` for live updates |

## Testing Strategy

- **Rust unit tests:** Graph operations, query logic, parser
- **Integration tests:** PyO3 bindings work correctly from Python
- **Property tests:** Fuzzing with arbitrary markdown files
- **Benchmarks:** Compare parsing speed vs Python markdown

## References

- [Graphingwiki MetaTable](http://moinmo.in/MetaDataInMoin) - Query patterns
- [petgraph docs](https://docs.rs/petgraph/) - Graph library
- [PyO3 guide](https://pyo3.rs/) - Rust-Python bindings
- [Maturin](https://www.maturin.rs/) - Build tool
