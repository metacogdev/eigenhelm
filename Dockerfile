FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first (layer cache)
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install serve extras only (no dev deps)
RUN uv pip install --system ".[serve]"

EXPOSE 8080

ENTRYPOINT ["eigenhelm-serve"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
