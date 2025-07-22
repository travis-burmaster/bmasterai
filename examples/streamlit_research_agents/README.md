# Multi-Agent Research System

A Streamlit application demonstrating collaborative AI agents for complex research tasks using the Perplexity API and BMasterAI framework.

## Overview

This example showcases a multi-agent system where specialized AI agents work together to conduct comprehensive research on any given topic. The system consists of four main agents:

- **Research Coordinator**: Orchestrates the entire research workflow
- **Search Agent**: Gathers information using the Perplexity API
- **Synthesis Agent**: Analyzes and synthesizes collected data
- **Editing Agent**: Refines and formats the final research output

## Features

- **Real-time Progress Tracking**: Monitor each agent's status and progress
- **Interactive Streamlit Interface**: User-friendly web interface for configuration and monitoring
- **Multiple Output Formats**: Generate reports in Markdown, HTML, and PDF formats
- **Configurable Research Parameters**: Customize search depth, focus areas, and output preferences
- **Error Handling and Recovery**: Robust error handling with automatic retry mechanisms
- **Rate Limiting**: Built-in rate limiting for API calls to ensure compliance

## Prerequisites

- Python 3.8+
- Streamlit
- BMasterAI framework
- Perplexity API key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository and navigate to the example directory:
```bash
cd examples/streamlit_research_agents
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export PERPLEXITY_API_KEY="your_perplexity_api_key_here"
export BMASTERAI_API_KEY="your_bmasterai_api_key_here"
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to the displayed URL (typically http://localhost:8501)

3. Configure your research parameters in the sidebar:
   - Enter your research topic
   - Set search depth and focus areas
   - Choose output format preferences
   - Configure agent behavior settings

4. Click "Start Research" to begin the multi-agent research process

5. Monitor progress in real-time as agents collaborate to complete the research

6. Download or view the generated research report once complete

## Configuration Options

### Research Parameters
- **Topic**: The main subject for research
- **Search Depth**: Number of search iterations (1-10)
- **Focus Areas**: Specific aspects to emphasize
- **Time Range**: Limit search to specific time periods
- **Source Types**: Academic, news, general web, etc.

### Agent Settings
- **Coordinator Timeout**: Maximum time for overall coordination
- **Search Iterations**: Number of search rounds per query
- **Synthesis Depth**: Level of analysis detail
- **Editing Strictness**: Quality control level for final output

### Output Options
- **Format**: Markdown, HTML, PDF
- **Length**: Brief, standard, comprehensive
- **Include Sources**: Citation preferences
- **Template**: Report structure template

## Architecture

### Agent Hierarchy
```
Research Coordinator (BMasterAI)
├── Search Agent (Perplexity API)
├── Synthesis Agent (Analysis & Insights)
└── Editing Agent (Formatting & Quality)
```

### Workflow Stages
1. **Initialization**: Coordinator sets up research parameters
2. **Information Gathering**: Search agent queries Perplexity API
3. **Data Processing**: Synthesis agent analyzes collected information
4. **Content Refinement**: Editing agent polishes the final output
5. **Report Generation**: System produces formatted research report

## API Integration

### Perplexity API
- Used for web search and information retrieval
- Handles real-time data access
- Provides source attribution and citations
- Rate limited to comply with API terms

### BMasterAI Framework
- Base agent architecture for coordination
- Inter-agent communication protocols
- Task scheduling and progress tracking
- Error handling and recovery mechanisms

## File Structure

```
streamlit_research_agents/
├── app.py                          # Main Streamlit application
├── agents/
│   ├── __init__.py
│   ├── research_coordinator.py     # Main coordination agent
│   ├── search_agent.py            # Perplexity API search agent
│   ├── synthesis_agent.py         # Data analysis agent
│   └── editing_agent.py           # Content refinement agent
├── utils/
│   ├── __init__.py
│   ├── perplexity_client.py       # Perplexity API client
│   └── report_generator.py        # Report formatting utilities
├── templates/
│   ├── research_report.md         # Markdown template
│   ├── research_report.html       # HTML template
│   └── styles.css                 # CSS styling
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## Error Handling

The system includes comprehensive error handling:

- **API Rate Limiting**: Automatic backoff and retry mechanisms
- **Network Failures**: Graceful degradation with cached results
- **Agent Failures**: Coordinator can reassign tasks or continue with partial results
- **Invalid Inputs**: Input validation with helpful error messages
- **Resource Limits**: Memory and time limit monitoring

## Customization

### Adding New Agents
1. Create a new agent class inheriting from BMasterAI base
2. Implement required methods: `initialize()`, `process()`, `finalize()`
3. Register the agent with the coordinator
4. Update the UI to display the new agent's status

### Custom Output Formats
1. Create new templates in the `templates/` directory
2. Implement format-specific generation in `report_generator.py`
3. Add format option to the Streamlit interface

### API Extensions
1. Extend `perplexity_client.py` for additional API endpoints
2. Implement new search strategies in `search_agent.py`
3. Add configuration options for new features

## Troubleshooting

### Common Issues

**API Key Errors**
- Ensure environment variables are set correctly
- Verify API keys are valid and have sufficient quota

**Rate Limiting**
- Reduce search depth or increase delays between requests
- Monitor API usage in the Streamlit interface

**Memory Issues**
- Limit the scope of research topics
- Reduce the number of concurrent search queries

**Slow Performance**
- Check network connectivity
- Reduce synthesis depth for faster processing

### Debug Mode
Enable debug mode by setting the environment variable:
```bash
export DEBUG_MODE=true
```

This will provide detailed logging and intermediate results for troubleshooting.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with appropriate tests
4. Submit a pull request with detailed description

## License

This example is provided under the same license as the BMasterAI framework.

## Support

For issues specific to this example:
- Check the troubleshooting section above
- Review the BMasterAI documentation
- Submit issues to the project repository

For Perplexity API support:
- Consult the Perplexity API documentation
- Contact Perplexity support for API-specific issues