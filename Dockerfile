# Free AI Model Router — Docker image
# Used for manual runs on sagitta server

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY config/ config/

# Install the package and dependencies
RUN pip install --no-cache-dir -e ".[litellm]"

# Create data and output directories
RUN mkdir -p data/raw data/normalized data/history data/cache output reports

# Run as non-root user
RUN useradd -m -u 1000 router
RUN chown -R router:router /app
USER router

# Default command
CMD ["python", "-m", "free_ai_model_router", "run-all"]
