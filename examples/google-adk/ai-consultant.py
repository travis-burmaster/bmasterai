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
"""

import logging
import os
import time
import uuid
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
from datetime import datetime
import base64
import requests
import json

# Google ADK imports
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# BMasterAI imports
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager, SlackConnector, EmailConnector

# Constants
MODEL_ID = "gemini-2.5-flash"
APP_NAME = "ai_consultant_agent_bmasterai"
AGENT_ID = "consultant-agent-001"
AGENT_NAME = "AI Business Consultant"

# Configure BMasterAI logging
logger = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    enable_json=True
)

# Initialize monitoring
monitor = get_monitor()
monitor.start_monitoring()

# Setup integrations
integration_manager = get_integration_manager()

# Configure Slack integration if webhook URL is provided
slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
if slack_webhook:
    slack_connector = SlackConnector(webhook_url=slack_webhook)
    integration_manager.add_connector("slack", slack_connector)

# Configure email integration if SMTP details are provided
email_config = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "username": os.getenv("EMAIL_USERNAME"),
    "password": os.getenv("EMAIL_PASSWORD")
}

if email_config["username"] and email_config["password"]:
    email_connector = EmailConnector(**email_config)
    integration_manager.add_connector("email", email_connector)

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
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.integration_manager = get_integration_manager()
        self.status = "initialized"
        self.task_counter = 0
        
        # Log agent initialization
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
            
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_START,
                message="Google ADK components initialized successfully",
                metadata={"tools_count": len(self.consultant_tools)}
            )
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to initialize ADK components: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"error": str(e)}
            )
            raise

    def _create_enhanced_tool(self, tool_func):
        """Create an enhanced tool with BMasterAI logging and monitoring"""
        def enhanced_tool(*args, **kwargs):
            tool_name = tool_func.__name__
            task_id = str(uuid.uuid4())
            start_time = time.time()
            
            try:
                # Log tool start
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
                self.monitor.track_task_duration(self.agent_id, tool_name, duration_ms)
                
                # Log success
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
                self.monitor.track_error(self.agent_id, tool_name)
                
                # Log error
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=f"Tool failed: {tool_name} - {str(e)}",
                    level=LogLevel.ERROR,
                    metadata={"task_id": task_id, "error": str(e), "duration_ms": duration_ms},
                    duration_ms=duration_ms
                )
                
                return {"error": f"Tool execution failed: {str(e)}", "tool": tool_name, "status": "error"}
        
        # Preserve function metadata
        enhanced_tool.__name__ = tool_func.__name__
        enhanced_tool.__doc__ = tool_func.__doc__
        return enhanced_tool

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Recursively sanitize objects for JSON serialization"""
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

    def _perplexity_search(self, query: str, system_prompt: str = "Be precise and concise. Focus on business insights and market data.") -> Dict[str, Any]:
        """Enhanced Perplexity search with BMasterAI integration"""
        try:
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if not api_key:
                return {
                    "error": "Perplexity API key not found. Please set PERPLEXITY_API_KEY environment variable.",
                    "query": query,
                    "status": "error"
                }
            
            # Track LLM call
            start_time = time.time()
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json={
                    "model": "sonar",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ]
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Track LLM usage
            if "usage" in result:
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
            
        except Exception as e:
            return {
                "error": f"Perplexity search failed: {str(e)}",
                "query": query,
                "status": "error"
            }

    def _analyze_market_data(self, research_query: str, industry: str = "") -> Dict[str, Any]:
        """Enhanced market analysis with BMasterAI tracking"""
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
            "analysis_timestamp": datetime.now().isoformat()
        }

    def _generate_strategic_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations with enhanced tracking"""
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

    def _conduct_competitor_analysis(self, industry: str, company_focus: str = "") -> Dict[str, Any]:
        """Conduct comprehensive competitor analysis"""
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

    def _assess_business_risks(self, business_type: str, market_conditions: str = "") -> Dict[str, Any]:
        """Assess business risks comprehensively"""
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
            
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_START,
                message="Monitoring alerts configured successfully",
                metadata={"alert_rules": 3}
            )
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to setup monitoring alerts: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"error": str(e)}
            )

    def _handle_error_alert(self, alert_data: Dict[str, Any]):
        """Handle error rate alerts"""
        message = f"🚨 **High Error Rate Alert**\n\nAgent: {self.name}\nError Rate: {alert_data.get('value', 'N/A')}\nThreshold: {alert_data.get('threshold', 'N/A')}\nTime: {datetime.now().isoformat()}"
        
        self.integration_manager.send_alert_to_all({
            "metric_name": "agent_errors",
            "message": message,
            "severity": "high",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        })

    def _handle_performance_alert(self, alert_data: Dict[str, Any]):
        """Handle performance alerts"""
        message = f"⚠️ **Performance Alert**\n\nAgent: {self.name}\nResponse Time: {alert_data.get('value', 'N/A')}ms\nThreshold: {alert_data.get('threshold', 'N/A')}ms\nTime: {datetime.now().isoformat()}"
        
        self.integration_manager.send_alert_to_all({
            "metric_name": "task_duration",
            "message": message,
            "severity": "medium",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        })

    def _handle_volume_alert(self, alert_data: Dict[str, Any]):
        """Handle high volume alerts"""
        message = f"📈 **High Volume Alert**\n\nAgent: {self.name}\nConsultation Requests: {alert_data.get('value', 'N/A')}\nThreshold: {alert_data.get('threshold', 'N/A')}\nTime: {datetime.now().isoformat()}"
        
        self.integration_manager.send_alert_to_all({
            "metric_name": "consultation_requests",
            "message": message,
            "severity": "low",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        })

    def start(self):
        """Start the consultant agent"""
        try:
            self.status = "running"
            self.monitor.track_agent_start(self.agent_id)
            
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_START,
                message=f"BMasterAI Consultant Agent {self.name} started successfully",
                level=LogLevel.INFO
            )
            
            # Send startup notification
            startup_message = f"🤖 **AI Consultant Agent Started**\n\nAgent: {self.name}\nModel: {MODEL_ID}\nTools: {len(self.consultant_tools)}\nStatus: {self.status}\nTime: {datetime.now().isoformat()}"
            
            self.integration_manager.send_notification_to_all({
                "message": startup_message,
                "type": "startup",
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to start agent: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"error": str(e)}
            )
            return False

    def stop(self):
        """Stop the consultant agent"""
        try:
            self.status = "stopped"
            self.monitor.track_agent_stop(self.agent_id)
            
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_STOP,
                message=f"BMasterAI Consultant Agent {self.name} stopped",
                level=LogLevel.INFO
            )
            
            # Send shutdown notification
            shutdown_message = f"🛑 **AI Consultant Agent Stopped**\n\nAgent: {self.name}\nTotal Tasks: {self.task_counter}\nStatus: {self.status}\nTime: {datetime.now().isoformat()}"
            
            self.integration_manager.send_notification_to_all({
                "message": shutdown_message,
                "type": "shutdown",
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to stop agent: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"error": str(e)}
            )
            return False

    def execute_consultation(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a consultation with comprehensive tracking"""
        consultation_id = str(uuid.uuid4())
        self.task_counter += 1
        start_time = time.time()
        
        try:
            # Log consultation start
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
            self.monitor.track_task_duration(self.agent_id, "consultation", duration_ms)
            
            # Log consultation completion
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
                "response": response,
                "duration_ms": duration_ms,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Track error
            self.monitor.track_error(self.agent_id, "consultation")
            
            # Log error
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Consultation failed: {str(e)}",
                level=LogLevel.ERROR,
                metadata={
                    "consultation_id": consultation_id,
                    "query": query,
                    "error": str(e),
                    "duration_ms": duration_ms
                },
                duration_ms=duration_ms
            )
            
            return {
                "consultation_id": consultation_id,
                "query": query,
                "error": str(e),
                "duration_ms": duration_ms,
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }

    def get_agent_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive agent dashboard"""
        return {
            "agent_info": {
                "agent_id": self.agent_id,
                "name": self.name,
                "status": self.status,
                "task_counter": self.task_counter,
                "model": MODEL_ID,
                "tools_count": len(self.consultant_tools)
            },
            "performance": self.monitor.get_agent_dashboard(self.agent_id),
            "system_health": self.monitor.get_system_health(),
            "integration_status": self.integration_manager.get_status(),
            "timestamp": datetime.now().isoformat()
        }

    def generate_consultation_report(self, time_period: str = "24h") -> Dict[str, Any]:
        """Generate comprehensive consultation report"""
        try:
            # Get recent events
            recent_events = self.logger.get_events(limit=1000)
            
            # Filter consultation events
            consultation_events = [
                event for event in recent_events
                if event.agent_id == self.agent_id and 
                event.event_type.value in ["task_start", "task_complete", "task_error"]
            ]
            
            # Calculate metrics
            total_consultations = len([e for e in consultation_events if e.event_type.value == "task_start"])
            successful_consultations = len([e for e in consultation_events if e.event_type.value == "task_complete"])
            failed_consultations = len([e for e in consultation_events if e.event_type.value == "task_error"])
            
            success_rate = (successful_consultations / total_consultations * 100) if total_consultations > 0 else 0
            
            # Calculate average response time
            completed_events = [e for e in consultation_events if e.event_type.value == "task_complete"]
            avg_response_time = sum(e.duration_ms for e in completed_events) / len(completed_events) if completed_events else 0
            
            report = {
                "report_info": {
                    "agent_id": self.agent_id,
                    "agent_name": self.name,
                    "time_period": time_period,
                    "generated_at": datetime.now().isoformat()
                },
                "consultation_metrics": {
                    "total_consultations": total_consultations,
                    "successful_consultations": successful_consultations,
                    "failed_consultations": failed_consultations,
                    "success_rate": round(success_rate, 2),
                    "average_response_time_ms": round(avg_response_time, 2)
                },
                "performance_data": self.monitor.get_agent_dashboard(self.agent_id),
                "system_health": self.monitor.get_system_health(),
                "integration_status": self.integration_manager.get_status(),
                "recent_activities": [
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type.value,
                        "message": event.message,
                        "duration_ms": event.duration_ms
                    }
                    for event in consultation_events[-10:]  # Last 10 events
                ]
            }
            
            return report
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to generate consultation report: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"error": str(e)}
            )
            return {"error": f"Failed to generate report: {str(e)}"}

# Global agent instance
consultant_agent = None

def get_consultant_agent() -> BMasterAIConsultantAgent:
    """Get or create the global consultant agent instance"""
    global consultant_agent
    if consultant_agent is None:
        consultant_agent = BMasterAIConsultantAgent()
    return consultant_agent

def main():
    """Main function to run the consultant agent"""
    print("🤖 AI Consultant Agent with Google ADK and BMasterAI Framework")
    print("=" * 65)
    print()
    print("This enhanced agent provides comprehensive business consultation including:")
    print("• Market research and analysis with real-time data")
    print("• Strategic recommendations with success metrics")
    print("• Competitor analysis and market positioning")
    print("• Risk assessment and mitigation strategies")
    print("• Enterprise-grade monitoring and alerting")
    print("• Multi-channel integrations (Slack, Email, etc.)")
    print()
    
    try:
        # Initialize and start the agent
        agent = get_consultant_agent()
        if agent.start():
            print("✅ Agent initialized successfully!")
            print(f"   Model: {MODEL_ID}")
            print(f"   Tools: {len(agent.consultant_tools)} available")
            print(f"   Integrations: {len(agent.integration_manager.active_integrations)} active")
            print()
            
            print("🔧 Setup Instructions:")
            print("1. Set your API keys:")
            print("   export GOOGLE_API_KEY=your-google-api-key")
            print("   export PERPLEXITY_API_KEY=your-perplexity-api-key")
            print()
            print("2. Optional integrations:")
            print("   export SLACK_WEBHOOK_URL=your-slack-webhook")
            print("   export EMAIL_USERNAME=your-email@gmail.com")
            print("   export EMAIL_PASSWORD=your-app-password")
            print()
            print("3. Start the Google ADK web interface:")
            print("   adk web")
            print()
            print("4. Open your browser and navigate to http://localhost:8000")
            print("5. Select 'AI Business Consultant' from available agents")
            print()
            
            print("📊 Example consultation topics:")
            print('• "I want to launch a SaaS startup for small businesses"')
            print('• "Should I expand my retail business to e-commerce?"')
            print('• "What are the market opportunities in healthcare technology?"')
            print('• "How should I position my new fintech product?"')
            print('• "What are the risks of entering the renewable energy market?"')
            print()
            
            print("🔍 Monitoring Features:")
            print("• Real-time performance tracking")
            print("• Automated alerting for issues")
            print("• Comprehensive reporting and analytics")
            print("• Integration with enterprise systems")
            print("• Success metrics and KPI tracking")
            print()
            
            print("📈 Access dashboards:")
            print("• Use the Eval tab in ADK web to save and evaluate sessions")
            print("• Monitor system health and performance metrics")
            print("• Generate comprehensive consultation reports")
            print("• Track success rates and response times")
            print()
            
            # Show current dashboard
            dashboard = agent.get_agent_dashboard()
            print("📋 Current Status:")
            print(f"   Agent Status: {dashboard['agent_info']['status']}")
            print(f"   Tools Available: {dashboard['agent_info']['tools_count']}")
            print(f"   Consultations Completed: {dashboard['agent_info']['task_counter']}")
            print(f"   Active Integrations: {len(dashboard['integration_status'])}")
            print()
            
            print("🎯 The agent is ready for consultations!")
            print("   Use 'adk web' to start the web interface")
            
        else:
            print("❌ Failed to initialize agent. Check your configuration.")
            
    except Exception as e:
        print(f"❌ Error starting agent: {str(e)}")
        print("   Please check your environment variables and dependencies")

if __name__ == "__main__":
    main()