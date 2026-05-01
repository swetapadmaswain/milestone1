"""
Restaurant Recommendation System - Streamlit UI
Phase 5: Lightweight deployment interface
"""

import os
import uuid
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="DineSmart - Restaurant Recommendations",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .restaurant-card {
        background-color: #f9fafb;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }
    .restaurant-name {
        font-size: 1.5rem;
        font-weight: bold;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    .restaurant-meta {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .explanation-box {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin-top: 0.5rem;
        border-radius: 0 8px 8px 0;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    .confidence-high {
        background-color: #d1fae5;
        color: #065f46;
    }
    .confidence-medium {
        background-color: #fef3c7;
        color: #92400e;
    }
    .confidence-low {
        background-color: #f3f4f6;
        color: #4b5563;
    }
    .score-badge {
        background-color: #e0e7ff;
        color: #3730a3;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    .rank-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-weight: bold;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = f"streamlit_{uuid.uuid4().hex[:8]}"
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "last_search" not in st.session_state:
    st.session_state.last_search = None


def get_recommendations(location, budget, cuisine, min_rating, top_n=5):
    """Call backend API to get recommendations."""
    try:
        payload = {
            "location": location.lower().strip(),
            "budget": budget,
            "preferred_cuisine": cuisine if cuisine != "Any" else "",
            "min_rating": min_rating,
            "top_n": top_n,
            "session_id": st.session_state.session_id
        }
        
        response = requests.post(
            f"{BACKEND_URL}/recommend",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The backend might be busy. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to backend. Please ensure the backend server is running.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


def submit_feedback(restaurant_name, feedback_type, cuisine, location, cost):
    """Submit user feedback to backend."""
    try:
        signal_map = {
            "👍 Like": (1.0, "like"),
            "👎 Dislike": (-1.0, "dislike"),
            "⭐ Favorite": (2.0, "favorite"),
            "🚫 Not Relevant": (-2.0, "not_relevant")
        }
        
        value, signal_name = signal_map.get(feedback_type, (0.0, "neutral"))
        
        payload = {
            "restaurant_name": restaurant_name,
            "signal_name": signal_name,
            "signal_type": "explicit",
            "value": value,
            "session_id": st.session_state.session_id,
            "cuisine": cuisine,
            "location": location,
            "estimated_cost": cost
        }
        
        response = requests.post(
            f"{BACKEND_URL}/feedback",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.warning(f"Could not submit feedback: {str(e)}")
        return False


def check_backend_health():
    """Check if backend is healthy."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


# Sidebar
with st.sidebar:
    st.markdown("### 🍽️ DineSmart")
    st.markdown("---")
    
    # Backend status
    if check_backend_health():
        st.success("🟢 Backend Connected")
    else:
        st.error("🔴 Backend Offline")
        st.info(f"Expected at: {BACKEND_URL}")
    
    st.markdown("---")
    st.markdown(f"**Session ID:** `{st.session_state.session_id}`")
    
    # About section
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    AI-powered restaurant recommendation system using:
    - 🤖 Groq LLM for explanations
    - 📊 Personalized scoring
    - ⚡ FastAPI backend
    """)


# Main content
st.markdown('<p class="main-header">🍽️ DineSmart</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Discover the perfect restaurant with AI-powered recommendations</p>', unsafe_allow_html=True)

# Search form
st.markdown("### 🔍 Find Your Perfect Restaurant")

col1, col2, col3, col4 = st.columns(4)

with col1:
    location = st.text_input(
        "📍 Location",
        placeholder="e.g., whitefield, btm, indiranagar",
        help="Enter a Bangalore locality (lowercase works best)"
    )

with col2:
    budget = st.selectbox(
        "💰 Budget",
        ["low", "medium", "high"],
        index=1,
        help="Select your budget range"
    )

with col3:
    cuisine = st.selectbox(
        "🍜 Cuisine",
        ["Any", "North Indian", "South Indian", "Chinese", "Italian", "Mexican", "Thai", "Continental", "Fast Food"],
        help="Select preferred cuisine or Any for all"
    )

with col4:
    min_rating = st.slider(
        "⭐ Min Rating",
        min_value=1.0,
        max_value=5.0,
        value=3.5,
        step=0.5,
        help="Minimum restaurant rating"
    )

# Top N selector
result_count = st.slider("Number of recommendations", min_value=1, max_value=10, value=5)

# Search button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    search_clicked = st.button("🔎 Get Recommendations", use_container_width=True, type="primary")

# Handle search
if search_clicked:
    if not location.strip():
        st.warning("⚠️ Please enter a location to search.")
    else:
        with st.spinner("🤖 Finding the best restaurants for you..."):
            result = get_recommendations(location, budget, cuisine, min_rating, result_count)
            
            if result:
                st.session_state.recommendations = result.get("recommendations", [])
                st.session_state.last_search = {
                    "location": location,
                    "budget": budget,
                    "cuisine": cuisine,
                    "min_rating": min_rating
                }

# Display results
if st.session_state.recommendations:
    st.markdown("---")
    st.markdown(f"### 🏆 Top {len(st.session_state.recommendations)} Recommendations")
    
    if st.session_state.last_search:
        ls = st.session_state.last_search
        st.markdown(f"**Location:** {ls['location']} | **Budget:** {ls['budget']} | **Cuisine:** {ls['cuisine']} | **Min Rating:** {ls['min_rating']}")
    
    st.markdown("---")
    
    for idx, restaurant in enumerate(st.session_state.recommendations, 1):
        with st.container():
            st.markdown(f"""
            <div class="restaurant-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span class="rank-badge">#{idx}</span>
                        <span class="restaurant-name">{restaurant['restaurant_name']}</span>
                    </div>
                    <span class="score-badge">Score: {restaurant['final_score']:.2f}</span>
                </div>
                <div class="restaurant-meta">
                    📍 {restaurant['location']} • ⭐ {restaurant['rating']:.1f}/5 • 💰 Rs. {restaurant['estimated_cost']:.0f} • 🍽️ {restaurant['cuisine']}
                </div>
                <div class="explanation-box">
                    <strong>💡 Why this restaurant?</strong><br>
                    {restaurant['explanation']}
                </div>
                <div style="margin-top: 0.5rem;">
                    <span class="confidence-badge confidence-{restaurant['confidence']}">
                        {restaurant['confidence'].upper()} CONFIDENCE
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Feedback buttons
            feedback_cols = st.columns(4)
            feedback_options = ["👍 Like", "👎 Dislike", "⭐ Favorite", "🚫 Not Relevant"]
            
            for i, option in enumerate(feedback_options):
                with feedback_cols[i]:
                    if st.button(option, key=f"feedback_{idx}_{i}", use_container_width=True):
                        success = submit_feedback(
                            restaurant['restaurant_name'],
                            option,
                            restaurant['cuisine'],
                            restaurant['location'],
                            restaurant['estimated_cost']
                        )
                        if success:
                            st.success(f"Feedback recorded! {option}")
            
            st.markdown("---")

elif search_clicked and not st.session_state.recommendations:
    st.info("🤔 No restaurants found matching your criteria. Try:")
    st.markdown("""
    - Different location (try: whitefield, btm, hsr, indiranagar)
    - Lower minimum rating
    - Different budget range
    - Different cuisine type
    """)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #6b7280;'>Powered by FastAPI + Groq LLM + Streamlit</p>", unsafe_allow_html=True)
