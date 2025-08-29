"""
Data Collection Agent for Sports Betting Analysis System

This agent is responsible for gathering comprehensive data from multiple sources
including odds APIs, sports statistics APIs, and web scraping.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# Import Tavily for web search
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

from base_agent import BaseAgent, AgentResult


class DataCollectionAgent(BaseAgent):
    """
    Agent responsible for collecting data from multiple sources:
    - The Odds API for betting odds
    - ESPN API for team/player statistics
    - Tavily API for news and analysis
    - Web scraping for additional information
    """
    
    def __init__(self):
        super().__init__("data_collection_agent")
        
        # API configurations
        self.odds_api_key = os.getenv("THE_ODDS_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        
        # Initialize Tavily client
        if TAVILY_AVAILABLE and self.tavily_api_key:
            self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
        else:
            self.tavily_client = None
        
        # API endpoints
        self.odds_api_base = "https://api.the-odds-api.com/v4"
        self.espn_api_base = "http://site.api.espn.com/apis/site/v2/sports"
        
        # Cache for reducing API calls
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get("timestamp", 0)
        return (datetime.now().timestamp() - cached_time) < self.cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]
        return None
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any]):
        """Set data in cache with timestamp"""
        self.cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now().timestamp()
        }
    
    async def get_odds_data(self, sport: str = "americanfootball_nfl", 
                           regions: str = "us", markets: str = "h2h,spreads,totals") -> Dict[str, Any]:
        """
        Get betting odds from The Odds API
        
        Args:
            sport: Sport key (e.g., 'americanfootball_nfl', 'basketball_nba')
            regions: Regions to get odds for (e.g., 'us', 'uk', 'au')
            markets: Markets to get odds for (e.g., 'h2h', 'spreads', 'totals')
        """
        cache_key = f"odds_{sport}_{regions}_{markets}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            self.log_thinking_step(
                step_type="cache_hit",
                reasoning=f"Using cached odds data for {sport}",
                confidence=1.0
            )
            return cached_data
        
        if not self.odds_api_key:
            self.log_thinking_step(
                step_type="api_unavailable",
                reasoning="The Odds API key not available, using mock data",
                confidence=0.3
            )
            return self._get_mock_odds_data(sport)
        
        try:
            self.log_thinking_step(
                step_type="api_request",
                reasoning=f"Fetching odds data from The Odds API for {sport}",
                confidence=0.8
            )
            
            url = f"{self.odds_api_base}/sports/{sport}/odds"
            params = {
                "apiKey": self.odds_api_key,
                "regions": regions,
                "markets": markets,
                "oddsFormat": "decimal",
                "dateFormat": "iso"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._set_cache(cache_key, data)
                        
                        self.log_thinking_step(
                            step_type="api_success",
                            reasoning=f"Successfully retrieved odds for {len(data)} games",
                            confidence=0.9,
                            data={"games_count": len(data)}
                        )
                        
                        return data
                    else:
                        error_text = await response.text()
                        raise Exception(f"API request failed with status {response.status}: {error_text}")
        
        except Exception as e:
            self.log_thinking_step(
                step_type="api_error",
                reasoning=f"Failed to fetch odds data: {str(e)}",
                confidence=0.1
            )
            return self._get_mock_odds_data(sport)
    
    def _get_mock_odds_data(self, sport: str) -> List[Dict[str, Any]]:
        """Generate mock odds data for testing purposes"""
        return [
            {
                "id": "mock_game_1",
                "sport_key": sport,
                "sport_title": "NFL" if "nfl" in sport else "NBA" if "nba" in sport else "Unknown",
                "commence_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "home_team": "Team A",
                "away_team": "Team B",
                "bookmakers": [
                    {
                        "key": "draftkings",
                        "title": "DraftKings",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Team A", "price": 1.85},
                                    {"name": "Team B", "price": 1.95}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    
    async def get_team_stats(self, sport: str = "football", league: str = "nfl") -> Dict[str, Any]:
        """
        Get team statistics from ESPN API
        
        Args:
            sport: Sport type (football, basketball, etc.)
            league: League (nfl, nba, etc.)
        """
        cache_key = f"team_stats_{sport}_{league}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            self.log_thinking_step(
                step_type="cache_hit",
                reasoning=f"Using cached team stats for {sport}/{league}",
                confidence=1.0
            )
            return cached_data
        
        try:
            self.log_thinking_step(
                step_type="api_request",
                reasoning=f"Fetching team statistics from ESPN API for {sport}/{league}",
                confidence=0.7
            )
            
            # ESPN API endpoints for different data
            endpoints = [
                f"{self.espn_api_base}/{sport}/{league}/teams",
                f"{self.espn_api_base}/{sport}/{league}/standings",
                f"{self.espn_api_base}/{sport}/{league}/scoreboard"
            ]
            
            all_data = {}
            
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    try:
                        async with session.get(endpoint) as response:
                            if response.status == 200:
                                data = await response.json()
                                endpoint_name = endpoint.split('/')[-1]
                                all_data[endpoint_name] = data
                                
                                self.log_thinking_step(
                                    step_type="api_partial_success",
                                    reasoning=f"Successfully retrieved {endpoint_name} data",
                                    confidence=0.8
                                )
                    except Exception as e:
                        self.log_thinking_step(
                            step_type="api_partial_error",
                            reasoning=f"Failed to fetch {endpoint}: {str(e)}",
                            confidence=0.3
                        )
            
            if all_data:
                self._set_cache(cache_key, all_data)
                return all_data
            else:
                return self._get_mock_team_stats(sport, league)
        
        except Exception as e:
            self.log_thinking_step(
                step_type="api_error",
                reasoning=f"Failed to fetch team stats: {str(e)}",
                confidence=0.1
            )
            return self._get_mock_team_stats(sport, league)
    
    def _get_mock_team_stats(self, sport: str, league: str) -> Dict[str, Any]:
        """Generate mock team statistics for testing"""
        return {
            "teams": {
                "items": [
                    {
                        "id": "1",
                        "displayName": "Team A",
                        "abbreviation": "TEA",
                        "record": {"items": [{"stats": [{"value": 8}, {"value": 4}]}]},
                        "statistics": [
                            {"name": "pointsPerGame", "value": 24.5},
                            {"name": "pointsAllowedPerGame", "value": 18.2}
                        ]
                    },
                    {
                        "id": "2", 
                        "displayName": "Team B",
                        "abbreviation": "TEB",
                        "record": {"items": [{"stats": [{"value": 6}, {"value": 6}]}]},
                        "statistics": [
                            {"name": "pointsPerGame", "value": 21.8},
                            {"name": "pointsAllowedPerGame", "value": 22.1}
                        ]
                    }
                ]
            }
        }
    
    async def get_news_and_analysis(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Get news and analysis using Tavily API
        
        Args:
            query: Search query for news and analysis
            max_results: Maximum number of results to return
        """
        cache_key = f"news_{hash(query)}_{max_results}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            self.log_thinking_step(
                step_type="cache_hit",
                reasoning=f"Using cached news data for query: {query}",
                confidence=1.0
            )
            return cached_data
        
        if not self.tavily_client:
            self.log_thinking_step(
                step_type="api_unavailable",
                reasoning="Tavily API not available, using mock news data",
                confidence=0.2
            )
            return self._get_mock_news_data(query)
        
        try:
            self.log_thinking_step(
                step_type="api_request",
                reasoning=f"Searching for news and analysis: {query}",
                confidence=0.8
            )
            
            # Use Tavily to search for relevant news and analysis
            search_result = self.tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_domains=["espn.com", "nfl.com", "nba.com", "bleacherreport.com", 
                               "si.com", "cbssports.com", "yahoo.com"],
                include_answer=True
            )
            
            self._set_cache(cache_key, search_result)
            
            self.log_thinking_step(
                step_type="api_success",
                reasoning=f"Retrieved {len(search_result.get('results', []))} news articles",
                confidence=0.9,
                data={"articles_count": len(search_result.get('results', []))}
            )
            
            return search_result
        
        except Exception as e:
            self.log_thinking_step(
                step_type="api_error",
                reasoning=f"Failed to fetch news data: {str(e)}",
                confidence=0.1
            )
            return self._get_mock_news_data(query)
    
    def _get_mock_news_data(self, query: str) -> Dict[str, Any]:
        """Generate mock news data for testing"""
        return {
            "answer": f"Mock analysis for {query}: Teams are evenly matched with recent form favoring the home team.",
            "results": [
                {
                    "title": f"Analysis: {query} Preview",
                    "url": "https://example.com/analysis",
                    "content": "Mock content about the upcoming game. Key players are healthy and weather conditions are favorable.",
                    "score": 0.9,
                    "published_date": datetime.now().isoformat()
                },
                {
                    "title": f"Injury Report: {query}",
                    "url": "https://example.com/injuries",
                    "content": "Mock injury report showing all key players are expected to play.",
                    "score": 0.8,
                    "published_date": (datetime.now() - timedelta(hours=2)).isoformat()
                }
            ]
        }
    
    async def collect_comprehensive_data(self, game_query: str, sport: str = "americanfootball_nfl") -> Dict[str, Any]:
        """
        Collect comprehensive data for a specific game or matchup
        
        Args:
            game_query: Query describing the game (e.g., "Chiefs vs Bills")
            sport: Sport type for odds API
        """
        self.log_thinking_step(
            step_type="comprehensive_collection_start",
            reasoning=f"Starting comprehensive data collection for: {game_query}",
            confidence=0.8
        )
        
        # Collect data from all sources in parallel
        tasks = [
            self.get_odds_data(sport),
            self.get_team_stats(),
            self.get_news_and_analysis(f"{game_query} betting analysis preview odds")
        ]
        
        try:
            odds_data, team_stats, news_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            result_data = {}
            
            if isinstance(odds_data, Exception):
                self.log_thinking_step(
                    step_type="odds_collection_error",
                    reasoning=f"Odds collection failed: {str(odds_data)}",
                    confidence=0.2
                )
                result_data["odds"] = {"error": str(odds_data)}
            else:
                result_data["odds"] = odds_data
            
            if isinstance(team_stats, Exception):
                self.log_thinking_step(
                    step_type="stats_collection_error", 
                    reasoning=f"Team stats collection failed: {str(team_stats)}",
                    confidence=0.2
                )
                result_data["team_stats"] = {"error": str(team_stats)}
            else:
                result_data["team_stats"] = team_stats
            
            if isinstance(news_data, Exception):
                self.log_thinking_step(
                    step_type="news_collection_error",
                    reasoning=f"News collection failed: {str(news_data)}",
                    confidence=0.2
                )
                result_data["news"] = {"error": str(news_data)}
            else:
                result_data["news"] = news_data
            
            # Calculate overall data quality score
            successful_sources = sum(1 for key in result_data if "error" not in result_data[key])
            total_sources = len(result_data)
            data_quality = successful_sources / total_sources if total_sources > 0 else 0.0
            
            self.log_thinking_step(
                step_type="comprehensive_collection_complete",
                reasoning=f"Data collection completed with {successful_sources}/{total_sources} sources successful",
                confidence=data_quality,
                data={
                    "successful_sources": successful_sources,
                    "total_sources": total_sources,
                    "data_quality_score": data_quality
                }
            )
            
            result_data["collection_metadata"] = {
                "query": game_query,
                "sport": sport,
                "collection_time": datetime.now().isoformat(),
                "successful_sources": successful_sources,
                "total_sources": total_sources,
                "data_quality_score": data_quality
            }
            
            return result_data
        
        except Exception as e:
            self.log_thinking_step(
                step_type="comprehensive_collection_error",
                reasoning=f"Comprehensive data collection failed: {str(e)}",
                confidence=0.0
            )
            raise e
    
    async def run_async(self) -> AgentResult:
        """Main execution method for the data collection agent"""
        task_id = self.start_task("Comprehensive sports data collection")
        
        try:
            # Default collection for demonstration
            default_query = "NFL game analysis"
            
            self.log_thinking_step(
                step_type="agent_start",
                reasoning="Starting data collection agent with default query",
                confidence=0.8,
                data={"default_query": default_query}
            )
            
            collected_data = await self.collect_comprehensive_data(default_query)
            
            return self.complete_task(
                task_id=task_id,
                success=True,
                result_data=collected_data,
                confidence=collected_data.get("collection_metadata", {}).get("data_quality_score", 0.5)
            )
        
        except Exception as e:
            return self.complete_task(
                task_id=task_id,
                success=False,
                result_data={},
                confidence=0.0,
                error_message=str(e)
            )

