import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class AlphaVantageApiClient:
    """API client for Alpha Vantage"""

    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"

    def get_time_series_daily(self, symbol: str, output_size: str = "compact") -> Dict[str, Any]:
        """
        Get time series daily data for a given stock symbol.
        """
        if not self.api_key:
            return {"error": "Alpha Vantage API key not found."}

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": output_size,
            "apikey": self.api_key,
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching data from Alpha Vantage: {e}"}
