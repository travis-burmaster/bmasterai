# Sports Betting Analysis - Multi-Agent AI System

A sophisticated multi-agent artificial intelligence system for sports betting analysis that demonstrates real-time AI reasoning transparency through BMasterAI logging framework, Agno multi-agent coordination, and Gemini AI integration.

## 🏈 Overview

This stock research agent approach into a comprehensive sports betting analysis system featuring:

- **Multi-Agent Architecture**: Specialized agents for data collection, statistical analysis, market analysis, news sentiment, and probability calculation
- **Real-Time Transparency**: BMasterAI logging framework provides complete visibility into AI reasoning processes
- **Advanced Analytics**: Poisson distribution models, Elo rating systems, Monte Carlo simulations, and Bayesian probability updating
- **Interactive UI**: Streamlit-based interface with live chain of thought visualization
- **Comprehensive Data Sources**: Integration with The Odds API, ESPN API, Tavily search, and Firecrawl

## 🚀 Features

### Core Functionality
- **Multi-Agent Coordination**: Orchestrated workflow between specialized AI agents
- **Statistical Modeling**: Advanced mathematical models for probability estimation
- **Market Analysis**: Betting line movement tracking and value identification
- **News Sentiment Analysis**: Real-time processing of sports news and social media
- **Expected Value Calculations**: Kelly Criterion and risk management recommendations
- **Chain of Thought Transparency**: Complete visibility into AI reasoning processes

### Technical Architecture
- **Agno Framework**: Latest multi-agent system coordination
- **BMasterAI Logging**: Comprehensive reasoning transparency and audit trails
- **Gemini AI Integration**: Advanced language model for analysis and reasoning
- **Streamlit UI**: Professional, responsive web interface
- **Async Processing**: High-performance concurrent agent execution
- **Bayesian Updating**: Dynamic probability refinement with new information

## 📋 Requirements

### System Requirements
- Python 3.11+
- 4GB+ RAM recommended
- Internet connection for API access

### API Keys Required
- Google/Gemini API Key
- Tavily API Key (optional, for enhanced news search)
- The Odds API Key (optional, for live betting odds)
- Firecrawl API Key (optional, for web scraping)

## 🛠️ Installation

### 1. Clone or Download the Project
```bash
git clone <repository-url>
cd sports_betting_analysis
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

Edit `.env` with your actual API keys:
```env
GOOGLE_API_KEY=your_google_api_key_here

TAVILY_API_KEY=your_tavily_api_key_here
THE_ODDS_API_KEY=your_odds_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

### 4. Run the Application
```bash
streamlit run sports_betting_streamlit_app.py
```

The application will be available at `http://localhost:8501`

## 🎯 Usage Guide

### Basic Analysis Workflow

1. **Configure Analysis Parameters**
   - Enter game/matchup query (e.g., "Chiefs vs Bills NFL")
   - Select sport type (NFL, NBA, MLB, etc.)
   - Choose analysis options (Market Analysis, News Sentiment, Statistical Models)

2. **Advanced Settings** (Optional)
   - Adjust confidence thresholds
   - Set maximum bet percentages
   - Configure Monte Carlo simulation parameters

3. **Run Analysis**
   - Click "🚀 Run Analysis" to start the multi-agent workflow
   - Watch real-time chain of thought reasoning
   - Monitor progress through analysis phases

4. **Review Results**
   - **Probabilities Tab**: View probability estimates with confidence intervals
   - **Recommendations Tab**: See betting recommendations with expected values
   - **Chain of Thought Tab**: Examine complete AI reasoning process

### Understanding the Results

#### Probability Analysis
- **Point Estimates**: Most likely probability for each outcome
- **Confidence Intervals**: Range of probable values (95% confidence)
- **Model Confidence**: Overall system confidence in the analysis

#### Betting Recommendations
- **Expected Value**: Percentage return expected from the bet
- **Kelly Fraction**: Optimal bet size as percentage of bankroll
- **Confidence Rating**: High/Medium/Low confidence classification
- **Reasoning**: Detailed explanation of the recommendation

#### Chain of Thought
- **Agent Activities**: Real-time view of each agent's reasoning
- **Confidence Levels**: How certain each agent is about its analysis
- **Processing Steps**: Detailed breakdown of the analysis workflow
- **Timestamps**: When each reasoning step occurred

## 🏗️ Architecture Overview

### Agent System Design

The system employs a sophisticated multi-agent architecture where specialized agents collaborate to provide comprehensive analysis:

#### 1. Coordination Agent
- Orchestrates workflow between all agents
- Manages task scheduling and result synthesis
- Provides overall system coordination and error handling

#### 2. Data Collection Agent
- Interfaces with external APIs (The Odds API, ESPN, etc.)
- Implements intelligent caching and rate limiting
- Handles data validation and quality assurance
- Provides fallback mechanisms for API failures

#### 3. Statistical Analysis Agent
- Implements Poisson distribution models for scoring predictions
- Maintains Elo rating systems for team strength assessment
- Runs Monte Carlo simulations for complex scenario modeling
- Applies machine learning models for pattern recognition

#### 4. Market Analysis Agent
- Tracks betting line movements across multiple sportsbooks
- Identifies sharp money vs. public betting patterns
- Calculates closing line value and market efficiency
- Detects arbitrage opportunities and value bets

#### 5. News and Sentiment Analysis Agent
- Processes sports news from multiple sources
- Performs sentiment analysis on articles and social media
- Tracks injury reports and team news
- Quantifies impact of external factors on game outcomes

#### 6. Probability Calculation Agent
- Synthesizes results from all other agents
- Applies Bayesian updating for probability refinement
- Calculates expected values and Kelly Criterion recommendations
- Provides confidence intervals and uncertainty quantification

### BMasterAI Logging Integration

The system provides unprecedented transparency through comprehensive logging:

- **Event Tracking**: Every agent action and decision is logged
- **Reasoning Chains**: Complete thought processes are captured
- **Confidence Metrics**: Uncertainty levels are tracked and displayed
- **Performance Monitoring**: Processing times and success rates are recorded
- **Real-Time Updates**: Live streaming of analysis progress to the UI

## 🔧 Configuration Options

### Analysis Parameters

#### Confidence Thresholds
- **Minimum Confidence**: Filter out low-confidence recommendations
- **Default**: 0.6 (60% confidence minimum)

#### Risk Management
- **Maximum Bet Percentage**: Cap on recommended bet sizes
- **Default**: 5% of bankroll maximum

#### Simulation Settings
- **Monte Carlo Runs**: Number of simulations for probability estimation
- **Default**: 10,000 simulations

### Data Source Configuration

#### API Priorities
1. **Primary**: The Odds API for live betting odds
2. **Secondary**: ESPN API for team statistics
3. **Tertiary**: Tavily API for news and analysis
4. **Fallback**: Mock data for demonstration purposes

#### Caching Settings
- **Cache TTL**: 5 minutes for real-time data
- **Historical Data**: Cached for 24 hours
- **News Articles**: Cached for 1 hour

## 📊 Statistical Models

### Poisson Distribution Model
Used for predicting game scores based on:
- Team offensive and defensive efficiency
- Historical scoring patterns
- Pace of play adjustments
- Home field advantage factors

### Elo Rating System
Dynamic team strength ratings that account for:
- Recent performance trends
- Strength of schedule
- Margin of victory
- Home/away performance differences

### Monte Carlo Simulation
Comprehensive scenario modeling including:
- Player availability and injury impacts
- Weather condition effects
- Motivational factors (playoffs, rivalries)
- Random variance in performance

### Bayesian Probability Updates
Continuous refinement of probabilities using:
- New information integration
- Prior probability distributions
- Evidence weighting systems
- Confidence interval calculations

## 🛡️ Risk Management

### Responsible Gambling Features
- **Educational Focus**: Emphasizes learning over profit
- **Risk Warnings**: Clear disclaimers about gambling risks
- **Bankroll Management**: Kelly Criterion implementation
- **Confidence Thresholds**: Filters low-confidence bets

### Data Quality Assurance
- **Multiple Source Validation**: Cross-reference data across APIs
- **Error Handling**: Graceful degradation when sources fail
- **Quality Metrics**: Track data freshness and accuracy
- **Fallback Systems**: Mock data when APIs unavailable

## 🔍 Troubleshooting

### Common Issues

#### Application Won't Start
1. Check Python version (3.11+ required)
2. Verify all dependencies are installed
3. Ensure port 8501 is available
4. Check for missing API keys in .env file

#### API Errors
1. Verify API keys are correct and active
2. Check API rate limits and quotas
3. Ensure internet connection is stable
4. Review API documentation for changes

#### Performance Issues
1. Reduce Monte Carlo simulation count
2. Check available system memory
3. Close other resource-intensive applications
4. Consider upgrading hardware specifications

### Debug Mode
Enable debug logging by setting in `.env`:
```env
LOG_LEVEL=DEBUG
FLASK_DEBUG=True
```

## 📈 Performance Optimization

### System Performance
- **Async Processing**: Concurrent agent execution
- **Intelligent Caching**: Reduce redundant API calls
- **Connection Pooling**: Efficient database connections
- **Memory Management**: Optimized data structures

### Analysis Speed
- **Parallel Execution**: Multiple agents run simultaneously
- **Smart Caching**: Reuse recent calculations
- **Optimized Models**: Efficient statistical computations
- **Progressive Loading**: Display results as they become available

## 🔮 Future Enhancements

### Planned Features
- **Additional Sports**: MLB, NBA, NHL, College Sports
- **Live Betting**: Real-time odds tracking during games
- **Portfolio Management**: Multi-bet optimization
- **Mobile App**: Native iOS/Android applications
- **Advanced ML**: Deep learning models for prediction

### API Integrations
- **Additional Sportsbooks**: More comprehensive odds comparison
- **Social Media**: Twitter/Reddit sentiment analysis
- **Weather APIs**: Enhanced environmental factor analysis
- **Player Tracking**: Advanced performance metrics

## 📝 License and Disclaimer

### Educational Use Only
This application is designed for educational and demonstration purposes only. It showcases:
- Multi-agent AI system architecture
- Real-time reasoning transparency
- Advanced statistical modeling techniques
- Responsible AI development practices

### Important Disclaimers
- **No Gambling Guarantees**: This tool does not guarantee profits
- **Risk Warning**: Sports betting involves significant financial risk
- **Legal Compliance**: Users must comply with local gambling laws
- **Professional Advice**: Consult professionals for actual betting decisions

### Liability Limitation
The developers and contributors to this project are not responsible for:
- Financial losses from betting decisions
- Accuracy of predictions or recommendations
- Compliance with local gambling regulations
- Technical issues or system failures

## 🤝 Contributing

We welcome contributions to improve the system:

### Development Guidelines
1. Follow Python PEP 8 style guidelines
2. Add comprehensive docstrings to all functions
3. Include unit tests for new features
4. Update documentation for any changes
5. Ensure BMasterAI logging integration

### Contribution Process
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request with detailed description
5. Participate in code review process

## 📞 Support

### Documentation
- **Architecture Guide**: Detailed system design documentation
- **API Reference**: Complete agent and function documentation
- **User Manual**: Step-by-step usage instructions
- **Troubleshooting**: Common issues and solutions

### Community
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and questions
- **Wiki**: Additional documentation and examples
- **Changelog**: Version history and updates

---

**Built with ❤️ using BMasterAI Logging Framework, Agno Multi-Agent System, and Gemini AI**

*Remember: This tool is for educational purposes only. Always gamble responsibly and never bet more than you can afford to lose.*

