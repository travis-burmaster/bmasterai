
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
        
        # Navigation - UPDATED ORDER: Repository Analysis, Feature Request, Monitoring Dashboard, Analysis History, Settings
        page = st.radio(
            "Navigate to:",
            ["🔍 Repository Analysis", "🚀 Feature Request", "📊 Monitoring Dashboard", "📋 Analysis History", "⚙️ Settings"],
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

def render_feature_request_form():
    """Render enhanced feature request input form with branch creation and code generation"""
    st.markdown("## 🚀 Feature Request")
    st.markdown("Generate and implement new features or fixes with automatic branch creation and code generation.")
    
    try:
        with st.form("feature_request_form"):
            # Repository URL
            repo_url = st.text_input(
                "GitHub Repository URL",
                placeholder="https://github.com/owner/repository",
                help="Enter the full GitHub repository URL where you want to implement the feature"
            )
            
            # Feature description
            feature_description = st.text_area(
                "Feature Description",
                placeholder="Describe the feature you want to add or the bug you want to fix. Be as detailed as possible.\n\nExamples:\n- Add a user authentication system with JWT tokens\n- Fix the memory leak in the data processing module\n- Implement dark mode toggle for the UI\n- Add input validation for the contact form",
                height=150,
                help="Provide a detailed description of what you want to implement"
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
                feature_branch_name = st.text_input(
                    "Feature Branch Name (optional)",
                    placeholder="Auto-generated if empty",
                    help="Name for the new feature branch. Leave empty for auto-generation based on feature description"
                )
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                col3, col4 = st.columns(2)
                
                with col3:
                    create_pr = st.checkbox(
                        "Create Pull Request",
                        value=True,
                        help="Automatically create a pull request after implementing the feature"
                    )
                    
                    include_tests = st.checkbox(
                        "Generate Tests",
                        value=True,
                        help="Generate test files and test cases for the new feature"
                    )
                    
                    include_docs = st.checkbox(
                        "Update Documentation",
                        value=True,
                        help="Update relevant documentation files"
                    )
                
                with col4:
                    complexity_level = st.selectbox(
                        "Implementation Complexity",
                        ["simple", "moderate", "complex"],
                        index=1,
                        help="Expected complexity level of the implementation"
                    )
                    
                    code_style = st.selectbox(
                        "Code Style",
                        ["auto-detect", "pep8", "google", "numpy"],
                        index=0,
                        help="Code style to follow for generated code"
                    )
                    
                    review_before_commit = st.checkbox(
                        "Review Before Commit",
                        value=False,
                        help="Show generated code for review before committing to branch"
                    )
        
            submitted = st.form_submit_button("🚀 Generate & Implement Feature", type="primary")
            
            if submitted:
                if not repo_url:
                    st.error("Please enter a repository URL")
                    return None
                
                if not repo_url.startswith("https://github.com/"):
                    st.error("Please enter a valid GitHub repository URL")
                    return None
                
                if not feature_description.strip():
                    st.error("Please provide a detailed feature description")
                    return None
                
                # Generate branch name if not provided
                if not feature_branch_name.strip():
                    # Create branch name from feature description
                    import re
                    branch_name = re.sub(r'[^a-zA-Z0-9\s]', '', feature_description.lower())
                    branch_name = re.sub(r'\s+', '-', branch_name.strip())
                    branch_name = branch_name[:50]  # Limit length
                    feature_branch_name = f"feature/{branch_name}"
                
                return {
                    "repo_url": repo_url,
                    "feature_description": feature_description.strip(),
                    "base_branch": base_branch,
                    "feature_branch_name": feature_branch_name.strip(),
                    "create_pr": create_pr,
                    "include_tests": include_tests,
                    "include_docs": include_docs,
                    "complexity_level": complexity_level,
                    "code_style": code_style,
                    "review_before_commit": review_before_commit
                }
    
    except Exception as e:
        st.error(f"Error in feature request form: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None
    
    return None

def render_feature_addition_form():
    """Render feature addition input form (legacy - keeping for compatibility)"""
    return render_feature_request_form()

def render_repository_input():
    """Render repository URL input form for security analysis"""
    st.markdown("## 🔗 Security Analysis")
    st.markdown("Analyze repository for security vulnerabilities and code quality issues.")
    
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

def render_feature_request_results(feature_result: Dict[str, Any]):
    """Render feature request implementation results"""
    if not feature_result.get("success"):
        st.error(f"Feature implementation failed: {feature_result.get('error', 'Unknown error')}")
        return
    
    # Success message
    st.success("🎉 Feature implementation completed successfully!")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        branch_created = "✅ Yes" if feature_result.get("branch_created") else "❌ No"
        st.metric("Branch Created", branch_created)
    
    with col2:
        files_modified = feature_result.get("files_modified", 0)
        st.metric("Files Modified", files_modified)
    
    with col3:
        pr_created = "✅ Yes" if feature_result.get("pr_created") else "❌ No"
        st.metric("PR Created", pr_created)
    
    with col4:
        tests_generated = "✅ Yes" if feature_result.get("tests_generated") else "❌ No"
        st.metric("Tests Generated", tests_generated)
    
    # Implementation details
    if feature_result.get("implementation_details"):
        st.markdown("## 📋 Implementation Details")
        
        details = feature_result["implementation_details"]
        
        # Branch information
        if details.get("branch_name"):
            st.info(f"🌿 **Feature Branch:** `{details['branch_name']}`")
        
        # Files created/modified
        if details.get("files_changed"):
            st.markdown("### 📁 Files Changed")
            for file_info in details["files_changed"]:
                file_path = file_info.get("path", "Unknown")
                change_type = file_info.get("type", "modified")
                icon = "🆕" if change_type == "created" else "✏️" if change_type == "modified" else "🗑️"
                st.write(f"{icon} `{file_path}` ({change_type})")
        
        # Generated code preview
        if details.get("code_preview"):
            st.markdown("### 👀 Code Preview")
            for file_path, code_content in details["code_preview"].items():
                with st.expander(f"📄 {file_path}"):
                    st.code(code_content, language="python")
        
        # Pull request information
        if details.get("pr_url"):
            st.markdown("### 🔗 Pull Request")
            st.markdown(f"[View Pull Request]({details['pr_url']})")
            
            if details.get("pr_description"):
                st.markdown("**PR Description:**")
                st.write(details["pr_description"])
    
    # Next steps
    st.markdown("## 🚀 Next Steps")
    next_steps = [
        "Review the generated code in the feature branch",
        "Test the implementation locally",
        "Review and merge the pull request when ready",
        "Deploy the changes to your environment"
    ]
    
    for i, step in enumerate(next_steps, 1):
        st.write(f"{i}. {step}")

# Keep all other existing functions unchanged...
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
            st.info(f"💡 {rec}")

def render_suggestions(suggestions_data: Dict[str, Any]):
    """Render improvement suggestions section"""
    suggestions = suggestions_data.get("suggestions", [])
    
    if not suggestions:
        st.info("No improvement suggestions found.")
        return
    
    # Group suggestions by priority
    high_priority = [s for s in suggestions if s.get("priority") == "high"]
    medium_priority = [s for s in suggestions if s.get("priority") == "medium"]
    low_priority = [s for s in suggestions if s.get("priority") == "low"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔴 High Priority")
        for suggestion in high_priority:
            with st.expander(f"🔧 {suggestion.get('title', 'Suggestion')}"):
                st.write(f"**Category:** {suggestion.get('category', 'General')}")
                st.write(f"**Description:** {suggestion.get('description', 'No description')}")
                if suggestion.get("implementation_steps"):
                    st.write("**Implementation Steps:**")
                    for step in suggestion["implementation_steps"]:
                        st.write(f"• {step}")
    
    with col2:
        st.markdown("### 🟡 Medium Priority")
        for suggestion in medium_priority:
            with st.expander(f"🔧 {suggestion.get('title', 'Suggestion')}"):
                st.write(f"**Category:** {suggestion.get('category', 'General')}")
                st.write(f"**Description:** {suggestion.get('description', 'No description')}")
                if suggestion.get("implementation_steps"):
                    st.write("**Implementation Steps:**")
                    for step in suggestion["implementation_steps"]:
                        st.write(f"• {step}")
    
    with col3:
        st.markdown("### 🟢 Low Priority")
        for suggestion in low_priority:
            with st.expander(f"🔧 {suggestion.get('title', 'Suggestion')}"):
                st.write(f"**Category:** {suggestion.get('category', 'General')}")
                st.write(f"**Description:** {suggestion.get('description', 'No description')}")
                if suggestion.get("implementation_steps"):
                    st.write("**Implementation Steps:**")
                    for step in suggestion["implementation_steps"]:
                        st.write(f"• {step}")

def render_analysis_summary(summary: Dict[str, Any]):
    """Render analysis summary section"""
    if not summary:
        st.info("No summary available.")
        return
    
    # Overall assessment
    overall_score = summary.get("overall_score", 0)
    
    if overall_score >= 80:
        st.success(f"🎉 Excellent! Overall score: {overall_score}/100")
    elif overall_score >= 60:
        st.warning(f"⚠️ Good with room for improvement. Overall score: {overall_score}/100")
    else:
        st.error(f"🚨 Needs attention. Overall score: {overall_score}/100")
    
    # Key findings
    key_findings = summary.get("key_findings", [])
    if key_findings:
        st.markdown("### 🔍 Key Findings")
        for finding in key_findings:
            st.write(f"• {finding}")
    
    # Recommendations
    recommendations = summary.get("recommendations", [])
    if recommendations:
        st.markdown("### 💡 Top Recommendations")
        for rec in recommendations:
            st.info(f"💡 {rec}")

def render_monitoring_dashboard():
    """Render monitoring dashboard"""
    st.markdown("## 📊 System Monitoring Dashboard")
    
    try:
        from utils.bmasterai_monitoring import get_monitor
        monitor = get_monitor()
        health = monitor.get_system_health()
        
        if health.get("status") == "no_data":
            st.info("📊 Monitoring data is being collected. Please check back in a few moments.")
            return
        
        # System metrics
        st.markdown("### 🖥️ System Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu = health.get("system_metrics", {}).get("cpu", {}).get("current", 0)
            st.metric("CPU Usage", f"{cpu:.1f}%")
        
        with col2:
            memory = health.get("system_metrics", {}).get("memory", {}).get("current", 0)
            st.metric("Memory Usage", f"{memory:.1f}%")
        
        with col3:
            active_agents = health.get("active_agents", 0)
            st.metric("Active Agents", active_agents)
        
        with col4:
            uptime = health.get("uptime_seconds", 0)
            st.metric("Uptime", f"{uptime/3600:.1f}h")
        
        # Performance charts
        st.markdown("### 📈 Performance Trends")
        
        # Create sample data for demonstration
        import numpy as np
        times = pd.date_range(start=datetime.now() - timedelta(hours=1), end=datetime.now(), freq='1min')
        cpu_data = np.random.normal(cpu, 10, len(times))
        memory_data = np.random.normal(memory, 5, len(times))
        
        chart_data = pd.DataFrame({
            'Time': times,
            'CPU': np.clip(cpu_data, 0, 100),
            'Memory': np.clip(memory_data, 0, 100)
        })
        
        fig = px.line(chart_data, x='Time', y=['CPU', 'Memory'], 
                     title='System Resource Usage Over Time')
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load monitoring data: {str(e)}")

def render_analysis_history():
    """Render analysis history"""
    st.markdown("## 📋 Analysis History")
    
    # Get analysis history from session state
    history = st.session_state.get("analysis_history", [])
    
    if not history:
        st.info("No analysis history available. Perform some analyses to see them here.")
        return
    
    # Display history
    for i, analysis in enumerate(reversed(history)):
        with st.expander(f"Analysis {len(history) - i}: {analysis.get('repo_url', 'Unknown')} - {analysis.get('timestamp', 'Unknown time')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Repository:** {analysis.get('repo_url', 'N/A')}")
                st.write(f"**Type:** {analysis.get('analysis_type', 'N/A')}")
                st.write(f"**Status:** {'✅ Success' if analysis.get('success') else '❌ Failed'}")
            
            with col2:
                st.write(f"**Timestamp:** {analysis.get('timestamp', 'N/A')}")
                st.write(f"**Duration:** {analysis.get('duration', 'N/A')}")
                
                if analysis.get('result'):
                    if st.button(f"View Results {len(history) - i}", key=f"view_{i}"):
                        st.session_state['current_analysis'] = analysis
                        st.experimental_rerun()

def render_settings():
    """Render settings page"""
    st.markdown("## ⚙️ Settings")
    
    # API Configuration
    st.markdown("### 🔑 API Configuration")
    
    with st.form("api_settings"):
        github_token = st.text_input(
            "GitHub Token",
            type="password",
            help="Your GitHub personal access token"
        )
        
        openai_api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Your OpenAI API key for AI-powered analysis"
        )
        
        submitted = st.form_submit_button("Save Settings")
        
        if submitted:
            # Save to session state (in production, use secure storage)
            st.session_state['github_token'] = github_token
            st.session_state['openai_api_key'] = openai_api_key
            st.success("Settings saved successfully!")
    
    # Analysis Preferences
    st.markdown("### 🎯 Analysis Preferences")
    
    default_analysis_type = st.selectbox(
        "Default Analysis Type",
        ["comprehensive", "quick", "security-focused"],
        help="Default analysis type for new analyses"
    )
    
    auto_create_pr = st.checkbox(
        "Auto-create Pull Requests",
        value=True,
        help="Automatically create pull requests for improvements"
    )
    
    max_suggestions = st.slider(
        "Maximum Suggestions",
        min_value=1,
        max_value=20,
        value=5,
        help="Maximum number of suggestions to generate"
    )
    
    # Save preferences
    if st.button("Save Preferences"):
        st.session_state.update({
            'default_analysis_type': default_analysis_type,
            'auto_create_pr': auto_create_pr,
            'max_suggestions': max_suggestions
        })
        st.success("Preferences saved!")
    
    # System Information
    st.markdown("### ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Application Version:** 1.0.0")
        st.write("**Python Version:** 3.9+")
        st.write("**Streamlit Version:** 1.28+")
    
    with col2:
        st.write("**Session ID:** " + st.session_state.get('session_id', 'N/A'))
        st.write("**Session Duration:** " + f"{(time.time() - st.session_state.get('session_start_time', time.time()))/60:.1f} min")

def render_pr_results(pr_result: Dict[str, Any]):
    """Render pull request creation results"""
    if not pr_result.get("success"):
        st.error(f"Pull request creation failed: {pr_result.get('error', 'Unknown error')}")
        return
    
    st.success("🎉 Pull request created successfully!")
    
    pr_info = pr_result.get("pr_info", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**PR Number:** #{pr_info.get('number', 'N/A')}")
        st.write(f"**Title:** {pr_info.get('title', 'N/A')}")
        st.write(f"**State:** {pr_info.get('state', 'N/A')}")
    
    with col2:
        st.write(f"**Branch:** {pr_info.get('head', {}).get('ref', 'N/A')}")
        st.write(f"**Base:** {pr_info.get('base', {}).get('ref', 'N/A')}")
        
        if pr_info.get('html_url'):
            st.markdown(f"[View Pull Request]({pr_info['html_url']})")
    
    if pr_info.get('body'):
        st.markdown("### 📝 PR Description")
        st.write(pr_info['body'])

def render_feature_implementation_results(feature_result: Dict[str, Any]):
    """Render feature implementation results"""
    return render_feature_request_results(feature_result)
