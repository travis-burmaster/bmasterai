#!/usr/bin/env python3
"""
AI Consultant Agent with Google ADK and BMasterAI Framework Integration

This agent combines the power of Google's Agent Development Kit (ADK) with 
the comprehensive monitoring and logging capabilities of the BMasterAI framework.

Features:
- Google ADK integration for advanced LLM capabilities
- BMasterAI framework for enterprise-grade monitoring and logging
- Real-time web research using Perplexity AI
- Market analysis and strategic recommendations
- Comprehensive performance tracking and alerting
- Multi-integration support (Slack, email, Discord, etc.)
- Enhanced error handling and input validation
- Environment variable configuration
- Improved security and logging
"""

import logging
import os
import sys
import time
import uuid
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
from datetime import datetime
import base64
import requests
import json
import re
from urllib.parse import urlparse

# Google ADK imports - preserved as per requirements
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# BMasterAI imports - preserved as per requirements
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager, SlackConnector, EmailConnector

# Environment variable configuration with defaults
MODEL_ID = os.getenv("MODEL_ID", "gemini-2.5-flash")
APP_NAME = os.getenv("APP_NAME", "ai_consultant_agent_bmasterai")
AGENT_ID = os.getenv("AGENT_ID", "consultant-agent-001")
AGENT_NAME = os.getenv("AGENT_NAME", "AI Business Consultant")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "5000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging with environment variables
def setup_logging():
    """Setup logging configuration with proper error handling"""
    try:
        log_level_map = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR
        }
        
        log_level = log_level_map.get(LOG_LEVEL.upper(), LogLevel.INFO)
        
        logger = configure_logging(
            log_level=log_level,
            enable_console=True,
            enable_file=True,
            enable_json=True
        )
        return logger
    except Exception as e:
        # Fallback to standard logging if BMasterAI logging fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to configure BMasterAI logging, using fallback: {e}")
        return logger

# Initialize logging
logger = setup_logging()

# Initialize monitoring with error handling
def setup_monitoring():
    """Setup monitoring with proper error handling"""
    try:
        monitor = get_monitor()
        monitor.start_monitoring()
        return monitor
    except Exception as e:
        logger.error(f"Failed to initialize BMasterAI monitoring: {e}")
        return None

monitor = setup_monitoring()

# Setup integrations with error handling
def setup_integrations():
    """Setup integrations with proper error handling"""
    try:
        integration_manager = get_integration_manager()
        
        # Configure Slack integration if webhook URL is provided
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook and _validate_url(slack_webhook):
            try:
                slack_connector = SlackConnector(webhook_url=slack_webhook)
                integration_manager.add_connector("slack", slack_connector)
                logger.info("Slack integration configured successfully")
            except Exception as e:
                logger.error(f"Failed to configure Slack integration: {e}")
        
        # Configure email integration if SMTP details are provided
        email_config = {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("EMAIL_USERNAME"),
            "password": os.getenv("EMAIL_PASSWORD")
        }
        
        if email_config["username"] and email_config["password"]:
            try:
                email_connector = EmailConnector(**email_config)
                integration_manager.add_connector("email", email_connector)
                logger.info("Email integration configured successfully")
            except Exception as e:
                logger.error(f"Failed to configure email integration: {e}")
        
        return integration_manager
    except Exception as e:
        logger.error(f"Failed to initialize integration manager: {e}")
        return None

integration_manager = setup_integrations()

def _validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def _validate_input(text: str, max_length: int = MAX_QUERY_LENGTH) -> bool:
    """Validate input text for security and length"""
    if not text or not isinstance(text, str):
        return False
    
    if len(text.strip()) == 0 or len(text) > max_length:
        return False
    
    # Basic security check for potential injection attempts
    dangerous_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\('
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    return True

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

class BMasterAIConsultantAgent:
    """
    Enhanced AI Consultant Agent with BMasterAI integration
    """
    
    def __init__(self, agent_id: str = AGENT_ID, name: str = AGENT_NAME):
        self.agent_id = agent_id
        self.name = name
        self.logger = logger
        self.monitor = monitor
        self.integration_manager = integration_manager
        self.status = "initialized"
        self.task_counter = 0
        
        try:
            # Log agent initialization
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.AGENT_START,
                    message=f"BMasterAI Consultant Agent {self.name} initialized",
                    metadata={"name": self.name, "model": MODEL_ID}
                )
            
            # Initialize Google ADK components
            self._initialize_adk_components()
            
            # Setup monitoring alerts
            self._setup_monitoring_alerts()
            
        except Exception as e:
            error_msg = f"Failed to initialize agent: {str(e)}"
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={"error": str(e)}
                )
            else:
                logging.error(error_msg)
            raise
        
    def _initialize_adk_components(self):
        """Initialize Google ADK components with BMasterAI integration"""
        try:
            # Create enhanced tools with BMasterAI logging
            self.consultant_tools = [
                self._create_enhanced_tool(self._perplexity_search),
                self._create_enhanced_tool(self._analyze_market_data),
                self._create_enhanced_tool(self._generate_strategic_recommendations),
                self._create_enhanced_tool(self._conduct_competitor_analysis),
                self._create_enhanced_tool(self._assess_business_risks)
            ]
            
            # Define enhanced instructions
            self.instructions = self._get_enhanced_instructions()
            
            # Create ADK agent with enhanced capabilities
            self.adk_agent = LlmAgent(
                model=MODEL_ID,
                name=self.name,
                description="An AI business consultant with BMasterAI monitoring and Google ADK integration",
                instruction=self.instructions,
                tools=self.consultant_tools,
                output_key="consultation_response"
            )
            
            # Setup session service and runner
            self.session_service = InMemorySessionService()
            self.runner = Runner(
                agent=self.adk_agent,
                app_name=APP_NAME,
                session_service=self.session_service
            )
            
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.AGENT_START,
                    message="Google ADK components initialized successfully",
                    metadata={"tools_count": len(self.consultant_tools)}
                )
            
        except Exception as e:
            error_msg = f"Failed to initialize ADK components: {str(e)}"
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={"error": str(e)}
                )
            else:
                logging.error(error_msg)
            raise

    def _create_enhanced_tool(self, tool_func):
        """Create an enhanced tool with BMasterAI logging and monitoring"""
        def enhanced_tool(*args, **kwargs):
            tool_name = tool_func.__name__
            task_id = str(uuid.uuid4())
            start_time = time.time()
            
            try:
                # Validate inputs
                if args and isinstance(args[0], str) and not _validate_input(args[0]):
                    return {
                        "error": "Invalid input: Input validation failed",
                        "tool": tool_name,
                        "status": "error"
                    }
                
                # Log tool start
                if self.logger:
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_START,
                        message=f"Starting tool: {tool_name}",
                        metadata={"task_id": task_id, "tool": tool_name, "args": str(args)[:200]}
                    )
                
                # Execute tool
                result = tool_func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Track performance
                if self.monitor:
                    self.monitor.track_task_duration(self.agent_id, tool_name, duration_ms)
                
                # Log success
                if self.logger:
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_COMPLETE,
                        message=f"Tool completed successfully: {tool_name}",
                        metadata={"task_id": task_id, "duration_ms": duration_ms},
                        duration_ms=duration_ms
                    )
                
                return self._sanitize_for_json(result)
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Track error
                if self.monitor:
                    self.monitor.track_error(self.agent_id, tool_name)
                
                # Log error
                error_msg = f"Tool failed: {tool_name} - {str(e)}"
                if self.logger:
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_ERROR,
                        message=error_msg,
                        level=LogLevel.ERROR,
                        metadata={"task_id": task_id, "error": str(e), "duration_ms": duration_ms},
                        duration_ms=duration_ms
                    )
                else:
                    logging.error(error_msg)
                
                return {"error": f"Tool execution failed: {str(e)}", "tool": tool_name, "status": "error"}
        
        # Preserve function metadata
        enhanced_tool.__name__ = tool_func.__name__
        enhanced_tool.__doc__ = tool_func.__doc__
        return enhanced_tool

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Recursively sanitize objects for JSON serialization"""
        try:
            if isinstance(obj, bytes):
                try:
                    return obj.decode('utf-8')
                except UnicodeDecodeError:
                    return base64.b64encode(obj).decode('ascii')
            elif isinstance(obj, dict):
                return {key: self._sanitize_for_json(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [self._sanitize_for_json(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(self._sanitize_for_json(item) for item in obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        except Exception as e:
            logging.error(f"Error sanitizing object for JSON: {e}")
            return str(obj)

    def _perplexity_search(self, query: str, system_prompt: str = "Be precise and concise. Focus on business insights and market data.") -> Dict[str, Any]:
        """Enhanced Perplexity search with BMasterAI integration and improved error handling"""
        try:
            # Validate inputs
            if not _validate_input(query):
                return {
                    "error": "Invalid query: Query validation failed",
                    "query": query,
                    "status": "error"
                }
            
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if not api_key:
                return {
                    "error": "Perplexity API key not found. Please set PERPLEXITY_API_KEY environment variable.",
                    "query": query,
                    "status": "error"
                }
            
            # Track LLM call
            start_time = time.time()
            
            # Prepare request with timeout and proper headers
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"{APP_NAME}/1.0"
            }
            
            payload = {
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
            }
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=API_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Track LLM usage
            if self.monitor and "usage" in result:
                tokens_used = result["usage"].get("total_tokens", 0)
                self.monitor.track_llm_call(self.agent_id, "perplexity-sonar", tokens_used, duration_ms)
            
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
                    "created": result.get("created", 0),
                    "duration_ms": duration_ms
                }
            
            return {
                "error": "No response content found",
                "query": query,
                "status": "error",
                "raw_response": result
            }
            
        except requests.exceptions.Timeout:
            return {
                "error": f"Request timeout after {API_TIMEOUT} seconds",
                "query": query,
                "status": "error"
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Request failed: {str(e)}",
                "query": query,
                "status": "error"
            }
        except json.JSONDecodeError as e:
            return {
                "error": f"Invalid JSON response: {str(e)}",
                "query": query,
                "status": "error"
            }
        except Exception as e:
            return {
                "error": f"Perplexity search failed: {str(e)}",
                "query": query,
                "status": "error"
            }

    def _analyze_market_data(self, research_query: str, industry: str = "") -> Dict[str, Any]:
        """Enhanced market analysis with BMasterAI tracking and improved error handling"""
        try:
            if not _validate_input(research_query):
                return {
                    "error": "Invalid research query",
                    "status": "error"
                }
            
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
            
            if industry and _validate_input(industry):
                insights.append(
                    MarketInsight("Industry Specific", f"{industry} sector shows growth potential", 0.7, "Industry Report")
                )
            
            return {
                "query": research_query,
                "industry": industry,
                "insights": [
                    {
                        "category": insight.category,
                        "finding": insight.finding,
                        "confidence": insight.confidence,
                        "source": insight.source,
                        "timestamp": insight.timestamp.isoformat()
                    }
                    for insight in insights
                ],
                "summary": f"Market analysis completed for: {research_query}",
                "total_insights": len(insights),
                "analysis_timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": f"Market analysis failed: {str(e)}",
                "query": research_query,
                "status": "error"
            }

    def _generate_strategic_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations with enhanced tracking and error handling"""
        try:
            if not isinstance(analysis_data, dict):
                return [{"error": "Invalid analysis data format", "status": "error"}]
            
            recommendations = []
            insights = analysis_data.get("insights", [])
            
            # Generate contextual recommendations
            if any("startup" in insight.get("finding", "").lower() for insight in insights):
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
            
            if any("saas" in insight.get("finding", "").lower() or "software" in insight.get("finding", "").lower() for insight in insights):
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
            
            if any("ai" in insight.get("finding", "").lower() for insight in insights):
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
            return [{"error": f"Failed to generate recommendations: {str(e)}", "status": "error"}]

    def _conduct_competitor_analysis(self, industry: str, company_focus: str = "") -> Dict[str, Any]:
        """Conduct comprehensive competitor analysis with improved error handling"""
        try:
            if not _validate_input(industry):
                return {
                    "error": "Invalid industry parameter",
                    "status": "error"
                }
            
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
                "recommendations": [],
                "status": "success"
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
            return {
                "error": f"Competitor analysis failed: {str(e)}",
                "industry": industry,
                "status": "error"
            }

    def _assess_business_risks(self, business_type: str, market_conditions: str = "") -> Dict[str, Any]:
        """Assess business risks comprehensively with improved error handling"""
        try:
            if not _validate_input(business_type):
                return {
                    "error": "Invalid business type parameter",
                    "status": "error"
                }
            
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
                "risk_matrix": [],
                "mitigation_strategies": [],
                "status": "success"
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
            
            # Risk matrix (High impact, High probability risks)
            risk_assessment["risk_matrix"] = [
                {"risk": "Market competition", "priority": "Critical"},
                {"risk": "Cash flow management", "priority": "Critical"},
                {"risk": "Key person dependency", "priority": "High"},
                {"risk": "Cybersecurity threats", "priority": "High"}
            ]
            
            # Mitigation strategies
            risk_assessment["mitigation_strategies"] = [
                {
                    "risk": "Market competition",
                    "strategy": "Develop unique value proposition and build customer loyalty",
                    "timeline": "Ongoing",
                    "responsibility": "Strategy team"
                },
                {
                    "risk": "Cash flow management",
                    "strategy": "Implement robust financial planning and monitoring systems",
                    "timeline": "1-2 months",
                    "responsibility": "Finance team"
                },
                {
                    "risk": "Key person dependency",
                    "strategy": "Document processes and cross-train team members",
                    "timeline": "2-3 months",
                    "responsibility": "Operations team"
                },
                {
                    "risk": "Cybersecurity threats",
                    "strategy": "Implement comprehensive security framework and regular audits",
                    "timeline": "1-3 months",
                    "responsibility": "IT security team"
                }
            ]
            
            return risk_assessment
            
        except Exception as e:
            return {
                "error": f"Risk assessment failed: {str(e)}",
                "business_type": business_type,
                "status": "error"
            }

    def _get_enhanced_instructions(self) -> str:
        """Get enhanced instructions for the consultant agent"""
        return """You are a senior AI business consultant with BMasterAI enterprise monitoring capabilities.

Your enhanced expertise includes:
- Strategic business consulting with real-time market data
- Risk assessment and mitigation with comprehensive frameworks
- Implementation planning with success metrics and tracking
- Competitive analysis and market positioning
- AI and technology strategy development
- Enterprise-grade monitoring and reporting

Core Responsibilities:
1. Use Perplexity search for real-time market data, competitor intelligence, and industry trends
2. Conduct comprehensive market analysis using multiple data sources
3. Generate strategic recommendations with clear action items and success metrics
4. Perform detailed competitor analysis with actionable insights
5. Assess business risks with comprehensive mitigation strategies
6. Provide implementation roadmaps with realistic timelines and responsibilities

Enhanced Capabilities with BMasterAI:
- All activities are monitored and logged for performance optimization
- Real-time alerts for critical issues or opportunities
- Comprehensive reporting and analytics
- Integration with enterprise communication systems
- Performance metrics and success tracking

Critical Rules:
- Always use current market data from Perplexity search when relevant
- Provide specific, actionable recommendations with measurable outcomes
- Include risk assessment in all strategic recommendations
- Prioritize recommendations by business impact and implementation feasibility
- Use evidence-based analysis with proper citations and sources
- Maintain professional, analytical approach while being results-oriented

Search Strategy:
- Research competitors, market size, funding trends, and regulatory changes
- Validate assumptions with current web data and market intelligence
- Look for case studies and best practices from similar businesses
- Monitor industry news and development patterns
- Always include citations and sources for credibility

Performance Optimization:
- Track consultation quality and client satisfaction
- Monitor tool performance and response times
- Alert on unusual patterns or potential issues
- Generate comprehensive reports on consultation effectiveness
- Integrate with business systems for seamless workflow

Always maintain the highest standards of professionalism and provide comprehensive, well-researched consultation backed by current data and enterprise-grade monitoring."""

    def _setup_monitoring_alerts(self):
        """Setup custom monitoring alerts for the consultant agent"""
        try:
            if not self.monitor:
                logging.warning("Monitor not available, skipping alert setup")
                return
            
            # Alert for high error rates
            self.monitor.metrics_collector.add_alert_rule(
                metric_name="agent_errors",
                threshold=3.0,
                condition="greater_than",
                duration_minutes=5,
                callback=self._handle_error_alert
            )
            
            # Alert for slow response times
            self.monitor.metrics_collector.add_alert_rule(
                metric_name="task_duration",
                threshold=30000.0,  # 30 seconds
                condition="greater_than",
                duration_minutes=2,
                callback=self._handle_performance_alert
            )
            
            # Alert for high consultation volume
            self.monitor.metrics_collector.add_alert_rule(
                metric_name="consultation_requests",
                threshold=50.0,
                condition="greater_than",
                duration_minutes=60,
                callback=self._handle_volume_alert
            )
            
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.AGENT_START,
                    message="Monitoring alerts configured successfully",
                    metadata={"alert_rules": 3}
                )
            
        except Exception as e:
            error_msg = f"Failed to setup monitoring alerts: {str(e)}"
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={"error": str(e)}
                )
            else:
                logging.error(error_msg)

    def _handle_error_alert(self, alert_data: Dict[str, Any]):
        """Handle error rate alerts"""
        try:
            message = f"🚨 **High Error Rate Alert**\n\nAgent: {self.name}\nError Rate: {alert_data.get('value', 'N/A')}\nThreshold: {alert_data.get('threshold', 'N/A')}\nTime: {datetime.now().isoformat()}"
            
            if self.integration_manager:
                self.integration_manager.send_alert_to_all({
                    "metric_name": "agent_errors",
                    "message": message,
                    "severity": "high",
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logging.error(f"Failed to handle error alert: {e}")

    def _handle_performance_alert(self, alert_data: Dict[str, Any]):
        """Handle performance alerts"""
        try:
            message = f"⚠️ **Performance Alert**\n\nAgent: {self.name}\nResponse Time: {alert_data.get('value', 'N/A')}ms\nThreshold: {alert_data.get('threshold', 'N/A')}ms\nTime: {datetime.now().isoformat()}"
            
            if self.integration_manager:
                self.integration_manager.send_alert_to_all({
                    "metric_name": "task_duration",
                    "message": message,
                    "severity": "medium",
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logging.error(f"Failed to handle performance alert: {e}")

    def _handle_volume_alert(self, alert_data: Dict[str, Any]):
        """Handle high volume alerts"""
        try:
            message = f"📈 **High Volume Alert**\n\nAgent: {self.name}\nConsultation Requests: {alert_data.get('value', 'N/A')}\nThreshold: {alert_data.get('threshold', 'N/A')}\nTime: {datetime.now().isoformat()}"
            
            if self.integration_manager:
                self.integration_manager.send_alert_to_all({
                    "metric_name": "consultation_requests",
                    "message": message,
                    "severity": "low",
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logging.error(f"Failed to handle volume alert: {e}")

    def start(self):
        """Start the consultant agent with improved error handling"""
        try:
            self.status = "running"
            if self.monitor:
                self.monitor.track_agent_start(self.agent_id)
            
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.AGENT_START,
                    message=f"BMasterAI Consultant Agent {self.name} started successfully",
                    level=LogLevel.INFO
                )
            
            # Send startup notification
            startup_message = f"🤖 **AI Consultant Agent Started**\n\nAgent: {self.name}\nModel: {MODEL_ID}\nTools: {len(self.consultant_tools) if hasattr(self, 'consultant_tools') else 0}\nStatus: {self.status}\nTime: {datetime.now().isoformat()}"
            
            if self.integration_manager:
                self.integration_manager.send_notification_to_all({
                    "message": startup_message,
                    "type": "startup",
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                })
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to start agent: {str(e)}"
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={"error": str(e)}
                )
            else:
                logging.error(error_msg)
            return False

    def stop(self):
        """Stop the consultant agent with improved error handling"""
        try:
            self.status = "stopped"
            if self.monitor:
                self.monitor.track_agent_stop(self.agent_id)
            
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.AGENT_STOP,
                    message=f"BMasterAI Consultant Agent {self.name} stopped",
                    level=LogLevel.INFO
                )
            
            # Send shutdown notification
            shutdown_message = f"🛑 **AI Consultant Agent Stopped**\n\nAgent: {self.name}\nTotal Tasks: {self.task_counter}\nStatus: {self.status}\nTime: {datetime.now().isoformat()}"
            
            if self.integration_manager:
                self.integration_manager.send_notification_to_all({
                    "message": shutdown_message,
                    "type": "shutdown",
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now().isoformat()
                })
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to stop agent: {str(e)}"
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={"error": str(e)}
                )
            else:
                logging.error(error_msg)
            return False

    def execute_consultation(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a consultation with comprehensive tracking and improved error handling"""
        consultation_id = str(uuid.uuid4())
        self.task_counter += 1
        start_time = time.time()
        
        try:
            # Validate input
            if not _validate_input(query):
                return {
                    "consultation_id": consultation_id,
                    "error": "Invalid query: Input validation failed",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Log consultation start
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_START,
                    message=f"Starting consultation: {query[:100]}...",
                    metadata={
                        "consultation_id": consultation_id,
                        "query": query,
                        "context": context or {},
                        "task_number": self.task_counter
                    }
                )
            
            # Track consultation request
            if self.monitor:
                self.monitor.track_custom_metric(
                    agent_id=self.agent_id,
                    metric_name="consultation_requests",
                    value=1,
                    timestamp=datetime.now()
                )
            
            # Execute consultation through ADK
            session_id = f"consultation-{consultation_id}"
            response = self.runner.run(
                session_id=session_id,
                input_data={"query": query, "context": context or {}}
            )
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Track performance
            if self.monitor:
                self.monitor.track_task_duration(self.agent_id, "consultation", duration_ms)
            
            # Log consultation completion
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"Consultation completed successfully",
                    metadata={
                        "consultation_id": consultation_id,
                        "duration_ms": duration_ms,
                        "response_length": len(str(response))
                    },
                    duration_ms=duration_ms
                )
            
            return {
                "consultation_id": consultation_id,
                "query": query,
                "context": context or {},
                "response": response,
                "status": "success",
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "task_number": self.task_counter
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Track error
            if self.monitor:
                self.monitor.track_error(self.agent_id, "consultation")
            
            # Log error
            error_msg = f"Consultation failed: {str(e)}"
            if self.logger:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    metadata={
                        "consultation_id": consultation_id,
                        "error": str(e),
                        "duration_ms": duration_ms
                    },
                    duration_ms=duration_ms
                )
            else:
                logging.error(error_msg)
            
            return {
                "consultation_id": consultation_id,
                "query": query,
                "context": context or {},
                "error": f"Consultation failed: {str(e)}",
                "status": "error",
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "task_number": self.task_counter
            }

def main():
    """Main entry point for the AI consultant agent"""
    try:
        # Initialize agent
        agent = BMasterAIConsultantAgent()
        
        # Start agent
        if agent.start():
            print(f"✅ AI Consultant Agent '{agent.name}' started successfully!")
            print(f"Agent ID: {agent.agent_id}")
            print(f"Model: {MODEL_ID}")
            print(f"Status: {agent.status}")
            
            # Example consultation (remove in production)
            if len(sys.argv) > 1:
                query = " ".join(sys.argv[1:])
                print(f"\n🔍 Executing consultation: {query}")
                result = agent.execute_consultation(query)
                print(f"📊 Result: {result}")
            
            return agent
        else:
            print("❌ Failed to start AI Consultant Agent")
            return None
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AI Consultant Agent...")
        if 'agent' in locals():
            agent.stop()
        return None
    except Exception as e:
        print(f"❌ Error initializing AI Consultant Agent: {e}")
        return None

if __name__ == "__main__":
    main()
