import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()

class StockNewsArticle(BaseModel):
    title: str = Field(description="Article title")
    content: str = Field(description="Article content or summary")
    url: str = Field(description="Article URL")
    source: str = Field(description="News source")
    date: Optional[str] = Field(description="Publication date if available")

class StockNewsResponse(BaseModel):
    articles: List[StockNewsArticle] = Field(description="List of news articles found")
    total_count: int = Field(description="Total number of articles found")

class FirecrawlAgent:
    """Agent for performing stock news research using the Firecrawl API"""

    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("Firecrawl API key not found in environment variables.")
        self.app = FirecrawlApp(api_key=self.api_key)

    def search(self, query: str):
        """Search for stock news and analysis from MarketWatch and Investing.com"""
        try:
            # Extract stock symbol from query
            symbol = query.split()[0] if query else "STOCK"
            
            # Create targeted URLs for financial news sites
            urls_to_search = [
                f"https://www.marketwatch.com/investing/stock/{symbol.lower()}",
                f"https://www.marketwatch.com/investing/stock/{symbol.lower()}/news",
                f"https://www.investing.com/search/?q={symbol}",
                f"https://finance.yahoo.com/quote/{symbol.upper()}/news/"
            ]
            
            # Create comprehensive prompt for financial news extraction
            prompt = f"""You are extracting financial news and analysis about stock {symbol}. 
            Extract ALL relevant news articles, analyst reports, and market commentary you can find.

            EXTRACTION INSTRUCTIONS:
            1. Find ALL news articles and analysis related to {symbol}
            2. For EACH article, extract:
               - title: Article headline (required)
               - content: Article summary or key points (required, max 500 chars)
               - url: Direct link to the article if available
               - source: News source name (MarketWatch, Investing.com, etc.)
               - date: Publication date if visible

            3. FOCUS ON:
               - Recent earnings reports
               - Analyst upgrades/downgrades
               - Company announcements
               - Market sentiment
               - Price target changes
               - Industry news affecting the stock

            4. RETURN FORMAT:
               - Extract at least 5-10 articles if available
               - Prioritize recent news (last 30 days)
               - Include both positive and negative sentiment
               - Focus on actionable investment insights

            Extract comprehensive financial news and analysis for investment decision making.
            """

            # Use Firecrawl extract method (like the real estate example)
            raw_response = self.app.extract(
                urls_to_search,
                prompt=prompt,
                schema=StockNewsResponse.model_json_schema()
            )
            
            # Process the response
            if hasattr(raw_response, 'success') and raw_response.success:
                # Handle Firecrawl response object
                articles = raw_response.data.get('articles', []) if hasattr(raw_response, 'data') else []
                
                # Convert to the expected format for the stock research agent
                scraped_results = []
                for article in articles:
                    scraped_results.append({
                        'content': article.get('content', ''),
                        'url': article.get('url', ''),
                        'metadata': {
                            'title': article.get('title', 'Financial News'),
                            'source': article.get('source', 'Financial News Site'),
                            'date': article.get('date', 'Recent')
                        }
                    })
                
                return scraped_results
                
            elif isinstance(raw_response, dict) and raw_response.get('success'):
                # Handle dictionary response
                articles = raw_response.get('data', {}).get('articles', [])
                
                # Convert to expected format
                scraped_results = []
                for article in articles:
                    scraped_results.append({
                        'content': article.get('content', ''),
                        'url': article.get('url', ''),
                        'metadata': {
                            'title': article.get('title', 'Financial News'),
                            'source': article.get('source', 'Financial News Site'),
                            'date': article.get('date', 'Recent')
                        }
                    })
                
                return scraped_results
            else:
                return {"error": f"Firecrawl extraction failed: {raw_response}"}
                
        except Exception as e:
            return {"error": f"Error during Firecrawl search: {e}"}
