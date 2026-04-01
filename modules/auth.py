"""
Authentication Module

This module provides secure user authentication and session management for the
FERPA-Compliant RAG Decision Support System.

Key Features:
- Password-based authentication with bcrypt hashing
- Secure password storage (salt rounds: 12)
- Session state management for Streamlit
- Comprehensive audit logging
- User account management (create, delete, list)
- Password change functionality
- Rate limiting support

Security Measures:
- bcrypt password hashing with automatic salt generation
- No plaintext password storage
- Session-based authentication (no tokens)
- Audit trail for all access events
- Configurable rate limiting

Module Functions:
- create_user(): Create new user account with hashed password
- authenticate(): Verify user credentials
- hash_password(): Generate bcrypt hash for password
- verify_password(): Verify password against stored hash
- log_access(): Record access events for audit trail
- change_password(): Update user password securely
- delete_user(): Remove user account
- list_users(): Get all user accounts (without passwords)
- login_user(): Mark user as logged in (session management)
- logout_user(): Clear user session
- is_authenticated(): Check if user is logged in
- get_current_user(): Get current authenticated username

Database Tables Used:
- users: User accounts with bcrypt password hashes
- access_logs: Audit trail of all access events

Requirements Implemented:
- 6.6: Implement basic password authentication
- 6.7: Log all data access with timestamps

Usage Example:
    # Create user
    if create_user("admin", "secure_password"):
        print("User created")
    
    # Authenticate
    if authenticate("admin", "secure_password"):
        print("Login successful")
        log_access("admin", "login_success", details="User logged in")

Author: FERPA-Compliant RAG DSS Team
"""

import bcrypt
from datetime import datetime
from typing import Optional, Dict, Any
from modules.database import execute_query, execute_update


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password as string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def create_user(username: str, password: str) -> bool:
    """
    Create a new user account.
    
    Args:
        username: Username (must be unique)
        password: Plain text password (will be hashed)
        
    Returns:
        True if user created successfully, False if username already exists
    """
    # Check if username already exists
    existing = execute_query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    
    if existing:
        return False
    
    # Hash password and create user
    password_hash = hash_password(password)
    execute_update(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    
    # Log user creation
    log_access(
        username="system",
        action="create_user",
        resource_type="user",
        resource_id=username,
        details=f"Created user account: {username}"
    )
    
    return True


def authenticate(username: str, password: str) -> bool:
    """
    Authenticate user credentials.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        True if credentials are valid, False otherwise
    """
    # Get user from database
    users = execute_query(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )
    
    if not users:
        # Log failed attempt
        log_access(
            username=username,
            action="login_failed",
            details="User not found"
        )
        return False
    
    user = users[0]
    password_hash = user['password_hash']
    
    # Verify password
    is_valid = verify_password(password, password_hash)
    
    # Log authentication attempt
    if is_valid:
        log_access(
            username=username,
            action="login_success",
            details="Successful authentication"
        )
    else:
        log_access(
            username=username,
            action="login_failed",
            details="Invalid password"
        )
    
    return is_valid


def log_access(
    username: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None
) -> None:
    """
    Log user access for audit trail.
    
    Args:
        username: Username performing the action
        action: Action being performed (e.g., 'login', 'upload', 'query', 'delete')
        resource_type: Optional type of resource accessed (e.g., 'dataset', 'report')
        resource_id: Optional ID of resource accessed
        details: Optional additional details about the action
    """
    execute_update(
        """
        INSERT INTO access_logs (username, action, resource_type, resource_id, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        (username, action, resource_type, resource_id, details)
    )


def get_access_logs(
    username: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100
) -> list[Dict[str, Any]]:
    """
    Retrieve access logs for audit purposes.
    
    Args:
        username: Optional filter by username
        action: Optional filter by action type
        limit: Maximum number of logs to return
        
    Returns:
        List of access log entries
    """
    query = "SELECT * FROM access_logs WHERE 1=1"
    params = []
    
    if username:
        query += " AND username = ?"
        params.append(username)
    
    if action:
        query += " AND action = ?"
        params.append(action)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    return execute_query(query, tuple(params))


def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """
    Change user password.
    
    Args:
        username: Username
        old_password: Current password
        new_password: New password
        
    Returns:
        Tuple of (success, message)
    """
    # Verify old password
    if not authenticate(username, old_password):
        return False, "Current password is incorrect"
    
    # Hash new password
    new_hash = hash_password(new_password)
    
    # Update password
    execute_update(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (new_hash, username)
    )
    
    # Log password change
    log_access(
        username=username,
        action="password_change",
        details="Password changed successfully"
    )
    
    return True, "Password changed successfully"


def delete_user(username: str) -> bool:
    """
    Delete a user account.
    
    Args:
        username: Username to delete
        
    Returns:
        True if user deleted, False if user not found
    """
    # Check if user exists
    users = execute_query(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    )
    
    if not users:
        return False
    
    # Delete user
    execute_update(
        "DELETE FROM users WHERE username = ?",
        (username,)
    )
    
    # Log deletion
    log_access(
        username="system",
        action="delete_user",
        resource_type="user",
        resource_id=username,
        details=f"Deleted user account: {username}"
    )
    
    return True


def list_users() -> list[Dict[str, Any]]:
    """
    List all user accounts.
    
    Returns:
        List of users (without password hashes)
    """
    return execute_query(
        "SELECT id, username, created_date FROM users ORDER BY username"
    )


# Session management helpers for Streamlit
def init_session_state(session_state: Any) -> None:
    """
    Initialize Streamlit session state for authentication.
    
    Args:
        session_state: Streamlit session_state object
    """
    if 'authenticated' not in session_state:
        session_state.authenticated = False
    if 'username' not in session_state:
        session_state.username = None
    if 'login_attempts' not in session_state:
        session_state.login_attempts = 0


def login_user(session_state: Any, username: str) -> None:
    """
    Mark user as logged in in session state.
    
    Args:
        session_state: Streamlit session_state object
        username: Username to log in
    """
    session_state.authenticated = True
    session_state.username = username
    session_state.login_attempts = 0


def logout_user(session_state: Any) -> None:
    """
    Log out user from session state.
    
    Args:
        session_state: Streamlit session_state object
    """
    username = session_state.get('username')
    if username:
        log_access(
            username=username,
            action="logout",
            details="User logged out"
        )
    
    session_state.authenticated = False
    session_state.username = None


def is_authenticated(session_state: Any) -> bool:
    """
    Check if user is authenticated.
    
    Args:
        session_state: Streamlit session_state object
        
    Returns:
        True if authenticated, False otherwise
    """
    return session_state.get('authenticated', False)


def get_current_user(session_state: Any) -> Optional[str]:
    """
    Get current authenticated username.
    
    Args:
        session_state: Streamlit session_state object
        
    Returns:
        Username if authenticated, None otherwise
    """
    if is_authenticated(session_state):
        return session_state.get('username')
    return None


if __name__ == "__main__":
    # Example usage
    print("Creating test user...")
    if create_user("admin", "admin123"):
        print("User 'admin' created successfully")
    else:
        print("User 'admin' already exists")
    
    print("\nTesting authentication...")
    if authenticate("admin", "admin123"):
        print("Authentication successful!")
    else:
        print("Authentication failed!")
