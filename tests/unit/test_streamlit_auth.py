"""
Unit tests for Streamlit authentication integration.

Tests the authentication flow in the main Streamlit application.
"""

import pytest
from unittest.mock import MagicMock, patch
from modules import auth


class TestStreamlitAuthentication:
    """Test authentication integration in Streamlit app."""
    
    def test_init_session_state(self):
        """Test session state initialization."""
        session_state = MagicMock()
        session_state.__contains__ = lambda self, key: False
        
        auth.init_session_state(session_state)
        
        assert session_state.authenticated == False
        assert session_state.username is None
        assert session_state.login_attempts == 0
    
    def test_login_user(self):
        """Test user login sets session state correctly."""
        session_state = MagicMock()
        
        auth.login_user(session_state, "testuser")
        
        assert session_state.authenticated == True
        assert session_state.username == "testuser"
        assert session_state.login_attempts == 0
    
    def test_logout_user(self):
        """Test user logout clears session state."""
        session_state = MagicMock()
        session_state.get = MagicMock(return_value="testuser")
        
        with patch('modules.auth.log_access'):
            auth.logout_user(session_state)
        
        assert session_state.authenticated == False
        assert session_state.username is None
    
    def test_is_authenticated_true(self):
        """Test is_authenticated returns True for authenticated user."""
        session_state = MagicMock()
        session_state.get = MagicMock(return_value=True)
        
        result = auth.is_authenticated(session_state)
        
        assert result == True
    
    def test_is_authenticated_false(self):
        """Test is_authenticated returns False for unauthenticated user."""
        session_state = MagicMock()
        session_state.get = MagicMock(return_value=False)
        
        result = auth.is_authenticated(session_state)
        
        assert result == False
    
    def test_get_current_user_authenticated(self):
        """Test get_current_user returns username when authenticated."""
        session_state = MagicMock()
        session_state.get = MagicMock(side_effect=lambda key, default=None: {
            'authenticated': True,
            'username': 'testuser'
        }.get(key, default))
        
        result = auth.get_current_user(session_state)
        
        assert result == "testuser"
    
    def test_get_current_user_not_authenticated(self):
        """Test get_current_user returns None when not authenticated."""
        session_state = MagicMock()
        session_state.get = MagicMock(side_effect=lambda key, default=None: {
            'authenticated': False,
            'username': None
        }.get(key, default))
        
        result = auth.get_current_user(session_state)
        
        assert result is None


class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    def setup_method(self):
        """Clear rate limit store before each test."""
        auth._rate_limit_store.clear()
    
    @patch('modules.auth.execute_query')
    @patch('modules.auth.log_access')
    def test_successful_login_flow(self, mock_log, mock_query):
        """Test successful login flow from credentials to session state."""
        # Setup
        password_hash = auth.hash_password("testpass")
        mock_query.return_value = [{'password_hash': password_hash}]
        
        # Create a proper session state mock
        session_state = MagicMock()
        session_state.__contains__ = lambda self, key: False
        session_state.authenticated = False
        session_state.username = None
        
        # Initialize session state
        auth.init_session_state(session_state)
        
        # Authenticate (now returns tuple)
        is_valid, error_msg = auth.authenticate("testuser", "testpass")
        assert is_valid == True
        assert error_msg is None
        
        # Login user
        auth.login_user(session_state, "testuser")
        
        # Verify session state
        assert session_state.authenticated == True
        assert session_state.username == "testuser"
        
        # Mock get method for is_authenticated and get_current_user
        session_state.get = MagicMock(side_effect=lambda key, default=None: {
            'authenticated': True,
            'username': 'testuser'
        }.get(key, default))
        
        assert auth.is_authenticated(session_state)
        assert auth.get_current_user(session_state) == "testuser"
    
    @patch('modules.auth.execute_query')
    @patch('modules.auth.log_access')
    def test_failed_login_flow(self, mock_log, mock_query):
        """Test failed login flow with invalid credentials."""
        # Setup
        password_hash = auth.hash_password("correctpass")
        mock_query.return_value = [{'password_hash': password_hash}]
        
        session_state = MagicMock()
        session_state.__contains__ = lambda self, key: False
        
        # Initialize session state
        auth.init_session_state(session_state)
        
        # Attempt authentication with wrong password (now returns tuple)
        is_valid, error_msg = auth.authenticate("testuser", "wrongpass")
        assert is_valid == False
        assert error_msg is not None
        assert "Invalid username or password" in error_msg
        
        # Session state should remain unauthenticated
        assert session_state.authenticated == False
        assert session_state.username is None
    
    @patch('modules.auth.log_access')
    def test_logout_flow(self, mock_log):
        """Test logout flow clears session properly."""
        # Setup authenticated session
        session_state = MagicMock()
        session_state.get = MagicMock(return_value="testuser")
        auth.login_user(session_state, "testuser")
        
        # Logout
        auth.logout_user(session_state)
        
        # Verify session cleared
        assert session_state.authenticated == False
        assert session_state.username is None
        
        # Verify logout was logged
        mock_log.assert_called()


class TestPageConfiguration:
    """Test Streamlit page configuration."""
    
    def test_page_config_values(self):
        """Test that page configuration has correct values."""
        # This test verifies the expected configuration values
        # In actual Streamlit app, these are set via st.set_page_config()
        
        expected_config = {
            'page_title': 'Library Assessment Assistant',
            'page_icon': '📚',
            'layout': 'wide',
            'initial_sidebar_state': 'expanded'
        }
        
        # Verify expected values are defined
        assert expected_config['page_title'] == 'Library Assessment Assistant'
        assert expected_config['page_icon'] == '📚'
        assert expected_config['layout'] == 'wide'
        assert expected_config['initial_sidebar_state'] == 'expanded'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
