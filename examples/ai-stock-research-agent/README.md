# Stock Research Agent

A comprehensive AI-powered stock analysis tool built with Streamlit and Google's Gemini AI model.

## Features

- **Real-time Stock Data**: Fetches current stock prices, volume, market cap, and other key metrics
- **Technical Analysis**: Calculates moving averages, RSI, momentum, and volatility indicators
- **Market Sentiment**: Scrapes and analyzes news headlines for sentiment analysis
- **Interactive Charts**: Displays price charts with Plotly
- **Institutional Holdings**: Shows major shareholders and ownership breakdown
- **AI-Powered Insights**: Uses Gemini AI for intelligent analysis and recommendations
- **Stock Ranking**: Compares multiple tickers by recent 30-day return
- **Recommendation Confidence**: Provides confidence scores with AI recommendations

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment Variables**:
   Create a `.env` file with your Google AI API key:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

3. **Run the Application**:
   ```bash
   streamlit run stock_research_agent.py
   ```

## Usage

1. **Enter API Key**: Input your Google AI (Gemini) API key in the sidebar
2. **Stock Symbol**: Enter a US stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
3. **Compare Symbols**: Optionally provide additional tickers (comma-separated) to rank by 30-day return
4. **Analysis Options**: Choose which analyses to perform:
   - Technical Analysis
   - Market Sentiment
   - Institutional Holdings
   - Stock Insights
5. **Time Period**: Select the time period for analysis (1d to 1y)
6. **Analyze**: Click the "Analyze Stock" button to start the analysis

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

## Technical Details

### Data Sources
- **Stock Data**: Yahoo Finance API via yfinance library
- **News Data**: Web scraping from Yahoo Finance news pages
- **AI Analysis**: Google Gemini AI model for sentiment analysis and insights

### Architecture
- **StockDataAgent**: Handles stock data fetching and parsing
- **TechnicalAnalysisAgent**: Performs technical indicator calculations
- **MarketSentimentAgent**: Scrapes news and analyzes sentiment
- **Streamlit UI**: Interactive web interface

### Dependencies
- `streamlit` - Web application framework
- `yfinance` - Yahoo Finance data access
- `agno` - AI agent framework
- `plotly` - Interactive charts
- `pandas` - Data manipulation
- `beautifulsoup4` - Web scraping
- `requests` - HTTP requests

## Troubleshooting

### Common Issues

1. **"No module named 'data_api'"**:
   - Ensure you're running from the correct directory
   - The `data_api.py` file should be in the same directory as `stock_research_agent.py`

2. **"No data available for symbol"**:
   - Verify the ticker symbol is correct
   - Try a different time period
   - Some stocks may be delisted or have limited data

3. **News scraping errors**:
   - Yahoo Finance may block requests or change their structure
   - The application will continue to work with other features

4. **API rate limits**:
   - Wait a few minutes between requests
   - Consider using a different time period or fewer analysis options

## License

This project is for educational and research purposes. Please respect the terms of service of data providers (Yahoo Finance, Google AI).