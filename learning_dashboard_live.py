#!/usr/bin/env python3
"""
SuccessFactors Learning Dashboard - Live Data Version
Connects to the actual SuccessFactors API
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

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="SuccessFactors Learning Dashboard",
    page_icon="📚",
    layout="wide"
)

# Initialize session state for token
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
    st.session_state.token_expiry = None

class SuccessFactorsAPI:
    def __init__(self):
        # Try to load from environment first
        self.client_id = os.getenv("SF_CLIENT_ID", "delta-sbx")
        self.client_secret = os.getenv("SF_CLIENT_SECRET", "0c49e9fe2aea9c80fef439b980c4657e152f15ae7ddaaedec7a098ef669d26a6219b3121819e9692b5392317360b7198")
        self.user_id = os.getenv("SF_USER_ID", "00780606")
        self.base_url = os.getenv("SF_BASE_URL", "https://delta-sandbox.plateau.com")
        
        # Debug: Check if credentials are loaded
        if not all([self.client_id, self.client_secret, self.user_id, self.base_url]):
            st.warning("⚠️ Missing credentials. Please check your .env file.")
            st.write("Loaded values:")
            st.write(f"- Client ID: {'✓' if self.client_id else '✗ Missing'}")
            st.write(f"- Client Secret: {'✓' if self.client_secret else '✗ Missing'}")
            st.write(f"- User ID: {'✓' if self.user_id else '✗ Missing'}")
            st.write(f"- Base URL: {'✓' if self.base_url else '✗ Missing'}")
    
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
            with st.expander("Debug Information", expanded=True):
                st.write("**Token URL:**", token_url)
                st.write("**Client ID:**", self.client_id)
                st.write("**User ID:**", self.user_id)
                st.write("**Payload:**")
                st.json({k: v if k != 'client_secret' else '***hidden***' for k, v in payload.items()})
            
            response = requests.post(token_url, json=payload, headers={"Content-Type": "application/json"})
            
            if response.status_code == 200:
                token_data = response.json()
                st.session_state.access_token = token_data.get("access_token")
                st.session_state.token_expiry = datetime.now() + timedelta(hours=1)
                return True
            else:
                st.error(f"Authentication failed with status {response.status_code}")
                st.error(f"Response: {response.text}")
                
        except Exception as e:
            st.error(f"Authentication exception: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
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
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"API request failed: {str(e)}")
        return None

# Initialize API
api = SuccessFactorsAPI()

# Title and description
st.title("📚 SuccessFactors Learning Dashboard")
st.markdown("*Live Data Connection*")

# Connection status in sidebar
with st.sidebar:
    st.header("🔌 Connection Status")
    
    if st.button("Connect to SuccessFactors"):
        with st.spinner("Authenticating..."):
            if api.authenticate():
                st.success("✓ Connected successfully!")
            else:
                st.error("✗ Connection failed")
    
    if st.session_state.access_token:
        st.success("✓ Connected")
        if st.session_state.token_expiry:
            remaining = (st.session_state.token_expiry - datetime.now()).total_seconds() / 60
            st.caption(f"Token expires in {remaining:.0f} minutes")
    else:
        st.warning("⚠️ Not connected")
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()

# Main content
if st.session_state.access_token:
    # Try to fetch data from various endpoints
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Learning History", "👥 Users", "🔍 Data Explorer"])
    
    with tab1:
        st.header("Learning Dashboard Overview")
        
        col1, col2, col3 = st.columns(3)
        
        # Try to get learning events
        learning_events = api.make_request("/learning/odatav4/public/admin/learningEvent/v1")
        if learning_events and 'value' in learning_events:
            events_count = len(learning_events['value'])
            col1.metric("Learning Events", events_count)
        else:
            col1.metric("Learning Events", "No data")
        
        # Try to get users
        users = api.make_request("/learning/odatav4/public/admin/user-service/v1")
        if users and 'value' in users:
            users_count = len(users['value'])
            col2.metric("Users", users_count)
        else:
            col2.metric("Users", "No data")
        
        # Try to get learning history
        history = api.make_request("/learning/odatav4/public/user/learningHistory/v1")
        if history and 'value' in history:
            history_count = len(history['value'])
            col3.metric("Learning Records", history_count)
        else:
            col3.metric("Learning Records", "No data")
    
    with tab2:
        st.header("Learning History")
        
        history_data = api.make_request("/learning/odatav4/public/user/learningHistory/v1")
        if history_data and 'value' in history_data and len(history_data['value']) > 0:
            df = pd.DataFrame(history_data['value'])
            
            # Display the data
            st.subheader("Raw Data")
            st.dataframe(df)
            
            # Show available columns
            st.subheader("Available Fields")
            st.write(df.columns.tolist())
            
            # Basic visualizations if data exists
            if len(df) > 0:
                st.subheader("Data Analysis")
                
                # Try to create charts based on available columns
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
                if numeric_cols:
                    col = st.selectbox("Select numeric column for histogram", numeric_cols)
                    fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                    st.plotly_chart(fig)
                
                # Count by categorical columns
                object_cols = df.select_dtypes(include=['object']).columns.tolist()
                if object_cols:
                    col = st.selectbox("Select categorical column for counts", object_cols)
                    value_counts = df[col].value_counts().head(10)
                    fig = px.bar(x=value_counts.index, y=value_counts.values, 
                                title=f"Top 10 {col} Values")
                    st.plotly_chart(fig)
        else:
            st.info("No learning history data available")
    
    with tab3:
        st.header("Users")
        
        users_data = api.make_request("/learning/odatav4/public/admin/user-service/v1")
        if users_data and 'value' in users_data and len(users_data['value']) > 0:
            df = pd.DataFrame(users_data['value'])
            st.dataframe(df)
        else:
            st.info("No user data available")
    
    with tab4:
        st.header("Data Explorer")
        st.markdown("Test different API endpoints")
        
        # Predefined endpoints
        endpoint_options = [
            "/learning/odatav4/public/admin/learningEvent/v1",
            "/learning/odatav4/public/user/learningHistory/v1",
            "/learning/odatav4/public/admin/user-service/v1",
            "/learning/odatav4/public/user/curriculum/v1",
            "/learning/odatav4/public/admin/searchStudent/v1",
            "/learning/odatav4/public/user/itemAssignment/v1"
        ]
        
        selected_endpoint = st.selectbox("Select endpoint", endpoint_options)
        
        # Custom endpoint
        custom_endpoint = st.text_input("Or enter custom endpoint")
        
        if st.button("Fetch Data"):
            endpoint = custom_endpoint if custom_endpoint else selected_endpoint
            
            with st.spinner(f"Fetching data from {endpoint}..."):
                data = api.make_request(endpoint)
                
                if data:
                    st.success("✓ Data retrieved successfully!")
                    
                    # Show raw JSON
                    with st.expander("Raw JSON Response"):
                        st.json(data)
                    
                    # If it has value array, show as dataframe
                    if 'value' in data and isinstance(data['value'], list):
                        st.subheader(f"Records: {len(data['value'])}")
                        if len(data['value']) > 0:
                            df = pd.DataFrame(data['value'])
                            st.dataframe(df)
                            
                            # Download button
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="Download as CSV",
                                data=csv,
                                file_name=f"sf_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                else:
                    st.error("Failed to retrieve data")
else:
    # Not connected
    st.info("👈 Please connect to SuccessFactors using the sidebar")
    
    # Show connection info
    with st.expander("Connection Details"):
        st.markdown("""
        **Current Configuration:**
        - Client ID: `delta-sbx`
        - User ID: `00780606`
        - Base URL: `https://delta-sandbox.plateau.com`
        
        The dashboard will connect using OAuth 2.0 authentication.
        """)

# Footer
st.markdown("---")
st.markdown("*SuccessFactors Learning Dashboard - Real-time data visualization*")