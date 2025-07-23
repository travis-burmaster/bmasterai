# Quick Start Guide

Get up and running with the Streamlit Airflow MCP integration in minutes!

## Prerequisites

- Python 3.8+
- Docker (recommended) or local Airflow installation
- Anthropic API key

## Option 1: Docker Setup (Recommended)

### 1. Clone and Navigate
```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai/examples/streamlit-airflow-mcp
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```env
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Start Everything
```bash
docker-compose up
```

This starts:
- Airflow MCP Server on http://localhost:3000
- Streamlit app on http://localhost:8501

### 4. Access the Application
Open http://localhost:8501 in your browser

## Option 2: Local Setup

### 1. Clone and Setup
```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai/examples/streamlit-airflow-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
ANTHROPIC_API_KEY=your_api_key_here
AIRFLOW_API_URL=http://localhost:8080/api/v1
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow
MCP_SERVER_URL=http://localhost:3000
```

### 3. Start MCP Server
```bash
docker run -i --rm \
  -e airflow_api_url="http://host.docker.internal:8080/api/v1" \
  -e airflow_username="airflow" \
  -e airflow_password="airflow" \
  -p 3000:3000 \
  hipposysai/airflow-mcp:latest
```

### 4. Run Streamlit
```bash
streamlit run app.py
```

## First Steps

### 1. Test Connection
In the chat, type:
```
What DAGs are available?
```

### 2. Check DAG Status
```
Show me running DAGs
```

### 3. View Failed DAGs
```
Which DAGs failed today?
```

### 4. Trigger a DAG
```
Trigger the example_data_pipeline DAG
```

## Common Issues

### Connection Error
- Ensure Airflow is running and accessible
- Check MCP server is running on port 3000
- Verify credentials in `.env`

### No DAGs Found
- Ensure Airflow has DAGs deployed
- Check Airflow API is enabled
- Verify user permissions

### Claude API Error
- Verify your Anthropic API key
- Check internet connection
- Ensure API key has sufficient credits

## Next Steps

1. **Explore Features**
   - Try different natural language queries
   - Use the visualization features
   - Monitor DAG performance

2. **Customize**
   - Modify prompts in `prompts.py`
   - Add new visualizations in `components.py`
   - Extend MCP client capabilities

3. **Deploy to Production**
   - Set up proper authentication
   - Configure HTTPS
   - Enable monitoring

## Getting Help

- Check the [full documentation](README.md)
- Review [example queries](README.md#usage-examples)
- Open an issue on GitHub

## Quick Commands

```bash
# Using Make
make setup      # Setup environment
make run        # Run application
make test       # Run tests
make docker-up  # Start with Docker

# Using Docker Compose
docker-compose up -d     # Start in background
docker-compose logs -f   # View logs
docker-compose down      # Stop everything
```