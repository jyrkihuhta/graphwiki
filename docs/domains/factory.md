# Domain: Agent Factory

**Owner:** TBD
**Status:** v1 complete (Phases 1–7), v2 in progress (Phases 8–11)
**Language:** Python (MeshWiki layer) + Python (LangGraph orchestrator)
**PRD:** `docs/prd/003-agent-factory.md`

## Scope

The autonomous agent software development factory:
- Task pages with structured frontmatter as the single source of truth
- State machine enforcing legal task transitions
- JSON API for programmatic CRUD and state transitions (used by agents)
- Outbound webhook dispatcher to notify the LangGraph orchestrator
- Inbound GitHub webhook receiver to sync PR merge events back to task state
- LangGraph orchestrator with PM and Grinder agents (future phases)

**Not in scope:** Wiki UI/rendering (business-logic), Rust graph engine (graph-engine), deployment (infrastructure)

## Current State

### Phase 1: MeshWiki Foundation ✅ (merged #32)
- [x] `src/meshwiki/core/task_machine.py` — state machine with `TASK_TRANSITIONS`, `InvalidTransitionError`, `transition_task()`
- [x] `src/meshwiki/core/webhooks.py` — `WebhookDispatcher` (async queue, HMAC-signed HTTP POST)
- [x] `src/meshwiki/api/auth.py` — `require_api_key` dependency (`MESHWIKI_FACTORY_API_KEY`)
- [x] `src/meshwiki/api/pages.py` — generic page CRUD (`GET/POST /api/v1/pages`)
- [x] `src/meshwiki/api/tasks.py` — task list + transition endpoints (`POST /api/v1/tasks/{name}/transition`)
- [x] `src/meshwiki/api/agents.py` — agent listing
- [x] Config additions: `factory_api_key`, `factory_webhook_url`, `factory_webhook_secret`, `github_webhook_secret`, `factory_enabled`

### Phase 2: GitHub Integration ✅ (merged #39)
- [x] `src/meshwiki/api/webhooks.py` — inbound GitHub webhook receiver
- [x] PR-to-task lookup via graph engine (find task page by `pr_number` or `pr_url` frontmatter)
- [x] On PR merge: auto-transition task `review → merged → done`
- [x] Factory Dashboard wiki page (`Factory_Dashboard.md`)

### Phase 3: LangGraph Orchestrator Scaffold ✅ (merged #40)
- [x] `orchestrator/` service structure with `pyproject.toml`
- [x] `factory/webhook_server.py` — FastAPI webhook receiver with HMAC verification
- [x] `factory/graph.py` — full StateGraph (11 nodes, all edges, conditional routing)
- [x] `factory/state.py` — `FactoryState` + `SubTask` TypedDicts
- [x] `factory/integrations/meshwiki_client.py` — async HTTP client

### Phase 4: PM Agent ✅ (merged #41)
- [x] `orchestrator/factory/agents/pm_agent.py` — `decompose_with_pm()` + `review_with_pm()` via Claude Opus 4
- [x] `task_intake` node — fetches task page from MeshWiki
- [x] `decompose` node — calls PM agent, writes subtask wiki pages, transitions state
- [x] `pm_review` node — PM reviews grinder PRs, approves or requests changes
- [x] `factory/integrations/github_client.py` — stub (implemented in Phase 5)

### Phase 5: Grinder Agent ✅ (merged #TBD)
- [x] `orchestrator/factory/agents/grinder_agent.py` — `grind_subtask()` agentic loop via MiniMax M2.7
- [x] `grind` node — runs grinder for a single subtask, returns updated subtask
- [x] `factory/integrations/github_client.py` — full async GitHub REST client (`get_pr`, `get_pr_diff`, `approve_pr`, `request_changes`, `close_pr`)
- [x] `collect_results` node — tallies completed/failed subtasks after fan-out
- [x] `merge_check` node — verifies all PRs merged via GitHub API
- [x] Direct-grind mode (`skip_decomposition: true` in task frontmatter)

### Phase 6: PM Chat Interface ✅ (merged #TBD)
- [x] `factory/webhook_server.py` — updated with HMAC verification and event routing
- [x] `factory/graph.py` — full StateGraph with all 11 nodes, conditional routing, interrupt points
- [x] `escalate` node — retry/abandon logic with attempt counter management
- [x] `finalize` node — transitions parent task to `done`, persists `cost_usd`

### Phase 7: End-to-End Pipeline Hardening ✅ (merged #TBD)
- [x] `orchestrator/factory/main.py` — orchestrator entrypoint (FastAPI + uvicorn, health at `/health`)
- [x] Standardized `MeshWikiClient` instantiation across all nodes (consistent no-arg constructor)
- [x] `pm_review` node fully wires diff fetching via `GitHubClient.get_pr_diff()` into `review_with_pm()`
- [x] `finalize` node completes `MeshWikiClient.transition_task(name, "done")` with `cost_usd`
- [x] `escalate` node completes retry logic: increments `attempt`, resets to `pending` for retriable subtasks
- [x] `orchestrator/tests/test_pipeline.py` — integration smoke tests (4 tests) exercising full graph with mocked I/O

## Architecture

```
src/meshwiki/
├── api/
│   ├── __init__.py      # Mounts router at /api/v1
│   ├── auth.py          # API key auth dependency
│   ├── pages.py         # Generic page CRUD
│   ├── tasks.py         # Task list + transition endpoints
│   ├── agents.py        # Agent listing
│   └── webhooks.py      # GitHub inbound webhook receiver (Phase 2)
├── core/
│   ├── task_machine.py  # State machine (TASK_TRANSITIONS, transition_task)
│   └── webhooks.py      # Outbound webhook dispatcher (async queue, HMAC)
└── config.py            # MESHWIKI_FACTORY_* env vars

docs/prd/003-agent-factory.md  # Full spec (4000+ lines)
```

## Task Data Model

All task state is stored as YAML frontmatter in wiki pages (`extra="allow"` passes through arbitrary fields).
Page naming: `Task_XXXX_short_description.md` (zero-padded four-digit ID).

Key frontmatter fields: `type: task`, `status`, `priority`, `branch`, `pr_url`, `pr_number`, `assignee`, `parent_task`, `token_budget`, `retry_count`.

## State Machine

```
draft → planned → decomposed → approved → in_progress → review → merged → done
                                                          ↓
                                                       rejected → in_progress
                                              failed → planned
                          (any) → blocked → planned | approved | in_progress
```

Full transition map in `src/meshwiki/core/task_machine.py:TASK_TRANSITIONS`.

## API Endpoints

All endpoints under `/api/v1/` require `X-API-Key` header matching `MESHWIKI_FACTORY_API_KEY`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/pages` | List all pages |
| GET | `/api/v1/pages/{name}` | Get page content + metadata |
| POST | `/api/v1/pages/{name}` | Create/update page |
| DELETE | `/api/v1/pages/{name}` | Delete page |
| GET | `/api/v1/tasks` | List tasks (filters: `status`, `assignee`, `parent_task`, `priority`) |
| POST | `/api/v1/tasks/{name}/transition` | Transition task state |
| GET | `/api/v1/agents` | List agent pages |
| POST | `/api/v1/github/webhook` | GitHub inbound webhook (Phase 2, no API key — uses HMAC) |

## Webhook Events

Outbound webhook POSTed to `MESHWIKI_FACTORY_WEBHOOK_URL` on each task transition.
Payload is HMAC-signed with `MESHWIKI_FACTORY_WEBHOOK_SECRET` in `X-MeshWiki-Signature` header.

Key canonical events: `task.decomposed`, `task.approved`, `task.assigned`, `task.pr_created`, `task.pr_merged`, `task.pr_rejected`, `task.failed`, `task.blocked`, `task.completed`.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MESHWIKI_FACTORY_ENABLED` | `false` | Enable factory features |
| `MESHWIKI_FACTORY_API_KEY` | `""` | API key for agent access |
| `MESHWIKI_FACTORY_WEBHOOK_URL` | `""` | Outbound webhook target (orchestrator) |
| `MESHWIKI_FACTORY_WEBHOOK_SECRET` | `""` | HMAC secret for outbound webhooks |
| `MESHWIKI_GITHUB_WEBHOOK_SECRET` | `""` | HMAC secret for inbound GitHub webhooks |

## Phase 2 Implementation Guide

The inbound GitHub webhook receiver (`src/meshwiki/api/webhooks.py`) needs to:

1. Accept `POST /api/v1/github/webhook` — no API key, verified via HMAC (`X-Hub-Signature-256`)
2. Handle `pull_request` events where `action == "closed"` and `merged == true`
3. Look up the task page by `pr_number` (use graph engine `metatable()` or scan task pages)
4. Transition the task: `review → merged`, then `merged → done`
5. Store `merged_at` timestamp in task frontmatter

PR-to-task lookup: query pages where `type=task` and `pr_number={pr_number}` using the graph engine's `query()` method, or fall back to scanning `list_pages_with_metadata()`.

Mount the router in `src/meshwiki/api/__init__.py` (already mounts `/api/v1`).

## Testing Strategy

- Unit tests for `task_machine.py` state transitions (valid + invalid)
- Unit tests for `webhooks.py` HMAC signing
- Integration tests for all `/api/v1/` endpoints (httpx TestClient with `X-API-Key`)
- Integration tests for GitHub webhook receiver (mock payload + HMAC)
- Test that invalid transitions return 422
- Test that missing pages return 404

Existing tests: `src/tests/test_task_machine.py`, `src/tests/test_api_*.py`

---

## Factory v2 Plan

v2 addresses structural gaps in v1, adds a live D3.js factory visualization, resource management, and an initial bot ecosystem. Bots interact with the factory by **creating task wiki pages** (the existing `task.assigned` webhook flow) — no separate bot API.

### Phase 8: v1 Gap Fixes (Orchestrator) 🔲
Fix correctness and reliability issues discovered in v1.

- [ ] **Cost tracking** — `cost_usd` is never incremented anywhere in v1. Add `factory/cost.py` with `estimate_cost(model, input_tokens, output_tokens)` price table. After each `client.messages.create()` call in `pm_agent.py` (lines 249, 370), read `response.usage` and accumulate cost. E2B path: track sandbox wall-clock time × configurable $/hr rate. Write to `state["cost_usd"]` from `grind_node` and `pm_review_node`.
- [ ] **Concurrency control** — `active_grinders` dict in state is declared but never populated. Cap `route_grinders` at `FACTORY_MAX_CONCURRENT_SANDBOXES` (default 3). Populate `active_grinders` in `grind_node` on entry/exit.
- [ ] **httpx client per call** — both `MeshWikiClient` and `GitHubClient` open a new `httpx.AsyncClient` for every call. Share a client instance per session with connection pooling.
- [ ] **Configurable PM model** — `pm_agent.py` hardcodes `"claude-sonnet-4-6"` at lines 249 and 370. Add `FACTORY_PM_MODEL` config setting.
- [ ] **Review feedback in rework prompt** — when PM requests changes, `subtask["review_feedback"]` is set but the grinder never reads it. Append it to `/tmp/task.md` in the E2B sandbox on rework iterations.
- [ ] **Signed grinder commits** — factory bot commits show as "unverified" on GitHub. Create a GitHub App and use its installation token, or configure GPG signing in the E2B sandbox with a dedicated factory key.
- [ ] **Bookkeeper bot** — periodic job (every 5 min) that scans task pages and reconciles stale states: tasks stuck `in_progress` with no active terminal session → `failed`; tasks in `review` where PR is already merged on GitHub → `merged`; tasks in `review` where PR was closed without merging → `failed`. Prevents tasks stuck when orchestrator crashes mid-run.
- [ ] **Redecompose escalation path** — `escalate_node` never sets `"redecompose"` decision despite the routing supporting it. Implement the logic: when multiple subtasks fail, trigger re-planning.
- [ ] **Tests for routing functions** — `route_after_grinding`, `route_after_pm_review`, `route_after_human_code_review`, `route_after_escalation`, and `route_grinders` file-overlap logic all lack unit tests.

**New config keys:** `FACTORY_PM_MODEL`, `FACTORY_MAX_CONCURRENT_SANDBOXES` (default 3), `FACTORY_E2B_COST_PER_HOUR` (default 0.20)
**New files:** `orchestrator/factory/cost.py`

---

### Phase 9: HBR Resource Manager + Scheduler (Orchestrator) 🔲
Internal resource tracking and 24/7 heartbeat scheduler so the factory can operate autonomously.

- [ ] **`factory/hbr.py`** — `HbrManager` tracking active sandboxes, daily cost vs budget, and per-model API usage. Methods: `can_allocate_sandbox()`, `sandbox_started/finished()`, `record_api_cost()`, `get_utilization()`. `route_grinders` checks `can_allocate_sandbox()` before dispatching.
- [ ] **`factory/scheduler.py`** — asyncio heartbeat (60s tick) that: resets daily budget at midnight UTC, scans for `status=approved, assignee=factory` task pages that weren't picked up by webhook, triggers the graph for the highest-priority queued task if resources are available. Started/stopped in webhook server lifespan.
- [ ] **`GET /hbr/status` endpoint** — returns current utilization: active sandboxes, daily cost, budget remaining, tasks queued.

**New config keys:** `FACTORY_DAILY_BUDGET_USD` (default 50.0), `FACTORY_SCHEDULER_INTERVAL_SECONDS` (default 60)
**New files:** `orchestrator/factory/hbr.py`, `orchestrator/factory/scheduler.py`

---

### Phase 10: Live D3.js Factory Visualization (MeshWiki) 🔲
A real-time factory activity view using the same D3.js visual language as the wiki graph page.

**New WebSocket channel:**
- [ ] **`core/factory_ws_manager.py`** — `FactoryConnectionManager` singleton (same pattern as `ws_manager.py` but push-based, no polling loop). Has a 500-entry activity ring buffer for replay on late connect.
- [ ] **`core/task_machine.py`** — after webhook emit (~line 121), also `await factory_manager.broadcast({type: "task_transition", page, from_status, to_status, canonical, metadata, timestamp})`.
- [ ] **`core/terminal_sessions.py`** — debounced `terminal_activity` broadcast in `put_chunk()` (max 1/sec per task) so the factory graph shows a "working" indicator on in_progress nodes.
- [ ] **`GET /ws/factory` WebSocket endpoint** in `main.py`.

**New API endpoints** in `api/tasks.py`:
- [ ] `GET /api/factory/graph?active_only=true` — graph snapshot: task nodes (status, title, assignee, parent_task, priority, has_terminal), agent nodes, parent_child and assignment links.
- [ ] `GET /api/factory/activity?limit=50` — recent events from ring buffer.

**New page: `/factory/live`** (`templates/factory_live.html`, full-width layout):
```
+-------------------------------------------------------------+
| Factory  |  3 active · 1 agent · $4.32 today  | [filters]  |
+-------------------------------------------------------------+
|                                        |  Detail Panel      |
|       D3 Force Graph                   |  (slides in right) |
|       Task circles (color=status)      |  - Title + badge   |
|       Agent diamonds                   |  - Terminal embed  |
|       Parent edges dashed              |  - Metadata        |
+-------------------------------------------------------------+
| Activity Feed (120px, scrolling log)                        |
+-------------------------------------------------------------+
```

**`static/js/factory.js`** (~500 lines):
- Force sim: link distance 80px (assignment) / 120px (parent_child), `forceManyBody(-400)`, `forceCollide(radius+10)`
- Task circles colored by status (same palette as `_BADGE_CLASS` in `parser.py`)
- Agent nodes as diamonds (`d3.symbolDiamond`)
- `task_transition` events: animate node color (600ms), flash (amber pulse), entrance/exit animations
- `terminal_activity` events: pulsing dot on in_progress node (clears after 3s)
- Click node → slide-in detail panel with xterm.js terminal embed for in_progress tasks (same pattern as `_render_task_status` in `parser.py` lines 567-611)
- Double-click → focus mode (same as `graph.js`)
- Race condition: connect WS first, buffer events, fetch REST snapshot, apply buffered events

**`static/css/factory.css`** (~200 lines): layout, detail panel slide-in, activity feed strip, node animations, dark mode.

**`templates/base.html`**: Add conditional "Factory" nav link when `factory_enabled`.

---

### Phase 11: Stale PR Fixer Bot 🔲
First autonomous bot using the factory. Monitors CI failures on factory-created PRs and re-dispatches them for fixing.

- [ ] **`factory/bots/stale_pr_bot.py`** — `StalePrBot.scan()` fetches open PRs (`factory/*` branch prefix only), checks check-run status via `GET /repos/{repo}/commits/{sha}/check-runs`. For PRs with failures > 30 min with no existing fix task: creates a MeshWiki task page (`type: task, status: planned, skip_decomposition: true, assignee: factory`) containing the failing check log + fix instructions, transitions to `approved` → factory picks it up via webhook.
- [ ] **Scheduler integration** — heartbeat calls `stale_pr_bot.scan()` every `FACTORY_STALE_PR_BOT_INTERVAL_SECONDS` (default 300). Respects HBR budget limits.
- [ ] **Safety guards** — only fixes `factory/*` branches; max 2 fix attempts per PR; respects concurrency limits.

**New config keys:** `FACTORY_STALE_PR_BOT_ENABLED` (default false), `FACTORY_STALE_PR_BOT_INTERVAL_SECONDS` (default 300)
**New files:** `orchestrator/factory/bots/__init__.py`, `orchestrator/factory/bots/stale_pr_bot.py`

---

## Gotchas

- **API key is optional** — if `MESHWIKI_FACTORY_API_KEY` is empty, `require_api_key` passes all requests. Intentional for dev/local use.
- **GitHub webhook uses HMAC, not API key** — `POST /api/v1/github/webhook` authenticates via `X-Hub-Signature-256` (SHA-256 HMAC of the raw body), not the factory API key.
- **Graph engine optional** — `core/graph.py` may be unavailable; PR-to-task lookup must fall back to scanning `list_pages_with_metadata()` if graph engine is not loaded.
- **Frontmatter strings** — `pr_number` is stored as a string (for graph filter compatibility), not an int.
- **Factory Dashboard is a wiki page** — `Factory_Dashboard.md` uses `<<MetaTable>>` macros; it's created manually, no code needed.
