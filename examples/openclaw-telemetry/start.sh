#!/bin/bash

echo "🔍 OpenClaw Telemetry Dashboard"
echo "================================"

# Change to script directory
cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Parse sessions
echo "🔄 Parsing OpenClaw sessions..."
python session_parser.py

# Check for existing dashboard process
if pgrep -f "streamlit run dashboard.py" > /dev/null; then
    echo "⚠️  Found running dashboard instance."
    echo "🛑 Stopping existing process..."
    pkill -f "streamlit run dashboard.py"
    sleep 2
    echo "✅ Stopped."
fi

# Launch dashboard
echo "🚀 Launching dashboard..."
echo ""
echo "Dashboard will open at: http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""

streamlit run dashboard.py
