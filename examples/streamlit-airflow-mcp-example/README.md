# Streamlit Airflow MCP Chatbot

This project provides a Streamlit-based chatbot that integrates with the OpenAI API and an Airflow Model Context Protocol (MCP) server. It allows users to interact with their Apache Airflow instance using natural language queries, which are then processed by OpenAI and translated into commands for the MCP server.

## Features

*   **Natural Language Interaction:** Ask questions about your Airflow DAGs in plain English.
*   **OpenAI Integration:** Leverages OpenAI's GPT models to interpret user queries and format MCP responses.
*   **Airflow MCP Server Integration:** Communicates with the `airflow-mcp` server to retrieve and act on Airflow data using the lightweight `fastmcp` client shipped with this repository.
*   **Built-in Logging:** Uses BMasterAI's structured logging utilities for consistent logs.
*   **User-Friendly Interface:** A simple and intuitive Streamlit interface for easy interaction.

## Prerequisites

Before running this application, ensure you have the following:

* **Docker:** Used to run the Streamlit app, Airflow services and the [hipposys-ltd/airflow-mcp](https://github.com/hipposys-ltd/airflow-mcp) server.
* **OpenAI API Key:** You will need an API key from OpenAI to use their GPT models.
* **Apache Airflow Instance:** A running Apache Airflow instance that the `airflow-mcp` server can connect to. The provided `docker-compose.yml` spins up a local instance automatically.
* **BMasterAI installed** (or `src` on your `PYTHONPATH`) so the bundled `fastmcp` module and logging utilities are available.

## Setup and Installation

### 1. Clone this Repository

```bash
git clone https://github.com/travis-burmaster/bmasterai
cd examples/streamlit-airflow-mcp-example
```

### 2. Configure Environment Variables

Create a `.env` file in the `streamlit-airflow-mcp-example` directory. You can use the provided `.env.example` as a template:

```bash
cp .env.example .env
```

Edit the `.env` file and replace `your_openai_api_key_here` with your actual OpenAI API key. Adjust `AIRFLOW_API_URL`, `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD`, and `MCP_SERVER_URL` if your setup differs from the defaults.

```ini
# .env
OPENAI_API_KEY=sk-your-openai-api-key

# Airflow Configuration
# Set to http://localhost:8088/api/v1 if Airflow runs on the host.
AIRFLOW_API_URL=http://airflow-webserver:8080/api/v1
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow

# Optional: MCP Server URL (if running separately)
MCP_SERVER_URL=http://localhost:3000
```

### 3. Install Python Dependencies

Install the example requirements and ensure the repository itself is available so the bundled `fastmcp` client can be imported:

```bash
pip install -r requirements.txt
pip install -e ../..  # install BMasterAI with built-in fastmcp
```

## Running the Application

You have two main options to run the Streamlit application:

### Option 1: Run Directly with Streamlit

Ensure your `airflow-mcp` server and Airflow instance are running. You can start the server with:

```bash
docker run -i --rm \
  --network host \
  -p 3000:3000 \
  -e airflow_api_url="http://localhost:8088/api/v1" \
  -e airflow_username="airflow" \
  -e airflow_password="airflow" \
  hipposysai/airflow-mcp:latest
```

Then navigate to the `streamlit-airflow-mcp-example` directory and run:

```bash
streamlit run enhanced_app.py
```

This will open the Streamlit application in your web browser, usually at `http://localhost:8501`.

### Option 2: Run with Docker Compose (Recommended for full setup)

This option brings up the Streamlit application, the `airflow-mcp` server, a PostgreSQL database and an Apache Airflow instance, all pre-configured to work together.

From the `streamlit-airflow-mcp-example` directory, run:

```bash
docker-compose build
docker-compose up
```

Access the Streamlit application at `http://localhost:8501`.

## Usage

Once the Streamlit application is running, you can type natural language queries into the input box, such as:

*   "What DAGs do we have?"
*   "Show me the failed DAGs."
*   "Trigger the `example_dag`."
*   "What is the status of `my_data_pipeline` DAG?"

The application will use OpenAI to interpret your query, send a corresponding command to the MCP server, and then interpret the MCP server's response back to you in a user-friendly format.

## Project Structure

```
streamlit-airflow-mcp-example/
├── .env.example             # Example environment variables
├── app.py                   # Original Streamlit application (can be ignored)
├── enhanced_app.py          # Main Streamlit application with improved logic
├── requirements.txt         # Python dependencies
├── Dockerfile               # Dockerfile for the Streamlit application
└── docker-compose.yml       # Docker Compose for full local setup (Streamlit + Airflow + Postgres)
└── README.md                # This documentation file
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open-source and available under the MIT License. (You might want to specify the actual license if different)


