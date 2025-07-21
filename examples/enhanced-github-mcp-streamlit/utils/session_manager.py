
"""Session management with BMasterAI integration"""
import time
import uuid
import streamlit as st
from typing import Dict, Any, Optional
from utils.bmasterai_logging import get_logger, EventType
from utils.bmasterai_monitoring import get_monitor

class SessionManager:
    """Streamlit session management with BMasterAI logging"""
    
    def __init__(self):
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.agent_id = "streamlit_session"
    
    def initialize_session(self) -> str:
        """Initialize user session with logging"""
        if "session_id" not in st.session_state:
            session_id = f"session_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            st.session_state.session_id = session_id
            st.session_state.session_start_time = time.time()
            st.session_state.analysis_history = []
            st.session_state.current_analysis = None
            st.session_state.monitoring_data = {}
            
            # Log session start
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_START,
                message="New user session started",
                metadata={
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "user_agent": st.context.headers.get("User-Agent", "unknown") if hasattr(st, 'context') else "unknown"
                }
            )
            
            # Track session in monitoring
            self.monitor.track_agent_start(f"session_{session_id}")
        
        return st.session_state.session_id
    
    def track_user_action(self, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track user action with logging"""
        session_id = st.session_state.get("session_id", "unknown")
        
        self.logger.log_user_action(
            user_session=session_id,
            action=action,
            metadata={
                "timestamp": time.time(),
                "session_duration": time.time() - st.session_state.get("session_start_time", time.time()),
                **(metadata or {})
            }
        )
    
    def save_analysis_result(self, repo_url: str, analysis_result: Dict[str, Any], analysis_type: Optional[str] = None) -> None:
        """Save analysis result to session history"""
        if "analysis_history" not in st.session_state:
            st.session_state.analysis_history = []
        
        analysis_entry = {
            "timestamp": time.time(),
            "repo_url": repo_url,
            "result": analysis_result,
            "session_id": st.session_state.get("session_id"),
            "analysis_type": analysis_type or "security_analysis"  # Default to security analysis for backward compatibility
        }
        
        st.session_state.analysis_history.append(analysis_entry)
        st.session_state.current_analysis = analysis_entry
        
        # Keep only last 10 analyses to prevent session bloat
        if len(st.session_state.analysis_history) > 10:
            st.session_state.analysis_history = st.session_state.analysis_history[-10:]
        
        self.track_user_action("analysis_saved", {
            "repo_url": repo_url,
            "analysis_type": analysis_type or "security_analysis",
            "success": analysis_result.get("success", False)
        })
    
    def get_analysis_history(self) -> list:
        """Get user's analysis history"""
        return st.session_state.get("analysis_history", [])
    
    def get_current_analysis(self) -> Optional[Dict[str, Any]]:
        """Get current analysis result"""
        return st.session_state.get("current_analysis")
    
    def clear_session(self) -> None:
        """Clear session data"""
        session_id = st.session_state.get("session_id", "unknown")
        
        # Log session end
        self.logger.log_event(
            agent_id=self.agent_id,
            event_type=EventType.AGENT_STOP,
            message="User session ended",
            metadata={
                "session_id": session_id,
                "session_duration": time.time() - st.session_state.get("session_start_time", time.time()),
                "analyses_performed": len(st.session_state.get("analysis_history", []))
            }
        )
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    def update_monitoring_data(self, data: Dict[str, Any]) -> None:
        """Update monitoring data in session"""
        if "monitoring_data" not in st.session_state:
            st.session_state.monitoring_data = {}
        
        st.session_state.monitoring_data.update(data)
    
    def get_monitoring_data(self) -> Dict[str, Any]:
        """Get monitoring data from session"""
        return st.session_state.get("monitoring_data", {})
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        history = self.get_analysis_history()
        start_time = st.session_state.get("session_start_time", time.time())
        
        return {
            "session_id": st.session_state.get("session_id", "unknown"),
            "duration": time.time() - start_time,
            "analyses_count": len(history),
            "successful_analyses": len([a for a in history if a.get("result", {}).get("success", False)]),
            "last_activity": max([a.get("timestamp", 0) for a in history]) if history else start_time
        }

@st.cache_resource
def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    return SessionManager()
