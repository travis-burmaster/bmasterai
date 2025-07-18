# AI Business Consultant - Streamlit Application

A comprehensive AI-powered business consultant built with Streamlit that provides market analysis, strategic recommendations, competitor research, and risk assessment capabilities.

## Features

- 🤖 **AI-Powered Consultations**: Interactive chat interface with streaming responses
- 📊 **Market Analysis**: Comprehensive market research and insights
- 🏢 **Competitor Analysis**: Detailed competitive landscape assessment
- ⚠️ **Risk Assessment**: Business risk evaluation and mitigation strategies
- 💡 **Strategic Recommendations**: Actionable business strategies with timelines
- 🔍 **Web Research**: Optional Perplexity API integration for real-time data
- 📈 **Interactive UI**: Clean, responsive interface with real-time updates

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd examples/streamlit-app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

4. **Configure your API keys** in the `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   PERPLEXITY_API_KEY=your_perplexity_api_key_here  # Optional
   ```

## Usage

1. **Run the application**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to `http://localhost:8501`

3. **Start consulting**:
   - Type your business questions in the chat
   - Use quick action buttons for specific analysis
   - Ask for market research, competitor analysis, or strategic advice

## Configuration

### Required Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Optional Environment Variables

- `PERPLEXITY_API_KEY`: For enhanced web research capabilities
- `OPENAI_MODEL`: AI model to use (default: gpt-4-turbo-preview)
- `MAX_TOKENS`: Maximum response length (default: 4000)
- `TEMPERATURE`: Response creativity (default: 0.7)

### Application Settings

- `APP_NAME`: Application name (default: AI Business Consultant)
- `AGENT_NAME`: AI agent name (default: AI Business Consultant)
- `SESSION_TIMEOUT`: Session timeout in seconds (default: 3600)
- `MAX_CONVERSATION_LENGTH`: Maximum conversation history (default: 50)

## Example Questions

- "I want to launch a SaaS startup for small businesses in the accounting space. What should I consider?"
- "Analyze the market opportunities for AI-powered customer service tools."
- "What are the key risks of entering the fintech space as a startup?"
- "Give me strategic recommendations for scaling my e-commerce business."
- "Conduct a competitor analysis for the project management software industry."

## Architecture

### Core Components

- **`app.py`**: Main Streamlit application
- **`config.py`**: Configuration management with validation
- **`utils/ai_client.py`**: AI service integrations (OpenAI, Perplexity)
- **`utils/business_tools.py`**: Business analysis tools and utilities
- **`components/chat_interface.py`**: Interactive chat interface
- **`components/sidebar.py`**: Sidebar controls and navigation

### Key Features

1. **Streaming Responses**: Real-time AI response streaming
2. **Session Management**: Persistent conversation history
3. **Analysis Tools**: Specialized business analysis capabilities
4. **Error Handling**: Robust error management and recovery
5. **Configuration**: Flexible configuration with validation

## Analysis Types

### Market Analysis
- Market opportunity assessment
- Key trends and drivers
- Competitive landscape overview
- Risk factors
- Strategic recommendations

### Competitor Analysis
- Market leaders identification
- Emerging players analysis
- Market gaps and opportunities
- Competitive advantages
- Strategic positioning

### Risk Assessment
- Financial, operational, and market risks
- Risk probability and impact assessment
- Mitigation strategies
- Monitoring recommendations
- Contingency planning

### Strategic Recommendations
- Prioritized action items
- Implementation timelines
- Success metrics
- Resource requirements
- Risk mitigation strategies

## Troubleshooting

### Common Issues

1. **API Not Connected**:
   - Check your `.env` file
   - Verify API key validity
   - Ensure proper environment variable names

2. **Slow Responses**:
   - Reduce `MAX_TOKENS` setting
   - Use a faster model (e.g., gpt-3.5-turbo)
   - Check your internet connection

3. **Memory Issues**:
   - Clear chat history regularly
   - Reduce `MAX_CONVERSATION_LENGTH`
   - Restart the application

### Getting Help

- Check the Help section in the sidebar
- Review example questions
- Verify configuration settings
- Check application logs

## Development

### Adding New Analysis Types

1. Add detection logic in `ChatInterface._detect_analysis_type()`
2. Implement analysis method in `BusinessAnalyzer`
3. Add display logic in `ChatInterface._display_analysis_results()`
4. Update sidebar quick actions if needed

### Customizing AI Behavior

- Modify system prompts in `ChatInterface._get_system_prompt()`
- Adjust model parameters in `config.py`
- Update analysis generation logic in `business_tools.py`

### Adding New Integrations

- Create new client in `utils/ai_client.py`
- Add configuration variables in `config.py`
- Update environment variable examples

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support, please open an issue in the repository or contact the development team.

---

Built with ❤️ using Streamlit, OpenAI, and modern Python practices.