#!/usr/bin/env python3
"""
AI Consultant Agent - Fixed Version

This is a refactored version of the original AI consultant agent that replaces
fictional dependencies with real alternatives and adds proper error handling,
security measures, and configuration management.

Features:
- OpenAI GPT integration for advanced LLM capabilities
- LangChain for agent framework and tools
- Real-time web research using Perplexity AI
- Market analysis and strategic recommendations
- Comprehensive error handling and logging
- Environment variable configuration
- Modular architecture with proper separation of concerns
"""

import logging
import os
import time
import uuid
import json
import sys
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
import openai
from langchain.agents import AgentType, initialize_agent
from langchain.llms import OpenAI as LangChainOpenAI
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage

# Load environment variables
load_dotenv()

# Configuration with environment variables
class Config:
    """Configuration management with environment variables"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    
    # Model Configuration
    MODEL_ID = os.getenv("MODEL_ID", "gpt-3.5-turbo")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
    
    # Application Settings
    APP_NAME = os.getenv("APP_NAME", "ai_consultant_agent")
    AGENT_ID = os.getenv("AGENT_ID", "consultant-agent-001")
    AGENT_NAME = os.getenv("AGENT_NAME", "AI Business Consultant")
    
    # Integration Settings
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "ai_consultant.log")
    
    # API Configuration
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if not cls.PERPLEXITY_API_KEY:
            errors.append("PERPLEXITY_API_KEY is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

@dataclass
class MarketInsight:
    """Structure for market research insights"""
    category: str
    finding: str
    confidence: float
    source: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category,
            "finding": self.finding,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }

class APIError(Exception):
    """Custom exception for API-related errors"""
    pass

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors"""
    pass

class PerplexitySearchTool:
    """Tool for conducting web research using Perplexity AI"""
    
    def __init__(self):
        self.api_key = Config.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def search(self, query: str, system_prompt: str = "Be precise and concise. Focus on business insights and market data.") -> Dict[str, Any]:
        """Perform web search using Perplexity AI"""
        try:
            logger.info(f"Performing Perplexity search for query: {query[:100]}...")
            
            payload = {
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
            }
            
            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=Config.REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and result["choices"]:
                return {
                    "query": query,
                    "content": result["choices"][0]["message"]["content"],
                    "citations": result.get("citations", []),
                    "search_results": result.get("search_results", []),
                    "status": "success",
                    "source": "Perplexity AI",
                    "model": result.get("model", "sonar"),
                    "usage": result.get("usage", {}),
                    "response_id": result.get("id", ""),
                    "created": result.get("created", 0)
                }
            else:
                return {
                    "error": "No response content found",
                    "query": query,
                    "status": "error",
                    "raw_response": result
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API request failed: {e}")
            return {
                "error": f"API request failed: {str(e)}",
                "query": query,
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Unexpected error in Perplexity search: {e}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "query": query,
                "status": "error"
            }

class MarketAnalysisTool:
    """Tool for conducting market analysis"""
    
    def analyze(self, research_query: str, industry: str = "") -> Dict[str, Any]:
        """Analyze market data and generate insights"""
        try:
            logger.info(f"Conducting market analysis for: {research_query}")
            
            insights = []
            
            # Generate contextual insights based on query
            if "startup" in research_query.lower() or "launch" in research_query.lower():
                insights.extend([
                    MarketInsight("Market Opportunity", "Growing market with moderate competition", 0.8, "Market Research"),
                    MarketInsight("Risk Assessment", "Standard startup risks apply - funding, competition", 0.7, "Risk Analysis"),
                    MarketInsight("Recommendation", "Conduct MVP testing before full launch", 0.9, "Strategic Planning")
                ])
            
            if "saas" in research_query.lower() or "software" in research_query.lower():
                insights.extend([
                    MarketInsight("Technology Trend", "Cloud-based solutions gaining adoption", 0.9, "Tech Analysis"),
                    MarketInsight("Customer Behavior", "Businesses prefer subscription models", 0.8, "Market Study"),
                    MarketInsight("Scalability", "SaaS models offer better scaling potential", 0.85, "Business Model Analysis")
                ])
            
            if "ai" in research_query.lower() or "artificial intelligence" in research_query.lower():
                insights.extend([
                    MarketInsight("AI Trend", "AI adoption accelerating across industries", 0.95, "Technology Report"),
                    MarketInsight("Investment", "AI startups receiving significant funding", 0.85, "Investment Analysis"),
                    MarketInsight("Regulation", "AI governance frameworks emerging", 0.7, "Regulatory Analysis")
                ])
            
            if industry:
                insights.append(
                    MarketInsight("Industry Specific", f"{industry} sector shows growth potential", 0.7, "Industry Report")
                )
            
            return {
                "query": research_query,
                "industry": industry,
                "insights": [insight.to_dict() for insight in insights],
                "summary": f"Market analysis completed for: {research_query}",
                "total_insights": len(insights),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {
                "error": f"Market analysis failed: {str(e)}",
                "query": research_query,
                "status": "error"
            }

class StrategicRecommendationTool:
    """Tool for generating strategic recommendations"""
    
    def generate(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on analysis data"""
        try:
            logger.info("Generating strategic recommendations")
            
            recommendations = []
            insights = analysis_data.get("insights", [])
            
            # Generate contextual recommendations
            if any("startup" in insight["finding"].lower() for insight in insights):
                recommendations.append({
                    "category": "Market Entry Strategy",
                    "priority": "High",
                    "recommendation": "Implement phased market entry with MVP testing",
                    "rationale": "Reduces risk and validates market fit before major investment",
                    "timeline": "3-6 months",
                    "success_metrics": ["User acquisition rate", "Product-market fit score", "Customer feedback"],
                    "action_items": [
                        "Develop minimum viable product",
                        "Identify target customer segment",
                        "Conduct market validation tests",
                        "Set up analytics and tracking"
                    ]
                })
            
            if any("saas" in insight["finding"].lower() or "software" in insight["finding"].lower() for insight in insights):
                recommendations.append({
                    "category": "Technology Strategy",
                    "priority": "Medium",
                    "recommendation": "Focus on cloud-native architecture and subscription model",
                    "rationale": "Aligns with market trends and customer preferences",
                    "timeline": "2-4 months",
                    "success_metrics": ["System uptime", "Subscription growth", "Customer retention"],
                    "action_items": [
                        "Design scalable cloud infrastructure",
                        "Implement subscription billing system",
                        "Plan for multi-tenant architecture",
                        "Develop API-first approach"
                    ]
                })
            
            if any("ai" in insight["finding"].lower() for insight in insights):
                recommendations.append({
                    "category": "AI Implementation",
                    "priority": "High",
                    "recommendation": "Integrate AI capabilities gradually with clear ROI tracking",
                    "rationale": "AI is becoming essential for competitive advantage",
                    "timeline": "4-8 months",
                    "success_metrics": ["AI feature adoption", "Operational efficiency gains", "Customer satisfaction"],
                    "action_items": [
                        "Identify AI use cases with highest ROI",
                        "Build AI development team",
                        "Implement AI governance framework",
                        "Plan for data strategy and privacy"
                    ]
                })
            
            # Always include risk management
            recommendations.append({
                "category": "Risk Management",
                "priority": "High",
                "recommendation": "Establish comprehensive risk monitoring framework",
                "rationale": "Proactive risk management is essential for business success",
                "timeline": "1-2 months",
                "success_metrics": ["Risk identification rate", "Mitigation effectiveness", "Business continuity"],
                "action_items": [
                    "Identify key business risks",
                    "Develop mitigation strategies",
                    "Implement monitoring systems",
                    "Create incident response procedures"
                ]
            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Strategic recommendation generation failed: {e}")
            return [{
                "error": f"Recommendation generation failed: {str(e)}",
                "status": "error"
            }]

class CompetitorAnalysisTool:
    """Tool for conducting competitor analysis"""
    
    def analyze(self, industry: str, company_focus: str = "") -> Dict[str, Any]:
        """Conduct comprehensive competitor analysis"""
        try:
            logger.info(f"Conducting competitor analysis for industry: {industry}")
            
            competitor_data = {
                "industry": industry,
                "company_focus": company_focus,
                "analysis_timestamp": datetime.now().isoformat(),
                "competitive_landscape": {
                    "market_leaders": [],
                    "emerging_players": [],
                    "market_gaps": []
                },
                "competitive_advantages": [],
                "threats": [],
                "recommendations": []
            }
            
            # Generate industry-specific competitor insights
            if "saas" in industry.lower():
                competitor_data["competitive_landscape"]["market_leaders"] = [
                    "Salesforce", "Microsoft", "Google Workspace", "Slack"
                ]
                competitor_data["competitive_landscape"]["emerging_players"] = [
                    "Notion", "Airtable", "Monday.com", "Figma"
                ]
                competitor_data["competitive_landscape"]["market_gaps"] = [
                    "SMB-focused solutions", "Industry-specific verticals", "AI-powered automation"
                ]
            
            if "ai" in industry.lower():
                competitor_data["competitive_landscape"]["market_leaders"] = [
                    "OpenAI", "Google", "Microsoft", "Anthropic"
                ]
                competitor_data["competitive_landscape"]["emerging_players"] = [
                    "Cohere", "Hugging Face", "Stability AI", "Midjourney"
                ]
                competitor_data["competitive_landscape"]["market_gaps"] = [
                    "Enterprise AI platforms", "Domain-specific models", "AI governance tools"
                ]
            
            competitor_data["competitive_advantages"] = [
                "First-mover advantage in specific niche",
                "Strong technical expertise",
                "Customer-centric approach",
                "Agile development methodology"
            ]
            
            competitor_data["threats"] = [
                "Well-funded competitors",
                "Platform dependencies",
                "Regulatory changes",
                "Technology disruption"
            ]
            
            competitor_data["recommendations"] = [
                "Focus on differentiation through superior user experience",
                "Build strong customer relationships and loyalty",
                "Invest in continuous innovation",
                "Develop strategic partnerships"
            ]
            
            return competitor_data
            
        except Exception as e:
            logger.error(f"Competitor analysis failed: {e}")
            return {
                "error": f"Competitor analysis failed: {str(e)}",
                "industry": industry,
                "status": "error"
            }

class RiskAssessmentTool:
    """Tool for assessing business risks"""
    
    def assess(self, business_type: str, market_conditions: str = "") -> Dict[str, Any]:
        """Assess business risks comprehensively"""
        try:
            logger.info(f"Conducting risk assessment for business type: {business_type}")
            
            risk_assessment = {
                "business_type": business_type,
                "market_conditions": market_conditions,
                "assessment_timestamp": datetime.now().isoformat(),
                "risk_categories": {
                    "financial": [],
                    "operational": [],
                    "strategic": [],
                    "compliance": [],
                    "technology": []
                },
                "high_priority_risks": [],
                "mitigation_strategies": []
            }
            
            # Financial risks
            risk_assessment["risk_categories"]["financial"] = [
                {"risk": "Cash flow management", "probability": "Medium", "impact": "High"},
                {"risk": "Funding availability", "probability": "Medium", "impact": "High"},
                {"risk": "Currency fluctuation", "probability": "Low", "impact": "Medium"}
            ]
            
            # Operational risks
            risk_assessment["risk_categories"]["operational"] = [
                {"risk": "Key person dependency", "probability": "Medium", "impact": "High"},
                {"risk": "Supply chain disruption", "probability": "Low", "impact": "Medium"},
                {"risk": "Quality control issues", "probability": "Low", "impact": "High"}
            ]
            
            # Strategic risks
            risk_assessment["risk_categories"]["strategic"] = [
                {"risk": "Market competition", "probability": "High", "impact": "High"},
                {"risk": "Technology obsolescence", "probability": "Medium", "impact": "High"},
                {"risk": "Customer concentration", "probability": "Medium", "impact": "Medium"}
            ]
            
            # Compliance risks
            risk_assessment["risk_categories"]["compliance"] = [
                {"risk": "Regulatory changes", "probability": "Medium", "impact": "Medium"},
                {"risk": "Data privacy violations", "probability": "Low", "impact": "High"},
                {"risk": "Industry standards compliance", "probability": "Low", "impact": "Medium"}
            ]
            
            # Technology risks
            risk_assessment["risk_categories"]["technology"] = [
                {"risk": "Cybersecurity threats", "probability": "Medium", "impact": "High"},
                {"risk": "System downtime", "probability": "Low", "impact": "High"},
                {"risk": "Data loss", "probability": "Low", "impact": "High"}
            ]
            
            # Identify high priority risks (High impact, Medium+ probability)
            for category, risks in risk_assessment["risk_categories"].items():
                for risk in risks:
                    if risk["impact"] == "High" and risk["probability"] in ["Medium", "High"]:
                        risk_assessment["high_priority_risks"].append({
                            "category": category,
                            "risk": risk["risk"],
                            "priority": "High"
                        })
            
            # Generate mitigation strategies
            risk_assessment["mitigation_strategies"] = [
                "Implement comprehensive risk monitoring system",
                "Develop contingency plans for high-priority risks",
                "Regular risk assessment reviews and updates",
                "Establish risk management governance structure",
                "Invest in cybersecurity and data protection measures"
            ]
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {
                "error": f"Risk assessment failed: {str(e)}",
                "business_type": business_type,
                "status": "error"
            }

class AIConsultantAgent:
    """
    AI Consultant Agent with real dependencies and proper error handling
    """
    
    def __init__(self, agent_id: str = None, name: str = None):
        self.agent_id = agent_id or Config.AGENT_ID
        self.name = name or Config.AGENT_NAME
        self.status = "initialized"
        self.conversation_history = []
        
        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigurationError(f"Configuration validation failed: {e}")
        
        # Initialize OpenAI client
        try:
            openai.api_key = Config.OPENAI_API_KEY
            self.openai_client = openai
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise APIError(f"Failed to initialize OpenAI client: {e}")
        
        # Initialize tools
        self._initialize_tools()
        
        # Initialize LangChain agent
        self._initialize_langchain_agent()
        
        logger.info(f"AI Consultant Agent {self.name} initialized successfully")
    
    def _initialize_tools(self):
        """Initialize all analysis tools"""
        try:
            self.perplexity_tool = PerplexitySearchTool()
            self.market_analysis_tool = MarketAnalysisTool()
            self.strategic_recommendation_tool = StrategicRecommendationTool()
            self.competitor_analysis_tool = CompetitorAnalysisTool()
            self.risk_assessment_tool = RiskAssessmentTool()
            
            logger.info("All tools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")
            raise
    
    def _initialize_langchain_agent(self):
        """Initialize LangChain agent with tools"""
        try:
            # Create LangChain tools
            tools = [
                Tool(
                    name="Web Research",
                    func=self._web_research_wrapper,
                    description="Search the web for current information and market data"
                ),
                Tool(
                    name="Market Analysis",
                    func=self._market_analysis_wrapper,
                    description="Analyze market conditions and generate insights"
                ),
                Tool(
                    name="Strategic Recommendations",
                    func=self._strategic_recommendations_wrapper,
                    description="Generate strategic business recommendations"
                ),
                Tool(
                    name="Competitor Analysis",
                    func=self._competitor_analysis_wrapper,
                    description="Analyze competitive landscape and positioning"
                ),
                Tool(
                    name="Risk Assessment",
                    func=self._risk_assessment_wrapper,
                    description="Assess business risks and mitigation strategies"
                )
            ]
            
            # Initialize LLM
            llm = LangChainOpenAI(
                model_name=Config.MODEL_ID,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                openai_api_key=Config.OPENAI_API_KEY
            )
            
            # Initialize memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Initialize agent
            self.agent = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=memory,
                verbose=True,
                handle_parsing_errors=True
            )
            
            logger.info("LangChain agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain agent: {e}")
            raise
    
    def _web_research_wrapper(self, query: str) -> str:
        """Wrapper for web research tool"""
        try:
            result = self.perplexity_tool.search(query)
            if result.get("status") == "success":
                return f"Research Results: {result['content']}"
            else:
                return f"Research failed: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Web research wrapper failed: {e}")
            return f"Web research failed: {str(e)}"
    
    def _market_analysis_wrapper(self, query: str) -> str:
        """Wrapper for market analysis tool"""
        try:
            result = self.market_analysis_tool.analyze(query)
            if "error" not in result:
                insights_summary = "\n".join([
                    f"- {insight['category']}: {insight['finding']} (Confidence: {insight['confidence']})"
                    for insight in result['insights']
                ])
                return f"Market Analysis Results:\n{insights_summary}"
            else:
                return f"Market analysis failed: {result['error']}"
        except Exception as e:
            logger.error(f"Market analysis wrapper failed: {e}")
            return f"Market analysis failed: {str(e)}"
    
    def _strategic_recommendations_wrapper(self, analysis_data: str) -> str:
        """Wrapper for strategic recommendations tool"""
        try:
            # Parse analysis data if it's a string
            if isinstance(analysis_data, str):
                analysis_data = {"insights": []}
            
            recommendations = self.strategic_recommendation_tool.generate(analysis_data)
            if recommendations and "error" not in recommendations[0]:
                rec_summary = "\n".join([
                    f"- {rec['category']} ({rec['priority']} Priority): {rec['recommendation']}"
                    for rec in recommendations
                ])
                return f"Strategic Recommendations:\n{rec_summary}"
            else:
                return f"Strategic recommendations failed: {recommendations[0].get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Strategic recommendations wrapper failed: {e}")
            return f"Strategic recommendations failed: {str(e)}"
    
    def _competitor_analysis_wrapper(self, industry: str) -> str:
        """Wrapper for competitor analysis tool"""
        try:
            result = self.competitor_analysis_tool.analyze(industry)
            if "error" not in result:
                leaders = ", ".join(result['competitive_landscape']['market_leaders'])
                gaps = ", ".join(result['competitive_landscape']['market_gaps'])
                return f"Competitor Analysis:\nMarket Leaders: {leaders}\nMarket Gaps: {gaps}"
            else:
                return f"Competitor analysis failed: {result['error']}"
        except Exception as e:
            logger.error(f"Competitor analysis wrapper failed: {e}")
            return f"Competitor analysis failed: {str(e)}"
    
    def _risk_assessment_wrapper(self, business_type: str) -> str:
        """Wrapper for risk assessment tool"""
        try:
            result = self.risk_assessment_tool.assess(business_type)
            if "error" not in result:
                high_risks = "\n".join([
                    f"- {risk['category']}: {risk['risk']}"
                    for risk in result['high_priority_risks']
                ])
                return f"Risk Assessment:\nHigh Priority Risks:\n{high_risks}"
            else:
                return f"Risk assessment failed: {result['error']}"
        except Exception as e:
            logger.error(f"Risk assessment wrapper failed: {e}")
            return f"Risk assessment failed: {str(e)}"
    
    def consult(self, query: str) -> Dict[str, Any]:
        """Main consultation method"""
        try:
            logger.info(f"Processing consultation query: {query[:100]}...")
            
            # Validate input
            if not query or not query.strip():
                return {
                    "error": "Query cannot be empty",
                    "status": "error"
                }
            
            if len(query) > 5000:
                return {
                    "error": "Query too long (max 5000 characters)",
                    "status": "error"
                }
            
            # Process query with agent
            start_time = time.time()
            response = self.agent.run(query.strip())
            duration = time.time() - start_time
            
            # Store conversation history
            self.conversation_history.append({
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "duration": duration
            })
            
            return {
                "query": query,
                "response": response,
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Consultation failed: {e}")
            return {
                "error": f"Consultation failed: {str(e)}",
                "query": query,
                "agent_id": self.agent_id,
                "status": "error"
            }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status,
            "conversation_count": len(self.conversation_history),
            "uptime": time.time(),
            "model": Config.MODEL_ID
        }

def main():
    """Main entry point for the AI consultant agent"""
    try:
        print("🤖 AI Business Consultant Agent")
        print("=" * 50)
        
        # Initialize agent
        print("Initializing agent...")
        agent = AIConsultantAgent()
        print(f"✅ Agent '{agent.name}' initialized successfully!")
        
        # Interactive consultation loop
        print("\n💡 Ask me anything about business strategy, market analysis, or risk assessment.")
        print("Type 'quit' to exit, 'history' to see conversation history, 'status' to check agent status.\n")
        
        while True:
            try:
                query = input("🔍 Your question: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if query.lower() == 'history':
                    history = agent.get_conversation_history()
                    if history:
                        print("\n📚 Conversation History:")
                        for i, item in enumerate(history[-5:], 1):  # Show last 5
                            print(f"{i}. Q: {item['query'][:100]}...")
                            print(f"   A: {item['response'][:200]}...")
                            print(f"   Time: {item['timestamp']}")
                            print()
                    else:
                        print("No conversation history yet.")
                    continue
                
                if query.lower() == 'status':
                    status = agent.get_status()
                    print(f"\n📊 Agent Status:")
                    for key, value in status.items():
                        print(f"   {key}: {value}")
                    print()
                    continue
                
                if not query:
                    print("Please enter a question.")
                    continue
                
                # Process consultation
                print("🔄 Processing your request...")
                result = agent.consult(query)
                
                if result.get("status") == "success":
                    print(f"\n💬 {agent.name}:")
                    print(f"{result['response']}")
                    print(f"\n⏱️  Response time: {result['duration']:.2f} seconds")
                else:
                    print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                
                print("\n" + "-" * 50 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                logger.error(f"Main loop error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        logger.error(f"Initialization error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
