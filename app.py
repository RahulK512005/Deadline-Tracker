"""Deadline Tracker - AI-Powered Academic Productivity Application for Students."""
import streamlit as st
import os
import sys

# Ensure local workspace packages are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import init_db, get_setting
from services.deadline_service import DeadlineService
from services.gemini_service import GeminiService
from views.dashboard_view import render_dashboard
from views.extract_view import render_extract_page
from views.all_deadlines_view import render_all_deadlines_page
from views.calendar_view import render_calendar_page
from views.notifications_view import render_notifications_page
from views.settings_view import render_settings_page


# Configure Page
st.set_page_config(
    page_title="Deadline Tracker | Academic Productivity",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Modern Clean Aesthetic
st.markdown(
    """
    <style>
    /* Main container and font */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Clean Card Layouts */
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.15s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Sidebar polish */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Metrics block styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    /* Headers */
    h1, h2, h3, h4 {
        letter-spacing: -0.02em;
    }

    /* Hide default header decor */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Ensure Database is Initialized
init_db()

# Services initialization
deadline_svc = DeadlineService()
custom_gemini_key = get_setting("gemini_api_key", "")
gemini_svc = GeminiService(api_key=custom_gemini_key or None)

# Student Name from settings
student_name = get_setting("student_name", "Student")

# Sidebar Navigation
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <div style="background: #2563eb; color: white; width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem;">
                📚
            </div>
            <div>
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #f8fafc;">Deadline Tracker</h3>
                <div style="font-size: 0.75rem; color: #94a3b8;">AI Academic Planner</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "🔍 Extract Deadlines",
            "📋 All Deadlines",
            "🗓️ Calendar",
            "🔔 Notifications",
            "⚙️ Settings",
        ],
        label_visibility="collapsed"
    )

    st.divider()

    # Quick Glance Sidebar Stats
    stats = deadline_svc.get_statistics()
    st.markdown("##### 📌 Quick Summary")
    st.markdown(
        f"""
        - 🔴 **Due Today:** {stats['due_today']}
        - 🟡 **This Week:** {stats['due_this_week']}
        - ⚠️ **Overdue:** {stats['overdue']}
        - 🔵 **Upcoming:** {stats['total_upcoming']}
        """
    )

    st.divider()
    st.caption("Powered by Google Gemini 2.5 Flash Multimodal AI.")


# Render Selected Page
if page == "📊 Dashboard":
    render_dashboard(deadline_svc, student_name=student_name)
elif page == "🔍 Extract Deadlines":
    render_extract_page(deadline_svc, gemini_svc)
elif page == "📋 All Deadlines":
    render_all_deadlines_page(deadline_svc)
elif page == "🗓️ Calendar":
    render_calendar_page(deadline_svc)
elif page == "🔔 Notifications":
    render_notifications_page(deadline_svc)
elif page == "⚙️ Settings":
    render_settings_page(deadline_svc, gemini_svc)
