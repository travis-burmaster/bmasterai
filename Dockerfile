# BMasterAI Dockerfile for Kubernetes/EKS Deployment
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BMASTERAI_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1001 bmasterai && \
    useradd --uid 1001 --gid bmasterai --shell /bin/bash --create-home bmasterai

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .
COPY setup.py .
COPY MANIFEST.in .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir .

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config && \
    chown -R bmasterai:bmasterai /app

# Switch to non-root user
USER bmasterai

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import bmasterai; print('BMasterAI healthy')" || exit 1

# Expose default port (if your application has a web interface)
EXPOSE 8080

# Default command - can be overridden in Kubernetes
CMD ["python", "-m", "bmasterai.cli", "--help"]
