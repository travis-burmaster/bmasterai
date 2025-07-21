
"""Main Streamlit application for MCP GitHub Analyzer"""
import streamlit as st
import asyncio
import os
import time
from typing import Dict, Any, Optional

# Configure page
st.set_page_config(
    page_title="MCP GitHub Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import components and utilities
from components.ui_components import (
    render_header, render_sidebar, render_mode_selector, render_repository_input,
    render_feature_request_form, render_analysis_results, render_monitoring_dashboard,
    render_analysis_history, render_settings, render_pr_results, render_feature_request_results
)
from utils.session_manager import get_session_manager
from utils.bmasterai_logging import configure_logging, get_logger, LogLevel, EventType
from utils.bmasterai_monitoring import get_monitor
from config import get_config_manager
from agents.coordinator import get_workflow_coordinator

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
            log_level=LogLevel.from_string(logging_config.level),
            enable_console=logging_config.enable_console,
            enable_file=logging_config.enable_file,
            enable_json=logging_config.enable_json,
            log_file=logging_config.log_file,
            json_log_file=logging_config.json_log_file
        )
        
        # Initialize monitoring
        monitor = get_monitor()
        monitor.start_monitoring(monitoring_config.collection_interval)
        
        return logger, monitor, config_manager
        
    except Exception as e:
        st.error(f"Failed to initialize application: {str(e)}")
        st.stop()

# Main application
def main():
    """Main application function"""
    
    # Initialize application components
    logger, monitor, config_manager = initialize_application()
    
    # Initialize session management
    session_manager = get_session_manager()
    session_id = session_manager.initialize_session()
    
    # Render header
    render_header()
    
    # Render sidebar and get current page
    current_page = render_sidebar()
    
    # Main content area - UPDATED to handle new page structure
    if current_page == "🔍 Repository Analysis":
        render_analysis_page(session_manager, logger)
    elif current_page == "🚀 Feature Request":
        render_feature_request_page(session_manager, logger)
    elif current_page == "📊 Monitoring Dashboard":
        render_monitoring_dashboard()
    elif current_page == "📋 Analysis History":
        render_analysis_history()
    elif current_page == "⚙️ Settings":
        render_settings()

def render_analysis_page(session_manager, logger):
    """Render the main repository analysis page (security and bugs focus)"""
    
    # Repository analysis form (security and bugs focused)
    analysis_config = render_repository_input()
    
    # Handle security analysis
    if analysis_config:
        # Track user action
        session_manager.track_user_action("analysis_started", {
            "repo_url": analysis_config["repo_url"],
            "analysis_type": analysis_config["analysis_type"],
            "create_pr": analysis_config["create_pr"]
        })
        
        # Execute analysis
        with st.spinner("🔄 Analyzing repository for security issues and bugs..."):
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

def render_feature_request_page(session_manager, logger):
    """Render the feature request page with enhanced functionality"""
    
    try:
        # Feature request form
        feature_config = render_feature_request_form()
        
        # Handle feature implementation
        if feature_config:
            # Track user action
            session_manager.track_user_action("feature_request_started", {
                "repo_url": feature_config["repo_url"],
                "feature_description": feature_config["feature_description"],
                "base_branch": feature_config["base_branch"],
                "create_pr": feature_config["create_pr"]
            })
            
            # Execute feature implementation
            with st.spinner("🚀 Implementing feature request..."):
                feature_result = run_feature_request(feature_config, logger)
            
            # Save results to session
            if feature_result:
                session_manager.save_analysis_result(
                    feature_config["repo_url"], 
                    feature_result,
                    analysis_type="feature_request"
                )
                
                # Display results
                if feature_result.get("success"):
                    render_feature_request_results(feature_result)
                else:
                    st.error(f"Feature request failed: {feature_result.get('error', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"Error in feature request page: {str(e)}")
        logger.log_event(
            agent_id="streamlit_app",
            event_type=EventType.TASK_ERROR,
            message=f"Feature request page error: {str(e)}",
            level=LogLevel.ERROR,
            metadata={"error": str(e)}
        )
        import traceback
        st.code(traceback.format_exc())

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
            event_type=EventType.TASK_ERROR,
            message=f"Analysis execution failed: {str(e)}",
            level=LogLevel.ERROR,
            metadata={"repo_url": config.get("repo_url"), "error": str(e)}
        )
        
        st.error(f"An error occurred during analysis: {str(e)}")
        return {"success": False, "error": str(e)}

def run_feature_request(config: Dict[str, Any], logger) -> Optional[Dict[str, Any]]:
    """Run feature request implementation with proper error handling"""
    try:
        # Get workflow coordinator
        coordinator = get_workflow_coordinator()
        
        # Create progress indicators
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🚀 Feature Implementation Progress")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step progress tracking
            steps = [
                "🔍 Analyzing repository structure",
                "🧠 Generating implementation plan", 
                "💻 Creating code changes",
                "🌿 Creating feature branch",
                "📝 Applying code changes",
                "🔧 Creating pull request (if enabled)"
            ]
            
            # Update progress for initialization
            progress_bar.progress(0.1)
            status_text.text("🔍 Initializing feature implementation")
        
        # Execute feature implementation workflow
        async def run_feature_workflow():
            try:
                return await coordinator.execute_feature_request(config)
            except Exception as e:
                st.error(f"Error in feature workflow: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                return {"success": False, "error": str(e)}
        
        # Run async workflow
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_feature_workflow())
            loop.close()
        except RuntimeError:
            # If we're already in an event loop, use asyncio.create_task
            result = asyncio.run(run_feature_workflow())
        
        # Update progress through steps
        for i, step in enumerate(steps[1:], 1):
            progress = (i + 1) / len(steps)
            progress_bar.progress(progress)
            status_text.text(step)
            time.sleep(0.3)  # Brief pause for UI feedback
        
        # Complete progress
        progress_bar.progress(1.0)
        if result.get("success"):
            status_text.text("✅ Feature implementation completed successfully!")
        else:
            status_text.text("❌ Feature implementation completed with errors")
        
        return result
        
    except Exception as e:
        logger.log_event(
            agent_id="streamlit_app",
            event_type=EventType.TASK_ERROR,
            message=f"Feature request execution failed: {str(e)}",
            level=LogLevel.ERROR,
            metadata={"repo_url": config.get("repo_url"), "error": str(e)}
        )
        
        st.error(f"An error occurred during feature implementation: {str(e)}")
        return {"success": False, "error": str(e)}

def render_feature_workflow_results(workflow_result: Dict[str, Any]):
    """Render comprehensive feature workflow results"""
    if not workflow_result.get("success"):
        st.error(f"Feature workflow failed: {workflow_result.get('error', 'Unknown error')}")
        return
    
    steps = workflow_result.get("steps", {})
    summary = workflow_result.get("summary", {})
    feature_implementation = steps.get("feature_implementation", {})
    
    # Workflow summary
    st.markdown("## 🎯 Feature Implementation Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "✅ Success" if summary.get("workflow_status") == "completed" else "❌ Failed"
        st.metric("Workflow Status", status)
    
    with col2:
        feature_status = "✅ Yes" if summary.get("feature_implemented") else "❌ No"
        st.metric("Feature Implemented", feature_status)
    
    with col3:
        pr_status = "✅ Yes" if summary.get("pr_created") else "❌ No"
        st.metric("PR Created", pr_status)
    
    with col4:
        files_modified = summary.get("metrics", {}).get("files_modified", 0)
        st.metric("Files Modified", files_modified)
    
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
    if feature_implementation.get("success"):
        implementation_tab, plan_tab, testing_tab = st.tabs(["🚀 Implementation Details", "📋 Implementation Plan", "🧪 Testing Strategy"])
        
        with implementation_tab:
            render_feature_request_results(feature_implementation)
        
        with plan_tab:
            feature_plan = feature_implementation.get("feature_plan", {})
            if feature_plan:
                st.markdown("### 📋 Feature Analysis")
                feature_analysis = feature_plan.get("feature_analysis", {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Summary:** {feature_analysis.get('summary', 'No summary')}")
                    st.write(f"**Complexity:** {feature_analysis.get('complexity', 'unknown').title()}")
                
                with col2:
                    requirements = feature_analysis.get("requirements", [])
                    if requirements:
                        st.markdown("**Requirements:**")
                        for req in requirements:
                            st.write(f"• {req}")
                
                st.markdown("### 🎯 Implementation Strategy")
                strategy = feature_plan.get("implementation_strategy", {})
                if strategy.get("approach"):
                    st.write(f"**Approach:** {strategy['approach']}")
                
                integration_points = strategy.get("integration_points", [])
                if integration_points:
                    st.markdown("**Integration Points:**")
                    for point in integration_points:
                        st.write(f"• {point}")
        
        with testing_tab:
            feature_plan = feature_implementation.get("feature_plan", {})
            testing_strategy = feature_plan.get("testing_strategy", {})
            
            if testing_strategy:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🧪 Unit Tests")
                    unit_tests = testing_strategy.get("unit_tests", [])
                    if unit_tests:
                        for test in unit_tests:
                            st.write(f"• {test}")
                    else:
                        st.info("No unit tests suggested")
                
                with col2:
                    st.markdown("### 🔍 Manual Testing")
                    manual_tests = testing_strategy.get("manual_testing", [])
                    if manual_tests:
                        for test in manual_tests:
                            st.write(f"• {test}")
                    else:
                        st.info("No manual tests suggested")
                
                integration_tests = testing_strategy.get("integration_tests", [])
                if integration_tests:
                    st.markdown("### 🔗 Integration Tests")
                    for test in integration_tests:
                        st.write(f"• {test}")
            else:
                st.info("No testing strategy provided")

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

# Error handling for the entire app
def run_app():
    """Run the application with error handling"""
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        
        # Log error if logger is available
        try:
            logger = get_logger()
            logger.log_event(
                agent_id="streamlit_app",
                event_type=EventType.TASK_ERROR,
                message=f"Application error: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"error": str(e)}
            )
        except:
            pass  # Logger might not be initialized
        
        st.markdown("### 🔧 Troubleshooting")
        st.markdown("""
        If you're experiencing issues:
        1. Check that all environment variables are set correctly
        2. Ensure the MCP server is running (if using real MCP)
        3. Verify your GitHub token permissions
        4. Check the application logs for more details
        """)

if __name__ == "__main__":
    run_app()
