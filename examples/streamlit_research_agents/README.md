
# Multi-Agent Research System

A sophisticated Streamlit application that demonstrates collaborative AI agents working together to conduct comprehensive research tasks. This system uses Google Gemini API for advanced language processing and Perplexity API for information gathering.

## Features

- **Multi-Agent Collaboration**: Four specialized agents work together:
  - **Research Coordinator**: Orchestrates the workflow and manages agent coordination
  - **Search Agent**: Handles information gathering using Perplexity API
  - **Synthesis Agent**: Analyzes and synthesizes research findings using Google Gemini
  - **Editing Agent**: Refines and formats the final research report

- **Real-time Progress Tracking**: Live updates on agent status and workflow progress
- **Configurable Research Parameters**: Adjustable depth, source limits, and output formats
- **Multiple Output Formats**: Support for Markdown, HTML, and PDF reports
- **Robust Error Handling**: Comprehensive error management with retry logic
- **Asynchronous Processing**: Non-blocking UI with background task execution

## Architecture

The system follows a structured 5-stage workflow:

1. **Planning**: Research Coordinator breaks down the topic and creates task plans
2. **Information Gathering**: Search Agent performs comprehensive searches using Perplexity API
3. **Analysis & Synthesis**: Synthesis Agent identifies patterns and insights using Google Gemini
4. **Content Editing**: Editing Agent refines content for clarity and professional presentation
5. **Quality Review**: Final validation and deliverable preparation

## Prerequisites

- Python 3.8 or higher
- Google API key for Gemini API
- Perplexity API key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd streamlit_research_agents
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export GOOGLE_API_KEY="your_google_gemini_api_key_here"
export PERPLEXITY_API_KEY="your_perplexity_api_key_here"
```

Alternatively, create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_gemini_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

## Getting API Keys

### Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key and set it as `GOOGLE_API_KEY`

### Perplexity API Key
1. Visit [Perplexity API](https://www.perplexity.ai/settings/api)
2. Sign up or log in to your account
3. Generate an API key
4. Copy the key and set it as `PERPLEXITY_API_KEY`

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Configure your API keys in the sidebar

4. Enter your research topic and configure parameters:
   - **Research Topic**: Describe what you want to research
   - **Research Depth**: Choose from Basic, Intermediate, or Comprehensive
   - **Maximum Sources**: Set the limit for information sources
   - **Output Format**: Select Markdown, HTML, or PDF

5. Click "🚀 Start Research" to begin the multi-agent research process

6. Monitor progress in real-time as agents collaborate

7. Review the final research report with insights, analysis, and recommendations

## Configuration

The system can be configured through `config/agent_config.yaml`:

- **Agent Settings**: Customize agent behavior and prompts
- **API Configuration**: Set rate limits, timeouts, and model parameters
- **Workflow Stages**: Modify the research workflow
- **Quality Standards**: Define minimum requirements for research quality
- **Output Templates**: Customize report formats and sections

## Project Structure

```
streamlit_research_agents/
├── README.md                    # This file
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── agents/                     # Agent implementations
│   ├── editing_agent.py       # Content editing and formatting
│   ├── research_coordinator.py # Workflow orchestration
│   ├── search_agent.py        # Information gathering
│   └── synthesis_agent.py     # Analysis and synthesis
├── config/
│   └── agent_config.yaml      # Agent configuration and settings
└── utils/
    ├── gemini_base.py         # Google Gemini API integration
    ├── perplexity_client.py   # Perplexity API wrapper
    └── report_generator.py    # Report generation utilities
```

## Key Components

### BaseAgent Class
Custom base class that provides:
- Status management and progress tracking
- Asynchronous processing capabilities
- Error handling and logging
- Callback system for real-time updates

### GeminiClient
Google Gemini API wrapper that handles:
- Authentication and configuration
- Structured response generation
- Error handling and retries
- Safety settings and content filtering

### Multi-Agent Workflow
Coordinated workflow where:
- Each agent has specialized responsibilities
- Agents communicate through structured data exchange
- Progress is tracked and reported in real-time
- Errors are handled gracefully with fallback options

## Migration from BMasterAI

This system has been migrated from BMasterAI framework to Google Gemini API:

### Changes Made:
- **API Integration**: Replaced BMasterAI API calls with Google Gemini API
- **Base Classes**: Implemented custom BaseAgent, GeminiClient, and TextProcessor
- **Environment Variables**: Changed from `BMASTERAI_API_KEY` to `GOOGLE_API_KEY`
- **Dependencies**: Updated requirements.txt to use google-generativeai
- **Agent Logic**: Adapted all agents to work with Gemini's response format
- **Configuration**: Updated agent_config.yaml for Gemini API settings

### Preserved Functionality:
- All original features and capabilities maintained
- Same user interface and experience
- Identical workflow stages and coordination
- Compatible output formats and quality standards

## Troubleshooting

### Common Issues:

1. **API Key Errors**:
   - Ensure your Google API key is valid and has Gemini API access enabled
   - Check that environment variables are set correctly
   - Verify API quotas and rate limits

2. **Import Errors**:
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+)

3. **Performance Issues**:
   - Reduce the number of maximum sources for faster processing
   - Choose "Basic" research depth for quicker results
   - Check your internet connection for API calls

4. **Memory Issues**:
   - Clear results regularly using the "🗑️ Clear Results" button
   - Restart the application if memory usage becomes high

### Getting Help:

- Check the application logs for detailed error messages
- Review the agent status indicators for workflow issues
- Ensure all API keys have sufficient quotas
- Verify network connectivity for API calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini API for advanced language processing
- Perplexity API for comprehensive information gathering
- Streamlit for the interactive web interface
- The open-source community for various supporting libraries
