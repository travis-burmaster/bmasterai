"""
OpenClaw Telemetry Dashboard
Real-time observability dashboard for OpenClaw LLM usage with bmasterai integration
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
from session_parser import SessionParser


# Page config
st.set_page_config(
    page_title="OpenClaw Telemetry",
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
        self.parser = SessionParser(db_path)
    
    def get_connection(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_bmasterai_alerts(self):
        """Get active bmasterai alerts"""
        try:
            return self.parser.get_bmasterai_alerts()
        except Exception as e:
            st.warning(f"Could not fetch bmasterai alerts: {e}")
            return []
    
    def get_bmasterai_metrics(self, metric_name: str, duration_minutes: int = 60):
        """Get bmasterai custom metrics"""
        try:
            return self.parser.get_bmasterai_metrics(metric_name, duration_minutes)
        except Exception as e:
            st.warning(f"Could not fetch metric {metric_name}: {e}")
            return None
    
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


def main():
    st.markdown('<p class="main-header">🔍 OpenClaw Telemetry Dashboard</p>', unsafe_allow_html=True)
    
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
    
    # Initialize dashboard
    dashboard = OpenClawDashboard()
    
    # Check if database exists
    if not Path(dashboard.db_path).exists():
        st.error(f"❌ Database not found: {dashboard.db_path}")
        st.info("Run `python session_parser.py` first to parse OpenClaw sessions.")
        return
    
    # Get overview metrics
    metrics = dashboard.get_overview_metrics(time_filter)
    
    # BMasterAI Alerts Section
    alerts = dashboard.get_bmasterai_alerts()
    if alerts:
        st.warning("⚠️ **Active Alerts**")
        for alert in alerts:
            alert_type = alert.get('type', 'unknown')
            message = alert.get('message', 'No message')
            severity = alert.get('severity', 'info')
            
            # Color code by severity
            if severity == 'critical':
                st.error(f"🔴 **{alert_type}**: {message}")
            elif severity == 'warning':
                st.warning(f"🟡 **{alert_type}**: {message}")
            else:
                st.info(f"🔵 **{alert_type}**: {message}")
    
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
    
    # BMasterAI Custom Metrics Section
    st.subheader("📈 BMasterAI Custom Metrics")
    
    metric_duration = st.selectbox(
        "Metric Time Window",
        [15, 30, 60, 120, 1440],
        index=2,
        format_func=lambda x: f"Last {x} minutes" if x < 1440 else "Last 24 hours"
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cost_stats = dashboard.get_bmasterai_metrics("session_cost", metric_duration)
        if cost_stats:
            avg_cost = cost_stats.get('mean', 0)
            max_cost = cost_stats.get('max', 0)
            st.metric(
                "Avg Session Cost",
                f"${avg_cost:.4f}",
                delta=f"Max: ${max_cost:.4f}",
                help="Average cost per session in selected time window"
            )
        else:
            st.metric("Avg Session Cost", "N/A")
    
    with col2:
        token_stats = dashboard.get_bmasterai_metrics("total_tokens", metric_duration)
        if token_stats:
            avg_tokens = int(token_stats.get('mean', 0))
            max_tokens = int(token_stats.get('max', 0))
            st.metric(
                "Avg Tokens/Session",
                f"{avg_tokens:,}",
                delta=f"Max: {max_tokens:,}",
                help="Average tokens per session"
            )
        else:
            st.metric("Avg Tokens/Session", "N/A")
    
    with col3:
        cache_stats = dashboard.get_bmasterai_metrics("cache_hit_rate", metric_duration)
        if cache_stats:
            avg_cache = cache_stats.get('mean', 0) * 100
            max_cache = cache_stats.get('max', 0) * 100
            st.metric(
                "Avg Cache Hit Rate",
                f"{avg_cache:.1f}%",
                delta=f"Max: {max_cache:.1f}%",
                help="Percentage of tokens served from cache"
            )
        else:
            st.metric("Avg Cache Hit Rate", "N/A")
    
    with col4:
        efficiency_stats = dashboard.get_bmasterai_metrics("tokens_per_dollar", metric_duration)
        if efficiency_stats:
            avg_eff = int(efficiency_stats.get('mean', 0))
            max_eff = int(efficiency_stats.get('max', 0))
            st.metric(
                "Token Efficiency",
                f"{avg_eff:,} tok/$",
                delta=f"Max: {max_eff:,}",
                help="Tokens per dollar spent (higher is better)"
            )
        else:
            st.metric("Token Efficiency", "N/A")
    
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
    
    # Model breakdown
    st.subheader("🤖 Model Breakdown")
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
        
        # Pie chart
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
    
    # Recent sessions
    st.subheader("🕐 Recent Sessions")
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
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>OpenClaw Telemetry Dashboard | Powered by <a href="https://github.com/travis-burmaster/bmasterai" target="_blank">bmasterai</a> observability framework</p>
        <p style='font-size: 0.8rem; margin-top: 0.5rem;'>Enterprise-grade monitoring • Custom metrics • Alert rules • Real-time insights</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
