#!/usr/bin/env python3
"""
SuccessFactors Learning Dashboard - Fixed Version
Improved button handling and connection management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="SuccessFactors Learning Dashboard",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'token_expiry' not in st.session_state:
    st.session_state.token_expiry = None
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "disconnected"
if 'last_error' not in st.session_state:
    st.session_state.last_error = None
if 'auth_attempted' not in st.session_state:
    st.session_state.auth_attempted = False

class SuccessFactorsAPI:
    def __init__(self):
        # Load credentials with defaults
        self.client_id = os.getenv("SF_CLIENT_ID", "delta-sbx")
        self.client_secret = os.getenv("SF_CLIENT_SECRET", "0c49e9fe2aea9c80fef439b980c4657e152f15ae7ddaaedec7a098ef669d26a6219b3121819e9692b5392317360b7198")
        self.user_id = os.getenv("SF_USER_ID", "00780606")
        self.base_url = os.getenv("SF_BASE_URL", "https://delta-sandbox.plateau.com")
    
    def authenticate(self):
        """Get OAuth token"""
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
                
        except requests.exceptions.Timeout:
            st.session_state.connection_status = "error"
            st.session_state.last_error = "Connection timeout - please check your network"
            return False
        except requests.exceptions.ConnectionError:
            st.session_state.connection_status = "error"
            st.session_state.last_error = "Connection error - please check your network"
            return False
        except Exception as e:
            st.session_state.connection_status = "error"
            st.session_state.last_error = f"Unexpected error: {str(e)}"
            return False
    
    def make_request(self, endpoint):
        """Make authenticated API request"""
        if not st.session_state.access_token or datetime.now() > st.session_state.token_expiry:
            if not self.authenticate():
                return None
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {st.session_state.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                st.session_state.last_error = f"API error: {response.status_code}"
                return None
        except Exception as e:
            st.session_state.last_error = f"Request failed: {str(e)}"
            return None

# Initialize API
api = SuccessFactorsAPI()

# Title
st.title("📚 SuccessFactors Learning Dashboard")
st.markdown("*Live Data Connection - Fixed Version*")

# Sidebar
with st.sidebar:
    st.header("🔌 Connection Manager")
    
    # Connection status display
    if st.session_state.connection_status == "disconnected":
        st.error("⚠️ Not Connected")
    elif st.session_state.connection_status == "connecting":
        st.warning("🔄 Connecting...")
    elif st.session_state.connection_status == "connected":
        st.success("✅ Connected")
        if st.session_state.token_expiry:
            remaining = (st.session_state.token_expiry - datetime.now()).total_seconds() / 60
            st.caption(f"Token expires in {remaining:.0f} minutes")
    elif st.session_state.connection_status == "error":
        st.error("❌ Connection Failed")
    
    # Show last error if any
    if st.session_state.last_error:
        with st.expander("Last Error", expanded=True):
            st.error(st.session_state.last_error)
    
    st.markdown("---")
    
    # Connection button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔌 Connect", disabled=st.session_state.connection_status == "connecting"):
            st.session_state.auth_attempted = True
            with st.spinner("Authenticating..."):
                if api.authenticate():
                    st.success("✓ Connected!")
                    st.rerun()
                else:
                    st.error("✗ Failed to connect")
    
    with col2:
        if st.button("🔄 Refresh", disabled=st.session_state.connection_status != "connected"):
            st.rerun()
    
    # Disconnect button
    if st.session_state.connection_status == "connected":
        if st.button("🔌 Disconnect"):
            st.session_state.access_token = None
            st.session_state.token_expiry = None
            st.session_state.connection_status = "disconnected"
            st.rerun()
    
    st.markdown("---")
    
    # Debug section
    with st.expander("🔧 Debug Info"):
        st.write("**Status:**", st.session_state.connection_status)
        st.write("**Token:**", "Present" if st.session_state.access_token else "None")
        st.write("**Expiry:**", st.session_state.token_expiry.strftime("%H:%M:%S") if st.session_state.token_expiry else "N/A")
        
        st.markdown("**Credentials:**")
        st.code(f"""
Client ID: {api.client_id}
User ID: {api.user_id}
Base URL: {api.base_url}
Secret: ***hidden***
        """)

# Main content area
if st.session_state.connection_status == "connected":
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Analytics", "🔍 Explorer", "📋 Logs"])
    
    with tab1:
        st.header("Dashboard Overview")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        # Fetch some data
        with st.spinner("Loading dashboard data..."):
            # Try different endpoints
            endpoints_to_try = [
                ("/learning/odatav4/public/admin/learningEvent/v1", "Learning Events"),
                ("/learning/odatav4/public/user/learningHistory/v1", "Learning History"),
                ("/learning/odatav4/public/admin/user-service/v1", "Users"),
                ("/learning/odatav4/public/user/curriculum/v1", "Curriculum Items")
            ]
            
            metrics = []
            for endpoint, label in endpoints_to_try:
                data = api.make_request(endpoint)
                if data and 'value' in data:
                    count = len(data['value'])
                    metrics.append((label, count))
                else:
                    metrics.append((label, "No data"))
            
            # Display metrics
            for i, (label, value) in enumerate(metrics):
                cols = [col1, col2, col3, col4]
                with cols[i]:
                    if isinstance(value, int):
                        st.metric(label, f"{value:,}")
                    else:
                        st.metric(label, value)
        
        # Data preview section
        st.markdown("---")
        st.subheader("📊 Quick Data Preview")
        
        # Show learning history if available
        history_data = api.make_request("/learning/odatav4/public/user/learningHistory/v1")
        if history_data and 'value' in history_data and len(history_data['value']) > 0:
            df = pd.DataFrame(history_data['value'])
            st.write(f"Found {len(df)} learning history records")
            
            # Show first few records
            with st.expander("View Learning History Data"):
                st.dataframe(df.head(10))
                
                # Show column info
                st.write("**Available columns:**")
                st.write(", ".join(df.columns.tolist()))
        else:
            st.info("No learning history data available in sandbox")
    
    with tab2:
        st.header("Analytics")
        st.info("Analytics features will be available once we have data from the production environment")
    
    with tab3:
        st.header("API Explorer")
        st.markdown("Test different API endpoints to see what data is available")
        
        # Predefined endpoints
        endpoint_options = [
            "/learning/odatav4/public/admin/learningEvent/v1",
            "/learning/odatav4/public/user/learningHistory/v1",
            "/learning/odatav4/public/admin/user-service/v1",
            "/learning/odatav4/public/user/curriculum/v1",
            "/learning/odatav4/public/admin/searchStudent/v1",
            "/learning/odatav4/public/user/itemAssignment/v1",
            "/learning/odatav4/public/user/learningplan-service/v1",
            "/learning/odatav4/public/user/userlearning-service/v1"
        ]
        
        selected_endpoint = st.selectbox("Select an endpoint to test:", endpoint_options)
        
        # Custom endpoint input
        custom_endpoint = st.text_input("Or enter a custom endpoint:")
        
        # Test button
        if st.button("🚀 Test Endpoint"):
            endpoint = custom_endpoint if custom_endpoint else selected_endpoint
            
            with st.spinner(f"Testing {endpoint}..."):
                start_time = time.time()
                data = api.make_request(endpoint)
                elapsed = time.time() - start_time
                
                if data:
                    st.success(f"✅ Success! (Response time: {elapsed:.2f}s)")
                    
                    # Show response structure
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.write("**Response Info:**")
                        if 'value' in data:
                            st.write(f"- Records: {len(data['value'])}")
                        st.write(f"- Keys: {', '.join(data.keys())}")
                    
                    with col2:
                        # Raw JSON viewer
                        with st.expander("View Raw JSON"):
                            st.json(data)
                    
                    # DataFrame view if applicable
                    if 'value' in data and isinstance(data['value'], list) and len(data['value']) > 0:
                        st.subheader("Data Table View")
                        df = pd.DataFrame(data['value'])
                        st.dataframe(df)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv,
                            file_name=f"sf_data_{endpoint.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                else:
                    st.error(f"❌ Failed to retrieve data from {endpoint}")
    
    with tab4:
        st.header("Connection Logs")
        st.markdown("Recent API activity and debugging information")
        
        # Show current session info
        with st.expander("Session Information", expanded=True):
            st.write("**Connection established at:**", 
                     (st.session_state.token_expiry - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S") 
                     if st.session_state.token_expiry else "N/A")
            st.write("**Token expires at:**", 
                     st.session_state.token_expiry.strftime("%Y-%m-%d %H:%M:%S") 
                     if st.session_state.token_expiry else "N/A")
            st.write("**Base URL:**", api.base_url)
            st.write("**Client ID:**", api.client_id)

else:
    # Not connected state
    st.info("👈 Click 'Connect' in the sidebar to connect to SuccessFactors")
    
    # Show helpful information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🔐 Connection Details
        
        This dashboard connects to your SuccessFactors sandbox using:
        - **OAuth 2.0** authentication
        - **Client credentials** grant type
        - **Admin** user permissions
        
        The connection is secure and tokens expire after 1 hour.
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Available Data
        
        Once connected, you can access:
        - Learning history and completions
        - User profiles and organizational data
        - Course and curriculum information
        - Assignment and enrollment data
        
        All data is retrieved in real-time from the API.
        """)
    
    # Troubleshooting section
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **If the Connect button doesn't work:**
        
        1. **Check your network connection** - Ensure you can access the internet
        2. **Verify credentials** - The .env file should contain valid credentials
        3. **Check the base URL** - Make sure the sandbox URL is correct
        4. **Look for errors** - Check the sidebar for any error messages
        
        **Current configuration:**
        """)
        st.code(f"""
Client ID: {api.client_id}
User ID: {api.user_id}
Base URL: {api.base_url}
        """)

# Footer
st.markdown("---")
st.markdown("*SuccessFactors Learning Dashboard v2.0 - Enhanced Connection Management*")