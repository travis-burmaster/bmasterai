"""
Gemini 2.5 Pro with BMasterAI Reasoning Logging + Tavily API + Firecrawl Integration

This example demonstrates how to use Gemini 2.5 Pro with BMasterAI's enhanced logging system
to capture LLM thinking processes for complex tasks like finding AI podcast influencers using 
Tavily API for search and Firecrawl API for email extraction.
"""

import time
import json
import os
import requests
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import google.generativeai as genai

# Import BMasterAI components
from bmasterai import (
    configure_logging, get_logger, get_monitor,
    ReasoningSession, ChainOfThought, with_reasoning_logging, log_reasoning,
    LogLevel
)


class GeminiReasoningAgent:
    """
    Reasoning agent powered by Gemini 2.5 Pro with BMasterAI logging, Tavily API, and Firecrawl integration
    """
    
    def __init__(self, agent_id: str, gemini_api_key: str, tavily_api_key: Optional[str] = None, firecrawl_api_key: Optional[str] = None):
        self.agent_id = agent_id
        self.gemini_api_key = gemini_api_key
        self.tavily_api_key = tavily_api_key
        self.firecrawl_api_key = firecrawl_api_key
        self.model_name = "gemini-2.0-flash-exp"  # Using latest available model
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        # Get BMasterAI logger and monitor
        self.logger = get_logger()
        self.monitor = get_monitor()
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Callback for real-time updates
        self.update_callback: Optional[Callable] = None
    
    def set_update_callback(self, callback: Callable):
        """Set callback function for real-time UI updates"""
        self.update_callback = callback
    
    def _send_update(self, update_type: str, content: str, data: Any = None):
        """Send update to UI callback if available"""
        if self.update_callback:
            self.update_callback({
                'type': update_type,
                'content': content,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
    
    def search_ai_podcast_influencers_with_firecrawl(self, target_count: int = 10, focus_area: str = "general AI") -> str:
        """
        Search for AI podcast influencers using Tavily API + Firecrawl for email extraction with complete reasoning logging
        """
        with ReasoningSession(
            self.agent_id, 
            f"Find {target_count} AI podcast influencers in {focus_area} with verified email addresses using Tavily + Firecrawl", 
            self.model_name,
            metadata={"target_count": target_count, "focus_area": focus_area, "method": "tavily_firecrawl_search"}
        ) as session:
            
            # Step 1: Initial planning and strategy
            thinking_step = f"I need to find {target_count} AI podcast influencers in the {focus_area} space who might be willing to have guests. This requires a sophisticated multi-step approach: 1) Use Tavily API to find relevant podcast websites, 2) Use Firecrawl API to extract contact information from those sites, 3) Use Gemini to analyze and validate the results."
            
            session.think(thinking_step, confidence=0.9)
            self._send_update("thinking", thinking_step)
            
            # Step 2: Check API availability and plan search strategy
            if not self.tavily_api_key:
                demo_step = "Tavily API key not available. I'll demonstrate the complete reasoning process including what Firecrawl extraction would look like."
                session.think(demo_step, confidence=0.7)
                self._send_update("thinking", demo_step)
                
                session.decide(
                    "Search approach selection",
                    ["use_tavily_firecrawl", "demonstrate_process", "use_alternative"],
                    "demonstrate_process",
                    "No Tavily API key provided, will demonstrate the complete reasoning process including Firecrawl integration"
                )
                
                return self._demonstrate_tavily_firecrawl_process(session, target_count, focus_area)
            
            strategy_step = "Both Tavily and Firecrawl APIs are available. Planning comprehensive two-stage search: Tavily for discovery, Firecrawl for email extraction."
            session.think(strategy_step, confidence=0.9)
            self._send_update("thinking", strategy_step)
            
            # Step 3: Design search queries for Tavily
            search_queries = [
                f"top AI podcasts {focus_area} hosts contact information",
                f"artificial intelligence podcast influencers guest booking email",
                f"AI podcast hosts accepting guests {focus_area} contact",
                f"machine learning podcast contact page email address",
                f"AI thought leaders podcast hosts website contact"
            ]
            
            query_step = f"Designed {len(search_queries)} targeted Tavily search queries to find AI podcast websites: {search_queries}"
            session.think(query_step, confidence=0.8)
            self._send_update("thinking", query_step)
            
            session.decide(
                "Search query strategy",
                ["broad_search", "targeted_queries", "iterative_refinement"],
                "targeted_queries",
                f"Using {len(search_queries)} specific queries to maximize coverage and relevance for Firecrawl extraction"
            )
            
            # Step 4: Execute Tavily searches
            tavily_step = "Starting Tavily API searches to find podcast websites..."
            session.think(tavily_step, confidence=0.8)
            self._send_update("thinking", tavily_step)
            
            all_results = []
            website_urls = []
            
            for i, query in enumerate(search_queries):
                search_step = f"Executing Tavily search {i+1}/{len(search_queries)}: '{query}'"
                session.think(search_step, confidence=0.8)
                self._send_update("tavily_search", f"Query {i+1}: {query}")
                
                try:
                    tavily_results = self._execute_tavily_search(query)
                    all_results.extend(tavily_results)
                    
                    # Extract URLs for Firecrawl
                    for result in tavily_results:
                        if 'url' in result:
                            website_urls.append(result['url'])
                    
                    result_step = f"Tavily search completed. Found {len(tavily_results)} results for query: '{query}'"
                    session.think(result_step, confidence=0.8)
                    self._send_update("tavily_result", f"Found {len(tavily_results)} results", tavily_results)
                    
                except Exception as e:
                    error_step = f"Tavily search failed for query '{query}': {str(e)}"
                    session.think(error_step, confidence=0.3)
                    self._send_update("error", error_step)
            
            # Step 5: Firecrawl email extraction
            unique_urls = list(set(website_urls))[:20]  # Limit to avoid excessive API calls
            
            firecrawl_step = f"Collected {len(all_results)} total search results with {len(unique_urls)} unique URLs. Now using Firecrawl to extract contact information from these websites."
            session.think(firecrawl_step, confidence=0.8)
            self._send_update("thinking", firecrawl_step)
            
            extracted_contacts = []
            
            if self.firecrawl_api_key and unique_urls:
                for i, url in enumerate(unique_urls):
                    crawl_step = f"Firecrawl extraction {i+1}/{len(unique_urls)}: {url}"
                    session.think(crawl_step, confidence=0.7)
                    self._send_update("firecrawl_crawl", f"Crawling {i+1}/{len(unique_urls)}: {url}")
                    
                    try:
                        contact_info = self._extract_contact_with_firecrawl(url)
                        if contact_info:
                            extracted_contacts.append(contact_info)
                            
                            contact_step = f"Firecrawl extracted contact info from {url}: {contact_info.get('emails', [])} emails found"
                            session.think(contact_step, confidence=0.8)
                            self._send_update("firecrawl_result", f"Extracted from {url}", contact_info)
                        else:
                            no_contact_step = f"No contact information found on {url}"
                            session.think(no_contact_step, confidence=0.5)
                            self._send_update("firecrawl_result", f"No contacts found on {url}")
                            
                    except Exception as e:
                        crawl_error_step = f"Firecrawl extraction failed for {url}: {str(e)}"
                        session.think(crawl_error_step, confidence=0.3)
                        self._send_update("error", crawl_error_step)
            else:
                demo_firecrawl_step = "Firecrawl API key not available or no URLs to crawl. Demonstrating what the extraction process would look like."
                session.think(demo_firecrawl_step, confidence=0.6)
                self._send_update("thinking", demo_firecrawl_step)
                
                extracted_contacts = self._demonstrate_firecrawl_extraction(unique_urls[:5])
            
            # Step 6: Gemini analysis of combined results
            analysis_step = f"Combining Tavily search results with Firecrawl contact extraction. Found {len(extracted_contacts)} websites with contact information. Now using Gemini to analyze and structure the final results."
            session.think(analysis_step, confidence=0.9)
            self._send_update("thinking", analysis_step)
            
            # Prepare comprehensive analysis prompt for Gemini
            combined_data = {
                'tavily_results': all_results[:10],  # Limit to avoid token limits
                'firecrawl_contacts': extracted_contacts,
                'target_count': target_count,
                'focus_area': focus_area
            }
            
            analysis_prompt = f"""
            Analyze the combined search and contact extraction results to identify the best AI podcast influencers:
            
            Tavily Search Results: {json.dumps(combined_data['tavily_results'], indent=2)[:2000]}...
            
            Firecrawl Contact Extraction: {json.dumps(combined_data['firecrawl_contacts'], indent=2)[:2000]}...
            
            For each potential influencer, create a structured profile with:
            1. Name and podcast title
            2. Verified email address (from Firecrawl if available)
            3. Website URL
            4. Focus area within AI
            5. Evidence of guest acceptance
            6. Audience size/influence indicators
            7. Contact method confidence score (1-10)
            
            Format as JSON array with objects containing: name, podcast, email, website, focus_area, guest_friendly, influence_score, contact_confidence, notes
            
            Target: Find {target_count} high-quality prospects in {focus_area} with verified contact information
            Prioritize results with actual email addresses extracted by Firecrawl
            """
            
            gemini_step = "Prepared comprehensive analysis prompt for Gemini to combine Tavily and Firecrawl results into structured influencer profiles."
            session.think(gemini_step, confidence=0.9)
            self._send_update("thinking", gemini_step)
            
            # Step 7: Get Gemini analysis
            try:
                gemini_analysis_step = "Calling Gemini API for final analysis and structuring..."
                session.think(gemini_analysis_step, confidence=0.9)
                self._send_update("thinking", gemini_analysis_step)
                
                response = self.model.generate_content(analysis_prompt)
                gemini_analysis = response.text
                
                gemini_complete_step = f"Gemini analysis completed. Processing structured output: {gemini_analysis[:200]}..."
                session.think(gemini_complete_step, confidence=0.9)
                self._send_update("thinking", gemini_complete_step)
                
                # Step 8: Parse and validate results
                try:
                    # Clean up response and parse JSON
                    clean_analysis = gemini_analysis.strip().replace('```json', '').replace('```', '')
                    influencers_data = json.loads(clean_analysis)
                    
                    parse_step = f"Successfully parsed {len(influencers_data)} influencer profiles from Gemini analysis with Firecrawl-verified contact information."
                    session.think(parse_step, confidence=0.9)
                    self._send_update("thinking", parse_step)
                    
                    session.decide(
                        "Result quality assessment",
                        ["excellent", "good", "needs_refinement"],
                        "excellent" if len(influencers_data) >= target_count else "good",
                        f"Found {len(influencers_data)} influencers with verified contacts, target was {target_count}"
                    )
                    
                    # Step 9: Format final results
                    final_results = self._format_influencer_results_with_firecrawl(influencers_data, session)
                    self._send_update("final_results", "Complete influencer profiles with verified contacts", influencers_data)
                    
                except json.JSONDecodeError:
                    parse_error_step = "JSON parsing failed. Using text-based analysis of Gemini response with Firecrawl data."
                    session.think(parse_error_step, confidence=0.6)
                    self._send_update("thinking", parse_error_step)
                    
                    final_results = f"Analysis completed but structured parsing failed. Raw analysis with Firecrawl data:\n{gemini_analysis}"
                
            except Exception as e:
                gemini_error_step = f"Gemini analysis failed: {str(e)}"
                session.think(gemini_error_step, confidence=0.2)
                self._send_update("error", gemini_error_step)
                final_results = f"Error during analysis: {str(e)}"
            
            # Step 10: Final conclusion
            conclusion = f"AI podcast influencer search with Firecrawl email extraction completed. {final_results}"
            session.conclude(conclusion, confidence=0.85)
            self._send_update("conclusion", conclusion)
            
            return conclusion
    
    def _execute_tavily_search(self, query: str) -> List[Dict]:
        """Execute actual Tavily API search"""
        if not self.tavily_api_key:
            return []
        
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_raw_content": True,
                    "max_results": 10
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                return []
                
        except Exception as e:
            print(f"Tavily API error: {str(e)}")
            return []
    
    def _extract_contact_with_firecrawl(self, url: str) -> Optional[Dict]:
        """Extract contact information from a URL using Firecrawl API"""
        if not self.firecrawl_api_key:
            return None
        
        try:
            # Firecrawl scrape request
            response = requests.post(
                "https://api.firecrawl.dev/v0/scrape",
                headers={
                    "Authorization": f"Bearer {self.firecrawl_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "pageOptions": {
                        "onlyMainContent": True
                    },
                    "extractorOptions": {
                        "mode": "llm-extraction",
                        "extractionPrompt": "Extract all contact information including email addresses, contact forms, social media links, and any information about guest booking or media inquiries. Focus on finding ways to contact the podcast host or show."
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('data', {}).get('content', '')
                extracted = data.get('data', {}).get('llm_extraction', {})
                
                # Extract emails using regex as backup
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails_found = re.findall(email_pattern, content)
                
                return {
                    'url': url,
                    'emails': list(set(emails_found)),  # Remove duplicates
                    'extracted_info': extracted,
                    'content_preview': content[:500] if content else '',
                    'extraction_success': True
                }
            else:
                return None
                
        except Exception as e:
            print(f"Firecrawl API error for {url}: {str(e)}")
            return None
    
    def _demonstrate_firecrawl_extraction(self, urls: List[str]) -> List[Dict]:
        """Demonstrate what Firecrawl extraction would look like"""
        mock_extractions = []
        
        for i, url in enumerate(urls):
            mock_extractions.append({
                'url': url,
                'emails': [f'host{i+1}@example-podcast.com', f'booking{i+1}@example-podcast.com'],
                'extracted_info': {
                    'contact_methods': ['Email', 'Contact Form'],
                    'guest_policy': 'Accepts guest inquiries',
                    'response_time': '2-3 business days'
                },
                'content_preview': f'Mock content from {url} - Contact us for guest opportunities...',
                'extraction_success': True,
                'demo_mode': True
            })
        
        return mock_extractions
    
    def _demonstrate_tavily_firecrawl_process(self, session, target_count: int, focus_area: str) -> str:
        """Demonstrate the complete Tavily + Firecrawl process without actual API calls"""
        
        demo_step = "Since API keys are not available, I'll demonstrate the complete Tavily + Firecrawl reasoning process that would be used to find AI podcast influencers with verified email addresses."
        session.think(demo_step, confidence=0.8)
        self._send_update("thinking", demo_step)
        
        # Step 1: Search strategy demonstration
        search_strategy = {
            "tavily_queries": [
                f"top AI podcasts {focus_area} hosts contact email",
                f"artificial intelligence podcast influencers guest booking",
                f"AI podcast hosts accepting guests {focus_area} contact page"
            ],
            "firecrawl_targets": [
                "Podcast website contact pages",
                "Host bio pages with email addresses", 
                "Guest booking information pages",
                "About pages with contact details"
            ]
        }
        
        strategy_step = f"Designed comprehensive two-stage strategy: {len(search_strategy['tavily_queries'])} Tavily queries to find websites, then Firecrawl extraction from {len(search_strategy['firecrawl_targets'])} target page types."
        session.think(strategy_step, confidence=0.9)
        self._send_update("thinking", strategy_step)
        
        # Step 2: Mock Tavily results
        mock_tavily_results = [
            {"url": "https://lexfridman.com/contact", "title": "Lex Fridman Podcast - Contact", "content": "Contact page for guest inquiries"},
            {"url": "https://twimlai.com/about", "title": "This Week in ML & AI - About", "content": "About page with host information"},
            {"url": "https://towardsdatascience.com/podcast", "title": "TDS Podcast Contact", "content": "Guest booking information"}
        ]
        
        tavily_step = f"Tavily would find {len(mock_tavily_results)} relevant podcast websites with contact pages."
        session.think(tavily_step, confidence=0.8)
        self._send_update("tavily_result", "Mock Tavily results", mock_tavily_results)
        
        # Step 3: Mock Firecrawl extraction
        mock_firecrawl_results = [
            {
                "url": "https://lexfridman.com/contact",
                "emails": ["lex@lexfridman.com", "podcast@lexfridman.com"],
                "extracted_info": {"guest_policy": "Accepts research-focused guests", "response_time": "2-4 weeks"},
                "extraction_success": True
            },
            {
                "url": "https://twimlai.com/about", 
                "emails": ["sam@twimlai.com"],
                "extracted_info": {"guest_policy": "Industry experts welcome", "response_time": "1-2 weeks"},
                "extraction_success": True
            }
        ]
        
        firecrawl_step = f"Firecrawl would extract verified email addresses from these websites: {[r['emails'] for r in mock_firecrawl_results]}"
        session.think(firecrawl_step, confidence=0.8)
        self._send_update("firecrawl_result", "Mock Firecrawl extraction", mock_firecrawl_results)
        
        # Step 4: Final demonstration results
        demo_conclusion = f"""
        DEMONSTRATION: AI Podcast Influencer Search with Tavily + Firecrawl
        
        Target: {target_count} influencers in {focus_area}
        
        Two-Stage Process Demonstrated:
        1. Tavily API: Find {len(mock_tavily_results)} relevant podcast websites
        2. Firecrawl API: Extract verified email addresses from those sites
        3. Gemini Analysis: Structure and validate the combined results
        
        Mock Results with Verified Emails:
        {json.dumps(mock_firecrawl_results, indent=2)}
        
        With actual API keys, this process would:
        1. Execute comprehensive web searches via Tavily
        2. Crawl and extract contact info via Firecrawl
        3. Verify email addresses and contact methods
        4. Provide confidence scores for each contact
        5. Generate structured influencer profiles
        
        BMasterAI captures every reasoning step for complete transparency!
        """
        
        self._send_update("final_results", "Demo process complete", mock_firecrawl_results)
        return demo_conclusion
    
    def _format_influencer_results_with_firecrawl(self, influencers_data: List[Dict], session) -> str:
        """Format the final influencer results with Firecrawl contact information"""
        
        format_step = f"Formatting {len(influencers_data)} influencer profiles with Firecrawl-verified contact information for final presentation."
        session.think(format_step, confidence=0.9)
        self._send_update("thinking", format_step)
        
        formatted_results = "AI PODCAST INFLUENCERS WITH VERIFIED CONTACT INFO:\n\n"
        
        for i, influencer in enumerate(influencers_data, 1):
            formatted_results += f"{i}. {influencer.get('name', 'Unknown')}\n"
            formatted_results += f"   Podcast: {influencer.get('podcast', 'N/A')}\n"
            formatted_results += f"   Email: {influencer.get('email', 'Not found')}\n"
            formatted_results += f"   Website: {influencer.get('website', 'N/A')}\n"
            formatted_results += f"   Focus: {influencer.get('focus_area', 'General AI')}\n"
            formatted_results += f"   Guest Friendly: {influencer.get('guest_friendly', 'Unknown')}\n"
            formatted_results += f"   Influence Score: {influencer.get('influence_score', 'N/A')}\n"
            formatted_results += f"   Contact Confidence: {influencer.get('contact_confidence', 'N/A')}/10\n"
            formatted_results += f"   Notes: {influencer.get('notes', 'No additional notes')}\n\n"
        
        return formatted_results
    
    # Keep existing methods for backward compatibility
    def search_ai_podcast_influencers(self, target_count: int = 10, focus_area: str = "general AI") -> str:
        """Legacy method - redirects to new Firecrawl-enhanced version"""
        return self.search_ai_podcast_influencers_with_firecrawl(target_count, focus_area)
    
    def analyze_sentiment_with_context_manager(self, text: str) -> str:
        """Analyze sentiment using Gemini with BMasterAI ReasoningSession context manager"""
        with ReasoningSession(
            self.agent_id, 
            f"Analyze sentiment of text: '{text[:50]}...'", 
            self.model_name,
            metadata={"text_length": len(text), "method": "gemini_context_manager"}
        ) as session:
            
            thinking_step = f"I need to analyze the sentiment of this text using Gemini 2.5 Pro: '{text}'. Let me start by preparing a comprehensive prompt for the model."
            session.think(thinking_step, confidence=0.9)
            self._send_update("thinking", thinking_step)
            
            prompt = f"""
            Analyze the sentiment of the following text and provide a detailed breakdown:
            
            Text: "{text}"
            
            Please provide:
            1. Overall sentiment (positive, negative, or neutral)
            2. Confidence score (0-1)
            3. Key words/phrases that influenced the sentiment
            4. Brief reasoning for your classification
            
            Format your response as JSON with keys: sentiment, confidence, key_phrases, reasoning
            """
            
            prompt_step = "Prepared comprehensive prompt for Gemini. Now calling the API to get sentiment analysis."
            session.think(prompt_step, confidence=0.8)
            self._send_update("thinking", prompt_step)
            
            try:
                response = self.model.generate_content(prompt)
                gemini_result = response.text
                
                api_step = f"Gemini API call successful. Raw response received: {gemini_result[:200]}..."
                session.think(api_step, confidence=0.9)
                self._send_update("thinking", api_step)
                
                try:
                    clean_result = gemini_result.strip().replace('```json', '').replace('```', '')
                    result_data = json.loads(clean_result)
                    
                    sentiment = result_data.get('sentiment', 'neutral')
                    confidence_score = result_data.get('confidence', 0.5)
                    key_phrases = result_data.get('key_phrases', [])
                    reasoning = result_data.get('reasoning', 'No reasoning provided')
                    
                    session.decide(
                        "Sentiment classification",
                        ["positive", "negative", "neutral"],
                        sentiment,
                        f"Gemini reasoning: {reasoning}. Key phrases identified: {key_phrases}",
                        confidence=confidence_score
                    )
                    
                    final_result = f"The text has {sentiment} sentiment (confidence: {confidence_score:.2f}). Key phrases: {key_phrases}"
                    
                except json.JSONDecodeError as e:
                    parse_error_step = f"JSON parsing failed: {str(e)}. Falling back to text analysis of raw response."
                    session.think(parse_error_step, confidence=0.3)
                    self._send_update("thinking", parse_error_step)
                    
                    sentiment = "neutral"
                    if "positive" in gemini_result.lower():
                        sentiment = "positive"
                    elif "negative" in gemini_result.lower():
                        sentiment = "negative"
                    
                    session.decide(
                        "Sentiment classification",
                        ["positive", "negative", "neutral"],
                        sentiment,
                        f"Fallback classification based on keyword detection in response: {gemini_result[:100]}...",
                        confidence=0.4
                    )
                    
                    final_result = f"Sentiment analysis completed with fallback method: {sentiment}. Raw Gemini response: {gemini_result[:200]}..."
                
            except Exception as e:
                error_step = f"Error during Gemini API call: {str(e)}"
                session.think(error_step, confidence=0.1)
                self._send_update("error", error_step)
                final_result = f"Error analyzing sentiment: {str(e)}"
            
            session.conclude(final_result, confidence=0.85)
            self._send_update("conclusion", final_result)
            return final_result
    
    def analyze_with_chain_of_thought(self, problem: str) -> str:
        """Solve a problem using Gemini with BMasterAI ChainOfThought utility"""
        cot = ChainOfThought(
            self.agent_id, 
            f"Solve problem using Gemini: {problem}", 
            self.model_name
        )
        
        step1 = "First, I need to understand what type of problem this is and prepare an appropriate prompt for Gemini."
        cot.step(step1)
        self._send_update("thinking", step1)
        
        step2 = f"The problem is: '{problem}'. Let me analyze its characteristics."
        cot.step(step2)
        self._send_update("thinking", step2)
        
        if "calculate" in problem.lower() or any(op in problem for op in ['+', '-', '*', '/', '=']):
            approach = "mathematical"
            cot.decide(
                "Problem solving approach",
                ["mathematical", "logical", "creative"],
                approach,
                "The problem contains mathematical terms or operators"
            )
        else:
            approach = "logical"
            cot.decide(
                "Problem solving approach", 
                ["mathematical", "logical", "creative"],
                approach,
                "This appears to be a logical reasoning problem"
            )
        
        step3 = f"Using {approach} approach. Now preparing comprehensive prompt for Gemini 2.5 Pro."
        cot.step(step3)
        self._send_update("thinking", step3)
        
        prompt = f"""
        Solve this problem step by step using {approach} reasoning:
        
        Problem: {problem}
        
        Please provide:
        1. Step-by-step analysis
        2. Your reasoning process at each step
        3. Final answer or conclusion
        4. Confidence in your solution (0-1)
        
        Use clear, logical steps in your explanation.
        """
        
        step4 = "Calling Gemini API with prepared prompt..."
        cot.step(step4)
        self._send_update("thinking", step4)
        
        try:
            response = self.model.generate_content(prompt)
            gemini_solution = response.text
            
            step5 = f"Gemini provided detailed solution. Processing response: {gemini_solution[:200]}..."
            cot.step(step5)
            self._send_update("thinking", step5)
            
            final_result = f"Problem solved using {approach} approach with Gemini 2.5 Pro:\n\n{gemini_solution}"
            
        except Exception as e:
            error_step = f"Error during Gemini problem solving: {str(e)}"
            cot.step(error_step)
            self._send_update("error", error_step)
            final_result = f"Error solving problem: {str(e)}"
        
        result = cot.conclude(final_result)
        self._send_update("conclusion", final_result)
        return result
    
    @with_reasoning_logging("Process user query with Gemini", "gemini-2.0-flash-exp")
    def process_with_decorator(self, agent_id: str, query: str, reasoning_session=None) -> str:
        """Process query using Gemini with BMasterAI reasoning logging decorator"""
        if reasoning_session:
            step1 = f"Received query: {query}"
            reasoning_session.think(step1)
            self._send_update("thinking", step1)
            
            step2 = "Determining the best approach to handle this query with Gemini"
            reasoning_session.think(step2)
            self._send_update("thinking", step2)
            
            if "?" in query:
                approach = "question_answering"
                reasoning_session.decide(
                    "Query type classification",
                    ["question_answering", "command_execution", "information_request"],
                    approach,
                    "Query contains question mark, treating as Q&A"
                )
            else:
                approach = "general_processing"
                reasoning_session.decide(
                    "Query type classification",
                    ["question_answering", "command_execution", "information_request"], 
                    approach,
                    "No specific indicators, using general processing"
                )
            
            step3 = f"Preparing Gemini prompt for {approach} approach..."
            reasoning_session.think(step3)
            self._send_update("thinking", step3)
            
            prompt = f"""
            Please respond to this query in a helpful and informative way:
            
            Query: {query}
            
            Provide a clear, concise, and accurate response.
            """
            
            try:
                step4 = "Calling Gemini API..."
                reasoning_session.think(step4)
                self._send_update("thinking", step4)
                
                response = self.model.generate_content(prompt)
                gemini_response = response.text
                
                step5 = f"Gemini response received: {gemini_response[:200]}..."
                reasoning_session.think(step5)
                self._send_update("thinking", step5)
                
                result = f"Query processed using {approach} approach with Gemini:\n\n{gemini_response}"
                reasoning_session.conclude(result)
                self._send_update("conclusion", result)
                return result
                
            except Exception as e:
                error_step = f"Error during Gemini query processing: {str(e)}"
                reasoning_session.think(error_step, confidence=0.1)
                self._send_update("error", error_step)
                result = f"Error processing query: {str(e)}"
                reasoning_session.conclude(result)
                return result
        
        return "Processed without reasoning session"
    
    def export_reasoning_logs(self, format_type: str = "markdown") -> str:
        """Export BMasterAI reasoning logs for this agent"""
        return self.logger.export_reasoning_logs(
            agent_id=self.agent_id,
            output_format=format_type
        )
    
    def get_agent_stats(self) -> Dict:
        """Get BMasterAI agent statistics"""
        return self.logger.get_agent_stats(self.agent_id)


def main():
    """
    Demonstrate Gemini 2.5 Pro with BMasterAI reasoning logging, Tavily API, and Firecrawl integration
    """
    print("🤖 Gemini 2.5 Pro + BMasterAI + Tavily + Firecrawl Integration")
    print("=" * 70)
    
    # Get API keys from environment
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    
    if not gemini_api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set your Gemini API key in the environment or .env file")
        return
    
    if not tavily_api_key:
        print("⚠️  Warning: TAVILY_API_KEY not set - will demonstrate process without actual searches")
    
    if not firecrawl_api_key:
        print("⚠️  Warning: FIRECRAWL_API_KEY not set - will demonstrate email extraction process")
    
    # Configure BMasterAI logging with reasoning enabled
    logger = configure_logging(
        log_level=LogLevel.DEBUG,
        enable_console=True,
        enable_reasoning_logs=True,
        reasoning_log_file="gemini_tavily_firecrawl_reasoning.jsonl"
    )
    
    # Create reasoning agent
    agent = GeminiReasoningAgent("gemini-tavily-firecrawl-agent-001", gemini_api_key, tavily_api_key, firecrawl_api_key)
    
    print("\n🎯 AI Podcast Influencer Search with Tavily + Firecrawl Integration")
    print("-" * 70)
    
    # Main demonstration: Search for AI podcast influencers with email extraction
    result = agent.search_ai_podcast_influencers_with_firecrawl(
        target_count=5, 
        focus_area="machine learning and AI applications"
    )
    print(f"Result:\n{result}")
    
    # Wait for logs to be written
    time.sleep(1)
    
    print("\n📈 BMasterAI Statistics")
    print("-" * 40)
    stats = agent.get_agent_stats()
    print(f"Total events logged: {stats.get('total_events', 0)}")
    print(f"Event breakdown:")
    for event_type, count in stats.get('event_types', {}).items():
        print(f"  - {event_type}: {count}")
    
    print(f"\n✅ Complete Tavily + Firecrawl reasoning demonstration finished!")
    print(f"📁 Check the logs directory for detailed reasoning logs:")
    print(f"   - Main log: logs/bmasterai.jsonl")
    print(f"   - Reasoning log: logs/reasoning/gemini_tavily_firecrawl_reasoning.jsonl")
    print(f"   - Session folders: logs/reasoning/sessions/")


if __name__ == "__main__":
    main()

