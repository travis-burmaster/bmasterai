# Streamlit Agent Search Example

This example demonstrates how to create a Streamlit application that searches for and integrates with other AI agents.

## Overview

The application provides:
- A search interface to discover AI agents
- Integration capabilities with found agents
- Results display and interaction

## Requirements

- Python 3.7+
- Streamlit
- Additional dependencies in requirements.txt

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Example

From this directory, run:
```bash
streamlit run app.py
```

## Project Structure

- `app.py`: Main Streamlit interface and application logic
- `agent_discovery.py`: Agent search and integration functionality
- `requirements.txt`: Project dependencies

## Features

- Search for AI agents by capability or description
- View agent details and specifications
- Test integration with selected agents
- Display interaction results
- Save favorite/frequently used agents

## Usage

1. Enter search criteria in the search box
2. Browse through discovered agents
3. Select an agent to view details
4. Test integration using the provided interface
5. View and export results

## Configuration

The application can be configured through environment variables:

- `AGENT_SEARCH_API_KEY`: API key for agent discovery service
- `MAX_RESULTS`: Maximum number of search results to display
- `CACHE_DURATION`: Duration to cache search results

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

## License

MIT License - see LICENSE file for details