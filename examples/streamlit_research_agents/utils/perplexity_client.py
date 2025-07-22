import os
import time
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PerplexityModel(Enum):
    """Available Perplexity models"""
    LLAMA_3_1_SONAR_SMALL_128K_ONLINE = "llama-3.1-sonar-small-128k-online"
    LLAMA_3_1_SONAR_LARGE_128K_ONLINE = "llama-3.1-sonar-large-128k-online"
    LLAMA_3_1_SONAR_HUGE_128K_ONLINE = "llama-3.1-sonar-huge-128k-online"
    LLAMA_3_1_SONAR_SMALL_128K_CHAT = "llama-3.1-sonar-small-128k-chat"
    LLAMA_3_1_SONAR_LARGE_128K_CHAT = "llama-3.1-sonar-large-128k-chat"

@dataclass
class PerplexityResponse:
    """Structured response from Perplexity API"""
    content: str
    citations: List[Dict[str, Any]]
    model: str
    usage: Dict[str, int]
    created: int
    raw_response: Dict[str, Any]

@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    requests_remaining: int
    requests_reset_time: datetime
    tokens_remaining: int
    tokens_reset_time: datetime

class PerplexityAPIError(Exception):
    """Custom exception for Perplexity API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class PerplexityClient:
    """
    Wrapper client for Perplexity API interactions with rate limiting,
    error handling, and response formatting.
    """
    
    BASE_URL = "https://api.perplexity.ai"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: PerplexityModel = PerplexityModel.LLAMA_3_1_SONAR_LARGE_128K_ONLINE,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 60
    ):
        """
        Initialize Perplexity client
        
        Args:
            api_key: Perplexity API key (if None, will try to get from environment)
            default_model: Default model to use for requests
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key is required. Set PERPLEXITY_API_KEY environment variable or pass api_key parameter.")
        
        self.default_model = default_model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        # Rate limiting tracking
        self._rate_limit_info: Optional[RateLimitInfo] = None
        self._last_request_time: Optional[datetime] = None
        
        # Session for connection pooling
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Initialized Perplexity client with model: {default_model.value}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "BMasterAI-Research-Agents/1.0"
                }
            )
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _update_rate_limit_info(self, headers: Dict[str, str]):
        """Update rate limit information from response headers"""
        try:
            self._rate_limit_info = RateLimitInfo(
                requests_remaining=int(headers.get("x-ratelimit-requests-remaining", 0)),
                requests_reset_time=datetime.fromtimestamp(
                    int(headers.get("x-ratelimit-requests-reset", 0))
                ),
                tokens_remaining=int(headers.get("x-ratelimit-tokens-remaining", 0)),
                tokens_reset_time=datetime.fromtimestamp(
                    int(headers.get("x-ratelimit-tokens-reset", 0))
                )
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")
    
    async def _wait_for_rate_limit(self):
        """Wait if rate limit is exceeded"""
        if not self._rate_limit_info:
            return
        
        now = datetime.now()
        
        # Check if we need to wait for request rate limit
        if (self._rate_limit_info.requests_remaining <= 0 and 
            now < self._rate_limit_info.requests_reset_time):
            wait_time = (self._rate_limit_info.requests_reset_time - now).total_seconds()
            logger.info(f"Rate limit exceeded, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        # Check if we need to wait for token rate limit
        if (self._rate_limit_info.tokens_remaining <= 100 and 
            now < self._rate_limit_info.tokens_reset_time):
            wait_time = (self._rate_limit_info.tokens_reset_time - now).total_seconds()
            logger.info(f"Token limit low, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
    
    async def _make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Perplexity API with retry logic
        
        Args:
            endpoint: API endpoint
            data: Request payload
            retry_count: Current retry attempt
            
        Returns:
            Response data
            
        Raises:
            PerplexityAPIError: If request fails after all retries
        """
        await self._ensure_session()
        await self._wait_for_rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            self._last_request_time = datetime.now()
            
            async with self._session.post(url, json=data) as response:
                # Update rate limit info
                self._update_rate_limit_info(dict(response.headers))
                
                response_data = await response.json()
                
                if response.status == 200:
                    return response_data
                elif response.status == 429:  # Rate limit exceeded
                    if retry_count < self.max_retries:
                        wait_time = self.retry_delay * (2 ** retry_count)
                        logger.warning(f"Rate limited, retrying in {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(endpoint, data, retry_count + 1)
                    else:
                        raise PerplexityAPIError(
                            "Rate limit exceeded and max retries reached",
                            response.status,
                            response_data
                        )
                elif response.status >= 500:  # Server error
                    if retry_count < self.max_retries:
                        wait_time = self.retry_delay * (2 ** retry_count)
                        logger.warning(f"Server error {response.status}, retrying in {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(endpoint, data, retry_count + 1)
                    else:
                        raise PerplexityAPIError(
                            f"Server error: {response.status}",
                            response.status,
                            response_data
                        )
                else:
                    # Client error
                    error_message = response_data.get("error", {}).get("message", f"HTTP {response.status}")
                    raise PerplexityAPIError(
                        f"API error: {error_message}",
                        response.status,
                        response_data
                    )
                    
        except aiohttp.ClientError as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(f"Connection error, retrying in {wait_time} seconds: {e}")
                await asyncio.sleep(wait_time)
                return await self._make_request(endpoint, data, retry_count + 1)
            else:
                raise PerplexityAPIError(f"Connection error after {self.max_retries} retries: {e}")
        except asyncio.TimeoutError:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.warning(f"Request timeout, retrying in {wait_time} seconds")
                await asyncio.sleep(wait_time)
                return await self._make_request(endpoint, data, retry_count + 1)
            else:
                raise PerplexityAPIError(f"Request timeout after {self.max_retries} retries")
    
    def _extract_citations(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and format citations from response"""
        citations = []
        
        # Extract from choices if available
        choices = response_data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            if "citations" in message:
                citations.extend(message["citations"])
        
        # Extract from top-level citations if available
        if "citations" in response_data:
            citations.extend(response_data["citations"])
        
        return citations
    
    async def search(
        self,
        query: str,
        model: Optional[PerplexityModel] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
        return_citations: bool = True,
        return_images: bool = False
    ) -> PerplexityResponse:
        """
        Perform a search query using Perplexity API
        
        Args:
            query: Search query
            model: Model to use (defaults to client default)
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0-2.0)
            system_prompt: System prompt to guide response
            return_citations: Whether to return citations
            return_images: Whether to return images
            
        Returns:
            PerplexityResponse object with structured data
        """
        model = model or self.default_model
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})
        
        payload = {
            "model": model.value,
            "messages": messages,
            "temperature": temperature,
            "return_citations": return_citations,
            "return_images": return_images
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            response_data = await self._make_request("chat/completions", payload)
            
            # Extract content from response
            choices = response_data.get("choices", [])
            content = ""
            if choices:
                content = choices[0].get("message", {}).get("content", "")
            
            # Extract citations
            citations = self._extract_citations(response_data)
            
            # Extract usage information
            usage = response_data.get("usage", {})
            
            return PerplexityResponse(
                content=content,
                citations=citations,
                model=response_data.get("model", model.value),
                usage=usage,
                created=response_data.get("created", int(time.time())),
                raw_response=response_data
            )
            
        except Exception as e:
            logger.error(f"Search failed for query '{query[:100]}...': {e}")
            raise
    
    async def multi_search(
        self,
        queries: List[str],
        model: Optional[PerplexityModel] = None,
        max_concurrent: int = 3,
        **kwargs
    ) -> List[PerplexityResponse]:
        """
        Perform multiple search queries concurrently
        
        Args:
            queries: List of search queries
            model: Model to use
            max_concurrent: Maximum concurrent requests
            **kwargs: Additional arguments passed to search()
            
        Returns:
            List of PerplexityResponse objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_with_semaphore(query: str) -> PerplexityResponse:
            async with semaphore:
                return await self.search(query, model=model, **kwargs)
        
        tasks = [search_with_semaphore(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Query {i} failed: {result}")
                # Create empty response for failed queries
                processed_results.append(PerplexityResponse(
                    content="",
                    citations=[],
                    model=model.value if model else self.default_model.value,
                    usage={},
                    created=int(time.time()),
                    raw_response={"error": str(result)}
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_rate_limit_info(self) -> Optional[RateLimitInfo]:
        """Get current rate limit information"""
        return self._rate_limit_info
    
    def is_rate_limited(self) -> bool:
        """Check if currently rate limited"""
        if not self._rate_limit_info:
            return False
        
        now = datetime.now()
        return (
            (self._rate_limit_info.requests_remaining <= 0 and 
             now < self._rate_limit_info.requests_reset_time) or
            (self._rate_limit_info.tokens_remaining <= 100 and 
             now < self._rate_limit_info.tokens_reset_time)
        )

# Convenience function for quick searches
async def quick_search(
    query: str,
    api_key: Optional[str] = None,
    model: PerplexityModel = PerplexityModel.LLAMA_3_1_SONAR_LARGE_128K_ONLINE
) -> PerplexityResponse:
    """
    Perform a quick search without managing client lifecycle
    
    Args:
        query: Search query
        api_key: API key (optional, will use environment variable)
        model: Model to use
        
    Returns:
        PerplexityResponse object
    """
    async with PerplexityClient(api_key=api_key, default_model=model) as client:
        return await client.search(query)