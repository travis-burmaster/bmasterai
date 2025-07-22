```python
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

from ..utils.perplexity_client import PerplexityClient
from bmasterai.agents.base_agent import BaseAgent


@dataclass
class SearchQuery:
    """Represents a search query with metadata"""
    query: str
    priority: int = 1
    category: str = "general"
    max_results: int = 10
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class SearchResult:
    """Represents a search result with structured data"""
    query: str
    content: str
    sources: List[str]
    relevance_score: float
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'content': self.content,
            'sources': self.sources,
            'relevance_score': self.relevance_score,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class SearchAgent(BaseAgent):
    """
    Specialized agent for information gathering using Perplexity API.
    Handles search queries, processes results, and maintains search history.
    """
    
    def __init__(self, 
                 name: str = "SearchAgent",
                 perplexity_api_key: str = None,
                 max_concurrent_searches: int = 3,
                 search_timeout: int = 30,
                 **kwargs):
        """
        Initialize the SearchAgent
        
        Args:
            name: Agent name
            perplexity_api_key: API key for Perplexity
            max_concurrent_searches: Maximum concurrent search requests
            search_timeout: Timeout for search requests in seconds
        """
        super().__init__(name=name, **kwargs)
        
        self.perplexity_client = PerplexityClient(api_key=perplexity_api_key)
        self.max_concurrent_searches = max_concurrent_searches
        self.search_timeout = search_timeout
        
        # Search management
        self.search_history: List[SearchResult] = []
        self.active_searches: Dict[str, asyncio.Task] = {}
        self.search_queue: List[SearchQuery] = []
        
        # Performance tracking
        self.total_searches = 0
        self.successful_searches = 0
        self.failed_searches = 0
        
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
    async def initialize(self) -> bool:
        """Initialize the search agent"""
        try:
            self.logger.info(f"Initializing {self.name}")
            
            # Test Perplexity API connection
            test_result = await self.perplexity_client.test_connection()
            if not test_result:
                self.logger.error("Failed to connect to Perplexity API")
                return False
                
            self.status = "ready"
            self.logger.info(f"{self.name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {str(e)}")
            self.status = "error"
            return False
    
    async def search(self, query: str, **kwargs) -> Optional[SearchResult]:
        """
        Perform a single search query
        
        Args:
            query: Search query string
            **kwargs: Additional search parameters
            
        Returns:
            SearchResult object or None if search failed
        """
        try:
            self.logger.info(f"Performing search: {query}")
            self.total_searches += 1
            
            # Create search query object
            search_query = SearchQuery(
                query=query,
                priority=kwargs.get('priority', 1),
                category=kwargs.get('category', 'general'),
                max_results=kwargs.get('max_results', 10)
            )
            
            # Perform search using Perplexity client
            response = await asyncio.wait_for(
                self.perplexity_client.search(
                    query=search_query.query,
                    max_results=search_query.max_results
                ),
                timeout=self.search_timeout
            )
            
            if not response:
                self.failed_searches += 1
                return None
            
            # Process and structure the response
            search_result = self._process_search_response(search_query, response)
            
            # Add to search history
            self.search_history.append(search_result)
            self.successful_searches += 1
            
            self.logger.info(f"Search completed successfully: {query}")
            return search_result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Search timeout for query: {query}")
            self.failed_searches += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {str(e)}")
            self.failed_searches += 1
            return None
    
    async def batch_search(self, queries: List[str], **kwargs) -> List[SearchResult]:
        """
        Perform multiple searches concurrently
        
        Args:
            queries: List of search query strings
            **kwargs: Additional search parameters
            
        Returns:
            List of SearchResult objects
        """
        try:
            self.logger.info(f"Starting batch search for {len(queries)} queries")
            
            # Create search tasks with concurrency limit
            semaphore = asyncio.Semaphore(self.max_concurrent_searches)
            
            async def limited_search(query: str) -> Optional[SearchResult]:
                async with semaphore:
                    return await self.search(query, **kwargs)
            
            # Execute searches concurrently
            tasks = [limited_search(query) for query in queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            valid_results = []
            for result in results:
                if isinstance(result, SearchResult):
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Batch search error: {str(result)}")
            
            self.logger.info(f"Batch search completed: {len(valid_results)}/{len(queries)} successful")
            return valid_results
            
        except Exception as e:
            self.logger.error(f"Batch search failed: {str(e)}")
            return []
    
    async def research_topic(self, topic: str, depth: str = "medium") -> Dict[str, Any]:
        """
        Perform comprehensive research on a topic
        
        Args:
            topic: Research topic
            depth: Research depth ("shallow", "medium", "deep")
            
        Returns:
            Structured research data
        """
        try:
            self.logger.info(f"Starting topic research: {topic} (depth: {depth})")
            
            # Generate search queries based on topic and depth
            queries = self._generate_research_queries(topic, depth)
            
            # Perform batch search
            search_results = await self.batch_search(queries)
            
            if not search_results:
                self.logger.warning(f"No search results for topic: {topic}")
                return {}
            
            # Analyze and structure results
            research_data = self._analyze_search_results(topic, search_results)
            
            self.logger.info(f"Topic research completed: {topic}")
            return research_data
            
        except Exception as e:
            self.logger.error(f"Topic research failed for '{topic}': {str(e)}")
            return {}
    
    def _generate_research_queries(self, topic: str, depth: str) -> List[str]:
        """Generate search queries for comprehensive topic research"""
        base_queries = [
            f"{topic} overview",
            f"{topic} latest developments",
            f"{topic} key concepts"
        ]
        
        if depth == "medium":
            base_queries.extend([
                f"{topic} applications",
                f"{topic} challenges",
                f"{topic} future trends"
            ])
        elif depth == "deep":
            base_queries.extend([
                f"{topic} applications",
                f"{topic} challenges",
                f"{topic} future trends",
                f"{topic} case studies",
                f"{topic} research papers",
                f"{topic} industry analysis",
                f"{topic} expert opinions"
            ])
        
        return base_queries
    
    def _process_search_response(self, query: SearchQuery, response: Dict[str, Any]) -> SearchResult:
        """Process raw search response into structured SearchResult"""
        try:
            content = response.get('content', '')
            sources = response.get('sources', [])
            
            # Calculate relevance score based on content quality
            relevance_score = self._calculate_relevance_score(query.query, content)
            
            # Extract metadata
            metadata = {
                'query_category': query.category,
                'query_priority': query.priority,
                'response_length': len(content),
                'source_count': len(sources),
                'processing_time': (datetime.now() - query.timestamp).total_seconds()
            }
            
            return SearchResult(
                query=query.query,
                content=content,
                sources=sources,
                relevance_score=relevance_score,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process search response: {str(e)}")
            # Return minimal result on error
            return SearchResult(
                query=query.query,
                content="",
                sources=[],
                relevance_score=0.0,
                timestamp=datetime.now(),
                metadata={'error': str(e)}
            )
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """Calculate relevance score for search result"""
        try:
            if not content:
                return 0.0
            
            # Simple relevance scoring based on query terms in content
            query_terms = query.lower().split()
            content_lower = content.lower()
            
            matches = sum(1 for term in query_terms if term in content_lower)
            score = matches / len(query_terms) if query_terms else 0.0
            
            # Boost score for longer, more detailed content
            length_factor = min(len(content) / 1000, 1.0)
            score = score * (0.7 + 0.3 * length_factor)
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5  # Default score on error
    
    def _analyze_search_results(self, topic: str, results: List[SearchResult]) -> Dict[str, Any]:
        """Analyze search results and create structured research data"""
        try:
            if not results:
                return {}
            
            # Aggregate data
            all_sources = []
            total_content = []
            avg_relevance = 0.0
            
            for result in results:
                all_sources.extend(result.sources)
                total_content.append(result.content)
                avg_relevance += result.relevance_score
            
            avg_relevance = avg_relevance / len(results)
            unique_sources = list(set(all_sources))
            
            # Create structured research data
            research_data = {
                'topic': topic,
                'summary': {
                    'total_searches': len(results),
                    'unique_sources': len(unique_sources),
                    'average_relevance': avg_relevance,
                    'total_content_length': sum(len(content) for content in total_content)
                },
                'search_results': [result.to_dict() for result in results],
                'sources': unique_sources,
                'timestamp': datetime.now().isoformat(),
                'agent': self.name
            }
            
            return research_data
            
        except Exception as e:
            self.logger.error(f"Failed to analyze search results: {str(e)}")
            return {'error': str(e)}
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search performance statistics"""
        success_rate = (self.successful_searches / self.total_searches * 100) if self.total_searches > 0 else 0
        
        return {
            'total_searches': self.total_searches,
            'successful_searches': self.successful_searches,
            'failed_searches': self.failed_searches,
            'success_rate': success_rate,
            'search_history_count': len(self.search_history),
            'active_searches': len(self.active_searches)
        }
    
    def clear_search_history(self):
        """Clear search history to free memory"""
        self.search_history.clear()
        self.logger.info("Search history cleared")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cancel active searches
            for task in self.active_searches.values():
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.active_searches:
                await asyncio.gather(*self.active_searches.values(), return_exceptions=True)
            
            # Cleanup Perplexity client
            if hasattr(self.perplexity_client, 'cleanup'):
                await self.perplexity_client.cleanup()
            
            self.logger.info(f"{self.name} cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
```