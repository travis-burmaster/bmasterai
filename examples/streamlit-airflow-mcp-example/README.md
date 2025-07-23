# Streamlit Airflow MCP Chatbot

This project provides a Streamlit-based chatbot that integrates with the Anthropic API and an Airflow Model Context Protocol (MCP) server. It allows users to interact with their Apache Airflow instance using natural language queries, which are then processed by Anthropic and translated into commands for the MCP server.

## Features

*   **Natural Language Interaction:** Ask questions about your Airflow DAGs in plain English.
*   **Anthropic Integration:** Leverages Anthropic's Claude models to interpret user queries and format MCP responses.
*   **Airflow MCP Server Integration:** Communicates with the `airflow-mcp` server to retrieve and act on Airflow data.
*   **User-Friendly Interface:** A simple and intuitive Streamlit interface for easy interaction.

## Prerequisites

Before running this application, ensure you have the following:

*   **Docker:** Required for running the `airflow-mcp` server and optionally for running this Streamlit application.
*   **Anthropic API Key:** You will need an API key from Anthropic to use their Claude models.
*   **Apache Airflow Instance:** A running Apache Airflow instance that the `airflow-mcp` server can connect to. This can be a local instance or a remote one.
*   **`airflow-mcp` Server:** The MCP server for Airflow needs to be running and accessible. Follow the instructions in the [hipposys-ltd/airflow-mcp](https://github.com/hipposys-ltd/airflow-mcp) repository to set it up.

## Setup and Installation

### 1. Clone the MCP Repository (if not already done)

If you haven't already, clone the `airflow-mcp` repository:

```bash
git clone https://github.com/hipposys-ltd/airflow-mcp
cd airflow-mcp
```

Follow their instructions to get the MCP server and a local Airflow instance running. The `docker-compose.airflow.yml` and `docker-compose.mcp.yml` files in their repository are good starting points.

### 2. Clone this Repository

```bash
git clone https://https://github.com/travis-burmaster/bmasterai
cd streamlit_airflow_mcp_example
```

### 3. Configure Environment Variables

Create a `.env` file in the `streamlit_airflow_mcp` directory. You can use the provided `.env.example` as a template:

```bash
cp .env.example .env
```

Edit the `.env` file and replace `your_anthropic_api_key_here` with your actual Anthropic API key. Adjust `AIRFLOW_API_URL`, `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD`, and `MCP_SERVER_URL` if your setup differs from the defaults.

```ini
# .env
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-api-key

# Airflow Configuration
AIRFLOW_API_URL=http://localhost:8088/api/v1
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow

# Optional: MCP Server URL (if running separately)
MCP_SERVER_URL=http://localhost:8000
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

You have two main options to run the Streamlit application:

### Option 1: Run Directly with Streamlit

Ensure your `airflow-mcp` server and Airflow instance are running, then navigate to the `streamlit_airflow_mcp` directory and run:

```bash
streamlit run enhanced_app.py
```

This will open the Streamlit application in your web browser, usually at `http://localhost:8501`.

### Option 2: Run with Docker Compose (Recommended for full setup)

This option will bring up the Streamlit application, a PostgreSQL database, and an Apache Airflow instance, all pre-configured to work together. It also assumes you have the `airflow-mcp` server running separately or integrate it into this `docker-compose.yml`.

From the `streamlit_airflow_mcp` directory, run:

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

The application will use Anthropic to interpret your query, send a corresponding command to the MCP server, and then interpret the MCP server's response back to you in a user-friendly format.

## Project Structure

```
streamlit_airflow_mcp/
├── .env.example             # Example environment variables
├── app.py                   # Original Streamlit application (can be ignored)
├── enhanced_app.py          # Main Streamlit application with improved logic
├── mcp_client.py            # Python client for interacting with the MCP server
├── requirements.txt         # Python dependencies
├── Dockerfile               # Dockerfile for the Streamlit application
└── docker-compose.yml       # Docker Compose for full local setup (Streamlit + Airflow + Postgres)
└── README.md                # This documentation file
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open-source and available under the MIT License. (You might want to specify the actual license if different)


