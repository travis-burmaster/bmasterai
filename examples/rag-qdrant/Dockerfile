FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gradio-app-rag.py .

# Create directories for uploads and logs
RUN mkdir -p /app/uploads /app/logs

# Create non-root user for security
RUN useradd -m -s /bin/bash rag-user && chown -R rag-user:rag-user /app
USER rag-user

# Expose port
EXPOSE 7860

# Environment variables
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860
ENV PYTHONUNBUFFERED=1
ENV QDRANT_URL=http://qdrant:6333

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application
CMD ["python", "gradio-app-rag.py"]
