# Stage 1: Build — install package and all dependencies using uv
FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy files required by the package installation
COPY pyproject.toml README.md uv.lock ./
COPY src/ ./src/
COPY mcp_server.py api.py gnmibuddy.py ./

# Install the exact locked dependencies (matches what was tested).
# --locked fails the build if uv.lock is out of sync with pyproject.toml.
# --no-editable so the runtime stage only needs the venv, not the source tree.
RUN uv sync --locked --no-dev --no-editable --no-cache


# Stage 2: Runtime — minimal image with only what is needed to run
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

# Copy the fully-installed virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Create a non-root user and transfer ownership of the working directory
RUN useradd --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
# Default mount point for the device inventory. 
# Mount your inventory file here at runtime (or override this
# variable to point elsewhere).
ENV NETWORK_INVENTORY=/app/inventory.json
ENV GNMIBUDDY_TRANSPORT=http
ENV GNMIBUDDY_HOST=0.0.0.0
ENV GNMIBUDDY_PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["gnmibuddy-mcp"]
