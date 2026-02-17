# WebMCP GCP Agent — Cloud Run Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Pin Playwright browser to a known-good path so the version matches the
# Python package. PLAYWRIGHT_BROWSERS_PATH must be set before `playwright install`.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

# System deps for Playwright (Chromium)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser.
# The version installed here is determined by the `playwright` pin in
# requirements.txt (playwright==1.47.0 → Chromium 130.x).
# PLAYWRIGHT_BROWSERS_PATH is set above so the path is deterministic.
RUN playwright install chromium --with-deps

# Copy agent source
COPY . .

# Cloud Run sets PORT automatically
ENV PORT=8080
EXPOSE 8080

# Run with uvicorn
CMD ["python", "agent.py"]
