
"""Streamlit UI components for MCP GitHub Analyzer"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time

def render_header():

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .success-alert {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-alert {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .info-alert {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="main-header">
        <h1>🤖 MCP GitHub Analyzer</h1>
        <p>Automated repository analysis and improvement suggestions powered by BMasterAI</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar with navigation and controls"""
    with st.sidebar:
        st.markdown("### 🎛️ Control Panel")
        
        # Navigation
        page = st.radio(
            "Navigate to:",
            ["🔍 Repository Analysis", "📊 Monitoring Dashboard", "📋 Analysis History", "⚙️ Settings"],
            index=0
        )
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### 📈 Quick Stats")
        
        # Session info
        if "session_id" in st.session_state:
            session_duration = time.time() - st.session_state.get("session_start_time", time.time())
            st.metric("Session Duration", f"{session_duration/60:.1f} min")
            
            analyses_count = len(st.session_state.get("analysis_history", []))
            st.metric("Analyses Performed", analyses_count)
        
        st.markdown("---")
        
        # System status
        st.markdown("### 🔋 System Status")
        render_system_status_mini()
        
        return page

def render_system_status_mini():
    """Render mini system status in sidebar"""
    try:
        from utils.bmasterai_monitoring import get_monitor
        monitor = get_monitor()
        health = monitor.get_system_health()
        
        if health.get("status") != "no_data":
            # CPU indicator
            cpu = health.get("system_metrics", {}).get("cpu", {}).get("current", 0)
            cpu_color = "🟢" if cpu < 70 else "🟡" if cpu < 85 else "🔴"
            st.write(f"{cpu_color} CPU: {cpu:.1f}%")
            
            # Memory indicator
            memory = health.get("system_metrics", {}).get("memory", {}).get("current", 0)
            memory_color = "🟢" if memory < 80 else "🟡" if memory < 90 else "🔴"
            st.write(f"{memory_color} Memory: {memory:.1f}%")
            
            # Active agents
            active_agents = health.get("active_agents", 0)
            st.write(f"🤖 Active Agents: {active_agents}")
        else:
            st.write("📊 Monitoring starting...")
    except Exception as e:
        st.write("⚠️ Monitoring unavailable")

def render_mode_selector():
    """Render mode selector for different operation modes"""
    st.markdown("## 🎯 Operation Mode")
    
    mode = st.radio(
        "Select operation mode:",
        ["🔍 Security Analysis", "🚀 Feature Addition"],
        index=0,
        horizontal=True,
        help="Choose between security analysis or feature implementation mode"
    )
    
    return mode

def render_feature_addition_form():
    """Render feature addition input form"""
    st.markdown("## 🚀 Feature Addition")
    
    with st.form("feature_addition_form"):
        # Repository URL
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/owner/repository",
            help="Enter the full GitHub repository URL"
        )
        
        # Feature prompt
        feature_prompt = st.text_area(
            "Feature Description",
            placeholder="Describe the feature you want to add (e.g., 'Add a login system with JWT authentication', 'Fix the bug in user profile update', 'Add dark mode toggle')",
            height=100,
            help="Describe what you want to implement in natural language"
        )
        
        # Branch configuration
        col1, col2 = st.columns(2)
        
        with col1:
            base_branch = st.text_input(
                "Base Branch",
                value="main",
                help="Branch to create the feature branch from"
            )
        
        with col2:
            feature_branch = st.text_input(
                "Feature Branch Name (optional)",
                placeholder="Auto-generated if empty",
                help="Name for the new feature branch. Leave empty for auto-generation"
            )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col3, col4 = st.columns(2)
            
            with col3:
                auto_pr = st.checkbox(
                    "Create Pull Request",
                    value=True,
                    help="Automatically create a pull request after implementing the feature"
                )
                
                include_tests = st.checkbox(
                    "Include Test Suggestions",
                    value=True,
                    help="Include testing recommendations in the implementation"
                )
            
            with col4:
                complexity_limit = st.selectbox(
                    "Complexity Limit",
                    ["low", "medium", "high"],
                    index=1,
                    help="Maximum complexity level for automatic implementation"
                )
                
                review_mode = st.checkbox(
                    "Review Mode",
                    value=False,
                    help="Generate implementation plan without making changes"
                )
        
        submitted = st.form_submit_button("🚀 Implement Feature", type="primary")
        
        if submitted:
            if not repo_url:
                st.error("Please enter a repository URL")
                return None
            
            if not repo_url.startswith("https://github.com/"):
                st.error("Please enter a valid GitHub repository URL")
                return None
            
            if not feature_prompt.strip():
                st.error("Please describe the feature you want to implement")
                return None
            
            return {
                "repo_url": repo_url,
                "feature_prompt": feature_prompt.strip(),
                "base_branch": base_branch,
                "feature_branch": feature_branch.strip() if feature_branch.strip() else None,
                "auto_pr": auto_pr,
                "include_tests": include_tests,
                "complexity_limit": complexity_limit,
                "review_mode": review_mode
            }
    
    return None

def render_repository_input():
    """Render repository URL input form"""
    st.markdown("## 🔗 Security Analysis")
    
    with st.form("repo_analysis_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            repo_url = st.text_input(
                "GitHub Repository URL",
                placeholder="https://github.com/owner/repository",
                help="Enter the full GitHub repository URL"
            )
        
        with col2:
            analysis_type = st.selectbox(
                "Analysis Type",
                ["comprehensive", "quick", "security-focused"],
                help="Choose the type of analysis to perform"
            )
        
        # Advanced options in expander
        with st.expander("🔧 Advanced Options"):
            col3, col4 = st.columns(2)
            
            with col3:
                create_pr = st.checkbox(
                    "Create Improvement PR",
                    value=True,
                    help="Automatically create a pull request with improvements"
                )
                
                include_security = st.checkbox(
                    "Include Security Analysis",
                    value=True,
                    help="Perform security vulnerability scanning"
                )
            
            with col4:
                max_suggestions = st.slider(
                    "Max Suggestions",
                    min_value=3,
                    max_value=10,
                    value=5,
                    help="Maximum number of improvement suggestions"
                )
                
                priority_filter = st.multiselect(
                    "Priority Filter",
                    ["High", "Medium", "Low"],
                    default=["High", "Medium"],
                    help="Filter suggestions by priority"
                )
        
        submitted = st.form_submit_button("🚀 Analyze Repository", type="primary")
        
        if submitted:
            if not repo_url:
                st.error("Please enter a repository URL")
                return None
            
            if not repo_url.startswith("https://github.com/"):
                st.error("Please enter a valid GitHub repository URL")
                return None
            
            return {
                "repo_url": repo_url,
                "analysis_type": analysis_type,
                "create_pr": create_pr,
                "include_security": include_security,
                "max_suggestions": max_suggestions,
                "priority_filter": priority_filter
            }
    
    return None

def render_analysis_progress(task_name: str = "Repository Analysis"):
    """Render analysis progress indicator"""
    progress_container = st.container()
    
    with progress_container:
        st.markdown(f"### 🔄 {task_name} in Progress")
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Progress steps
        steps = [
            "🔍 Fetching repository information",
            "📊 Analyzing code structure", 
            "🔒 Performing security analysis",
            "🤖 Generating improvement suggestions",
            "📝 Creating pull request (if enabled)"
        ]
        
        # Simulate progress updates
        for i, step in enumerate(steps):
            progress = (i + 1) / len(steps)
            progress_bar.progress(progress)
            status_text.text(step)
            time.sleep(0.5)  # Simulate processing time
        
        progress_bar.progress(1.0)
        status_text.text("✅ Analysis complete!")
    
    return progress_container

def render_analysis_results(analysis_result: Dict[str, Any]):
    """Render analysis results in a comprehensive dashboard"""
    if not analysis_result.get("success"):
        st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
        return
    
    result = analysis_result["result"]
    
    # Overview section
    st.markdown("## 📊 Analysis Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        quality_score = result.get("code_analysis", {}).get("quality_score", 0)
        st.metric(
            "Code Quality Score",
            f"{quality_score}/100",
            delta=None,
            help="Overall code quality assessment"
        )
    
    with col2:
        security_score = result.get("security_analysis", {}).get("score", 0)
        st.metric(
            "Security Score", 
            f"{security_score}/100",
            delta=None,
            help="Security posture assessment"
        )
    
    with col3:
        suggestions_count = len(result.get("improvement_suggestions", {}).get("suggestions", []))
        st.metric(
            "Suggestions",
            suggestions_count,
            delta=None,
            help="Number of improvement suggestions"
        )
    
    with col4:
        duration_ms = result.get("duration_ms", 0)
        st.metric(
            "Analysis Time",
            f"{duration_ms/1000:.1f}s",
            delta=None,
            help="Time taken for analysis"
        )
    
    # Repository information
    st.markdown("## 📋 Repository Information")
    render_repository_info(result.get("repository_info", {}))
    
    # Code analysis
    st.markdown("## 💻 Code Analysis")
    render_code_analysis(result.get("code_analysis", {}))
    
    # Security analysis
    st.markdown("## 🔒 Security Analysis")
    render_security_analysis(result.get("security_analysis", {}))
    
    # Improvement suggestions
    st.markdown("## 💡 Improvement Suggestions")
    render_suggestions(result.get("improvement_suggestions", {}))
    
    # Summary
    st.markdown("## 📝 Summary")
    render_analysis_summary(result.get("summary", {}))

def render_repository_info(repo_info: Dict[str, Any]):
    """Render repository information section"""
    basic_info = repo_info.get("basic_info", {})
    stats = repo_info.get("stats", {})
    languages = repo_info.get("languages", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Basic Information")
        info_data = {
            "Name": basic_info.get("name", "N/A"),
            "Description": basic_info.get("description", "No description") or "No description",
            "Owner": basic_info.get("owner", {}).get("login", "N/A"),
            "Default Branch": stats.get("default_branch", "main"),
            "Created": stats.get("created_at", "N/A")[:10] if stats.get("created_at") else "N/A",
            "Last Updated": stats.get("updated_at", "N/A")[:10] if stats.get("updated_at") else "N/A"
        }
        
        for key, value in info_data.items():
            st.write(f"**{key}:** {value}")
    
    with col2:
        st.markdown("### Repository Statistics")
        stats_data = {
            "Stars": stats.get("stars", 0),
            "Forks": stats.get("forks", 0),
            "Open Issues": stats.get("open_issues", 0),
            "Size (KB)": stats.get("size", 0)
        }
        
        for key, value in stats_data.items():
            st.write(f"**{key}:** {value:,}")
    
    # Languages chart
    if languages:
        st.markdown("### Programming Languages")
        
        # Create language distribution chart
        lang_df = pd.DataFrame([
            {"Language": lang, "Bytes": bytes_count}
            for lang, bytes_count in languages.items()
        ])
        
        fig = px.pie(
            lang_df,
            values="Bytes",
            names="Language",
            title="Language Distribution"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def render_code_analysis(code_analysis: Dict[str, Any]):
    """Render code analysis section"""
    file_structure = code_analysis.get("file_structure", {})
    quality_score = code_analysis.get("quality_score", 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### File Structure")
        structure_data = {
            "Total Files": file_structure.get("total_files", 0),
            "Code Files": file_structure.get("code_files", 0),
            "Documentation Files": file_structure.get("documentation_files", 0),
            "Configuration Files": file_structure.get("config_files", 0),
            "Test Files": file_structure.get("test_files", 0),
            "Directories": file_structure.get("directories", 0)
        }
        
        for key, value in structure_data.items():
            st.write(f"**{key}:** {value}")
    
    with col2:
        st.markdown("### Quality Metrics")
        
        # Quality score gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=quality_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Quality Score"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    # Important files status
    key_files = code_analysis.get("key_files", {})
    if key_files:
        st.markdown("### Important Files")
        
        files_status = []
        for file_name, file_info in key_files.items():
            status = "✅ Present" if file_info.get("exists", False) else "❌ Missing"
            files_status.append({"File": file_name, "Status": status})
        
        files_df = pd.DataFrame(files_status)
        st.dataframe(files_df, use_container_width=True)

def render_security_analysis(security_analysis: Dict[str, Any]):
    """Render security analysis section"""
    security_score = security_analysis.get("score", 100)
    issues = security_analysis.get("issues", [])
    recommendations = security_analysis.get("recommendations", [])
    
    # Security score
    col1, col2 = st.columns(2)
    
    with col1:
        # Security score gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=security_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Security Score"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "green" if security_score >= 80 else "orange" if security_score >= 60 else "red"},
                'steps': [
                    {'range': [0, 60], 'color': "lightgray"},
                    {'range': [60, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Security Summary")
        st.write(f"**Overall Score:** {security_score}/100")
        st.write(f"**Issues Found:** {len(issues)}")
        st.write(f"**Recommendations:** {len(recommendations)}")
        
        # Security level
        if security_score >= 90:
            st.success("🔒 Excellent security posture")
        elif security_score >= 70:
            st.warning("⚠️ Good security with minor issues")
        else:
            st.error("🚨 Security needs attention")
    
    # Security issues
    if issues:
        st.markdown("### 🚨 Security Issues")
        for issue in issues:
            severity = issue.get("severity", "medium")
            severity_color = {
                "high": "🔴",
                "medium": "🟡", 
                "low": "🟢"
            }.get(severity, "🟡")
            
            with st.expander(f"{severity_color} {issue.get('description', 'Security issue')}"):
                st.write(f"**Type:** {issue.get('type', 'Unknown')}")
                st.write(f"**Severity:** {severity.title()}")
                if issue.get("file"):
                    st.write(f"**File:** {issue['file']}")
                st.write(f"**Description:** {issue.get('description', 'No description')}")
    
    # Recommendations
    if recommendations:
        st.markdown("### 💡 Security Recommendations")
        for rec in recommendations:
            st.info(f"**{rec.get('type', 'Recommendation').replace('_', ' ').title()}:** {rec.get('description', 'No description')}")

def render_suggestions(suggestions_data: Dict[str, Any]):
    """Render improvement suggestions section"""
    suggestions = suggestions_data.get("suggestions", [])
    
    if not suggestions:
        st.info("No improvement suggestions generated.")
        return
    
    # Group suggestions by priority
    high_priority = [s for s in suggestions if s.get("priority") == "High"]
    medium_priority = [s for s in suggestions if s.get("priority") == "Medium"]
    low_priority = [s for s in suggestions if s.get("priority") == "Low"]
    
    # Priority summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔴 High Priority", len(high_priority))
    with col2:
        st.metric("🟡 Medium Priority", len(medium_priority))
    with col3:
        st.metric("🟢 Low Priority", len(low_priority))
    
    # Render suggestions by priority
    for priority, priority_suggestions in [
        ("High", high_priority),
        ("Medium", medium_priority), 
        ("Low", low_priority)
    ]:
        if priority_suggestions:
            st.markdown(f"### {priority} Priority Suggestions")
            
            for i, suggestion in enumerate(priority_suggestions):
                priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[priority]
                
                with st.expander(f"{priority_color} {suggestion.get('title', f'Suggestion {i+1}')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Description:** {suggestion.get('description', 'No description')}")
                        st.write(f"**Category:** {suggestion.get('category', 'General').title()}")
                        st.write(f"**Estimated Time:** {suggestion.get('estimated_time', 'Unknown')}")
                    
                    with col2:
                        st.write(f"**Expected Impact:** {suggestion.get('expected_impact', 'Not specified')}")
                        
                        # Implementation steps
                        steps = suggestion.get("implementation_steps", [])
                        if steps:
                            st.write("**Implementation Steps:**")
                            for step in steps:
                                st.write(f"• {step}")
                        
                        # Files to modify
                        files = suggestion.get("files_to_modify", [])
                        if files:
                            st.write("**Files to Modify:**")
                            for file in files:
                                st.code(file)

def render_analysis_summary(summary: Dict[str, Any]):
    """Render analysis summary section"""
    overall_score = summary.get("overall_score", 0)
    strengths = summary.get("strengths", [])
    improvements = summary.get("areas_for_improvement", [])
    priority_actions = summary.get("priority_actions", [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Overall Assessment")
        
        # Overall score with color coding
        if overall_score >= 80:
            st.success(f"**Overall Score: {overall_score:.1f}/100** - Excellent!")
        elif overall_score >= 60:
            st.warning(f"**Overall Score: {overall_score:.1f}/100** - Good")
        else:
            st.error(f"**Overall Score: {overall_score:.1f}/100** - Needs Improvement")
        
        # Strengths
        if strengths:
            st.markdown("**✅ Strengths:**")
            for strength in strengths:
                st.write(f"• {strength}")
        
        # Areas for improvement
        if improvements:
            st.markdown("**🔧 Areas for Improvement:**")
            for improvement in improvements:
                st.write(f"• {improvement}")
    
    with col2:
        st.markdown("### 🚀 Priority Actions")
        
        if priority_actions:
            for i, action in enumerate(priority_actions[:3], 1):
                st.markdown(f"**{i}. {action.get('title', 'Action')}**")
                st.write(f"   {action.get('description', 'No description')}")
                st.write(f"   📅 Estimated time: {action.get('estimated_time', 'Unknown')}")
                st.write("")
        else:
            st.info("No high-priority actions identified.")

def render_monitoring_dashboard():
    """Render monitoring dashboard"""
    st.markdown("## 📊 System Monitoring Dashboard")
    
    try:
        from utils.bmasterai_monitoring import get_monitor
        monitor = get_monitor()
        health = monitor.get_system_health()
        
        if health.get("status") == "no_data":
            st.info("Monitoring data is being collected. Please wait a moment and refresh.")
            return
        
        # System metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu = health.get("system_metrics", {}).get("cpu", {}).get("current", 0)
            st.metric("CPU Usage", f"{cpu:.1f}%", delta=None)
        
        with col2:
            memory = health.get("system_metrics", {}).get("memory", {}).get("current", 0)
            st.metric("Memory Usage", f"{memory:.1f}%", delta=None)
        
        with col3:
            active_agents = health.get("active_agents", 0)
            st.metric("Active Agents", active_agents, delta=None)
        
        with col4:
            total_tasks = health.get("total_tasks_completed", 0)
            st.metric("Tasks Completed", total_tasks, delta=None)
        
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU/Memory chart
            system_history = monitor.metrics_collector.get_metrics_history("system", hours=1)
            if system_history:
                df = pd.DataFrame(system_history)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['cpu_percent'],
                    mode='lines',
                    name='CPU %',
                    line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['memory_percent'],
                    mode='lines',
                    name='Memory %',
                    line=dict(color='red')
                ))
                
                fig.update_layout(
                    title="System Performance (Last Hour)",
                    xaxis_title="Time",
                    yaxis_title="Usage %",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Error rate and task metrics
            error_rate = health.get("error_rate", 0)
            avg_duration = health.get("average_task_duration", 0)
            
            fig = go.Figure()
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=error_rate,
                title={'text': "Error Rate %"},
                gauge={
                    'axis': {'range': [None, 10]},
                    'bar': {'color': "red" if error_rate > 5 else "orange" if error_rate > 2 else "green"},
                    'steps': [
                        {'range': [0, 2], 'color': "lightgray"},
                        {'range': [2, 5], 'color': "gray"}
                    ]
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Active alerts
        active_alerts = health.get("active_alerts", [])
        if active_alerts:
            st.markdown("### 🚨 Active Alerts")
            for alert in active_alerts:
                severity = "error" if alert.get("metric_name") in ["cpu_percent", "memory_percent"] else "warning"
                if severity == "error":
                    st.error(f"**{alert.get('metric_name')}**: {alert.get('message')}")
                else:
                    st.warning(f"**{alert.get('metric_name')}**: {alert.get('message')}")
        
        # Agent status
        st.markdown("### 🤖 Agent Status")
        
        agents_data = []
        for agent_id in ["github_analyzer", "pr_creator", "llm_client"]:
            agent_metrics = monitor.get_agent_dashboard(agent_id)
            if agent_metrics.get("status") != "not_found":
                agents_data.append({
                    "Agent": agent_id.replace("_", " ").title(),
                    "Tasks Completed": agent_metrics.get("tasks_completed", 0),
                    "Tasks Failed": agent_metrics.get("tasks_failed", 0),
                    "Avg Duration (ms)": f"{agent_metrics.get('average_task_duration', 0):.1f}",
                    "Error Rate %": f"{agent_metrics.get('error_rate', 0):.1f}",
                    "Last Activity": agent_metrics.get("last_activity", "Never")[:19] if agent_metrics.get("last_activity") != "Never" else "Never"
                })
        
        if agents_data:
            agents_df = pd.DataFrame(agents_data)
            st.dataframe(agents_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load monitoring data: {str(e)}")

def render_analysis_history():
    """Render analysis history"""
    st.markdown("## 📋 Analysis History")
    
    from utils.session_manager import get_session_manager
    session_manager = get_session_manager()
    history = session_manager.get_analysis_history()
    
    if not history:
        st.info("No analysis history available. Perform some repository analyses to see them here.")
        return
    
    # Summary stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Analyses", len(history))
    
    with col2:
        successful = len([h for h in history if h.get("result", {}).get("success", False)])
        st.metric("Successful", successful)
    
    with col3:
        if history:
            latest = max(h.get("timestamp", 0) for h in history)
            latest_time = datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M")
            st.metric("Latest Analysis", latest_time)
    
    # History table
    st.markdown("### Analysis Records")
    
    history_data = []
    for entry in sorted(history, key=lambda x: x.get("timestamp", 0), reverse=True):
        result = entry.get("result", {})
        repo_url = entry.get("repo_url", "Unknown")
        repo_name = repo_url.split("/")[-1] if "/" in repo_url else repo_url
        
        timestamp = datetime.fromtimestamp(entry.get("timestamp", 0))
        
        history_data.append({
            "Repository": repo_name,
            "URL": repo_url,
            "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Success": "✅" if result.get("success", False) else "❌",
            "Quality Score": result.get("result", {}).get("code_analysis", {}).get("quality_score", "N/A"),
            "Security Score": result.get("result", {}).get("security_analysis", {}).get("score", "N/A"),
            "Suggestions": len(result.get("result", {}).get("improvement_suggestions", {}).get("suggestions", []))
        })
    
    if history_data:
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, use_container_width=True)
        
        # Detailed view
        selected_repo = st.selectbox(
            "View detailed results for:",
            options=range(len(history)),
            format_func=lambda x: f"{history_data[x]['Repository']} - {history_data[x]['Timestamp']}"
        )
        
        if st.button("Show Detailed Results"):
            selected_entry = history[-(selected_repo + 1)]  # Reverse order
            if selected_entry.get("result", {}).get("success", False):
                st.markdown("---")
                render_analysis_results(selected_entry["result"])

def render_settings():
    """Render settings page"""
    st.markdown("## ⚙️ Settings")
    
    # System settings
    st.markdown("### 🔧 System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Monitoring Settings")
        
        monitoring_enabled = st.checkbox("Enable System Monitoring", value=True)
        collection_interval = st.slider("Collection Interval (seconds)", 10, 300, 30)
        
        st.markdown("#### Analysis Settings")
        default_analysis_type = st.selectbox(
            "Default Analysis Type",
            ["comprehensive", "quick", "security-focused"],
            index=0
        )
        
        auto_create_pr = st.checkbox("Auto-create PRs by default", value=True)
    
    with col2:
        st.markdown("#### Display Settings")
        
        show_debug_info = st.checkbox("Show Debug Information", value=False)
        compact_view = st.checkbox("Compact View Mode", value=False)
        
        st.markdown("#### Session Settings")
        max_history = st.slider("Max History Entries", 5, 50, 10)
        
        if st.button("Clear Session Data"):
            from utils.session_manager import get_session_manager
            session_manager = get_session_manager()
            session_manager.clear_session()
            st.success("Session data cleared!")
            st.experimental_rerun()
    
    # API settings
    st.markdown("### 🔑 API Configuration")
    
    # GitHub token status
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        st.success("✅ GitHub token is configured")
    else:
        st.warning("⚠️ GitHub token not found. Some features may be limited.")
    
    # LLM API status
    llm_api_key = os.getenv('ANTHROPIC_API_KEY')
    if llm_api_key:
        st.success("✅ Anthropic API key is configured")
    else:
        st.error("❌ Anthropic API key not found. Analysis will not work.")
    
    # Save settings
    if st.button("Save Settings", type="primary"):
        # Save settings to session state or config file
        st.session_state.update({
            "monitoring_enabled": monitoring_enabled,
            "collection_interval": collection_interval,
            "default_analysis_type": default_analysis_type,
            "auto_create_pr": auto_create_pr,
            "show_debug_info": show_debug_info,
            "compact_view": compact_view,
            "max_history": max_history
        })
        st.success("Settings saved successfully!")

def show_alert(message: str, alert_type: str = "info"):
    """Show styled alert message"""
    alert_class = f"{alert_type}-alert"
    st.markdown(f'<div class="{alert_class}">{message}</div>', unsafe_allow_html=True)

def render_feature_implementation_results(feature_result: Dict[str, Any]):
    """Render feature implementation results"""
    if not feature_result.get("success"):
        st.error(f"Feature implementation failed: {feature_result.get('error', 'Unknown error')}")
        return
    
    st.markdown("## 🚀 Feature Implementation Results")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "✅ Success" if feature_result.get("success") else "❌ Failed"
        st.metric("Implementation Status", status)
    
    with col2:
        branch_status = "✅ Created" if feature_result.get("branch_created") else "❌ Failed"
        st.metric("Feature Branch", branch_status)
    
    with col3:
        files_count = len(feature_result.get("files_modified", []))
        st.metric("Files Modified", files_count)
    
    with col4:
        pr_status = "✅ Created" if feature_result.get("pr_created") else "❌ Not Created"
        st.metric("Pull Request", pr_status)
    
    # Feature plan summary
    feature_plan = feature_result.get("feature_plan", {})
    if feature_plan:
        st.markdown("### 📋 Implementation Plan")
        
        feature_analysis = feature_plan.get("feature_analysis", {})
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Feature Summary:**")
            st.write(feature_analysis.get("summary", "No summary available"))
            
            complexity = feature_analysis.get("complexity", "unknown")
            complexity_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(complexity, "⚪")
            st.write(f"**Complexity:** {complexity_color} {complexity.title()}")
        
        with col2:
            requirements = feature_analysis.get("requirements", [])
            if requirements:
                st.markdown("**Requirements Addressed:**")
                for req in requirements:
                    st.write(f"• {req}")
    
    # Files modified
    files_modified = feature_result.get("files_modified", [])
    if files_modified:
        st.markdown("### 📁 Files Modified")
        
        code_changes = feature_result.get("code_changes", [])
        
        for file_path in files_modified:
            # Find corresponding code change
            file_change = next((c for c in code_changes if c.get("file_path") == file_path), None)
            
            with st.expander(f"📝 {file_path}"):
                if file_change:
                    st.write(f"**Action:** {file_change.get('action', 'modify').title()}")
                    st.write(f"**Purpose:** {file_change.get('purpose', 'No description')}")
                    
                    # Show code preview
                    new_content = file_change.get("new_content", "")
                    if new_content:
                        st.markdown("**Code Preview:**")
                        # Show first 20 lines
                        preview_lines = new_content.split('\n')[:20]
                        preview = '\n'.join(preview_lines)
                        if len(preview_lines) == 20:
                            preview += "\n... (truncated)"
                        st.code(preview, language="python" if file_path.endswith('.py') else None)
                else:
                    st.write("File was modified as part of the feature implementation.")
    
    # Pull request information
    if feature_result.get("pr_created"):
        st.markdown("### 🔧 Pull Request")
        
        pr_url = feature_result.get("pr_url")
        feature_branch = feature_result.get("feature_branch", "feature branch")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Branch:** {feature_branch}")
            if pr_url:
                st.markdown(f"[🔗 View Pull Request]({pr_url})")
        
        with col2:
            st.write("**Status:** Ready for review")
            st.write("**Next Step:** Review and merge the PR")
    
    # Implementation strategy
    implementation_strategy = feature_plan.get("implementation_strategy", {})
    if implementation_strategy:
        st.markdown("### 🎯 Implementation Strategy")
        
        approach = implementation_strategy.get("approach", "")
        if approach:
            st.write(f"**Approach:** {approach}")
        
        integration_points = implementation_strategy.get("integration_points", [])
        if integration_points:
            st.markdown("**Integration Points:**")
            for point in integration_points:
                st.write(f"• {point}")
    
    # Dependencies
    dependencies = feature_plan.get("dependencies", [])
    if dependencies:
        st.markdown("### 📦 New Dependencies")
        
        for dep in dependencies:
            with st.expander(f"📦 {dep.get('name', 'Unknown')}"):
                st.write(f"**Version:** {dep.get('version', 'latest')}")
                st.write(f"**Purpose:** {dep.get('purpose', 'No description')}")
    
    # Testing strategy
    testing_strategy = feature_plan.get("testing_strategy", {})
    if testing_strategy:
        st.markdown("### 🧪 Testing Recommendations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            unit_tests = testing_strategy.get("unit_tests", [])
            if unit_tests:
                st.markdown("**Unit Tests:**")
                for test in unit_tests:
                    st.write(f"• {test}")
        
        with col2:
            manual_testing = testing_strategy.get("manual_testing", [])
            if manual_testing:
                st.markdown("**Manual Testing:**")
                for test in manual_testing:
                    st.write(f"• {test}")
    
    # Potential issues
    potential_issues = feature_plan.get("potential_issues", [])
    if potential_issues:
        st.markdown("### ⚠️ Potential Issues & Mitigations")
        
        for issue in potential_issues:
            with st.expander(f"⚠️ {issue.get('issue', 'Issue')}"):
                st.write(f"**Mitigation:** {issue.get('mitigation', 'No mitigation provided')}")
    
    # Success message
    if feature_result.get("pr_created"):
        st.success("🎉 Feature implemented successfully! Pull request created and ready for review.")
    elif feature_result.get("branch_created"):
        st.success("🎉 Feature implemented successfully! Feature branch created with changes.")
    else:
        st.info("Feature implementation completed. Check the repository for changes.")

def render_pr_results(pr_result: Dict[str, Any]):
    """Render pull request creation results"""
    if not pr_result.get("success"):
        st.error(f"PR creation failed: {pr_result.get('error', 'Unknown error')}")
        return
    
    result = pr_result["result"]
    pr_info = result.get("pr_result", {}).get("pull_request", {})
    
    st.markdown("## 🔧 Pull Request Created")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### PR Information")
        st.write(f"**PR Number:** #{pr_info.get('number', 'N/A')}")
        st.write(f"**Title:** {pr_info.get('title', 'N/A')}")
        st.write(f"**Branch:** {result.get('branch_name', 'N/A')}")
        st.write(f"**Status:** {pr_info.get('status', 'N/A').title()}")
        
        if pr_info.get('url'):
            st.markdown(f"[🔗 View Pull Request]({pr_info['url']})")
    
    with col2:
        st.markdown("### Summary")
        summary = result.get("summary", {})
        st.write(f"**Changes Made:** {summary.get('changes_count', 0)}")
        st.write(f"**Suggestions Implemented:** {summary.get('suggestions_count', 0)}")
        st.write(f"**Estimated Impact:** {summary.get('estimated_impact', 'Not specified')}")
    
    # File changes
    file_changes = result.get("file_changes", [])
    if file_changes:
        st.markdown("### 📁 File Changes")
        
        for change in file_changes:
            with st.expander(f"{change.get('action', 'modify').title()}: {change.get('file_path', 'Unknown file')}"):
                st.write(f"**Description:** {change.get('description', 'No description')}")
                if change.get('content'):
                    st.code(change['content'][:500] + "..." if len(change['content']) > 500 else change['content'])
    
    st.success("🎉 Pull request created successfully! Check your repository for the new PR.")
