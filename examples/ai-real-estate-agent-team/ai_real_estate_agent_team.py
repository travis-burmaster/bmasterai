import os
import streamlit as st
import json
import time
import re
from agno.agent import Agent
from agno.models.google import Gemini
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime

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
load_dotenv()

# API keys - must be set in environment variables
DEFAULT_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEFAULT_FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Initialize BMasterAI Logger
if BMASTERAI_AVAILABLE:
    logger = BMasterLogger(
        log_file="real_estate_agent.log",
        json_log_file="real_estate_agent.json",
        log_level=LogLevel.INFO,
        enable_console=True,
        enable_file=True,
        enable_json=True
    )
else:
    # Fallback to standard logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Pydantic schemas
class PropertyDetails(BaseModel):
    address: str = Field(description="Full property address")
    price: Optional[str] = Field(description="Property price")
    bedrooms: Optional[str] = Field(description="Number of bedrooms")
    bathrooms: Optional[str] = Field(description="Number of bathrooms")
    square_feet: Optional[str] = Field(description="Square footage")
    property_type: Optional[str] = Field(description="Type of property")
    description: Optional[str] = Field(description="Property description")
    features: Optional[List[str]] = Field(description="Property features")
    images: Optional[List[str]] = Field(description="Property image URLs")
    agent_contact: Optional[str] = Field(description="Agent contact information")
    listing_url: Optional[str] = Field(description="Original listing URL")

class PropertyListing(BaseModel):
    properties: List[PropertyDetails] = Field(description="List of properties found")
    total_count: int = Field(description="Total number of properties found")
    source_website: str = Field(description="Website where properties were found")

class DirectFirecrawlAgent:
    """Agent with direct Firecrawl integration for property search and BMasterAI logging"""
    
    def __init__(self, firecrawl_api_key: str, google_api_key: str, model_id: str = "gemini-2.5-flash"):
        self.agent_id = f"property_search_agent_{uuid.uuid4().hex[:8]}"
        self.agent = Agent(
            model=Gemini(id=model_id, api_key=google_api_key),
            markdown=True,
            description="I am a real estate expert who helps find and analyze properties based on user preferences."
        )
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
        
        # Log agent initialization
        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_START,
                message="Property Search Agent initialized",
                level=LogLevel.INFO,
                metadata={
                    "model_id": model_id,
                    "agent_type": "DirectFirecrawlAgent"
                }
            )
        else:
            logger.info(f"Property Search Agent {self.agent_id} initialized")

    def find_properties_direct(self, city: str, state: str, user_criteria: dict, selected_websites: list) -> dict:
        """Direct Firecrawl integration for property search with comprehensive logging"""
        task_id = f"property_search_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        # Log task start
        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message=f"Starting property search for {city}, {state}",
                level=LogLevel.INFO,
                metadata={
                    "task_id": task_id,
                    "city": city,
                    "state": state,
                    "user_criteria": user_criteria,
                    "selected_websites": selected_websites
                }
            )
        else:
            logger.info(f"Starting property search for {city}, {state}")
        
        try:
            city_formatted = city.replace(' ', '-').lower()
            state_upper = state.upper() if state else ''
            
            # Create URLs for selected websites
            state_lower = state.lower() if state else ''
            city_trulia = city.replace(' ', '_')  # Trulia uses underscores for spaces
            search_urls = {
                "Zillow": f"https://www.zillow.com/homes/for_sale/{city_formatted}-{state_upper}/",
                "Realtor.com": f"https://www.realtor.com/realestateandhomes-search/{city_formatted}_{state_upper}/pg-1",
                "Trulia": f"https://www.trulia.com/{state_upper}/{city_trulia}/",
                "Homes.com": f"https://www.homes.com/homes-for-sale/{city_formatted}-{state_lower}/"
            }
            
            # Filter URLs based on selected websites
            urls_to_search = [url for site, url in search_urls.items() if site in selected_websites]
            
            # Log URL generation
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TOOL_USE,
                    message="Generated search URLs",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "urls_generated": len(urls_to_search),
                        "search_urls": search_urls
                    }
                )
            
            if not urls_to_search:
                error_msg = "No websites selected"
                if BMASTERAI_AVAILABLE:
                    logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_ERROR,
                        message=error_msg,
                        level=LogLevel.ERROR,
                        metadata={"task_id": task_id}
                    )
                return {"error": error_msg}
            
            # Create comprehensive prompt with specific schema guidance (matching old version)
            prompt = f"""You are extracting property listings from real estate websites. Extract EVERY property listing you can find on the page.

USER SEARCH CRITERIA:
- Budget: {user_criteria.get('budget_range', 'Any')}
- Property Type: {user_criteria.get('property_type', 'Any')}
- Bedrooms: {user_criteria.get('bedrooms', 'Any')}
- Bathrooms: {user_criteria.get('bathrooms', 'Any')}
- Min Square Feet: {user_criteria.get('min_sqft', 'Any')}
- Special Features: {user_criteria.get('special_features', 'Any')}

EXTRACTION INSTRUCTIONS:
1. Find ALL property listings on the page (usually 20-40 per page)
2. For EACH property, extract these fields:
   - address: Full street address (required)
   - price: Listed price with $ symbol (required) 
   - bedrooms: Number of bedrooms (required)
   - bathrooms: Number of bathrooms (required)
   - square_feet: Square footage if available
   - property_type: House/Condo/Townhouse/Apartment etc.
   - description: Brief property description if available
   - listing_url: Direct link to property details if available
   - agent_contact: Agent name/phone if visible

3. CRITICAL REQUIREMENTS:
   - Extract AT LEAST 10 properties if they exist on the page
   - Do NOT skip properties even if some fields are missing
   - Use "Not specified" for missing optional fields
   - Ensure address and price are always filled
   - Look for property cards, listings, search results

4. RETURN FORMAT:
   - Return JSON with "properties" array containing all extracted properties
   - Each property should be a complete object with all available fields
   - Set "total_count" to the number of properties extracted
   - Set "source_website" to the main website name (Zillow/Realtor/Trulia/Homes)

EXTRACT EVERY VISIBLE PROPERTY LISTING - DO NOT LIMIT TO JUST A FEW!
        """

            # Use Firecrawl extract with correct API format (like the old version)
            try:
                extract_start = time.time()
                
                # Log extraction start
                if BMASTERAI_AVAILABLE:
                    logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TOOL_USE,
                        message=f"Starting Firecrawl extraction for {len(urls_to_search)} URLs",
                        level=LogLevel.INFO,
                        metadata={
                            "task_id": task_id,
                            "urls_count": len(urls_to_search),
                            "urls": urls_to_search
                        }
                    )
                
                # Use the correct Firecrawl API format from the old version
                raw_response = self.firecrawl.extract(
                    urls_to_search,
                    prompt=prompt,
                    schema=PropertyListing.model_json_schema()
                )
                
                extract_duration = (time.time() - extract_start) * 1000
                
                # Log Firecrawl API call
                if BMASTERAI_AVAILABLE:
                    logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.LLM_CALL,
                        message="Firecrawl extraction completed",
                        level=LogLevel.INFO,
                        metadata={
                            "task_id": task_id,
                            "urls_processed": len(urls_to_search),
                            "success": True
                        },
                        duration_ms=extract_duration
                    )
                
                all_results = []
                
                # Process the response (adapted from old version)
                if hasattr(raw_response, 'success') and raw_response.success:
                    # Handle Firecrawl response object
                    properties = raw_response.data.get('properties', []) if hasattr(raw_response, 'data') else []
                    total_count = raw_response.data.get('total_count', 0) if hasattr(raw_response, 'data') else 0
                    
                    if properties:
                        result_data = {
                            'properties': properties,
                            'total_count': total_count,
                            'source_website': 'Multiple Sources'
                        }
                        all_results.append(result_data)
                        
                        # Log successful extraction
                        if BMASTERAI_AVAILABLE:
                            logger.log_event(
                                agent_id=self.agent_id,
                                event_type=EventType.PERFORMANCE_METRIC,
                                message="Properties extracted successfully",
                                level=LogLevel.INFO,
                                metadata={
                                    "task_id": task_id,
                                    "properties_found": len(properties),
                                    "total_count": total_count
                                }
                            )
                
                elif isinstance(raw_response, dict) and raw_response.get('success'):
                    # Handle dictionary response
                    properties = raw_response.get('data', {}).get('properties', [])
                    total_count = raw_response.get('data', {}).get('total_count', 0)
                    
                    if properties:
                        result_data = {
                            'properties': properties,
                            'total_count': total_count,
                            'source_website': 'Multiple Sources'
                        }
                        all_results.append(result_data)
                        
                        # Log successful extraction
                        if BMASTERAI_AVAILABLE:
                            logger.log_event(
                                agent_id=self.agent_id,
                                event_type=EventType.PERFORMANCE_METRIC,
                                message="Properties extracted successfully",
                                level=LogLevel.INFO,
                                metadata={
                                    "task_id": task_id,
                                    "properties_found": len(properties),
                                    "total_count": total_count
                                }
                            )
                
                else:
                    error_msg = f"Firecrawl extraction failed: {raw_response}"
                    if BMASTERAI_AVAILABLE:
                        logger.log_event(
                            agent_id=self.agent_id,
                            event_type=EventType.TASK_ERROR,
                            message=error_msg,
                            level=LogLevel.ERROR,
                            metadata={
                                "task_id": task_id,
                                "response": str(raw_response)
                            }
                        )
                    
            except Exception as e:
                error_msg = f"Error in Firecrawl extraction: {str(e)}"
                if BMASTERAI_AVAILABLE:
                    logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_ERROR,
                        message=error_msg,
                        level=LogLevel.ERROR,
                        metadata={
                            "task_id": task_id,
                            "error": str(e)
                        }
                    )
                else:
                    logger.error(error_msg)
                all_results = []
            
            # Calculate total duration and log task completion
            total_duration = (time.time() - start_time) * 1000
            total_properties = sum(len(result.get('properties', [])) for result in all_results)
            
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"Property search completed for {city}, {state}",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "total_properties_found": total_properties,
                        "websites_searched": len(urls_to_search),
                        "successful_extractions": len(all_results),
                        "city": city,
                        "state": state
                    },
                    duration_ms=total_duration
                )
            else:
                logger.info(f"Property search completed: {total_properties} properties found")
            
            return {
                "success": True,
                "results": all_results,
                "total_properties": total_properties,
                "websites_searched": len(urls_to_search),
                "task_id": task_id
            }
            
        except Exception as e:
            error_duration = (time.time() - start_time) * 1000
            error_msg = f"Critical error in property search: {str(e)}"
            
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.CRITICAL,
                    metadata={
                        "task_id": task_id,
                        "error": str(e),
                        "city": city,
                        "state": state
                    },
                    duration_ms=error_duration
                )
            else:
                logger.error(error_msg)
            
            return {"error": error_msg, "task_id": task_id}

class MarketAnalysisAgent:
    """Agent for market analysis with BMasterAI logging"""
    
    def __init__(self, google_api_key: str, model_id: str = "gemini-2.5-flash"):
        self.agent_id = f"market_analysis_agent_{uuid.uuid4().hex[:8]}"
        self.agent = Agent(
            model=Gemini(id=model_id, api_key=google_api_key),
            markdown=True,
            description="I am a market analysis expert who provides insights on real estate markets and trends."
        )
        
        # Log agent initialization
        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_START,
                message="Market Analysis Agent initialized",
                level=LogLevel.INFO,
                metadata={
                    "model_id": model_id,
                    "agent_type": "MarketAnalysisAgent"
                }
            )
        else:
            logger.info(f"Market Analysis Agent {self.agent_id} initialized")

    def analyze_market(self, city: str, state: str, properties_data: list) -> str:
        """Analyze market conditions with logging"""
        task_id = f"market_analysis_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        # Log task start
        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message=f"Starting market analysis for {city}, {state}",
                level=LogLevel.INFO,
                metadata={
                    "task_id": task_id,
                    "city": city,
                    "state": state,
                    "properties_count": len(properties_data) if properties_data else 0
                }
            )
        
        try:
            # Prepare property data summary for analysis
            property_summary = []
            for result in properties_data:
                if 'properties' in result:
                    for prop in result['properties']:
                        property_summary.append({
                            'price': prop.get('price', 'N/A'),
                            'bedrooms': prop.get('bedrooms', 'N/A'),
                            'bathrooms': prop.get('bathrooms', 'N/A'),
                            'square_feet': prop.get('square_feet', 'N/A'),
                            'property_type': prop.get('property_type', 'N/A')
                        })
            
            prompt = f"""
            Based on the following property data from {city}, {state}, provide a concise market analysis:

            Property Data Summary:
            {json.dumps(property_summary[:20], indent=2)}  # Limit to first 20 properties

            Please provide:
            
            **Market Condition**: Brief assessment of whether it's a buyer's or seller's market
            
            **Key Neighborhoods**: Overview of areas where properties are located
            
            **Investment Outlook**: 2-3 key points about investment potential
            
            Keep each section under 100 words and use bullet points for clarity.
            """
            
            # Log LLM call
            llm_start = time.time()
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.LLM_CALL,
                    message="Requesting market analysis from LLM",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "properties_analyzed": len(property_summary),
                        "model": "gemini-2.5-flash"
                    }
                )
            
            response = self.agent.run(prompt)
            llm_duration = (time.time() - llm_start) * 1000
            
            # Log successful LLM response
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.LLM_CALL,
                    message="Market analysis completed by LLM",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "response_length": len(response.content) if hasattr(response, 'content') else len(str(response)),
                        "success": True
                    },
                    duration_ms=llm_duration
                )
            
            # Log task completion
            total_duration = (time.time() - start_time) * 1000
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"Market analysis completed for {city}, {state}",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "city": city,
                        "state": state,
                        "properties_analyzed": len(property_summary)
                    },
                    duration_ms=total_duration
                )
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            error_duration = (time.time() - start_time) * 1000
            error_msg = f"Error in market analysis: {str(e)}"
            
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={
                        "task_id": task_id,
                        "error": str(e),
                        "city": city,
                        "state": state
                    },
                    duration_ms=error_duration
                )
            else:
                logger.error(error_msg)
            
            return f"Error generating market analysis: {str(e)}"

class PropertyValuationAgent:
    """Agent for property valuation with BMasterAI logging"""
    
    def __init__(self, google_api_key: str, model_id: str = "gemini-2.5-flash"):
        self.agent_id = f"valuation_agent_{uuid.uuid4().hex[:8]}"
        self.agent = Agent(
            model=Gemini(id=model_id, api_key=google_api_key),
            markdown=True,
            description="I am a property valuation expert who provides investment analysis and recommendations."
        )
        
        # Log agent initialization
        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_START,
                message="Property Valuation Agent initialized",
                level=LogLevel.INFO,
                metadata={
                    "model_id": model_id,
                    "agent_type": "PropertyValuationAgent"
                }
            )
        else:
            logger.info(f"Property Valuation Agent {self.agent_id} initialized")

    def evaluate_properties(self, properties_data: list, user_criteria: dict) -> str:
        """Evaluate properties with logging"""
        task_id = f"property_valuation_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        # Log task start
        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message="Starting property valuation analysis",
                level=LogLevel.INFO,
                metadata={
                    "task_id": task_id,
                    "properties_count": len(properties_data) if properties_data else 0,
                    "user_criteria": user_criteria
                }
            )
        
        try:
            # Prepare property data for valuation
            all_properties = []
            for result in properties_data:
                if 'properties' in result:
                    for prop in result['properties']:
                        all_properties.append(prop)
            
            # Limit to first 10 properties for detailed analysis
            properties_to_analyze = all_properties[:10]
            
            prompt = f"""
            Based on the user criteria and property listings below, provide brief valuations:

            USER CRITERIA:
            - Budget: {user_criteria.get('budget_range', 'Any')}
            - Property Type: {user_criteria.get('property_type', 'Any')}
            - Bedrooms: {user_criteria.get('bedrooms', 'Any')}
            - Bathrooms: {user_criteria.get('bathrooms', 'Any')}

            PROPERTIES TO EVALUATE:
            {json.dumps(properties_to_analyze, indent=2)}

            For each property, provide:
            
            **Value Assessment**: Fair price, over/under priced (under 30 words)
            **Investment Potential**: High/Medium/Low with brief reasoning (under 20 words)
            **Key Recommendation**: One actionable insight (under 20 words)

            Format as a numbered list for each property.
            """
            
            # Log LLM call
            llm_start = time.time()
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.LLM_CALL,
                    message="Requesting property valuation from LLM",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "properties_to_evaluate": len(properties_to_analyze),
                        "model": "gemini-2.5-flash"
                    }
                )
            
            response = self.agent.run(prompt)
            llm_duration = (time.time() - llm_start) * 1000
            
            # Log successful LLM response
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.LLM_CALL,
                    message="Property valuation completed by LLM",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "response_length": len(response.content) if hasattr(response, 'content') else len(str(response)),
                        "success": True
                    },
                    duration_ms=llm_duration
                )
            
            # Log task completion
            total_duration = (time.time() - start_time) * 1000
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message="Property valuation analysis completed",
                    level=LogLevel.INFO,
                    metadata={
                        "task_id": task_id,
                        "properties_evaluated": len(properties_to_analyze)
                    },
                    duration_ms=total_duration
                )
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            error_duration = (time.time() - start_time) * 1000
            error_msg = f"Error in property valuation: {str(e)}"
            
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={
                        "task_id": task_id,
                        "error": str(e)
                    },
                    duration_ms=error_duration
                )
            else:
                logger.error(error_msg)
            
            return f"Error generating property valuations: {str(e)}"

def run_sequential_analysis(city, state, user_criteria, selected_websites, firecrawl_api_key, google_api_key, update_callback):
    """Run sequential analysis with manual coordination and BMasterAI logging"""
    session_id = f"analysis_session_{uuid.uuid4().hex[:8]}"
    start_time = time.time()
    
    # Log analysis session start
    if BMASTERAI_AVAILABLE:
        logger.log_event(
            agent_id="analysis_coordinator",
            event_type=EventType.TASK_START,
            message=f"Starting sequential analysis session for {city}, {state}",
            level=LogLevel.INFO,
            metadata={
                "session_id": session_id,
                "city": city,
                "state": state,
                "user_criteria": user_criteria,
                "selected_websites": selected_websites
            }
        )
    
    try:
        # Step 1: Property Search
        update_callback(0.2, "Searching properties...", "🔍 Property Search Agent working...")
        
        property_agent = DirectFirecrawlAgent(firecrawl_api_key, google_api_key)
        property_results = property_agent.find_properties_direct(city, state, user_criteria, selected_websites)
        
        if 'error' in property_results:
            return property_results
        
        # Extract properties for analysis
        all_properties = []
        for result in property_results.get('results', []):
            if 'properties' in result:
                all_properties.extend(result['properties'])
        
        update_callback(0.5, "Analyzing market...", "📊 Market Analysis Agent working...")
        
        # Step 2: Market Analysis
        market_agent = MarketAnalysisAgent(google_api_key)
        market_analysis = market_agent.analyze_market(city, state, property_results.get('results', []))
        
        update_callback(0.8, "Evaluating properties...", "💰 Property Valuation Agent working...")
        
        # Step 3: Property Valuation
        valuation_agent = PropertyValuationAgent(google_api_key)
        property_valuations = valuation_agent.evaluate_properties(property_results.get('results', []), user_criteria)
        
        # Log session completion
        total_duration = (time.time() - start_time) * 1000
        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id="analysis_coordinator",
                event_type=EventType.TASK_COMPLETE,
                message=f"Sequential analysis session completed for {city}, {state}",
                level=LogLevel.INFO,
                metadata={
                    "session_id": session_id,
                    "total_properties_found": len(all_properties),
                    "websites_searched": len(selected_websites),
                    "city": city,
                    "state": state
                },
                duration_ms=total_duration
            )
        
        update_callback(1.0, "Analysis complete", "🎉 Complete analysis ready!")
        
        return {
            'properties': all_properties,
            'market_analysis': market_analysis,
            'property_valuations': property_valuations,
            'total_properties': len(all_properties),
            'session_id': session_id
        }
        
    except Exception as e:
        error_duration = (time.time() - start_time) * 1000
        error_msg = f"Error in sequential analysis: {str(e)}"
        
        if BMASTERAI_AVAILABLE:
            logger.log_event(
                agent_id="analysis_coordinator",
                event_type=EventType.TASK_ERROR,
                message=error_msg,
                level=LogLevel.ERROR,
                metadata={
                    "session_id": session_id,
                    "error": str(e),
                    "city": city,
                    "state": state
                },
                duration_ms=error_duration
            )
        
        return {"error": error_msg, "session_id": session_id}

def display_properties_professionally(properties, market_analysis, property_valuations, total_properties):
    """Display properties in a clean, professional UI using Streamlit components"""
    
    # Header with key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Properties Found", total_properties)
    with col2:
        # Calculate average price
        prices = []
        for p in properties:
            price_str = p.get('price', '') if isinstance(p, dict) else getattr(p, 'price', '')
            if price_str and price_str != 'Price not available':
                try:
                    price_num = ''.join(filter(str.isdigit, str(price_str)))
                    if price_num:
                        prices.append(int(price_num))
                except:
                    pass
        avg_price = f"${sum(prices) // len(prices):,}" if prices else "N/A"
        st.metric("Average Price", avg_price)
    with col3:
        types = {}
        for p in properties:
            t = p.get('property_type', 'Unknown') if isinstance(p, dict) else getattr(p, 'property_type', 'Unknown')
            types[t] = types.get(t, 0) + 1
        most_common = max(types.items(), key=lambda x: x[1])[0] if types else "N/A"
        st.metric("Most Common Type", most_common)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["🏠 Properties", "📊 Market Analysis", "💰 Valuations"])
    
    with tab1:
        for i, prop in enumerate(properties, 1):
            # Extract property data
            data = {k: prop.get(k, '') if isinstance(prop, dict) else getattr(prop, k, '') 
                   for k in ['address', 'price', 'property_type', 'bedrooms', 'bathrooms', 'square_feet', 'description', 'listing_url']}
            
            with st.container():
                # Property header with number and price
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"#{i} 🏠 {data['address']}")
                with col2:
                    st.metric("Price", data['price'])
                
                # Property details with right-aligned button
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**Type:** {data['property_type']}")
                    st.markdown(f"**Beds/Baths:** {data['bedrooms']}/{data['bathrooms']}")
                    st.markdown(f"**Area:** {data['square_feet']}")
                with col2:
                    with st.expander("💰 Investment Analysis"):
                        st.markdown("Property-specific analysis available in Valuations tab")
                with col3:
                    if data['listing_url'] and data['listing_url'] != '#':
                        st.markdown(
                            f"""
                            <div style="height: 100%; display: flex; align-items: center; justify-content: flex-end;">
                                <a href="{data['listing_url']}" target="_blank" 
                                   style="text-decoration: none; padding: 0.5rem 1rem; 
                                   background-color: #0066cc; color: white; 
                                   border-radius: 6px; font-size: 0.9em; font-weight: 500;">
                                    Property Link
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                st.divider()
    
    with tab2:
        st.subheader("📊 Market Analysis")
        if market_analysis:
            st.markdown(market_analysis)
        else:
            st.info("No market analysis available")
    
    with tab3:
        st.subheader("💰 Investment Analysis")
        if property_valuations:
            st.markdown(property_valuations)
        else:
            st.info("No valuation data available")

def main():
    """Main Streamlit application with BMasterAI logging"""
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    # Log application start
    if BMASTERAI_AVAILABLE:
        logger.log_event(
            agent_id="streamlit_app",
            event_type=EventType.AGENT_START,
            message="Real Estate Agent Team application started",
            level=LogLevel.INFO,
            metadata={
                "session_id": session_id,
                "bmasterai_logging": True
            }
        )
    else:
        logger.info("Real Estate Agent Team application started with fallback logging")
    
    st.set_page_config(
        page_title="🏠 AI Real Estate Agent Team with BMasterAI Logging", 
        page_icon="🏠", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Clean header
    st.title("🏠 AI Real Estate Agent Team with BMasterAI Logging")
    st.caption("Find Your Dream Home with Specialized AI Agents - Enhanced with Comprehensive Logging")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key inputs with validation
        with st.expander("🔑 API Keys", expanded=True):
            google_key = st.text_input(
                "Google AI API Key", 
                value=DEFAULT_GOOGLE_API_KEY, 
                type="password",
                help="Get your API key from https://aistudio.google.com/app/apikey",
                placeholder="AIza..."
            )
            firecrawl_key = st.text_input(
                "Firecrawl API Key", 
                value=DEFAULT_FIRECRAWL_API_KEY, 
                type="password",
                help="Get your API key from https://firecrawl.dev",
                placeholder="fc_..."
            )
            
            # Update environment variables
            if google_key: os.environ["GOOGLE_API_KEY"] = google_key
            if firecrawl_key: os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
        
        # Website selection
        with st.expander("🌐 Search Sources", expanded=True):
            st.markdown("**Select real estate websites to search:**")
            available_websites = ["Zillow", "Realtor.com", "Trulia", "Homes.com"]
            selected_websites = [site for site in available_websites if st.checkbox(site, value=site in ["Zillow", "Realtor.com"])]
            
            if selected_websites:
                st.success(f'✅ {len(selected_websites)} sources selected')
            else:
                st.warning('⚠️ Please select at least one website')
        
        # BMasterAI Logging Status
        with st.expander("📊 Logging Status", expanded=False):
            if BMASTERAI_AVAILABLE:
                st.success("✅ BMasterAI Logging Active")
                st.info("All agent activities are being logged with structured data")
            else:
                st.warning("⚠️ BMasterAI Not Available")
                st.info("Using fallback logging. Install bmasterai for enhanced logging.")
        
        # How it works
        with st.expander("🤖 How It Works", expanded=False):
            st.markdown("**🔍 Property Search Agent**")
            st.markdown("Uses direct Firecrawl integration to find properties")
            
            st.markdown("**📊 Market Analysis Agent**")
            st.markdown("Analyzes market trends and neighborhood insights")
            
            st.markdown("**💰 Property Valuation Agent**")
            st.markdown("Evaluates properties and provides investment analysis")
            
            if BMASTERAI_AVAILABLE:
                st.markdown("**📊 BMasterAI Logging**")
                st.markdown("Comprehensive logging of all agent activities, performance metrics, and errors")
    
    # Main form
    st.header("Your Property Requirements")
    st.info("Please provide the location, budget, and property details to help us find your ideal home.")
    
    with st.form("property_preferences"):
        # Location and Budget Section
        st.markdown("### 📍 Location & Budget")
        col1, col2 = st.columns(2)
        
        with col1:
            city = st.text_input(
                "🏙️ City", 
                placeholder="e.g., San Francisco",
                help="Enter the city where you want to buy property"
            )
            state = st.text_input(
                "🗺️ State/Province (optional)", 
                placeholder="e.g., CA",
                help="Enter the state or province (optional)"
            )
        
        with col2:
            min_price = st.number_input(
                "💰 Minimum Price ($)", 
                min_value=0, 
                value=500000, 
                step=50000,
                help="Your minimum budget for the property"
            )
            max_price = st.number_input(
                "💰 Maximum Price ($)", 
                min_value=0, 
                value=1500000, 
                step=50000,
                help="Your maximum budget for the property"
            )
        
        # Property Details Section
        st.markdown("### 🏡 Property Details")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            property_type = st.selectbox(
                "🏠 Property Type",
                ["Any", "House", "Condo", "Townhouse", "Apartment"],
                help="Type of property you're looking for"
            )
            bedrooms = st.selectbox(
                "🛏️ Bedrooms",
                ["Any", "1", "2", "3", "4", "5+"],
                help="Number of bedrooms required"
            )
        
        with col2:
            bathrooms = st.selectbox(
                "🚿 Bathrooms",
                ["Any", "1", "1.5", "2", "2.5", "3", "3.5", "4+"],
                help="Number of bathrooms required"
            )
            min_sqft = st.number_input(
                "📏 Minimum Square Feet",
                min_value=0,
                value=1000,
                step=100,
                help="Minimum square footage required"
            )
        
        with col3:
            timeline = st.selectbox(
                "⏰ Timeline",
                ["Flexible", "1-3 months", "3-6 months", "6+ months"],
                help="When do you plan to buy?"
            )
            urgency = st.selectbox(
                "🚨 Urgency",
                ["Not urgent", "Somewhat urgent", "Very urgent"],
                help="How urgent is your purchase?"
            )
        
        # Special Features
        st.markdown("### ✨ Special Features")
        special_features = st.text_area(
            "🎯 Special Features & Requirements",
            placeholder="e.g., Parking, Yard, View, Near public transport, Good schools, Walkable neighborhood, etc.",
            help="Any specific features or requirements you're looking for"
        )
        
        # Submit button with custom styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Start Property Analysis",
                type="primary",
                use_container_width=True
            )
    
    # Process form submission
    if submitted:
        # Validate all required inputs
        missing_items = []
        if not google_key:
            missing_items.append("Google AI API Key")
        if not firecrawl_key:
            missing_items.append("Firecrawl API Key")
        if not city:
            missing_items.append("City")
        if not selected_websites:
            missing_items.append("At least one website selection")
        
        if missing_items:
            st.error(f"⚠️ Please provide: {', '.join(missing_items)}")
            return
        
        try:
            user_criteria = {
                'budget_range': f"${min_price:,} - ${max_price:,}",
                'property_type': property_type,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'min_sqft': min_sqft,
                'special_features': special_features if special_features else 'None specified'
            }
            
        except Exception as e:
            st.error(f"❌ Error initializing: {str(e)}")
            return
        
        # Display progress
        st.markdown("#### Property Analysis in Progress")
        st.info("AI Agents are searching for your perfect home...")
        
        status_container = st.container()
        with status_container:
            st.markdown("### 📊 Current Activity")
            progress_bar = st.progress(0)
            current_activity = st.empty()
        
        def update_progress(progress, status, activity=None):
            if activity:
                progress_bar.progress(progress)
                current_activity.text(activity)
        
        try:
            start_time = time.time()
            update_progress(0.1, "Initializing...", "Starting sequential property analysis")
            
            # Run sequential analysis with manual coordination
            final_result = run_sequential_analysis(
                city=city,
                state=state,
                user_criteria=user_criteria,
                selected_websites=selected_websites,
                firecrawl_api_key=firecrawl_key,
                google_api_key=google_key,
                update_callback=update_progress
            )
            
            total_time = time.time() - start_time
            
            # Display results
            if isinstance(final_result, dict) and 'properties' in final_result:
                # Use the professional display
                display_properties_professionally(
                    final_result['properties'],
                    final_result['market_analysis'],
                    final_result['property_valuations'],
                    final_result['total_properties']
                )
                
                # Show completion message with logging info
                st.success(f"✅ Analysis completed in {total_time:.1f} seconds!")
                if BMASTERAI_AVAILABLE:
                    st.info(f"📊 Session logged with ID: {final_result.get('session_id', 'N/A')}")
                
            else:
                st.error(f"❌ Analysis failed: {final_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Critical error: {str(e)}")
            if BMASTERAI_AVAILABLE:
                logger.log_event(
                    agent_id="streamlit_app",
                    event_type=EventType.TASK_ERROR,
                    message=f"Critical application error: {str(e)}",
                    level=LogLevel.CRITICAL,
                    metadata={
                        "session_id": session_id,
                        "error": str(e)
                    }
                )

if __name__ == "__main__":
    main()

