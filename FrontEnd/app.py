import streamlit as st
import requests
from pages import customer_dashboard, admin_dashboard, auditor_dashboard, auth
import json

API_BASE_URL = "http://127.0.0.1:8000/api"

def initialize_state():
    """Initializes necessary session state variables."""
    if 'auth_token' not in st.session_state:
        st.session_state['auth_token'] = None
    if 'user_role' not in st.session_state:
        st.session_state['user_role'] = None
    if 'api_url' not in st.session_state:
        st.session_state['api_url'] = API_BASE_URL
        
def get_headers():
    """Returns headers including the authorization token if available."""
    headers = {"Content-Type": "application/json"}
    if st.session_state['auth_token']:
        headers["Authorization"] = f"Bearer {st.session_state['auth_token']}"
    return headers

def logout():
    """Clears session state and resets the view."""
    st.session_state['auth_token'] = None
    st.session_state['user_role'] = None
    st.success("Logged out successfully!")

def main_app():
    st.set_page_config(
        page_title="Smart Bank Modular POC",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_state()

    st.sidebar.title("Smart Bank Navigation")
    
    if not st.session_state['auth_token']:
        st.sidebar.empty()
        st.title("🏦 Smart Bank: Login / Signup")
        auth.show_auth_page(API_BASE_URL)
        
    else:
        st.sidebar.success(f"Logged in as: {st.session_state['user_role'].capitalize()}")
        st.sidebar.button("Logout", on_click=logout)
        
        role = st.session_state['user_role']

        if role == 'customer':
            customer_dashboard.show_dashboard(API_BASE_URL, get_headers)
        elif role == 'admin':
            admin_dashboard.show_dashboard(API_BASE_URL, get_headers)
        elif role == 'auditor':
            auditor_dashboard.show_dashboard(API_BASE_URL, get_headers)
        else:
            st.error("Unknown user role. Please log out and try again.")

if __name__ == "__main__":
    import os
    if not os.path.exists("pages"):
        os.makedirs("pages")
    
    main_app()