"""
Authentication UI Module

Handles login/logout interface for the Library Assessment Decision Support System.
"""

import streamlit as st
from modules import auth


def show_login_page():
    """Display login page with authentication form."""
    st.title("Library Assessment Assistant")
    st.markdown("### Welcome")
    st.markdown("Please log in to access the system.")
    
    # Create login form
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Log In")
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                # Attempt authentication with rate limiting
                is_valid, error_msg = auth.authenticate(username, password)
                if is_valid:
                    auth.login_user(st.session_state, username)
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    # Display specific error message from rate limiting
                    st.error(error_msg or "Invalid username or password.")
    
    # First-time setup instructions
    st.markdown("---")
    st.markdown("#### First Time Setup")
    st.markdown("""
    If this is your first time using the system, you need to create a user account.
    Run the following command in your terminal:
    
    ```bash
    python -c "from modules.auth import create_user; create_user('your_username', 'your_password')"
    ```
    
    Replace `your_username` and `your_password` with your desired credentials.
    """)


def show_logout_button():
    """Display logout button in sidebar."""
    if st.sidebar.button("Logout"):
        auth.logout_user(st.session_state)
        st.rerun()
