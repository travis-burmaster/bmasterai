# GEMINI.md

## Project Overview

This project is a stock research application built with Python and Streamlit. It provides a user interface to analyze US stock market data. The application fetches real-time stock data, performs technical analysis, scrapes news for market sentiment, and displays institutional holdings. It uses the `yfinance` library for stock data, `beautifulsoup4` for web scraping, and `plotly` for interactive charts. The application is structured with a main Streamlit app file (`stock_research_agent.py`), a data API module (`data_api.py`), and a requirements file (`requirements.txt`).

The project also includes an example of a multi-agent Streamlit application (`streamlit_agents_app.py`) that uses the `agno` framework to create a team of AI agents with different specializations (knowledge and travel).

**Key Technologies:**

*   **Python:** The core language of the project.
*   **Streamlit:** For building the interactive web application.
*   **yfinance:** For fetching stock data from Yahoo Finance.
*   **Beautiful Soup:** For web scraping news headlines.
*   **Plotly:** For creating interactive charts.
*   **Agno:** For building multi-agent AI systems.
*   **BMasterAI:** For advanced logging and monitoring.

**Architecture:**

The project is structured as follows:

*   `stock_research_agent.py`: The main Streamlit application file.
*   `data_api.py`: A module that provides a client for accessing Yahoo Finance data.
*   `streamlit_agents_app.py`: An example of a multi-agent Streamlit application.
*   `requirements.txt`: A list of the Python dependencies for the project.
*   `.env`: A file for storing environment variables, such as API keys.

## Building and Running

**Installation:**

To install the dependencies for this project, run the following command:

```bash
pip install -r requirements.txt
```

**Running the Application:**

To run the stock research application, use the following command:

```bash
streamlit run stock_research_agent.py
```

To run the multi-agent Streamlit application, use the following command:

```bash
streamlit run streamlit_agents_app.py
```

## Development Conventions

*   **Logging:** The project uses the `bmasterai` logging framework for advanced logging and monitoring. If the framework is not available, it falls back to the standard Python logging module.
*   **Environment Variables:** The project uses a `.env` file to manage environment variables, such as API keys.
*   **Code Style:** The project follows the standard Python code style guidelines (PEP 8).
