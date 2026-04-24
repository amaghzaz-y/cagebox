# Use uv-provided Python image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY cagebox/ ./cagebox/

# Install dependencies (frozen, no dev)
RUN uv sync --frozen --no-dev

# Install developer tooling for debugging and local dev
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    bash \
    curl \
    ca-certificates \
    ripgrep \
    jq \
    unzip \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://bun.sh/install | BUN_INSTALL="/root/.bun" bash \
    && ln -sf /root/.bun/bin/bun /usr/local/bin/bun

# Expose HTTP port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default workspace mount point
ENV CAGEBOX_PORT=8000
ENV CAGEBOX_HOST=0.0.0.0

# Run the server
ENTRYPOINT ["uv", "run", "python", "-m", "cagebox", "/workspace"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
