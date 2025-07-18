"""Business analysis tools for the AI consultant."""

import json
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from utils.ai_client import ai_client

@dataclass
class MarketInsight:
    """Structure for market research insights."""
    category: str
    finding: str
    confidence: float
    source: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class BusinessAnalyzer:
    """Business analysis tools with AI-powered insights."""
    
    def __init__(self):
        self.ai_client = ai_client
    
    def analyze_market_data(self, research_query: str, industry: str = "") -> Dict[str, Any]:
        """Analyze market data with AI-powered insights."""
        try:
            # Create context-aware prompt
            prompt = f"""
            Analyze the following market research query and provide detailed insights:
            
            Query: {research_query}
            Industry: {industry if industry else "General"}
            
            Please provide a comprehensive market analysis including:
            1. Market opportunity assessment
            2. Key trends and drivers
            3. Competitive landscape overview
            4. Risk factors
            5. Strategic recommendations
            
            Format your response as a structured analysis with clear sections.
            """
            
            response = self.ai_client.chat_completion([
                {"role": "system", "content": "You are a market research analyst. Provide detailed, data-driven insights."},
                {"role": "user", "content": prompt}
            ])
            
            if response["success"]:
                # Generate structured insights
                insights = self._generate_market_insights(research_query, industry)
                
                return {
                    "query": research_query,
                    "industry": industry,
                    "ai_analysis": response["content"],
                    "insights": insights,
                    "summary": f"Market analysis completed for: {research_query}",
                    "total_insights": len(insights),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "success": True
                }
            else:
                return {
                    "query": research_query,
                    "industry": industry,
                    "error": response["error"],
                    "success": False
                }
                
        except Exception as e:
            return {
                "query": research_query,
                "industry": industry,
                "error": str(e),
                "success": False
            }
    
    def _generate_market_insights(self, query: str, industry: str) -> List[Dict[str, Any]]:
        """Generate contextual market insights."""
        insights = []
        
        # Generate insights based on query keywords
        if "startup" in query.lower() or "launch" in query.lower():
            insights.extend([
                MarketInsight("Market Opportunity", "Growing market with moderate competition", 0.8, "Market Research"),
                MarketInsight("Risk Assessment", "Standard startup risks apply - funding, competition", 0.7, "Risk Analysis"),
                MarketInsight("Recommendation", "Conduct MVP testing before full launch", 0.9, "Strategic Planning")
            ])
        
        if "saas" in query.lower() or "software" in query.lower():
            insights.extend([
                MarketInsight("Technology Trend", "Cloud-based solutions gaining adoption", 0.9, "Tech Analysis"),
                MarketInsight("Customer Behavior", "Businesses prefer subscription models", 0.8, "Market Study"),
                MarketInsight("Scalability", "SaaS models offer better scaling potential", 0.85, "Business Model Analysis")
            ])
        
        if "ai" in query.lower() or "artificial intelligence" in query.lower():
            insights.extend([
                MarketInsight("AI Trend", "AI adoption accelerating across industries", 0.95, "Technology Report"),
                MarketInsight("Investment", "AI startups receiving significant funding", 0.85, "Investment Analysis"),
                MarketInsight("Regulation", "AI governance frameworks emerging", 0.7, "Regulatory Analysis")
            ])
        
        if industry:
            insights.append(
                MarketInsight("Industry Specific", f"{industry} sector shows growth potential", 0.7, "Industry Report")
            )
        
        return [asdict(insight) for insight in insights]
    
    def generate_strategic_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on analysis."""
        try:
            prompt = f"""
            Based on the following market analysis, generate 3-5 strategic recommendations:
            
            Analysis Data: {json.dumps(analysis_data, indent=2)}
            
            For each recommendation, provide:
            1. Category (e.g., Market Entry, Technology, Risk Management)
            2. Priority (High/Medium/Low)
            3. Specific recommendation
            4. Clear rationale
            5. Implementation timeline
            6. Success metrics
            7. Action items
            
            Format as a JSON array of recommendation objects.
            """
            
            response = self.ai_client.chat_completion([
                {"role": "system", "content": "You are a strategic business consultant. Provide actionable recommendations."},
                {"role": "user", "content": prompt}
            ])
            
            if response["success"]:
                try:
                    # Try to parse as JSON
                    recommendations = json.loads(response["content"])
                    return recommendations if isinstance(recommendations, list) else [recommendations]
                except json.JSONDecodeError:
                    # If JSON parsing fails, return a structured response
                    return self._generate_default_recommendations(analysis_data)
            else:
                return self._generate_default_recommendations(analysis_data)
                
        except Exception as e:
            return self._generate_default_recommendations(analysis_data)
    
    def _generate_default_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default recommendations when AI parsing fails."""
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
        
        if any("saas" in insight.get("finding", "").lower() for insight in insights):
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
    
    def conduct_competitor_analysis(self, industry: str, company_focus: str = "") -> Dict[str, Any]:
        """Conduct AI-powered competitor analysis."""
        try:
            prompt = f"""
            Conduct a comprehensive competitor analysis for:
            
            Industry: {industry}
            Company Focus: {company_focus if company_focus else "General"}
            
            Please provide:
            1. Market leaders and their key strengths
            2. Emerging players to watch
            3. Market gaps and opportunities
            4. Competitive advantages to focus on
            5. Key threats and challenges
            6. Strategic recommendations
            
            Provide a structured analysis with specific examples where possible.
            """
            
            response = self.ai_client.chat_completion([
                {"role": "system", "content": "You are a competitive intelligence analyst with expertise in market analysis."},
                {"role": "user", "content": prompt}
            ])
            
            if response["success"]:
                return {
                    "industry": industry,
                    "company_focus": company_focus,
                    "analysis": response["content"],
                    "analysis_timestamp": datetime.now().isoformat(),
                    "success": True
                }
            else:
                return {
                    "industry": industry,
                    "company_focus": company_focus,
                    "error": response["error"],
                    "success": False
                }
                
        except Exception as e:
            return {
                "industry": industry,
                "company_focus": company_focus,
                "error": str(e),
                "success": False
            }
    
    def assess_business_risks(self, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess business risks based on context."""
        try:
            prompt = f"""
            Assess the business risks for the following context:
            
            Business Context: {json.dumps(business_context, indent=2)}
            
            Please provide:
            1. Key risk categories (financial, operational, market, technology, regulatory)
            2. Risk assessment with probability and impact
            3. Risk mitigation strategies
            4. Monitoring recommendations
            5. Contingency planning suggestions
            
            Focus on actionable risk management strategies.
            """
            
            response = self.ai_client.chat_completion([
                {"role": "system", "content": "You are a risk management consultant with expertise in business risk assessment."},
                {"role": "user", "content": prompt}
            ])
            
            if response["success"]:
                return {
                    "business_context": business_context,
                    "risk_assessment": response["content"],
                    "assessment_timestamp": datetime.now().isoformat(),
                    "success": True
                }
            else:
                return {
                    "business_context": business_context,
                    "error": response["error"],
                    "success": False
                }
                
        except Exception as e:
            return {
                "business_context": business_context,
                "error": str(e),
                "success": False
            }

# Global business analyzer instance
business_analyzer = BusinessAnalyzer()