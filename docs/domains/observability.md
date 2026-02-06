# Domain: Observability

**Owner:** TBD
**Status:** Not started
**Language:** Python, YAML (Kubernetes)

## Scope

Monitoring, logging, and tracing for GraphWiki:
- Structured logging
- Metrics collection and dashboards
- Distributed tracing
- Alerting

**Not in scope:** Application features, infrastructure provisioning

## Current State

Minimal observability:
- Basic stdout logging from uvicorn
- No metrics
- No tracing
- No alerting

## Architecture Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                        GraphWiki App                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Logging   │  │   Metrics   │  │   Tracing   │              │
│  │ (structlog) │  │ (prometheus)│  │(opentelemetry)│            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Loki     │    │ Prometheus  │    │   Jaeger    │
│  (log store)│    │  (metrics)  │    │  (traces)   │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                   ┌─────────────┐
                   │   Grafana   │
                   │ (dashboards)│
                   └─────────────┘
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Logging library | structlog | Structured JSON, good Python integration |
| Metrics | Prometheus client | Standard, Istio integration |
| Tracing | OpenTelemetry | Vendor-neutral, future-proof |
| Visualization | Grafana | Industry standard, good UX |
| Log aggregation | Loki | Lightweight, Grafana-native |

## Implementation Plan

### Phase 1: Structured Logging

```python
# Add to dependencies
"structlog>=24.0",

# Configure in main.py
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()

# Usage
logger.info("page_viewed", page=name, user=user_id)
logger.error("page_save_failed", page=name, error=str(e))
```

Log structure:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "event": "page_viewed",
  "page": "HomePage",
  "user": "anonymous",
  "request_id": "abc123"
}
```

### Phase 2: Metrics

```python
# Add to dependencies
"prometheus-client>=0.19",

# Metrics
from prometheus_client import Counter, Histogram

page_views = Counter(
    "graphwiki_page_views_total",
    "Total page views",
    ["page", "status"]
)

request_latency = Histogram(
    "graphwiki_request_latency_seconds",
    "Request latency",
    ["method", "endpoint"]
)

# Expose metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

Key metrics:
| Metric | Type | Description |
|--------|------|-------------|
| `page_views_total` | Counter | Page views by page and status |
| `page_edits_total` | Counter | Page edits |
| `request_latency_seconds` | Histogram | Request duration |
| `active_sessions` | Gauge | Current sessions (with auth) |
| `graph_nodes_total` | Gauge | Pages in graph |
| `graph_edges_total` | Gauge | Links in graph |

### Phase 3: Tracing

```python
# Add to dependencies
"opentelemetry-api>=1.20",
"opentelemetry-sdk>=1.20",
"opentelemetry-instrumentation-fastapi>=0.41",

# Configure
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

FastAPIInstrumentor.instrument_app(app)

# Custom spans
tracer = trace.get_tracer(__name__)

async def render_page(name: str):
    with tracer.start_as_current_span("render_page") as span:
        span.set_attribute("page.name", name)
        # ... rendering logic
```

### Phase 4: Infrastructure

Deploy observability stack to Kubernetes:

```yaml
# Prometheus (or use kube-prometheus-stack)
# Loki
# Grafana
# Jaeger (or Tempo)
```

Istio provides:
- Automatic request metrics
- Distributed tracing (with header propagation)
- Service mesh telemetry

## Dashboards

### Application Dashboard
- Request rate and latency (p50, p95, p99)
- Error rate by endpoint
- Page view trends
- Active users (with auth)

### Graph Engine Dashboard
- Graph size (nodes, edges)
- Query latency
- File watcher events
- Parse errors

### Infrastructure Dashboard
- Pod CPU/memory
- PVC usage
- Network traffic

## Alerting Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| High error rate | >5% 5xx in 5min | Warning |
| High latency | p99 >2s for 5min | Warning |
| Pod crash loop | Restarts >3 in 10min | Critical |
| PVC nearly full | >80% used | Warning |

## Integration Points

| Component | Integration |
|-----------|-------------|
| FastAPI | Middleware for request logging/metrics |
| Graph engine | Expose metrics via PyO3 bindings |
| Istio | Automatic sidecar telemetry |
| Kubernetes | Pod metrics, events |

## Testing Strategy

- Verify log format and fields
- Test metrics endpoint returns valid Prometheus format
- Integration tests include trace context propagation
- Load tests validate metrics accuracy
