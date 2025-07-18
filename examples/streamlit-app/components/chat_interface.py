"""Chat interface component for the AI consultant."""

import streamlit as st
import time
from typing import Dict, Any, List
from utils.ai_client import ai_client
from utils.business_tools import business_analyzer

class ChatInterface:
    """Chat interface for AI consultant interactions."""
    
    def __init__(self):
        self.ai_client = ai_client
        self.business_analyzer = business_analyzer
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "consultation_context" not in st.session_state:
            st.session_state.consultation_context = {}
        
        if "current_analysis" not in st.session_state:
            st.session_state.current_analysis = None
    
    def display_chat_history(self):
        """Display the chat history."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Display analysis results if available
                if "analysis" in message:
                    self._display_analysis_results(message["analysis"])
    
    def _display_analysis_results(self, analysis: Dict[str, Any]):
        """Display analysis results in the chat."""
        if analysis.get("type") == "market_analysis":
            st.subheader("📊 Market Analysis Results")
            
            # Display AI analysis
            if analysis.get("ai_analysis"):
                st.markdown("### AI Analysis")
                st.markdown(analysis["ai_analysis"])
            
            # Display insights
            if analysis.get("insights"):
                st.markdown("### Key Insights")
                for insight in analysis["insights"]:
                    with st.expander(f"🔍 {insight['category']}", expanded=False):
                        st.write(f"**Finding:** {insight['finding']}")
                        st.write(f"**Confidence:** {insight['confidence']:.1%}")
                        st.write(f"**Source:** {insight['source']}")
                        st.write(f"**Timestamp:** {insight['timestamp']}")
        
        elif analysis.get("type") == "recommendations":
            st.subheader("💡 Strategic Recommendations")
            
            for i, rec in enumerate(analysis.get("recommendations", []), 1):
                with st.expander(f"📋 {rec.get('category', 'Recommendation')} - {rec.get('priority', 'Medium')} Priority", expanded=False):
                    st.write(f"**Recommendation:** {rec.get('recommendation', 'N/A')}")
                    st.write(f"**Rationale:** {rec.get('rationale', 'N/A')}")
                    st.write(f"**Timeline:** {rec.get('timeline', 'N/A')}")
                    
                    if rec.get('success_metrics'):
                        st.write("**Success Metrics:**")
                        for metric in rec['success_metrics']:
                            st.write(f"• {metric}")
                    
                    if rec.get('action_items'):
                        st.write("**Action Items:**")
                        for item in rec['action_items']:
                            st.write(f"• {item}")
        
        elif analysis.get("type") == "competitor_analysis":
            st.subheader("🏢 Competitor Analysis")
            st.markdown(analysis.get("analysis", "No analysis available."))
        
        elif analysis.get("type") == "risk_assessment":
            st.subheader("⚠️ Risk Assessment")
            st.markdown(analysis.get("risk_assessment", "No risk assessment available."))
    
    def handle_user_input(self, user_input: str):
        """Handle user input and generate AI response."""
        # Log user interaction with BMasterAI
        from utils.bmasterai_integration import bmasterai_manager
        bmasterai_manager.log_user_interaction(user_input, {
            "session_id": id(st.session_state),
            "message_count": len(st.session_state.get("messages", [])),
            "has_context": bool(st.session_state.get("consultation_context", {}))
        })
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate AI response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            # Check if user is asking for specific analysis
            analysis_type = self._detect_analysis_type(user_input)
            
            if analysis_type:
                # Show analysis in progress
                with st.spinner(f"Conducting {analysis_type}..."):
                    analysis_result = self._conduct_analysis(user_input, analysis_type)
                
                # Display analysis results
                if analysis_result and analysis_result.get("success"):
                    self._display_analysis_results(analysis_result)
                    
                    # Add to session state
                    st.session_state.current_analysis = analysis_result
                    
                    # Generate AI response based on analysis
                    full_response = self._generate_response_from_analysis(analysis_result, user_input)
                else:
                    full_response = f"I encountered an error while conducting the {analysis_type}. Please try rephrasing your question."
            else:
                # Regular conversation - stream the response
                try:
                    messages = [
                        {"role": "system", "content": self._get_system_prompt()},
                        *[{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages[:-1]],
                        {"role": "user", "content": user_input}
                    ]
                    
                    # Stream the response
                    for chunk in self.ai_client.stream_chat_completion(messages):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)  # Small delay for smooth streaming
                    
                except Exception as e:
                    full_response = f"I apologize, but I encountered an error: {str(e)}"
            
            # Final response display
            response_placeholder.markdown(full_response)
            
            # Add assistant response to chat history
            assistant_message = {"role": "assistant", "content": full_response}
            if analysis_type and st.session_state.current_analysis:
                assistant_message["analysis"] = st.session_state.current_analysis
            
            st.session_state.messages.append(assistant_message)
    
    def _detect_analysis_type(self, user_input: str) -> str:
        """Detect what type of analysis the user is requesting."""
        user_input_lower = user_input.lower()
        
        market_keywords = ["market analysis", "market research", "industry analysis", "market opportunity", "market size"]
        competitor_keywords = ["competitor analysis", "competitive analysis", "competition", "competitors"]
        risk_keywords = ["risk assessment", "risk analysis", "risks", "threats", "challenges"]
        recommendation_keywords = ["recommendations", "advice", "strategy", "what should i do"]
        
        if any(keyword in user_input_lower for keyword in market_keywords):
            return "market_analysis"
        elif any(keyword in user_input_lower for keyword in competitor_keywords):
            return "competitor_analysis"
        elif any(keyword in user_input_lower for keyword in risk_keywords):
            return "risk_assessment"
        elif any(keyword in user_input_lower for keyword in recommendation_keywords):
            return "recommendations"
        
        return None
    
    def _conduct_analysis(self, user_input: str, analysis_type: str) -> Dict[str, Any]:
        """Conduct the requested analysis."""
        try:
            if analysis_type == "market_analysis":
                # Extract industry from user input if possible
                industry = self._extract_industry(user_input)
                result = self.business_analyzer.analyze_market_data(user_input, industry)
                result["type"] = "market_analysis"
                return result
            
            elif analysis_type == "competitor_analysis":
                industry = self._extract_industry(user_input)
                result = self.business_analyzer.conduct_competitor_analysis(industry, user_input)
                result["type"] = "competitor_analysis"
                return result
            
            elif analysis_type == "risk_assessment":
                context = {"query": user_input, "business_context": st.session_state.consultation_context}
                result = self.business_analyzer.assess_business_risks(context)
                result["type"] = "risk_assessment"
                return result
            
            elif analysis_type == "recommendations":
                # Use current analysis or create new one
                if st.session_state.current_analysis:
                    recommendations = self.business_analyzer.generate_strategic_recommendations(st.session_state.current_analysis)
                else:
                    # Create a simple analysis first
                    analysis = self.business_analyzer.analyze_market_data(user_input)
                    recommendations = self.business_analyzer.generate_strategic_recommendations(analysis)
                
                return {
                    "type": "recommendations",
                    "recommendations": recommendations,
                    "success": True
                }
            
        except Exception as e:
            return {
                "type": analysis_type,
                "error": str(e),
                "success": False
            }
    
    def _extract_industry(self, user_input: str) -> str:
        """Extract industry from user input."""
        # Simple keyword extraction - could be enhanced with NLP
        industries = {
            "technology": ["tech", "software", "saas", "ai", "artificial intelligence"],
            "healthcare": ["health", "medical", "pharma", "biotech"],
            "finance": ["fintech", "banking", "financial", "investment"],
            "retail": ["retail", "e-commerce", "shopping", "consumer"],
            "manufacturing": ["manufacturing", "industrial", "production"],
            "education": ["education", "learning", "training", "academic"],
            "real estate": ["real estate", "property", "housing"],
            "food": ["food", "restaurant", "culinary", "dining"]
        }
        
        user_input_lower = user_input.lower()
        
        for industry, keywords in industries.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return industry
        
        return ""
    
    def _generate_response_from_analysis(self, analysis: Dict[str, Any], user_input: str) -> str:
        """Generate a conversational response based on analysis results."""
        analysis_type = analysis.get("type", "")
        
        if analysis_type == "market_analysis":
            return f"I've completed a comprehensive market analysis for your query. The analysis shows several key insights including market opportunities, trends, and recommendations. You can see the detailed results above."
        
        elif analysis_type == "competitor_analysis":
            return f"I've conducted a thorough competitor analysis for your industry. The analysis covers market leaders, emerging players, and strategic recommendations. Please review the detailed findings above."
        
        elif analysis_type == "risk_assessment":
            return f"I've assessed the business risks based on your context. The assessment includes key risk categories, mitigation strategies, and monitoring recommendations. See the detailed analysis above."
        
        elif analysis_type == "recommendations":
            return f"Based on the analysis, I've generated strategic recommendations with specific action items and timelines. These recommendations are prioritized and include success metrics for tracking progress."
        
        return "I've completed the requested analysis. Please review the results above for detailed insights and recommendations."
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI assistant."""
        return """You are an expert AI business consultant with deep knowledge in:
        - Market analysis and business strategy
        - Technology trends and digital transformation
        - Risk assessment and mitigation
        - Strategic planning and implementation
        - Competitive analysis and positioning
        
        Provide helpful, detailed, and actionable advice. Be conversational but professional.
        When users ask for specific analysis (market, competitor, risk, recommendations), 
        let them know that you'll conduct a detailed analysis for them.
        
        Always structure your responses clearly and provide specific, actionable insights.
        """
    
    def render(self):
        """Render the chat interface."""
        self.initialize_session_state()
        
        # Display chat history
        self.display_chat_history()
        
        # Chat input
        if prompt := st.chat_input("Ask me about your business strategy, market analysis, or any business question..."):
            self.handle_user_input(prompt)
    
    def clear_chat(self):
        """Clear the chat history."""
        st.session_state.messages = []
        st.session_state.consultation_context = {}
        st.session_state.current_analysis = None
        st.rerun()

# Global chat interface instance
chat_interface = ChatInterface()