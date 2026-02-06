# Domain: Testing

**Owner:** TBD
**Status:** Partial implementation
**Language:** Python (pytest), Rust (cargo test)

## Scope

Testing strategy and infrastructure across all domains:
- Unit tests
- Integration tests
- End-to-end tests
- Performance tests
- CI/CD integration

**Not in scope:** Application features (tested by this domain)

## Current State

Basic test infrastructure exists:
- [x] pytest configured
- [x] pytest-asyncio for async tests
- [x] httpx for API testing
- [ ] Comprehensive test coverage
- [ ] CI/CD pipeline
- [ ] E2E tests

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── unit/
│   ├── test_parser.py    # Markdown parser tests
│   ├── test_storage.py   # FileStorage tests
│   └── test_models.py    # Model validation tests
├── integration/
│   ├── test_routes.py    # API endpoint tests
│   └── test_htmx.py      # HTMX interaction tests
├── e2e/
│   └── test_workflows.py # Full user workflows
└── performance/
    └── test_benchmarks.py # Performance benchmarks

# Rust tests (in graph-core/)
graph-core/
├── src/
│   └── *.rs              # Inline unit tests
└── tests/
    └── integration.rs    # Integration tests
```

## Testing by Domain

### Business Logic (Python)

```python
# tests/unit/test_parser.py
def test_wiki_link_existing_page(parser, storage):
    """Wiki links to existing pages get correct class."""
    storage.save_page("Target", "# Target")
    html = parser.parse("Link to [[Target]]")
    assert 'class="wiki-link"' in html
    assert 'href="/page/Target"' in html

def test_wiki_link_missing_page(parser, storage):
    """Wiki links to missing pages get missing class."""
    html = parser.parse("Link to [[Missing]]")
    assert 'class="wiki-link missing"' in html

# tests/integration/test_routes.py
@pytest.mark.asyncio
async def test_create_and_view_page(client):
    """Create a page and verify it renders."""
    response = await client.post(
        "/page/TestPage",
        data={"content": "# Hello World"}
    )
    assert response.status_code == 200

    response = await client.get("/page/TestPage")
    assert "Hello World" in response.text
```

### Graph Engine (Rust)

```rust
// src/graph.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add_page_creates_node() {
        let mut graph = WikiGraph::new();
        graph.add_page("TestPage", HashMap::new());
        assert!(graph.page_exists("TestPage"));
    }

    #[test]
    fn test_backlinks() {
        let mut graph = WikiGraph::new();
        graph.add_page("A", HashMap::new());
        graph.add_page("B", HashMap::new());
        graph.add_link("A", "B");

        let backlinks = graph.get_backlinks("B");
        assert_eq!(backlinks, vec!["A"]);
    }
}

// tests/integration.rs
use graph_core::GraphEngine;

#[test]
fn test_python_bindings() {
    // Test that PyO3 bindings work correctly
    let engine = GraphEngine::new("test_data").unwrap();
    let pages = engine.list_pages();
    assert!(pages.is_empty());
}
```

### Authentication (Python)

```python
# tests/unit/test_auth.py
def test_password_hashing():
    """Passwords are hashed and verified correctly."""
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)

# tests/integration/test_auth_routes.py
@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """Valid credentials return session cookie."""
    response = await client.post("/login", data={
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 302
    assert "session" in response.cookies

@pytest.mark.asyncio
async def test_protected_route_requires_auth(client):
    """Protected routes redirect to login."""
    response = await client.post("/page/Test", data={"content": "x"})
    assert response.status_code == 401
```

## Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path
from httpx import AsyncClient
from graphwiki.main import app
from graphwiki.core.storage import FileStorage

@pytest.fixture
def tmp_storage(tmp_path: Path) -> FileStorage:
    """Create temporary storage for tests."""
    return FileStorage(tmp_path)

@pytest.fixture
async def client(tmp_storage):
    """Create test client with temporary storage."""
    app.state.storage = tmp_storage
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_pages(tmp_storage):
    """Create sample pages for testing."""
    pages = {
        "HomePage": "# Welcome\n\nLink to [[About]]",
        "About": "# About\n\nBack to [[HomePage]]",
    }
    for name, content in pages.items():
        tmp_storage.save_page(name, content)
    return pages
```

## Coverage Goals

| Domain | Target | Current |
|--------|--------|---------|
| Business logic | 80% | TBD |
| Graph engine | 90% | N/A |
| Authentication | 85% | N/A |
| Overall | 80% | TBD |

## CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=graphwiki --cov-report=xml
      - uses: codecov/codecov-action@v4

  rust-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cd graph-core && cargo test
      - run: cd graph-core && cargo clippy -- -D warnings

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [python-tests, rust-tests]
    steps:
      - uses: actions/checkout@v4
      - run: docker-compose up -d
      - run: pytest tests/e2e/
```

## Commands

```bash
# Run all Python tests
cd src && pytest

# With coverage
pytest --cov=graphwiki --cov-report=html

# Run specific tests
pytest -k "test_parser"
pytest tests/unit/

# Stop on first failure
pytest -x

# Verbose output
pytest -v

# Rust tests
cd graph-core && cargo test

# Rust with output
cargo test -- --nocapture
```

## Test Types

### Unit Tests
- Fast, isolated
- Mock external dependencies
- Test single functions/methods
- Run on every commit

### Integration Tests
- Test component interactions
- Use real (temporary) storage
- Test API endpoints
- Run on every commit

### E2E Tests
- Full user workflows
- Run against deployed app
- Browser automation (Playwright)
- Run on PR merge

### Performance Tests
- Benchmark critical paths
- Detect regressions
- Run periodically

## Best Practices

1. **Arrange-Act-Assert** pattern for clarity
2. **One assertion per test** (when practical)
3. **Descriptive test names** that explain the scenario
4. **Test edge cases** and error conditions
5. **Don't test implementation details**, test behavior
6. **Keep tests fast** - mock slow operations
7. **Use fixtures** to reduce duplication
8. **Test the contract**, not the code

## Integration Points

| Component | Testing Approach |
|-----------|------------------|
| Graph engine (Rust) | PyO3 integration tests from Python |
| HTMX responses | Check partial HTML fragments |
| Istio routing | E2E tests against deployed app |
| File watching | Mock notify events |
