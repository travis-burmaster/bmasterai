# AI Stock Research Agent

A comprehensive AI-powered stock analysis tool that combines real-time market data, web research, and advanced AI analysis to provide intelligent investment recommendations.

## Features

- **Professional Stock Data**: Powered by Alpha Vantage API for accurate daily time series data
- **Web Research Integration**: Automated news and analysis gathering from MarketWatch, Investing.com, and Yahoo Finance
- **AI-Powered Recommendations**: Uses Google Gemini AI to provide BUY/HOLD/SELL recommendations based on both technical and fundamental analysis
- **Company Intelligence**: Automatic company name and business description lookup
- **Interactive Visualizations**: Real-time price charts with Plotly
- **Advanced Logging**: BMasterAI logging framework for comprehensive analysis tracking
- **Multi-Source Analysis**: Combines price data with recent news, earnings reports, and analyst insights

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment Variables**:
   Create a `.env` file with your API keys:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   ```

3. **Get API Keys**:
   - **Google AI (Gemini)**: Get your free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
   - **Alpha Vantage**: Get your free API key at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
   - **Firecrawl**: Get your API key at [Firecrawl](https://firecrawl.dev/)

4. **Run the Application**:
   ```bash
   streamlit run stock_research_agent.py
   ```

## Usage

1. **Stock Symbol**: Enter a US stock ticker symbol (e.g., AAPL, MSFT, GOOGL, DUK)
2. **Analysis Options**: 
   - **Web Research**: Enable to gather recent news, earnings reports, and analyst insights
   - **Time Period**: Select analysis timeframe (1d, 5d, 1mo, 3mo, 6mo, 1y)
3. **Analyze**: Click "🔍 Analyze Stock" to start comprehensive analysis
4. **Review Results**:
   - **Company Information**: Business description and overview
   - **Price Chart**: Interactive daily price visualization
   - **AI Recommendation**: BUY/HOLD/SELL recommendation with detailed explanation
   - **Web Research**: Recent news and market analysis (if enabled)

## Supported Stock Symbols

The application works with US stock ticker symbols. Examples:
- **AAPL** - Apple Inc.
- **MSFT** - Microsoft Corporation
- **GOOGL** - Alphabet Inc.
- **TSLA** - Tesla Inc.
- **AMZN** - Amazon.com Inc.

## Error Handling

The application includes robust error handling for:
- Invalid or delisted ticker symbols
- Network connectivity issues
- Missing or incomplete data
- API rate limits

If a stock symbol cannot be found or has no data available, the application will display helpful error messages and suggestions.

## Technical Architecture

### AI Agents
- **AlphaVantageAgent**: Fetches professional-grade daily stock data from Alpha Vantage
- **FirecrawlAgent**: Performs intelligent web research from financial news sources
- **CompanyInfoAgent**: Retrieves company names and business descriptions using Gemini AI
- **RecommendationAgent**: Provides comprehensive BUY/HOLD/SELL analysis combining technical and fundamental factors

### Data Sources
- **Stock Data**: Alpha Vantage API for accurate daily time series data
- **Web Research**: MarketWatch, Investing.com, Yahoo Finance via Firecrawl
- **AI Analysis**: Google Gemini 1.5 Flash for intelligent recommendations
- **Logging**: BMasterAI framework for comprehensive analysis tracking

### Key Features
- **Multi-Source Analysis**: Combines price trends with recent news and analyst reports
- **Intelligent Extraction**: Structured data extraction from financial news sites
- **Advanced Logging**: Task tracking, performance metrics, and error handling
- **Real-time Visualization**: Interactive price charts with Plotly
- **Comprehensive Recommendations**: Technical analysis enhanced with fundamental insights

### Dependencies
- `streamlit>=1.28.0` - Web application framework
- `agno>=0.1.0` - AI agent framework
- `firecrawl-py>=2.16.5` - Web scraping and extraction
- `bmasterai>=0.2.0` - Advanced logging and analytics
- `plotly>=5.15.0` - Interactive visualizations
- `pandas>=2.0.0` - Data manipulation
- `pydantic>=2.0.0` - Data validation and schemas

## What's New

### Recent Updates
- **🔄 Firecrawl Integration**: Upgraded to firecrawl-py 2.16.5 with proper `extract()` API usage
- **📰 Enhanced Web Research**: Targeted financial news extraction from MarketWatch and Investing.com
- **🤖 Smarter Recommendations**: AI now considers both technical analysis and recent news/earnings
- **📊 Professional Data**: Switched to Alpha Vantage for institutional-grade stock data
- **📝 Advanced Logging**: BMasterAI integration for comprehensive analysis tracking
- **🏢 Company Intelligence**: Automatic company information and business description lookup

## Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure all three API keys are set in your `.env` file
   - Verify API keys are valid and have sufficient quota
   - Alpha Vantage free tier allows 25 requests per day

2. **"No data available for symbol"**:
   - Verify the ticker symbol is correct (US stocks only)
   - Try a different symbol or check if the company is publicly traded
   - Some stocks may have limited historical data

3. **Web Research Errors**:
   - Firecrawl API may have rate limits or temporary issues
   - The application will continue with price analysis if web research fails
   - Check your Firecrawl API key and quota

4. **Pydantic Deprecation Warnings**:
   - These are from the firecrawl library and don't affect functionality
   - Will be resolved in future firecrawl updates

5. **BMasterAI Logging Issues**:
   - If BMasterAI is not available, the app falls back to standard Python logging
   - Install bmasterai package for advanced logging features

## License

This project is for educational and research purposes. Please respect the terms of service of data providers (Yahoo Finance, Google AI).