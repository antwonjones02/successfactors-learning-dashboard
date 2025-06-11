#!/usr/bin/env python3
"""
SuccessFactors Learning Dashboard Demo
This demonstrates the dashboard interface using simulated data.
Once authentication is resolved, this will connect to the actual API.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json

# Page config
st.set_page_config(
    page_title="SuccessFactors Learning Dashboard",
    page_icon="📚",
    layout="wide"
)

# Simulate API data
@st.cache_data
def generate_mock_learning_data():
    """Generate mock data similar to what we'd get from SuccessFactors API"""
    
    courses = [
        'Compliance Training 2024', 'Leadership Excellence', 'Data Analytics Fundamentals',
        'Cybersecurity Awareness', 'Project Management Basics', 'Customer Service Excellence',
        'Financial Planning', 'Diversity & Inclusion', 'Time Management', 'Communication Skills'
    ]
    
    departments = ['Sales', 'Engineering', 'Marketing', 'HR', 'Finance', 'Operations', 'IT']
    statuses = ['Completed', 'In Progress', 'Not Started', 'Overdue']
    
    data = []
    for i in range(500):
        status = random.choices(statuses, weights=[60, 25, 10, 5])[0]
        completion_date = None
        score = None
        
        if status == 'Completed':
            completion_date = datetime.now() - timedelta(days=random.randint(0, 180))
            score = random.randint(75, 100)
        elif status == 'In Progress':
            score = random.randint(20, 80)
        
        data.append({
            'userId': f'00{random.randint(100000, 999999)}',
            'userName': f'User {i+1}',
            'course': random.choice(courses),
            'department': random.choice(departments),
            'status': status,
            'completionDate': completion_date,
            'creditHours': random.randint(1, 8),
            'cpeHours': random.randint(0, 4),
            'score': score,
            'dueDate': datetime.now() + timedelta(days=random.randint(-30, 90))
        })
    
    return pd.DataFrame(data)

# Load data
df = generate_mock_learning_data()

# Title and description
st.title("📚 SuccessFactors Learning Dashboard")
st.markdown("*Demo Mode - Using simulated data*")

# Connection status
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.info("🔌 To connect to live data, configure your SuccessFactors credentials in the sidebar")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    with st.expander("API Credentials", expanded=False):
        client_id = st.text_input("Client ID", value="delta-sbx", type="default")
        client_secret = st.text_input("Client Secret", type="password")
        user_id = st.text_input("User ID", value="00780606")
        base_url = st.text_input("Base URL", value="https://delta-sandbox.plateau.com")
        
        if st.button("Test Connection"):
            st.warning("Authentication pending - using demo data")
    
    st.markdown("---")
    
    # Filters
    st.header("🔍 Filters")
    
    selected_dept = st.multiselect(
        "Department",
        options=df['department'].unique(),
        default=df['department'].unique()
    )
    
    selected_status = st.multiselect(
        "Status",
        options=df['status'].unique(),
        default=df['status'].unique()
    )
    
    date_range = st.date_input(
        "Date Range",
        value=(datetime.now() - timedelta(days=180), datetime.now()),
        max_value=datetime.now()
    )

# Filter data
filtered_df = df[
    (df['department'].isin(selected_dept)) &
    (df['status'].isin(selected_status))
]

# Key Metrics
st.markdown("## 📊 Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Learners",
        f"{filtered_df['userId'].nunique():,}",
        f"{filtered_df['userId'].nunique() - df['userId'].nunique():+,}"
    )

with col2:
    completed = len(filtered_df[filtered_df['status'] == 'Completed'])
    st.metric(
        "Courses Completed",
        f"{completed:,}",
        f"{int(completed * 0.15):+,}"
    )

with col3:
    completion_rate = (completed / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
    st.metric(
        "Completion Rate",
        f"{completion_rate:.1f}%",
        f"{completion_rate * 0.05:.1f}%"
    )

with col4:
    total_hours = filtered_df['creditHours'].sum()
    st.metric(
        "Total Credit Hours",
        f"{total_hours:,}",
        f"{int(total_hours * 0.1):+,}"
    )

with col5:
    avg_score = filtered_df[filtered_df['score'].notna()]['score'].mean()
    st.metric(
        "Average Score",
        f"{avg_score:.1f}%" if not pd.isna(avg_score) else "N/A",
        f"{2.3:.1f}%"
    )

# Charts
st.markdown("## 📈 Analytics")

col1, col2 = st.columns(2)

with col1:
    # Completion by Department
    dept_completion = filtered_df[filtered_df['status'] == 'Completed'].groupby('department').size().reset_index(name='count')
    fig1 = px.bar(
        dept_completion,
        x='department',
        y='count',
        title='Completions by Department',
        color='count',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Status Distribution
    status_dist = filtered_df['status'].value_counts().reset_index()
    fig2 = px.pie(
        status_dist,
        values='count',
        names='status',
        title='Learning Status Distribution',
        color_discrete_map={
            'Completed': '#2ecc71',
            'In Progress': '#f39c12',
            'Not Started': '#95a5a6',
            'Overdue': '#e74c3c'
        }
    )
    st.plotly_chart(fig2, use_container_width=True)

# Time series
completed_df = filtered_df[filtered_df['status'] == 'Completed'].copy()
if not completed_df.empty:
    completed_df['completion_month'] = completed_df['completionDate'].dt.to_period('M')
    monthly_completions = completed_df.groupby('completion_month').size().reset_index(name='count')
    monthly_completions['completion_month'] = monthly_completions['completion_month'].astype(str)
    
    fig3 = px.line(
        monthly_completions,
        x='completion_month',
        y='count',
        title='Monthly Completion Trend',
        markers=True
    )
    st.plotly_chart(fig3, use_container_width=True)

# Course popularity
st.markdown("## 🏆 Top Courses")
col1, col2 = st.columns(2)

with col1:
    top_courses = filtered_df['course'].value_counts().head(10).reset_index()
    fig4 = px.bar(
        top_courses,
        y='course',
        x='count',
        title='Most Popular Courses',
        orientation='h'
    )
    st.plotly_chart(fig4, use_container_width=True)

with col2:
    # Average score by course
    avg_scores = filtered_df[filtered_df['score'].notna()].groupby('course')['score'].mean().sort_values(ascending=False).head(10).reset_index()
    fig5 = px.bar(
        avg_scores,
        y='course',
        x='score',
        title='Average Score by Course',
        orientation='h',
        color='score',
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig5, use_container_width=True)

# Data Table
st.markdown("## 📋 Recent Learning Activities")

# Prepare display data
display_df = filtered_df.head(100).copy()
display_df['completionDate'] = display_df['completionDate'].dt.strftime('%Y-%m-%d')
display_df['dueDate'] = display_df['dueDate'].dt.strftime('%Y-%m-%d')

# Select columns to display
display_columns = ['userId', 'userName', 'course', 'department', 'status', 
                  'completionDate', 'score', 'creditHours', 'dueDate']

st.dataframe(
    display_df[display_columns],
    use_container_width=True,
    hide_index=True,
    column_config={
        'userId': 'User ID',
        'userName': 'Name',
        'course': 'Course',
        'department': 'Department',
        'status': st.column_config.Column(
            'Status',
            help='Current learning status'
        ),
        'completionDate': 'Completed',
        'score': st.column_config.ProgressColumn(
            'Score',
            help='Assessment score',
            format='%d%%',
            min_value=0,
            max_value=100
        ),
        'creditHours': 'Credit Hours',
        'dueDate': 'Due Date'
    }
)

# Export functionality
st.markdown("## 💾 Export Data")
col1, col2, col3 = st.columns(3)

with col1:
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=f'learning_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv'
    )

with col2:
    json_str = filtered_df.to_json(orient='records', date_format='iso')
    st.download_button(
        label="📥 Download as JSON",
        data=json_str,
        file_name=f'learning_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        mime='application/json'
    )

# Footer
st.markdown("---")
st.markdown("*Dashboard created for SuccessFactors Learning data visualization*")