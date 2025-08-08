import os
import streamlit as st
import json
import time
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import sys
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Import local data API client
from alpha_vantage_api import AlphaVantageApiClient
from firecrawl_agent import FirecrawlAgent

# Agno and AI imports
from agno.agent import Agent
from agno.models.google import Gemini
from pydantic import BaseModel, Field
from typing import List, Optional

# BMasterAI Logging Integration
try:
    from bmasterai.logging import BMasterLogger, LogLevel, EventType
    BMASTERAI_AVAILABLE = True
except ImportError:
    # Fallback logging if bmasterai is not available
    import logging
    BMASTERAI_AVAILABLE = False
    print("BMasterAI not available, using standard logging")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# API keys - must be set in environment variables
DEFAULT_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize BMasterAI Logger
if BMASTERAI_AVAILABLE:
    logger = BMasterLogger(
        log_file="stock_research_agent.log",
        json_log_file="stock_research_agent.json",
        log_level=LogLevel.INFO,
        enable_console=True,
        enable_file=True,
        enable_json=True
    )
else:
    # Fallback to standard logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class AlphaVantageAgent:
    """Agent for collecting stock data from Alpha Vantage"""

    def __init__(self):
        self.api_client = AlphaVantageApiClient()

    @property
    def agent_id(self):
        return "alpha_vantage_agent"

    def get_daily_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch daily time series data from Alpha Vantage"""
        task_id = f"alpha_vantage_daily_{symbol}_{int(time.time())}"
        start_time = time.time()

        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message=f"Starting Alpha Vantage daily data fetch for {symbol}",
                level=LogLevel.INFO,
                metadata={
                    "task_id": task_id,
                    "symbol": symbol,
                }
            )

        try:
            response = self.api_client.get_time_series_daily(symbol)
            extract_duration = (time.time() - start_time) * 1000

            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"Alpha Vantage daily data fetch completed for {symbol}",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "symbol": symbol,
                        "duration_ms": extract_duration,
                    }
                )

            return response

        except Exception as e:
            error_msg = f"Error fetching Alpha Vantage data for {symbol}: {str(e)}"

            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={"task_id": task_id, "symbol": symbol}
                )
            else:
                logger.error(error_msg)

            return {"error": error_msg}


def rank_stocks(symbols: List[str], alpha_agent: AlphaVantageAgent, window: int = 30) -> List[Dict[str, Any]]:
    """Rank stocks by percentage return over the given window of days."""
    rankings: List[Dict[str, Any]] = []
    for sym in symbols:
        data = alpha_agent.get_daily_data(sym)
        if "Time Series (Daily)" not in data:
            continue
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index").astype(float).sort_index()
        recent = df.tail(window)
        if len(recent) >= 2:
            change = (recent["4. close"].iloc[-1] - recent["4. close"].iloc[0]) / recent["4. close"].iloc[0] * 100
            rankings.append({"symbol": sym.upper(), "return_pct": round(change, 2)})
    return sorted(rankings, key=lambda x: x["return_pct"], reverse=True)


class CompanyInfoAgent:
    """Agent for fetching company information"""

    def __init__(self, google_api_key: str):
        self.agent = Agent(
            model=Gemini(id="gemini-1.5-flash", api_key=google_api_key),
            markdown=True,
            description="I am a company information expert who provides company names and descriptions based on their stock ticker symbol."
        )

    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Get the company name and description for a given stock symbol."""
        try:
            prompt = f"""
            What is the full company name and a brief description of the business for the stock with the ticker symbol {symbol}?

            Respond in JSON format:
            {{
                "company_name": "Full Company Name",
                "description": "A brief description of the company's business."
            }}
            """
            response = self.agent.run(prompt)
            # Extract JSON from the response, which may be wrapped in markdown
            json_match = re.search(r"```json\n(.*?)\n```", response.content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.content

            return json.loads(json_str)
        except Exception as e:
            return {"error": f"Error getting company information: {e}"}


class RecommendationAgent:
    """Agent for providing buy/hold/sell recommendations"""

    def __init__(self, google_api_key: str):
        self.agent = Agent(
            model=Gemini(id="gemini-1.5-flash", api_key=google_api_key),
            markdown=True,
            description="I am a stock recommendation expert who provides buy, hold, or sell recommendations based on technical analysis."
        )

    def get_recommendation(self, symbol: str, data: pd.DataFrame, time_period: str, web_research_data: Optional[List] = None) -> Dict[str, Any]:
        """Get a buy/hold/sell recommendation based on the data, time period, and recent news."""
        try:
            # Prepare web research context
            news_context = ""
            if web_research_data and not isinstance(web_research_data, dict):
                news_context = "\n\nRecent News and Analysis:\n"
                for item in web_research_data[:3]:  # Use top 3 results
                    if isinstance(item, dict) and 'content' in item:
                        title = item.get('metadata', {}).get('title', 'News Article')
                        content = item['content'][:800]  # Limit content length
                        news_context += f"- {title}: {content}...\n"
            
            prompt = f"""
            Analyze the following stock data for {symbol} over the last {time_period} and provide a recommendation.

            Stock Price Data:
            {data.to_string()}
            {news_context}

            Based on both the technical analysis of the price data AND the recent news/research, should I buy, hold, or sell?
            Consider how recent developments might impact the stock's future performance.
            Provide a comprehensive explanation that incorporates both technical and fundamental factors.

            Respond in JSON format:
            {{
                "recommendation": "BUY/HOLD/SELL",
                "confidence": "0-100 integer indicating confidence level",
                "explanation": "Your comprehensive explanation incorporating both technical analysis and recent news/developments."
            }}
            """
            response = self.agent.run(prompt)
            # Extract JSON from the response, which may be wrapped in markdown
            json_match = re.search(r"```json\n(.*?)\n```", response.content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.content

            return json.loads(json_str)
        except Exception as e:
            return {"error": f"Error getting recommendation: {e}"}


# Streamlit Application
def main():
    st.set_page_config(
        page_title="Stock Research Agent",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏦 Stock Research Agent")
    st.markdown("*Powered by Alpha Vantage*")
    st.warning(
        "This application is for educational purposes only and does not provide"
        " financial advice. Always consult a licensed financial advisor before"
        " making investment decisions. Travis Burmaster is not responsible for"
        " any financial opinions generated by this tool."
    )
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Stock symbol input
        symbol = st.text_input(
            "Stock Symbol",
            value="AAPL",
            help="Enter a US stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
        ).upper()
        compare_symbols = st.text_input(
            "Compare Symbols (comma-separated)",
            value="",
            help="Optional additional tickers for ranking by 30-day return",
        )

        
        # Analysis options
        st.subheader("Analysis Options")
        include_web_research = st.checkbox("Web Research", value=True)

        # Time period for analysis
        time_period = st.selectbox(
            "Time Period",
            ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
            index=2
        )

        # Analyze button
        analyze_button = st.button("🔍 Analyze Stock", type="primary")

    compare_list = [s.strip().upper() for s in compare_symbols.split(',') if s.strip()]
    if compare_list and symbol not in compare_list:
        compare_list.insert(0, symbol)

    
    # Main content area
    if analyze_button and symbol:
        with st.spinner(f"Analyzing {symbol}..."):
            # Initialize agent
            alpha_vantage_agent = AlphaVantageAgent()
            
            # Fetch stock data
            alpha_vantage_data = alpha_vantage_agent.get_daily_data(symbol)
            
            # Store results in session state
            st.session_state.analysis_results = {
                'symbol': symbol,
                'alpha_vantage_data': alpha_vantage_data,
                'timestamp': datetime.now()
            }
            if compare_list:
                rankings = rank_stocks(compare_list, alpha_vantage_agent)
                st.session_state.analysis_results['rankings'] = rankings


            web_research_data = None
            if include_web_research:
                firecrawl_agent = FirecrawlAgent()
                web_research_data = firecrawl_agent.search(f"{symbol} earnings analyst reports price target news")
                st.session_state.analysis_results['web_research_data'] = web_research_data

            recommendation_agent = RecommendationAgent(google_api_key=DEFAULT_GOOGLE_API_KEY)
            recommendation = recommendation_agent.get_recommendation(
                symbol, 
                pd.DataFrame.from_dict(alpha_vantage_data['Time Series (Daily)'], orient='index'), 
                time_period,
                web_research_data
            )
            st.session_state.analysis_results['recommendation'] = recommendation

            company_info_agent = CompanyInfoAgent(google_api_key=DEFAULT_GOOGLE_API_KEY)
            company_info = company_info_agent.get_company_info(symbol)
            st.session_state.analysis_results['company_info'] = company_info
    
    # Display results if available
    if 'analysis_results' in st.session_state and st.session_state.analysis_results:
        results = st.session_state.analysis_results
        symbol = results.get('symbol')
        av_data = results.get('alpha_vantage_data')
        
        if av_data and 'Time Series (Daily)' in av_data:
            st.header(f"📊 {av_data['Meta Data']['2. Symbol']} Analysis")

            if 'company_info' in results:
                company_info = results['company_info']
                if 'error' in company_info:
                    st.error(f"Could not retrieve company information: {company_info['error']}")
                else:
                    st.subheader(company_info['company_name'])
                    st.write(company_info['description'])

            df = pd.DataFrame.from_dict(av_data['Time Series (Daily)'], orient='index')
            
            # Create price chart
            st.subheader("📈 Price Chart")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['4. close'],
                mode='lines',
                name='Close Price',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.update_layout(
                title=f"{av_data['Meta Data']['2. Symbol']} Price Chart",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

            if 'rankings' in results:
                rankings = results['rankings']
                if rankings:
                    st.subheader("🏅 Stock Rankings (30-day return %)")
                    st.table(pd.DataFrame(rankings))

            if 'recommendation' in results:
                st.subheader("💡 Recommendation")
                recommendation = results['recommendation']
                if 'error' in recommendation:
                    st.error(f"Could not retrieve recommendation: {recommendation['error']}")
                else:
                    st.write(f"**Recommendation:** {recommendation['recommendation'].upper()}")
                    if 'confidence' in recommendation:
                        st.write(f"**Confidence:** {recommendation['confidence']}%")
                    st.write(f"**Explanation:** {recommendation['explanation']}")

            if 'web_research_data' in results:
                st.subheader("🌐 Web Research")
                web_data = results['web_research_data']
                if 'error' in web_data:
                    st.error(f"Could not retrieve web research data: {web_data['error']}")
                elif web_data:
                    for item in web_data:
                        st.write(f"**[{item['metadata']['title']}]({item['url']})**")
                        st.write(item['content'][:500] + "...")
                else:
                    st.info("No web research results found.")
            
        elif av_data and 'error' in av_data:
            st.error(f"❌ **Failed to retrieve data for {symbol}**")
            st.warning(f"**Reason:** {av_data['error']}")
        else:
            st.info("No analysis data available. Please run the stock analysis above.")
    # Footer
    st.markdown("---")
    st.markdown("*Powered by BMasterAI Logging Framework, Alpha Vantage, and Firecrawl*")

if __name__ == "__main__":
    main()