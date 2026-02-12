# Multi-stage Dockerfile for GraphWiki with Rust graph engine
#
# Build from repo root:
#   docker build -t graphwiki:latest .

# ── Stage 1: Build Rust graph engine ────────────────────────
FROM python:3.12-slim AS rust-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Install Maturin
RUN pip install --no-cache-dir maturin

WORKDIR /build
COPY graph-core/ ./graph-core/

# Build the graph_core wheel
WORKDIR /build/graph-core
RUN PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin build --release --out /wheels

# ── Stage 2: Runtime image ──────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY src/pyproject.toml .
RUN pip install --no-cache-dir .

# Install the graph_core wheel from builder stage
COPY --from=rust-builder /wheels/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

# Copy application code
COPY src/graphwiki/ ./graphwiki/

# Create data directory
RUN mkdir -p /data/pages

ENV GRAPHWIKI_DATA_DIR=/data/pages
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "graphwiki.main:app", "--host", "0.0.0.0", "--port", "8000"]
