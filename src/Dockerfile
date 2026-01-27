FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY graphwiki/ ./graphwiki/

# Create data directory
RUN mkdir -p /data/pages

# Set environment variables
ENV GRAPHWIKI_DATA_DIR=/data/pages
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "graphwiki.main:app", "--host", "0.0.0.0", "--port", "8000"]
