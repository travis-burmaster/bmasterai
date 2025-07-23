# Streamlit Research Agents Example

This example demonstrates how to use BMasterAI research agents with a Streamlit web interface for conducting automated research tasks.

## Prerequisites

- Python 3.8 or higher
- BMasterAI API key
- OpenAI API key (or other LLM provider keys as needed)

## Installation

1. Clone the repository and navigate to this example:
```bash
cd examples/streamlit_research_agents
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API keys:
   - Create a `.env` file in the example directory
   - Add your API keys:
```env
BMASTERAI_API_KEY=your_bmasterai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
# Add other provider keys as needed
```

## Configuration

The application uses a `config.py` file to manage settings. You can customize:
- Agent parameters (model, temperature, max tokens)
- Research depth and scope
- Output formatting options
- API timeout settings

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your browser to the displayed URL (typically http://localhost:8501)

3. Using the interface:
   - Enter your research query in the text input field
   - Select the research depth (Quick, Standard, or Deep)
   - Choose output format (Summary, Detailed, or Academic)
   - Click "Start Research" to begin

4. The application will:
   - Initialize the research agents
   - Conduct multi-stage research
   - Display progress in real-time
   - Present findings in your chosen format

## Features

- **Multi-Agent Research**: Utilizes multiple specialized agents for comprehensive research
- **Real-time Progress**: Shows research progress with status updates
- **Error Handling**: Graceful handling of API errors and rate limits
- **Customizable Output**: Choose between different output formats
- **Session Management**: Maintains research history during your session

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure your `.env` file is in the correct directory
   - Verify API keys are valid and have sufficient credits
   - Check that environment variables are loaded correctly

2. **Import Errors**
   - Make sure BMasterAI is installed: `pip install bmasterai`
   - Verify all dependencies are installed from requirements.txt

3. **Connection Errors**
   - Check your internet connection
   - Verify API endpoints are accessible
   - Consider proxy settings if behind a firewall

4. **Rate Limiting**
   - The app includes automatic retry logic for rate limits
   - Consider upgrading your API plan for higher limits
   - Adjust research depth to reduce API calls

### Debug Mode

Run the app in debug mode for detailed logging:
```bash
streamlit run app.py --logger.level=debug
```

## Architecture

The example consists of:
- `app.py`: Main Streamlit application
- `config.py`: Configuration management
- `requirements.txt`: Python dependencies
- `.env`: API keys and secrets (not tracked in git)

## Extending the Example

You can extend this example by:
1. Adding custom research agents
2. Implementing additional output formats
3. Adding data visualization components
4. Integrating with external data sources
5. Adding export functionality (PDF, Word, etc.)

## Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- Consider implementing user authentication for production use
- Regularly rotate API keys

## Support

For issues specific to this example:
1. Check the troubleshooting section above
2. Review the BMasterAI documentation
3. Open an issue in the repository with:
   - Error messages
   - Steps to reproduce
   - Environment details (OS, Python version, etc.)