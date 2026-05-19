# Stage 1: Build — install package and all dependencies using uv
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy files required by the package installation
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY mcp_server.py api.py gnmibuddy.py ./

# Create a venv and install the package with all dependencies.
# No cache to keep the layer lean.
RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python --no-cache .


# Stage 2: Runtime — minimal image with only what is needed to run
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

# Copy the fully-installed virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Bake the network inventory into the image.
# This file is staged by `make build` from the path provided in INVENTORY_FILE.
# The build fails here if the inventory was not staged — this is intentional.
COPY .build_inventory.json /app/inventory.json

# Create a non-root user and transfer ownership of the working directory
RUN useradd --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV NETWORK_INVENTORY=/app/inventory.json
ENV GNMIBUDDY_TRANSPORT=http
ENV GNMIBUDDY_HOST=0.0.0.0
ENV GNMIBUDDY_PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["gnmibuddy-mcp"]
