"""
OpenClaw Telemetry Dashboard - Enhanced with BMasterAI
Real-time observability dashboard for OpenClaw LLM usage with BMasterAI metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import time
from pathlib import Path
import json

# Try to import bmasterai
try:
    from session_parser import OpenClawSessionParser
    BMASTERAI_AVAILABLE = True
except:
    BMASTERAI_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="OpenClaw Telemetry - Enhanced",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .alert-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)


class OpenClawDashboard:
    def __init__(self, db_path: str = "openclaw_telemetry.db"):
        self.db_path = db_path
        self.parser = None
        if BMASTERAI_AVAILABLE:
            try:
                sessions_dir = "/home/tadmin/.openclaw/agents/main/sessions"
                self.parser = OpenClawSessionParser(sessions_dir, db_path, enable_bmasterai=True)
            except:
                pass
    
    def get_connection(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_bmasterai_alerts(self):
        """Get active BMasterAI alerts"""
        if self.parser and hasattr(self.parser, 'get_bmasterai_alerts'):
            return self.parser.get_bmasterai_alerts()
        return []
    
    def get_bmasterai_metrics(self, metric_name, duration_minutes=60):
        """Get BMasterAI metric stats"""
        if self.parser and hasattr(self.parser, 'get_bmasterai_metrics'):
            return self.parser.get_bmasterai_metrics(metric_name, duration_minutes)
        return {}
    
    def get_exec_history(self, limit=100):
        """Get exec command history"""
        if self.parser and hasattr(self.parser, 'get_exec_history'):
            return self.parser.get_exec_history(limit)
        return []
    
    def get_overview_metrics(self, time_filter: str = "all"):
        """Get high-level overview metrics"""
        conn = self.get_connection()
        
        # Time filter
        time_clause = ""
        if time_filter == "today":
            time_clause = f"WHERE date(start_time) = date('now')"
        elif time_filter == "week":
            time_clause = f"WHERE start_time >= datetime('now', '-7 days')"
        elif time_filter == "month":
            time_clause = f"WHERE start_time >= datetime('now', '-30 days')"
        
        query = f"""
            SELECT 
                COUNT(*) as total_sessions,
                SUM(total_messages) as total_messages,
                SUM(total_tool_calls) as total_tool_calls,
                SUM(total_input_tokens) as total_input_tokens,
                SUM(total_output_tokens) as total_output_tokens,
                SUM(total_cache_read_tokens) as total_cache_read_tokens,
                SUM(total_cache_write_tokens) as total_cache_write_tokens,
                SUM(total_cost) as total_cost
            FROM sessions
            {time_clause}
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.iloc[0].to_dict()
    
    def get_cache_efficiency_metrics(self, time_filter: str = "all"):
        """Calculate cache efficiency metrics"""
        conn = self.get_connection()
        
        time_clause = ""
        if time_filter == "today":
            time_clause = "WHERE date(start_time) = date('now')"
        elif time_filter == "week":
            time_clause = "WHERE start_time >= datetime('now', '-7 days')"
        elif time_filter == "month":
            time_clause = "WHERE start_time >= datetime('now', '-30 days')"
        
        query = f"""
            SELECT 
                session_id,
                start_time,
                model,
                total_input_tokens + total_output_tokens as total_tokens,
                total_cache_read_tokens,
                total_cost,
                CASE 
                    WHEN (total_input_tokens + total_output_tokens) > 0 
                    THEN CAST(total_cache_read_tokens AS FLOAT) / (total_input_tokens + total_output_tokens)
                    ELSE 0
                END as cache_hit_rate,
                CASE 
                    WHEN total_cost > 0 
                    THEN (total_input_tokens + total_output_tokens + total_cache_read_tokens + total_cache_write_tokens) / total_cost
                    ELSE 0
                END as tokens_per_dollar
            FROM sessions
            {time_clause}
            ORDER BY start_time DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_model_breakdown(self, time_filter: str = "all"):
        """Get usage breakdown by model"""
        conn = self.get_connection()
        
        time_clause = ""
        if time_filter == "today":
            time_clause = "WHERE date(start_time) = date('now')"
        elif time_filter == "week":
            time_clause = "WHERE start_time >= datetime('now', '-7 days')"
        elif time_filter == "month":
            time_clause = "WHERE start_time >= datetime('now', '-30 days')"
        
        query = f"""
            SELECT 
                model,
                provider,
                COUNT(*) as session_count,
                SUM(total_input_tokens) as input_tokens,
                SUM(total_output_tokens) as output_tokens,
                SUM(total_cache_read_tokens) as cache_read_tokens,
                SUM(total_cost) as total_cost
            FROM sessions
            {time_clause}
            GROUP BY model, provider
            ORDER BY total_cost DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_timeline_data(self, time_filter: str = "today"):
        """Get timeline data for charts"""
        conn = self.get_connection()
        
        if time_filter == "today":
            time_clause = "WHERE date(timestamp) = date('now')"
            date_format = "strftime('%H:%M', timestamp)"
        elif time_filter == "week":
            time_clause = "WHERE timestamp >= datetime('now', '-7 days')"
            date_format = "strftime('%Y-%m-%d %H:00', timestamp)"
        else:  # month
            time_clause = "WHERE timestamp >= datetime('now', '-30 days')"
            date_format = "date(timestamp)"
        
        query = f"""
            SELECT 
                {date_format} as time_bucket,
                COUNT(*) as message_count,
                SUM(total_tokens) as total_tokens,
                SUM(cost) as total_cost
            FROM messages
            {time_clause}
            GROUP BY time_bucket
            ORDER BY time_bucket
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_tool_usage(self, limit: int = 10):
        """Get most used tools"""
        conn = self.get_connection()
        
        query = f"""
            SELECT 
                tool_name,
                COUNT(*) as usage_count
            FROM tool_calls
            GROUP BY tool_name
            ORDER BY usage_count DESC
            LIMIT {limit}
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_recent_sessions(self, limit: int = 10):
        """Get recent sessions"""
        conn = self.get_connection()
        
        query = f"""
            SELECT 
                session_id,
                datetime(start_time) as start_time,
                model,
                provider,
                total_messages,
                total_tool_calls,
                total_input_tokens + total_output_tokens as total_tokens,
                printf('$%.4f', total_cost) as cost
            FROM sessions
            ORDER BY start_time DESC
            LIMIT {limit}
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df


def show_alerts_panel(dashboard):
    """Show BMasterAI alerts panel"""
    alerts = dashboard.get_bmasterai_alerts()
    
    if alerts:
        st.markdown('<div class="alert-box">', unsafe_allow_html=True)
        st.subheader("🚨 Active Alerts")
        for alert in alerts:
            st.warning(f"**{alert.get('name', 'Alert')}:** {alert.get('message', 'No details')}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("✅ No active alerts")


def show_bmasterai_tab(dashboard, time_filter):
    """Show BMasterAI metrics tab"""
    st.header("📊 BMasterAI Metrics & Analytics")
    
    if not BMASTERAI_AVAILABLE or not dashboard.parser:
        st.warning("⚠️ BMasterAI integration not available. Install with: `pip install bmasterai>=0.2.3`")
        st.info("""
        **What you're missing:**
        - Real-time alert notifications
        - Custom metric tracking (session cost, token efficiency, cache hit rate)
        - Time-windowed metric aggregation
        - Performance monitoring with percentiles
        
        **To enable:** Run `pip install bmasterai>=0.2.3` in your virtual environment.
        """)
        return
    
    # Check if advanced metrics are available
    # Note: The custom metrics API (record_custom_metric, get_metric_stats, get_active_alerts) 
    # was designed for a future bmasterai version but isn't available in 0.2.1
    test_metrics = dashboard.get_bmasterai_metrics("session_cost", 60)
    if not test_metrics or not test_metrics.get('mean'):
        st.info("""
        **📊 BMasterAI Custom Metrics**
        
        The custom metrics API (session cost stats, token efficiency, cache monitoring, alerts) 
        is now available in bmasterai 0.2.3!
        
        **What works now:**
        - Basic monitoring (via `track_llm_call`, `track_task_duration`)
        - System health tracking
        - Agent dashboard
        
        **For advanced metrics, use:**
        - The **Overview** tab (session costs, tokens, cache stats)
        - The **Model Analytics** tab (per-model breakdowns)
        - The **Exec History** tab (command drill-down)
        
        These tabs provide comprehensive telemetry without requiring custom bmasterai metrics.
        """)
        return
    
    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cache_metrics = dashboard.get_bmasterai_metrics("cache_hit_rate", duration_minutes=1440)
        avg_cache_rate = cache_metrics.get('avg', 0) * 100 if cache_metrics else 0
        st.metric(
            "Avg Cache Hit Rate",
            f"{avg_cache_rate:.1f}%",
            help="Average cache efficiency across sessions"
        )
    
    with col2:
        cost_metrics = dashboard.get_bmasterai_metrics("session_cost", duration_minutes=1440)
        avg_cost = cost_metrics.get('avg', 0) if cost_metrics else 0
        st.metric(
            "Avg Session Cost",
            f"${avg_cost:.4f}",
            help="Average cost per session"
        )
    
    with col3:
        token_metrics = dashboard.get_bmasterai_metrics("session_total_tokens", duration_minutes=1440)
        avg_tokens = token_metrics.get('avg', 0) if token_metrics else 0
        st.metric(
            "Avg Tokens/Session",
            f"{int(avg_tokens):,}",
            help="Average tokens per session"
        )
    
    with col4:
        efficiency_metrics = dashboard.get_bmasterai_metrics("tokens_per_dollar", duration_minutes=1440)
        avg_efficiency = efficiency_metrics.get('avg', 0) if efficiency_metrics else 0
        st.metric(
            "Tokens per Dollar",
            f"{int(avg_efficiency):,}",
            help="Cost efficiency metric"
        )
    
    # Cache Efficiency Analysis
    st.subheader("💎 Cache Efficiency Analysis")
    cache_df = dashboard.get_cache_efficiency_metrics(time_filter)
    
    if not cache_df.empty and len(cache_df) > 0:
        # Cache hit rate over time
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cache_df['start_time'],
            y=cache_df['cache_hit_rate'] * 100,
            mode='lines+markers',
            name='Cache Hit Rate %',
            line=dict(color='#667eea', width=2),
            marker=dict(size=8)
        ))
        fig.update_layout(
            title='Cache Hit Rate Over Time',
            xaxis_title='Session Time',
            yaxis_title='Cache Hit Rate (%)',
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Cost Efficiency
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Cost Efficiency")
            fig = px.scatter(
                cache_df.head(50),
                x='total_tokens',
                y='total_cost',
                color='cache_hit_rate',
                size='total_tokens',
                hover_data=['model', 'session_id'],
                color_continuous_scale='Viridis',
                labels={
                    'total_tokens': 'Total Tokens',
                    'total_cost': 'Cost ($)',
                    'cache_hit_rate': 'Cache Hit Rate'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("⚡ Tokens per Dollar")
            fig = px.bar(
                cache_df.head(20).sort_values('tokens_per_dollar', ascending=False),
                x='session_id',
                y='tokens_per_dollar',
                color='tokens_per_dollar',
                color_continuous_scale='Greens',
                labels={'tokens_per_dollar': 'Tokens/$', 'session_id': 'Session'}
            )
            fig.update_layout(height=400, showlegend=False)
            fig.update_xaxes(showticklabels=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        st.subheader("📈 Summary Statistics")
        summary_cols = st.columns(4)
        
        with summary_cols[0]:
            avg_cache_rate = cache_df['cache_hit_rate'].mean() * 100
            st.metric("Avg Cache Hit Rate", f"{avg_cache_rate:.1f}%")
        
        with summary_cols[1]:
            max_cache_rate = cache_df['cache_hit_rate'].max() * 100
            st.metric("Max Cache Hit Rate", f"{max_cache_rate:.1f}%")
        
        with summary_cols[2]:
            avg_efficiency = cache_df['tokens_per_dollar'].mean()
            st.metric("Avg Tokens/$", f"{int(avg_efficiency):,}")
        
        with summary_cols[3]:
            total_cached = cache_df['total_cache_read_tokens'].sum()
            st.metric("Total Cached Tokens", f"{int(total_cached):,}")
    
    else:
        st.info("No cache efficiency data available for selected time range")


def main():
    st.markdown('<p class="main-header">🔍 OpenClaw Telemetry - Enhanced</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    
    # Time filter
    time_filter = st.sidebar.selectbox(
        "Time Range",
        ["all", "today", "week", "month"],
        format_func=lambda x: {
            "all": "All Time",
            "today": "Today",
            "week": "Last 7 Days",
            "month": "Last 30 Days"
        }[x]
    )
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    # BMasterAI status
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 BMasterAI Status")
    if BMASTERAI_AVAILABLE:
        st.sidebar.success("✅ BMasterAI Enabled")
    else:
        st.sidebar.warning("⚠️ BMasterAI Not Available")
    
    # Initialize dashboard
    dashboard = OpenClawDashboard()
    
    # Check if database exists
    if not Path(dashboard.db_path).exists():
        st.error(f"❌ Database not found: {dashboard.db_path}")
        st.info("Run `python session_parser.py` first to parse OpenClaw sessions.")
        return
    
    # Alerts panel (always visible)
    if BMASTERAI_AVAILABLE:
        show_alerts_panel(dashboard)
    
    # Tab navigation
    tabs = st.tabs(["📊 Overview", "🧠 BMasterAI Metrics", "🤖 Model Analytics", "🕐 Recent Activity", "⚡ Exec History"])
    
    # Tab 1: Overview (existing dashboard)
    with tabs[0]:
        # Get overview metrics
        metrics = dashboard.get_overview_metrics(time_filter)
        
        # Overview metrics row
        st.subheader("📊 Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Sessions",
                f"{int(metrics.get('total_sessions', 0)):,}",
                help="Number of OpenClaw sessions"
            )
        
        with col2:
            st.metric(
                "Total Messages",
                f"{int(metrics.get('total_messages', 0)):,}",
                help="LLM API calls made"
            )
        
        with col3:
            total_tokens = int(metrics.get('total_input_tokens', 0)) + int(metrics.get('total_output_tokens', 0))
            st.metric(
                "Total Tokens",
                f"{total_tokens:,}",
                help="Input + Output tokens"
            )
        
        with col4:
            st.metric(
                "Total Cost",
                f"${metrics.get('total_cost', 0):.2f}",
                help="Total API costs"
            )
        
        # Token breakdown
        st.subheader("💎 Token Breakdown")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Input Tokens", f"{int(metrics.get('total_input_tokens', 0)):,}")
        
        with col2:
            st.metric("Output Tokens", f"{int(metrics.get('total_output_tokens', 0)):,}")
        
        with col3:
            st.metric("Cache Read", f"{int(metrics.get('total_cache_read_tokens', 0)):,}")
        
        with col4:
            st.metric("Cache Write", f"{int(metrics.get('total_cache_write_tokens', 0)):,}")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Usage Over Time")
            timeline_df = dashboard.get_timeline_data(time_filter)
            
            if not timeline_df.empty:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig.add_trace(
                    go.Bar(x=timeline_df['time_bucket'], y=timeline_df['message_count'], 
                           name="Messages", marker_color="#667eea"),
                    secondary_y=False
                )
                
                fig.add_trace(
                    go.Scatter(x=timeline_df['time_bucket'], y=timeline_df['total_cost'],
                              name="Cost ($)", mode='lines+markers', marker_color="#764ba2"),
                    secondary_y=True
                )
                
                fig.update_layout(
                    height=400,
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig.update_yaxes(title_text="Messages", secondary_y=False)
                fig.update_yaxes(title_text="Cost ($)", secondary_y=True)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timeline data available for selected time range")
        
        with col2:
            st.subheader("🔧 Tool Usage")
            tool_df = dashboard.get_tool_usage(limit=10)
            
            if not tool_df.empty:
                fig = px.bar(
                    tool_df, 
                    x='usage_count', 
                    y='tool_name',
                    orientation='h',
                    color='usage_count',
                    color_continuous_scale='Purples'
                )
                fig.update_layout(height=400, showlegend=False)
                fig.update_yaxes(categoryorder='total ascending')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tool usage data available")
    
    # Tab 2: BMasterAI Metrics
    with tabs[1]:
        show_bmasterai_tab(dashboard, time_filter)
    
    # Tab 3: Model Analytics
    with tabs[2]:
        st.header("🤖 Model Analytics")
        model_df = dashboard.get_model_breakdown(time_filter)
        
        if not model_df.empty:
            # Add formatted cost column
            model_df['cost_formatted'] = model_df['total_cost'].apply(lambda x: f"${x:.4f}")
            
            # Display as table
            st.dataframe(
                model_df[['model', 'provider', 'session_count', 'input_tokens', 
                         'output_tokens', 'cache_read_tokens', 'cost_formatted']].rename(columns={
                    'session_count': 'Sessions',
                    'input_tokens': 'Input Tokens',
                    'output_tokens': 'Output Tokens',
                    'cache_read_tokens': 'Cache Reads',
                    'cost_formatted': 'Total Cost'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Pie charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    model_df, 
                    values='total_cost', 
                    names='model',
                    title='Cost Distribution by Model',
                    color_discrete_sequence=px.colors.sequential.Purples_r
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.pie(
                    model_df,
                    values='session_count',
                    names='model',
                    title='Session Distribution by Model',
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No model data available for selected time range")
    
    # Tab 4: Recent Activity
    with tabs[3]:
        st.header("🕐 Recent Sessions")
        recent_df = dashboard.get_recent_sessions(limit=20)
        
        if not recent_df.empty:
            st.dataframe(
                recent_df.rename(columns={
                    'session_id': 'Session ID',
                    'start_time': 'Start Time',
                    'model': 'Model',
                    'provider': 'Provider',
                    'total_messages': 'Messages',
                    'total_tool_calls': 'Tools',
                    'total_tokens': 'Tokens',
                    'cost': 'Cost'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent sessions found")
    
    # Tab 5: Exec History
    with tabs[4]:
        st.header("⚡ Exec Command History")
        st.markdown("Drill down into all bash commands executed by OpenClaw via the `exec` tool.")
        
        # Limit selector
        col1, col2 = st.columns([3, 1])
        with col2:
            limit = st.selectbox("Show commands", [50, 100, 200, 500], index=1)
        
        # Get exec history
        exec_history = dashboard.get_exec_history(limit=limit)
        
        if exec_history:
            # Convert to DataFrame
            df = pd.DataFrame(exec_history)
            
            # Add search filter
            with col1:
                search = st.text_input("🔍 Filter commands", placeholder="grep, git, cd, etc...")
            
            # Apply filter
            if search:
                df = df[df['command'].str.contains(search, case=False, na=False)]
            
            st.markdown(f"**Showing {len(df)} of {len(exec_history)} commands**")
            
            # Display table with enhanced formatting
            st.dataframe(
                df.rename(columns={
                    'timestamp': 'Timestamp',
                    'session_id': 'Session',
                    'model': 'Model',
                    'command': 'Command'
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Command": st.column_config.TextColumn(
                        "Command",
                        width="large",
                    ),
                    "Timestamp": st.column_config.DatetimeColumn(
                        "Timestamp",
                        format="MMM DD, HH:mm:ss",
                    )
                }
            )
            
            # Command statistics
            st.markdown("---")
            st.subheader("📊 Command Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_commands = len(exec_history)
                st.metric("Total Commands", f"{total_commands:,}")
            
            with col2:
                # Top command prefixes (first word)
                if not df.empty:
                    commands = df['command'].str.split().str[0].value_counts()
                    top_cmd = commands.index[0] if len(commands) > 0 else "N/A"
                    st.metric("Most Common", top_cmd)
            
            with col3:
                # Unique sessions
                unique_sessions = df['session_id'].nunique()
                st.metric("Sessions", unique_sessions)
            
            # Top commands chart
            if not df.empty:
                st.markdown("### Most Frequent Commands")
                commands = df['command'].str.split().str[0].value_counts().head(10)
                
                fig = px.bar(
                    x=commands.values,
                    y=commands.index,
                    orientation='h',
                    labels={'x': 'Count', 'y': 'Command'},
                    color=commands.values,
                    color_continuous_scale='Purples'
                )
                fig.update_layout(height=400, showlegend=False)
                fig.update_yaxes(categoryorder='total ascending')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No exec command history found. Make sure the session parser has processed sessions with the updated schema.")
            st.markdown("""
            **To enable exec history tracking:**
            1. Re-run the session parser: `python session_parser.py`
            2. The parser will rebuild the database with parameter tracking
            3. Refresh this dashboard to see command history
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>OpenClaw Telemetry Dashboard - Enhanced with BMasterAI | Powered by bmasterai telemetry patterns</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
