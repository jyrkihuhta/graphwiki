FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

CMD ["python", "-m", "factory.main"]
