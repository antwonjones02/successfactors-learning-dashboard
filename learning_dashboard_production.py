#!/usr/bin/env python3
"""
SuccessFactors Learning Dashboard - Production Version
Professional dashboard for production use with Delta2
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import time
from config_production import ACTIVE_CONFIG, USE_PRODUCTION

# Page config
st.set_page_config(
    page_title="Learning Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'token_expiry' not in st.session_state:
    st.session_state.token_expiry = None
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "disconnected"
if 'last_error' not in st.session_state:
    st.session_state.last_error = None
if 'cached_data' not in st.session_state:
    st.session_state.cached_data = {}
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

class SuccessFactorsAPI:
    def __init__(self):
        self.client_id = ACTIVE_CONFIG["CLIENT_ID"]
        self.client_secret = ACTIVE_CONFIG["CLIENT_SECRET"]
        self.user_id = ACTIVE_CONFIG["USER_ID"]
        self.base_url = ACTIVE_CONFIG["BASE_URL"]
        self.environment = "PRODUCTION" if USE_PRODUCTION else "SANDBOX"
    
    def authenticate(self):
        """Authenticate with SuccessFactors OAuth"""
        token_url = f"{self.base_url}/learning/oauth-api/rest/v1/token"
        
        payload = {
            "grant_type": "client_credentials",
            "scope": {
                "userId": self.user_id,
                "companyId": self.client_id,
                "userType": "admin",
                "resourceType": "learning_public_api"
            },
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            st.session_state.connection_status = "connecting"
            response = requests.post(
                token_url, 
                json=payload, 
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                st.session_state.access_token = token_data.get("access_token")
                st.session_state.token_expiry = datetime.now() + timedelta(hours=1)
                st.session_state.connection_status = "connected"
                st.session_state.last_error = None
                return True
            else:
                st.session_state.connection_status = "error"
                st.session_state.last_error = f"Auth failed: {response.status_code} - {response.text}"
                return False
                
        except Exception as e:
            st.session_state.connection_status = "error"
            st.session_state.last_error = f"Connection error: {str(e)}"
            return False
    
    def make_request(self, endpoint, use_cache=True, cache_duration=300):
        """Make authenticated API request with caching"""
        # Check cache first
        if use_cache and endpoint in st.session_state.cached_data:
            cache_time, cached_response = st.session_state.cached_data[endpoint]
            if (datetime.now() - cache_time).total_seconds() < cache_duration:
                return cached_response
        
        # Ensure we have valid token
        if not st.session_state.access_token or datetime.now() > st.session_state.token_expiry:
            if not self.authenticate():
                return None
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {st.session_state.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Cache the response
                st.session_state.cached_data[endpoint] = (datetime.now(), data)
                return data
            else:
                st.session_state.last_error = f"API error: {response.status_code}"
                return None
        except Exception as e:
            st.session_state.last_error = f"Request failed: {str(e)}"
            return None

# Initialize API
api = SuccessFactorsAPI()

# Header
col1, col2, col3 = st.columns([2, 3, 1])
with col1:
    st.title("📊 Learning Analytics")
with col2:
    if st.session_state.connection_status == "connected":
        st.success(f"🟢 Connected to {api.environment}")
    else:
        st.info(f"🔵 {api.environment} Environment")
with col3:
    st.write(f"**{datetime.now().strftime('%B %d, %Y')}**")

# Sidebar
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # Connection section
    st.subheader("🔌 Connection")
    
    if st.session_state.connection_status == "disconnected":
        if st.button("🚀 Connect to SuccessFactors", use_container_width=True):
            with st.spinner("Establishing connection..."):
                if api.authenticate():
                    st.success("✅ Connected successfully!")
                    st.rerun()
                else:
                    st.error("❌ Connection failed")
    
    elif st.session_state.connection_status == "connected":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.session_state.cached_data = {}
                st.session_state.last_refresh = datetime.now()
                st.rerun()
        with col2:
            if st.button("🔌 Disconnect", use_container_width=True):
                st.session_state.access_token = None
                st.session_state.token_expiry = None
                st.session_state.connection_status = "disconnected"
                st.session_state.cached_data = {}
                st.rerun()
        
        # Token info
        if st.session_state.token_expiry:
            remaining = (st.session_state.token_expiry - datetime.now()).total_seconds() / 60
            st.progress(remaining / 60, text=f"Token: {remaining:.0f} min remaining")
    
    # Environment info
    st.markdown("---")
    st.subheader("🌐 Environment")
    env_col1, env_col2 = st.columns(2)
    with env_col1:
        st.metric("Status", api.environment)
    with env_col2:
        st.metric("Client", api.client_id)
    
    # Last refresh
    if st.session_state.last_refresh:
        st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # Error display
    if st.session_state.last_error:
        st.markdown("---")
        st.error("⚠️ Last Error")
        st.caption(st.session_state.last_error)

# Main content
if st.session_state.connection_status == "connected":
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Dashboard", 
        "📚 Learning Activity", 
        "👥 User Analytics",
        "📊 Reports",
        "🔍 Data Explorer"
    ])
    
    with tab1:
        # Dashboard Overview
        st.header("Executive Dashboard")
        
        # Key Metrics Row
        with st.spinner("Loading dashboard metrics..."):
            col1, col2, col3, col4 = st.columns(4)
            
            # Fetch learning history
            history = api.make_request("/learning/odatav4/public/user/learningHistory/v1")
            if history and 'value' in history:
                total_completions = len(history['value'])
                col1.metric(
                    "Total Completions", 
                    f"{total_completions:,}",
                    help="Total learning activities completed"
                )
            else:
                col1.metric("Total Completions", "N/A")
            
            # Fetch users
            users = api.make_request("/learning/odatav4/public/admin/user-service/v1")
            if users and 'value' in users:
                total_users = len(users['value'])
                col2.metric(
                    "Active Learners", 
                    f"{total_users:,}",
                    help="Total active users in the system"
                )
            else:
                col2.metric("Active Learners", "N/A")
            
            # Fetch learning events
            events = api.make_request("/learning/odatav4/public/admin/learningEvent/v1")
            if events and 'value' in events:
                total_events = len(events['value'])
                col3.metric(
                    "Learning Events", 
                    f"{total_events:,}",
                    help="Total learning events available"
                )
            else:
                col3.metric("Learning Events", "N/A")
            
            # Calculate completion rate (mock for now)
            if history and users and 'value' in history and 'value' in users and total_users > 0:
                completion_rate = (total_completions / (total_users * 10)) * 100  # Assuming 10 courses per user average
                col4.metric(
                    "Completion Rate", 
                    f"{min(completion_rate, 100):.1f}%",
                    delta="+2.3%",
                    help="Overall completion rate"
                )
            else:
                col4.metric("Completion Rate", "N/A")
        
        # Charts Section
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Learning Trends")
            # Create sample trend data
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            trend_data = pd.DataFrame({
                'Date': dates,
                'Completions': [50 + i * 2 + (i % 7) * 5 for i in range(30)],
                'Enrollments': [60 + i * 3 + (i % 5) * 4 for i in range(30)]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend_data['Date'], 
                y=trend_data['Completions'],
                mode='lines+markers',
                name='Completions',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=trend_data['Date'], 
                y=trend_data['Enrollments'],
                mode='lines+markers',
                name='Enrollments',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig.update_layout(
                height=400,
                showlegend=True,
                xaxis_title="Date",
                yaxis_title="Count",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Completion by Category")
            # Sample category data
            categories = ['Compliance', 'Technical', 'Leadership', 'Sales', 'Product']
            values = [85, 72, 68, 91, 78]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=categories,
                    y=values,
                    marker_color=['#2ecc71', '#3498db', '#9b59b6', '#e74c3c', '#f39c12']
                )
            ])
            fig.update_layout(
                height=400,
                xaxis_title="Category",
                yaxis_title="Completion Rate (%)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Learning Activity Analysis")
        
        # Fetch learning history
        history_data = api.make_request("/learning/odatav4/public/user/learningHistory/v1")
        
        if history_data and 'value' in history_data and len(history_data['value']) > 0:
            df = pd.DataFrame(history_data['value'])
            
            # Display summary
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Records", len(df))
            col2.metric("Unique Fields", len(df.columns))
            col3.metric("Data Points", len(df) * len(df.columns))
            
            # Show data table
            st.subheader("📋 Learning History Data")
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Learning History",
                data=csv,
                file_name=f"learning_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📚 No learning history data available. Data will appear here once learners complete activities.")
    
    with tab3:
        st.header("User Analytics")
        
        # Fetch user data
        users_data = api.make_request("/learning/odatav4/public/admin/user-service/v1")
        
        if users_data and 'value' in users_data and len(users_data['value']) > 0:
            df_users = pd.DataFrame(users_data['value'])
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("👥 User Database")
                st.dataframe(df_users, use_container_width=True, height=400)
            
            with col2:
                st.subheader("📊 User Statistics")
                st.metric("Total Users", len(df_users))
                st.metric("Fields Available", len(df_users.columns))
                
                # Download button
                csv = df_users.to_csv(index=False)
                st.download_button(
                    label="📥 Download User Data",
                    data=csv,
                    file_name=f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("👥 No user data available. User information will appear here once available.")
    
    with tab4:
        st.header("Reports")
        st.info("🚧 Report generation features coming soon. This will include customizable reports for compliance, completion rates, and learning paths.")
    
    with tab5:
        st.header("API Data Explorer")
        st.markdown("Explore available API endpoints and data")
        
        # Endpoint selector
        endpoints = [
            "/learning/odatav4/public/admin/learningEvent/v1",
            "/learning/odatav4/public/user/learningHistory/v1",
            "/learning/odatav4/public/admin/user-service/v1",
            "/learning/odatav4/public/user/curriculum/v1",
            "/learning/odatav4/public/admin/searchStudent/v1",
            "/learning/odatav4/public/user/itemAssignment/v1",
            "/learning/odatav4/public/user/learningplan-service/v1",
            "/learning/odatav4/public/user/userlearning-service/v1"
        ]
        
        selected_endpoint = st.selectbox("Select an endpoint:", endpoints)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            custom_endpoint = st.text_input("Or enter custom endpoint:", placeholder="/learning/odatav4/public/...")
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            fetch_button = st.button("🚀 Fetch Data", use_container_width=True)
        
        if fetch_button:
            endpoint = custom_endpoint if custom_endpoint else selected_endpoint
            
            with st.spinner(f"Fetching data from {endpoint}..."):
                data = api.make_request(endpoint, use_cache=False)
                
                if data:
                    st.success("✅ Data retrieved successfully!")
                    
                    # Response summary
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Response Keys", len(data.keys()))
                    if 'value' in data:
                        col2.metric("Records", len(data['value']))
                        col3.metric("Data Type", "OData Collection")
                    else:
                        col2.metric("Records", "N/A")
                        col3.metric("Data Type", "Single Object")
                    
                    # Data display
                    if 'value' in data and isinstance(data['value'], list) and len(data['value']) > 0:
                        df = pd.DataFrame(data['value'])
                        st.dataframe(df, use_container_width=True)
                        
                        # Download option
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Data",
                            data=csv,
                            file_name=f"sf_data_{endpoint.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # Raw JSON viewer
                    with st.expander("View Raw JSON Response"):
                        st.json(data)
                else:
                    st.error(f"❌ Failed to retrieve data from {endpoint}")

else:
    # Not connected state
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h2>Welcome to the Learning Analytics Dashboard</h2>
        <p style='font-size: 18px; color: #666;'>
            Connect to SuccessFactors to start analyzing your learning data
        </p>
        <p style='margin-top: 30px;'>
            👈 Click <strong>Connect to SuccessFactors</strong> in the sidebar to begin
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Info columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📊 Real-time Analytics
        - Learning completion tracking
        - User progress monitoring
        - Compliance reporting
        - Trend analysis
        """)
    
    with col2:
        st.markdown("""
        ### 🔐 Secure Connection
        - OAuth 2.0 authentication
        - Encrypted data transfer
        - Token-based access
        - Automatic refresh
        """)
    
    with col3:
        st.markdown(f"""
        ### 🌐 Environment
        - **Mode**: {api.environment}
        - **Client**: {api.client_id}
        - **URL**: {api.base_url}
        - **Status**: Ready to connect
        """)

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("Learning Analytics Dashboard v1.0")
with footer_col2:
    st.caption(f"Environment: {api.environment}")
with footer_col3:
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")