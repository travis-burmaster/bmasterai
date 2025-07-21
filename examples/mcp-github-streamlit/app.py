"""Main Streamlit application for MCP GitHub Analyzer"""
import streamlit as st
import asyncio
import os
import time
import json
from typing import Dict, Any, Optional

# Fix for JSON parsing error in Streamlit metrics
def fix_streamlit_config():
    """Fix Streamlit configuration issues"""
    try:
        # Disable metrics collection to prevent JSON parsing errors
        os.environ['STREAMLIT_SERVER_ENABLE_STATIC_SERVING'] = 'false'
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false' 
        os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
        os.environ['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
        
        # Alternative: Configure Streamlit to not use metrics (if config is available)
        try:
            if hasattr(st, '_config'):
                st._config.set_option('browser.gatherUsageStats', False)
                st._config.set_option('server.enableCORS', False)
                st._config.set_option('server.enableXsrfProtection', False)
        except Exception:
            pass  # Ignore if config is not accessible
            
    except Exception as e:
        # If we can't set configs, continue anyway
        pass

# Apply Streamlit fixes before page config
fix_streamlit_config()

# Configure page
st.set_page_config(
    page_title="MCP GitHub Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import components and utilities
from components.ui_components import (
    render_header, render_sidebar, render_repository_input,
    render_analysis_results, render_monitoring_dashboard,
    render_analysis_history, render_settings, render_pr_results
)
from utils.session_manager import get_session_manager
from utils.bmasterai_logging import configure_logging, get_logger, LogLevel
from utils.bmasterai_monitoring import get_monitor
from config import get_config_manager
from agents.coordinator import get_workflow_coordinator

def safe_session_init():
    """Safely initialize session state with error handling"""
    try:
        # Clear potentially corrupted session state
        if 'initialized' not in st.session_state:
            # Clear all existing session state to prevent corruption
            for key in list(st.session_state.keys()):
                try:
                    del st.session_state[key]
                except Exception:
                    pass
            
            # Initialize fresh session state
            st.session_state.initialized = True
            st.session_state.analysis_results = {}
            st.session_state.current_analysis = None
            st.session_state.user_actions = []
            
    except Exception as e:
        st.error(f"Session initialization error: {e}")
        # Force clear all session state
        try:
            st.session_state.clear()
        except Exception:
            pass
        st.rerun()

# Initialize application
@st.cache_resource
def initialize_application():
    """Initialize BMasterAI components and logging"""
    try:
        # Load configuration
        config_manager = get_config_manager()
        logging_config = config_manager.get_logging_config()
        monitoring_config = config_manager.get_monitoring_config()
        
        # Configure logging
        logger = configure_logging(
            log_level=LogLevel(logging_config.level),
            enable_console=logging_config.enable_console,
            enable_file=logging_config.enable_file,
            enable_json=logging_config.enable_json,
            log_file=logging_config.log_file,
            json_log_file=logging_config.json_log_file
        )
        
        # Initialize monitoring
        monitor = get_monitor()
        monitor.start_monitoring(monitoring_config.collection_interval)
        
        # Log application start
        logger.log_event(
            agent_id="streamlit_app",
            event_type="agent_start",
            message="MCP GitHub Analyzer application started",
            metadata={
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development")
            }
        )
        
        return logger, monitor, config_manager
        
    except Exception as e:
        st.error(f"Failed to initialize application: {str(e)}")
        st.stop()

# Main application
def main():
    """Main application function with safe session initialization"""
    
    # Safe session initialization
    safe_session_init()
    
    # Initialize application components
    logger, monitor, config_manager = initialize_application()
    
    # Initialize session management with error handling  
    try:
        session_manager = get_session_manager()
        session_id = session_manager.initialize_session()
    except Exception as e:
        st.error(f"Session manager initialization failed: {e}")
        st.info("Please refresh the page to reset the session.")
        st.stop()
    
    # Render header
    render_header()
    
    # Render sidebar and get current page
    current_page = render_sidebar()
    
    # Main content area
    if current_page == "🔍 Repository Analysis":
        render_analysis_page(session_manager, logger)
    elif current_page == "📊 Monitoring Dashboard":
        render_monitoring_dashboard()
    elif current_page == "📋 Analysis History":
        render_analysis_history()
    elif current_page == "⚙️ Settings":
        render_settings()

def render_analysis_page(session_manager, logger):
    """Render the main repository analysis page"""
    
    # Repository input form
    analysis_config = render_repository_input()
    
    if analysis_config:
        # Track user action
        session_manager.track_user_action("analysis_started", {
            "repo_url": analysis_config["repo_url"],
            "analysis_type": analysis_config["analysis_type"],
            "create_pr": analysis_config["create_pr"]
        })
        
        # Execute analysis
        with st.spinner("🔄 Analyzing repository..."):
            analysis_result = run_analysis(analysis_config, logger)
        
        # Save results to session
        if analysis_result:
            session_manager.save_analysis_result(
                analysis_config["repo_url"], 
                analysis_result
            )
            
            # Display results
            if analysis_result.get("success"):
                if "steps" in analysis_result:
                    # Full workflow result
                    render_workflow_results(analysis_result)
                else:
                    # Simple analysis result
                    render_analysis_results(analysis_result)
            else:
                st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
    
    # Show recent analysis if available
    current_analysis = session_manager.get_current_analysis()
    if current_analysis and not analysis_config:
        st.markdown("## 📊 Latest Analysis Results")
        
        if current_analysis["result"].get("success"):
            if "steps" in current_analysis["result"]:
                render_workflow_results(current_analysis["result"])
            else:
                render_analysis_results(current_analysis["result"])

def run_analysis(config: Dict[str, Any], logger) -> Optional[Dict[str, Any]]:
    """Run repository analysis with proper error handling"""
    try:
        # Get workflow coordinator
        coordinator = get_workflow_coordinator()
        
        # Create progress indicators
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🔄 Analysis Progress")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step progress tracking
            steps = [
                "🔍 Initializing analysis",
                "📊 Fetching repository information", 
                "💻 Analyzing code structure",
                "🔒 Performing security analysis",
                "🤖 Generating suggestions",
                "📝 Creating pull request (if enabled)"
            ]
            
            # Update progress for initialization
            progress_bar.progress(0.1)
            status_text.text(steps[0])
        
        # Execute workflow
        async def run_workflow():
            return await coordinator.execute_full_workflow(config)
        
        # Run async workflow
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_workflow())
            loop.close()
        except RuntimeError:
            # If we're already in an event loop, use asyncio.create_task
            result = asyncio.run(run_workflow())
        
        # Update progress through steps
        for i, step in enumerate(steps[1:], 1):
            progress = (i + 1) / len(steps)
            progress_bar.progress(progress)
            status_text.text(step)
            time.sleep(0.3)  # Brief pause for UI feedback
        
        # Complete progress
        progress_bar.progress(1.0)
        if result.get("success"):
            status_text.text("✅ Analysis completed successfully!")
        else:
            status_text.text("❌ Analysis completed with errors")
        
        return result
        
    except Exception as e:
        logger.log_event(
            agent_id="streamlit_app",
            event_type="task_error",
            message=f"Analysis execution failed: {str(e)}",
            level="ERROR",
            metadata={"repo_url": config.get("repo_url"), "error": str(e)}
        )
        
        st.error(f"An error occurred during analysis: {str(e)}")
        return {"success": False, "error": str(e)}

def render_workflow_results(workflow_result: Dict[str, Any]):
    """Render comprehensive workflow results"""
    if not workflow_result.get("success"):
        st.error(f"Workflow failed: {workflow_result.get('error', 'Unknown error')}")
        return
    
    steps = workflow_result.get("steps", {})
    summary = workflow_result.get("summary", {})
    
    # Workflow summary
    st.markdown("## 🎯 Workflow Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "✅ Success" if summary.get("workflow_status") == "completed" else "❌ Failed"
        st.metric("Workflow Status", status)
    
    with col2:
        analysis_status = "✅ Yes" if summary.get("analysis_performed") else "❌ No"
        st.metric("Analysis Completed", analysis_status)
    
    with col3:
        pr_status = "✅ Yes" if summary.get("pr_created") else "❌ No"
        st.metric("PR Created", pr_status)
    
    with col4:
        overall_score = summary.get("metrics", {}).get("overall_score", 0)
        st.metric("Overall Score", f"{overall_score:.1f}/100")
    
    # Display outcomes
    outcomes = summary.get("outcomes", [])
    if outcomes:
        st.markdown("### 📋 Key Outcomes")
        for outcome in outcomes:
            st.write(f"• {outcome}")
    
    # Display recommendations
    recommendations = summary.get("recommendations", [])
    if recommendations:
        st.markdown("### 💡 Recommendations")
        for rec in recommendations:
            st.info(f"💡 {rec}")
    
    # Display next steps
    next_steps = summary.get("next_steps", [])
    if next_steps:
        st.markdown("### 🚀 Next Steps")
        for i, step in enumerate(next_steps, 1):
            st.write(f"{i}. {step}")
    
    # Detailed results in tabs
    if steps.get("analysis", {}).get("success"):
        analysis_tab, pr_tab, suggestions_tab = st.tabs(["📊 Analysis Details", "🔧 Pull Request", "💡 Suggestions"])
        
        with analysis_tab:
            render_analysis_results(steps["analysis"])
        
        with pr_tab:
            if steps.get("pr_creation"):
                render_pr_results(steps["pr_creation"])
            else:
                st.info("Pull request creation was not enabled for this analysis.")
        
        with suggestions_tab:
            processed_suggestions = steps.get("processed_suggestions", {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🤖 Implementable Suggestions")
                implementable = processed_suggestions.get("implementable_suggestions", [])
                if implementable:
                    for suggestion in implementable:
                        with st.expander(f"🔧 {suggestion.get('title', 'Suggestion')}"):
                            st.write(f"**Priority:** {suggestion.get('priority', 'Unknown')}")
                            st.write(f"**Category:** {suggestion.get('category', 'Unknown')}")
                            st.write(f"**Description:** {suggestion.get('description', 'No description')}")
                else:
                    st.info("No automatically implementable suggestions found.")
            
            with col2:
                st.markdown("### 👤 Manual Suggestions")
                manual = processed_suggestions.get("manual_suggestions", [])
                if manual:
                    for suggestion in manual:
                        with st.expander(f"📝 {suggestion.get('title', 'Suggestion')}"):
                            st.write(f"**Priority:** {suggestion.get('priority', 'Unknown')}")
                            st.write(f"**Category:** {suggestion.get('category', 'Unknown')}")
                            st.write(f"**Description:** {suggestion.get('description', 'No description')}")
                            
                            # Implementation steps
                            steps_list = suggestion.get("implementation_steps", [])
                            if steps_list:
                                st.write("**Implementation Steps:**")
                                for step in steps_list:
                                    st.write(f"• {step}")
                else:
                    st.info("No manual suggestions found.")

# Enhanced error handling for the entire app
def run_app():
    """Run the application with enhanced error handling"""
    try:
        main()
        
    except json.JSONDecodeError as e:
        st.error("Browser storage corruption detected. Please clear your browser cache and refresh.")
        st.markdown("""
        ### 🔧 Quick Fix Instructions:
        1. **Clear Browser Storage:**
           - Press F12 to open developer tools
           - Go to Application → Storage
           - Clear Local Storage and Session Storage
           - Refresh the page
        
        2. **Or use Private/Incognito browsing mode**
        
        3. **If the issue persists:**
           - Try a different browser
           - Disable browser extensions
           - Check console for additional errors
        """)
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if it's a Streamlit-specific error
        if "MetricsManager" in error_msg or "JSON" in error_msg:
            st.error("Streamlit configuration error detected.")
            st.info("This is likely due to corrupted browser storage. Please refresh and clear your cache.")
        else:
            st.error(f"Application error: {error_msg}")
        
        # Log error if logger is available
        try:
            logger = get_logger()
            logger.log_event(
                agent_id="streamlit_app",
                event_type="task_error",
                message=f"Application error: {error_msg}",
                level="ERROR",
                metadata={"error": error_msg, "error_type": type(e).__name__}
            )
        except:
            pass  # Logger might not be initialized
        
        # Enhanced troubleshooting
        with st.expander("🔧 Troubleshooting Guide"):
            st.markdown("""
            **For JSON/MetricsManager errors:**
            1. Clear browser cache and local storage
            2. Try incognito/private browsing mode
            3. Disable browser extensions temporarily
            
            **For general application issues:**
            1. Check that all environment variables are set correctly
            2. Ensure the MCP server is running (if using real MCP)
            3. Verify your GitHub token permissions
            4. Check the application logs for more details
            
            **Environment Variables Required:**
            - `GITHUB_TOKEN`: Your GitHub personal access token
            - `ANTHROPIC_API_KEY`: Your Anthropic API key (if using)
            - `MCP_SERVER_HOST`: MCP server host (default: localhost)
            - `MCP_SERVER_PORT`: MCP server port (default: 8080)
            """)
            
        # Add a reset button
        if st.button("🔄 Reset Application State"):
            try:
                st.session_state.clear()
                st.rerun()
            except Exception:
                st.info("Please refresh the page manually to reset the application state.")

if __name__ == "__main__":
    run_app()
