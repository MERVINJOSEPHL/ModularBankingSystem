# smart-bank-modular/pages/auth.py

import streamlit as st
import requests
import json

def handle_login(username, password, api_url):
    """Handles user login."""
    try:
        response = requests.post(
            f"{api_url}/auth/login",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state['auth_token'] = data.get("access_token")
            st.session_state['user_role'] = data.get("role")
            st.success(f"Login successful! Role: {data.get('role').capitalize()}")
            st.rerun()
        else:
            st.error(f"Login failed: {response.json().get('detail', 'Invalid credentials')}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API server. Ensure FastAPI is running.")

def handle_signup(data, api_url):
    """Handles user signup."""
    try:
        response = requests.post(
            f"{api_url}/auth/signup",
            json=data
        )
        if response.status_code == 200:
            st.success(f"Signup successful! User ID: {response.json()['user_id']}. Please log in.")
        else:
            st.error(f"Signup failed: {response.json().get('detail', 'An error occurred.')}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API server. Ensure FastAPI is running.")

def show_auth_page(api_url):
    """Renders the login and signup forms."""
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")

            if login_submitted:
                handle_login(login_username, login_password, api_url)

    with tab2:
        st.subheader("Register New User")
        with st.form("signup_form"):
            signup_username = st.text_input("Choose Username")
            signup_password = st.text_input("Choose Password", type="password")
            signup_role = st.selectbox("Select Role", ["customer", "admin", "auditor"])
            
            signup_data = {
                "username": signup_username,
                "password": signup_password,
                "role": signup_role
            }

            if signup_role == 'customer':
                st.info("Customer registration requires initial account details.")
                signup_data["initial_deposit"] = st.number_input("Initial Deposit Amount", min_value=1.0, value=100.0)
                signup_data["account_type"] = st.selectbox("Account Type", ["Saving", "Current", "FD"])
            else:
                signup_data["initial_deposit"] = 1.0 # Set dummy values for Pydantic validation bypass (if needed)
                signup_data["account_type"] = "Saving"

            signup_submitted = st.form_submit_button("Register")
            if signup_submitted:
                handle_signup(signup_data, api_url)