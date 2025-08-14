#!/usr/bin/env python3
"""
SuccessFactors LMS Feature Tracker Dashboard
Tracks LMS features, their enablement status, and upcoming recommendations.
"""

import os
import json
from datetime import datetime

import requests
import streamlit as st

# Constants
FEATURES_SOURCE_URL = os.getenv("FEATURES_SOURCE_URL", "")
LOCAL_FEATURE_FILE = os.path.join("data", "features_sample.json")
ENABLED_FILE = os.path.join("data", "enabled_features.json")


@st.cache_data(ttl=3600)
def fetch_features():
    """Retrieve feature data from remote source with local fallback."""
    if FEATURES_SOURCE_URL:
        try:
            response = requests.get(FEATURES_SOURCE_URL, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:
            st.warning("Could not fetch latest features. Using local data.")
    with open(LOCAL_FEATURE_FILE, "r") as f:
        return json.load(f)


def load_enabled():
    """Load enablement data from local storage."""
    if os.path.exists(ENABLED_FILE):
        with open(ENABLED_FILE, "r") as f:
            return json.load(f)
    return {}


def save_enabled(data):
    """Persist enablement data to local storage."""
    os.makedirs(os.path.dirname(ENABLED_FILE), exist_ok=True)
    with open(ENABLED_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Initialize
st.set_page_config(page_title="LMS Feature Tracker", page_icon="🧭", layout="wide")

features = fetch_features()
enabled_info = load_enabled()

st.title("📚 SuccessFactors LMS Feature Tracker")
st.caption("Auto-updating view of LMS capabilities")

view = st.sidebar.radio("View", ["Feature Profiles", "Recommendations"])

if view == "Feature Profiles":
    feature_names = [f["name"] for f in features]
    selected_name = st.sidebar.selectbox("Select Feature", feature_names)
    feature = next(f for f in features if f["name"] == selected_name)

    st.header(feature["name"])
    st.markdown(f"**Status:** {feature.get('status', 'unknown').replace('_', ' ').title()}")

    enabled = enabled_info.get(feature["id"], {}).get("enabled", False)
    date_str = enabled_info.get(feature["id"], {}).get("date")
    enabled_date = datetime.fromisoformat(date_str) if date_str else datetime.today()

    enabled_checkbox = st.checkbox("Feature Enabled", enabled)
    date_input = st.date_input("Enabled Date", enabled_date)

    enabled_info[feature["id"]] = {
        "enabled": enabled_checkbox,
        "date": date_input.isoformat() if enabled_checkbox else None,
    }
    save_enabled(enabled_info)

    st.subheader("Description")
    st.write(feature["description"])
    st.subheader("Benefits")
    st.write(feature["benefits"])
    st.subheader("How to Leverage")
    st.write(feature["leverage"])
    st.subheader("User Experience")
    st.write(feature["user_experience"])
    st.subheader("Tips & Tricks")
    st.write(feature["tips"])
    st.markdown(f"[User Documentation]({feature['user_docs']})")
    st.markdown(f"[Admin Documentation]({feature['admin_docs']})")
else:
    st.header("Recommendations")
    upcoming = [f for f in features if f.get("status") == "coming_soon"]
    if upcoming:
        for feature in upcoming:
            st.markdown(f"### {feature['name']}")
            st.write(feature["description"])
            st.write(f"**Target Release:** {feature.get('release_date', 'TBD')}")
    else:
        st.write("No upcoming features at this time.")
