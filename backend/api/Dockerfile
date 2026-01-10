FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration
COPY pyproject.toml .
# Copy lock file if it exists (not strictly required but good practice if available)
# COPY uv.lock . 

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-install-project || uv sync --no-install-project

# Copy source code
COPY api/ .

# Expose port
EXPOSE 8000

# Run the API server using uv run (which uses the venv)
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
