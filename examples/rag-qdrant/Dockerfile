FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache and logs directories
RUN mkdir -p /app/cache /app/logs

# Create a non-root user
RUN useradd -m -u 1000 nonroot

# Change ownership of the app directory to the nonroot user
RUN chown -R nonroot:nonroot /app

# Switch to the non-root user
USER nonroot

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application
CMD ["python", "bmasterai-gradio-rag.py"]