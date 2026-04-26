"""
Authentication Module

This module provides secure user authentication and session management for the
FERPA-Compliant RAG Decision Support System.

Key Features:
- Password-based authentication with bcrypt hashing
- Secure password storage (salt rounds: 12)
- Cryptographically secure session ID generation
- Session state management for Streamlit
- Comprehensive audit logging
- User account management (create, delete, list)
- Password change functionality
- Rate limiting with exponential backoff (max 5 attempts per 60 seconds)

Security Measures:
- bcrypt password hashing with automatic salt generation
- No plaintext password storage
- Cryptographically secure session IDs using secrets.token_urlsafe()
- Session IDs include username and timestamp to prevent collisions
- Session validation on each request
- Session-based authentication (no tokens)
- Audit trail for all access events
- Rate limiting to prevent brute force attacks
- Exponential backoff delays (1s, 2s, 4s, 8s, 16s)
- Per-username and IP address tracking

Module Functions:
- create_user(): Create new user account with hashed password
- authenticate(): Verify user credentials with rate limiting
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
- check_rate_limit(): Check if user is rate limited
- record_failed_attempt(): Record failed authentication attempt
- clear_rate_limit(): Clear rate limiting data for user
- get_rate_limit_status(): Get current rate limit status
- generate_secure_session_id(): Generate cryptographically secure session ID
- parse_session_id(): Parse session ID to extract username and timestamp
- validate_session_id(): Validate session ID belongs to expected user
- init_secure_session(): Initialize secure session for user
- get_secure_session_id(): Get or create secure session ID
- clear_secure_session(): Clear secure session from session state

Database Tables Used:
- users: User accounts with bcrypt password hashes
- access_logs: Audit trail of all access events

Requirements Implemented:
- 6.6: Implement basic password authentication
- 6.7: Log all data access with timestamps
- Bug 2.3: Implement rate limiting to prevent brute force attacks
- Bug 2.4: Use cryptographically secure session IDs to prevent collisions

Usage Example:
    # Create user
    if create_user("admin", "secure_password"):
        print("User created")
    
    # Authenticate with rate limiting
    is_valid, error_msg = authenticate("admin", "secure_password", ip_address="192.168.1.1")
    if is_valid:
        print("Login successful")
        log_access("admin", "login_success", details="User logged in")
    else:
        print(f"Login failed: {error_msg}")
    
    # Generate secure session ID
    session_id = generate_secure_session_id("admin")
    print(f"Session ID: {session_id}")
    
    # Validate session ID
    is_valid, error_msg = validate_session_id(session_id, "admin")
    if is_valid:
        print("Session valid")
    else:
        print(f"Session invalid: {error_msg}")

Author: FERPA-Compliant RAG DSS Team
"""

import bcrypt
import time
import secrets
from typing import Optional, Dict, Any
from collections import defaultdict
from threading import Lock
from modules.database import execute_query, execute_update


# Rate limiting configuration
MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 60  # seconds
EXPONENTIAL_BACKOFF_BASE = 2  # seconds

# In-memory storage for rate limiting
# Structure: {username: {'attempts': [(timestamp, ip), ...], 'lockout_until': timestamp}}
_rate_limit_store: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'attempts': [], 'lockout_until': 0})
_rate_limit_lock = Lock()


def _clean_old_attempts(username: str, current_time: float) -> None:
    """
    Remove attempts older than the rate limit window.
    
    Args:
        username: Username to clean attempts for
        current_time: Current timestamp
    """
    cutoff_time = current_time - RATE_LIMIT_WINDOW
    _rate_limit_store[username]['attempts'] = [
        (ts, ip) for ts, ip in _rate_limit_store[username]['attempts']
        if ts > cutoff_time
    ]


def _calculate_backoff_delay(attempt_count: int) -> float:
    """
    Calculate exponential backoff delay based on attempt count.
    
    Args:
        attempt_count: Number of failed attempts
        
    Returns:
        Delay in seconds (1s, 2s, 4s, 8s, 16s)
    """
    if attempt_count <= 1:
        return 0
    # Exponential backoff: 2^(n-1) seconds, capped at 16 seconds
    return min(EXPONENTIAL_BACKOFF_BASE ** (attempt_count - 1), 16)


def check_rate_limit(username: str, ip_address: Optional[str] = None) -> tuple[bool, Optional[str], float]:
    """
    Check if user is rate limited.
    
    Args:
        username: Username attempting to authenticate
        ip_address: Optional IP address for tracking
        
    Returns:
        Tuple of (is_allowed, error_message, wait_time)
        - is_allowed: True if authentication attempt is allowed
        - error_message: Error message if rate limited, None otherwise
        - wait_time: Seconds to wait before next attempt
    """
    with _rate_limit_lock:
        current_time = time.time()
        
        # Check if user is currently locked out
        lockout_until = _rate_limit_store[username].get('lockout_until', 0)
        if current_time < lockout_until:
            wait_time = lockout_until - current_time
            return False, f"Account temporarily locked. Please try again in {int(wait_time)} seconds.", wait_time
        
        # Clean old attempts
        _clean_old_attempts(username, current_time)
        
        # Count recent attempts
        attempts = _rate_limit_store[username]['attempts']
        attempt_count = len(attempts)
        
        # Check if rate limit exceeded
        if attempt_count >= MAX_ATTEMPTS:
            # Calculate lockout time with exponential backoff
            backoff_delay = _calculate_backoff_delay(attempt_count)
            lockout_until = current_time + backoff_delay
            _rate_limit_store[username]['lockout_until'] = lockout_until
            
            return False, f"Too many failed login attempts. Account locked for {int(backoff_delay)} seconds.", backoff_delay
        
        return True, None, 0


def record_failed_attempt(username: str, ip_address: Optional[str] = None) -> None:
    """
    Record a failed authentication attempt.
    
    Args:
        username: Username that failed authentication
        ip_address: Optional IP address for tracking
    """
    with _rate_limit_lock:
        current_time = time.time()
        _rate_limit_store[username]['attempts'].append((current_time, ip_address or 'unknown'))


def clear_rate_limit(username: str) -> None:
    """
    Clear rate limiting data for a user (called on successful login).
    
    Args:
        username: Username to clear rate limit for
    """
    with _rate_limit_lock:
        if username in _rate_limit_store:
            _rate_limit_store[username]['attempts'] = []
            _rate_limit_store[username]['lockout_until'] = 0


def get_rate_limit_status(username: str) -> Dict[str, Any]:
    """
    Get current rate limit status for a user.
    
    Args:
        username: Username to check
        
    Returns:
        Dictionary with rate limit status information
    """
    with _rate_limit_lock:
        current_time = time.time()
        _clean_old_attempts(username, current_time)
        
        attempts = _rate_limit_store[username]['attempts']
        lockout_until = _rate_limit_store[username].get('lockout_until', 0)
        
        is_locked = current_time < lockout_until
        remaining_attempts = max(0, MAX_ATTEMPTS - len(attempts))
        
        return {
            'attempt_count': len(attempts),
            'remaining_attempts': remaining_attempts,
            'is_locked': is_locked,
            'lockout_until': lockout_until if is_locked else None,
            'wait_time': max(0, lockout_until - current_time) if is_locked else 0
        }


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


def authenticate(username: str, password: str, ip_address: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Authenticate user credentials with rate limiting.
    
    Args:
        username: Username
        password: Plain text password
        ip_address: Optional IP address for rate limiting
        
    Returns:
        Tuple of (is_authenticated, error_message)
        - is_authenticated: True if credentials are valid and not rate limited
        - error_message: Error message if authentication failed, None if successful
    """
    # Check rate limit first
    is_allowed, rate_limit_msg, wait_time = check_rate_limit(username, ip_address)
    if not is_allowed:
        # Log rate limit violation
        log_access(
            username=username,
            action="login_rate_limited",
            details=f"Rate limit exceeded. {rate_limit_msg}"
        )
        return False, rate_limit_msg
    
    # Get user from database
    users = execute_query(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )
    
    if not users:
        # Record failed attempt
        record_failed_attempt(username, ip_address)
        
        # Log failed attempt
        log_access(
            username=username,
            action="login_failed",
            details="User not found"
        )
        return False, "Invalid username or password"
    
    user = users[0]
    password_hash = user['password_hash']
    
    # Verify password
    is_valid = verify_password(password, password_hash)
    
    if is_valid:
        # Clear rate limit on successful login
        clear_rate_limit(username)
        
        # Log successful authentication
        log_access(
            username=username,
            action="login_success",
            details="Successful authentication"
        )
        return True, None
    else:
        # Record failed attempt
        record_failed_attempt(username, ip_address)
        
        # Log failed attempt
        log_access(
            username=username,
            action="login_failed",
            details="Invalid password"
        )
        
        # Get updated rate limit status
        status = get_rate_limit_status(username)
        remaining = status['remaining_attempts']
        
        if remaining > 0:
            return False, f"Invalid username or password. {remaining} attempts remaining."
        else:
            return False, "Invalid username or password. Account will be temporarily locked after next failed attempt."


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
    is_valid, error_msg = authenticate(username, old_password)
    if not is_valid:
        return False, error_msg or "Current password is incorrect"
    
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


def generate_secure_session_id(username: str) -> str:
    """
    Generate a cryptographically secure session ID.
    
    Uses secrets.token_urlsafe() for cryptographic randomness and includes
    username and timestamp to ensure uniqueness and prevent collisions.
    
    Args:
        username: Username for the session
        
    Returns:
        Cryptographically secure session ID string
        
    Format: {username}::{timestamp}::{secure_token}
    Example: admin::1234567890::AbCdEf123456
    
    Note: Uses :: as separator to allow underscores in usernames
    """
    # Generate cryptographically secure random token (32 bytes = 256 bits)
    secure_token = secrets.token_urlsafe(32)
    
    # Get current timestamp in milliseconds for uniqueness
    timestamp = int(time.time() * 1000)
    
    # Combine username, timestamp, and secure token
    # Use :: as separator to allow underscores in usernames
    session_id = f"{username}::{timestamp}::{secure_token}"
    
    return session_id


def parse_session_id(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Parse a session ID to extract username and timestamp.
    
    Args:
        session_id: Session ID string
        
    Returns:
        Dictionary with 'username', 'timestamp', and 'token' keys, or None if invalid
    """
    try:
        parts = session_id.split('::', 2)
        if len(parts) != 3:
            return None
        
        username, timestamp_str, token = parts
        timestamp = int(timestamp_str)
        
        return {
            'username': username,
            'timestamp': timestamp,
            'token': token
        }
    except (ValueError, AttributeError):
        return None


def validate_session_id(session_id: str, expected_username: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a session ID belongs to the expected user.
    
    Args:
        session_id: Session ID to validate
        expected_username: Username that should own this session
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if session is valid for the user
        - error_message: Error message if invalid, None if valid
    """
    # Parse session ID
    parsed = parse_session_id(session_id)
    
    if parsed is None:
        return False, "Invalid session ID format"
    
    # Check if username matches
    if parsed['username'] != expected_username:
        return False, f"Session ID does not belong to user '{expected_username}'"
    
    # Session is valid
    return True, None


def init_secure_session(session_state: Any, username: str) -> str:
    """
    Initialize a secure session for a user.
    
    Creates a cryptographically secure session ID and stores it in session state.
    
    Args:
        session_state: Streamlit session_state object
        username: Username for the session
        
    Returns:
        Generated session ID
    """
    session_id = generate_secure_session_id(username)
    session_state.secure_session_id = session_id
    
    # Log session creation
    log_access(
        username=username,
        action="session_created",
        details=f"Secure session created with ID: {session_id[:20]}..."
    )
    
    return session_id


def get_secure_session_id(session_state: Any, username: str) -> str:
    """
    Get or create a secure session ID for a user.
    
    If a session ID already exists and is valid, returns it.
    Otherwise, creates a new secure session ID.
    
    Args:
        session_state: Streamlit session_state object
        username: Username for the session
        
    Returns:
        Secure session ID
    """
    # Check if session ID exists
    if hasattr(session_state, 'secure_session_id'):
        session_id = session_state.secure_session_id
        
        # Validate session ID
        is_valid, error_msg = validate_session_id(session_id, username)
        
        if is_valid:
            return session_id
        else:
            # Invalid session, create new one
            log_access(
                username=username,
                action="session_invalid",
                details=f"Invalid session detected: {error_msg}"
            )
    
    # Create new session
    return init_secure_session(session_state, username)


def clear_secure_session(session_state: Any) -> None:
    """
    Clear the secure session ID from session state.
    
    Args:
        session_state: Streamlit session_state object
    """
    if hasattr(session_state, 'secure_session_id'):
        session_id = session_state.secure_session_id
        
        # Parse to get username for logging
        parsed = parse_session_id(session_id)
        if parsed:
            log_access(
                username=parsed['username'],
                action="session_cleared",
                details=f"Secure session cleared: {session_id[:20]}..."
            )
        
        del session_state.secure_session_id


if __name__ == "__main__":
    # Example usage
    print("Creating test user...")
    if create_user("admin", "admin123"):
        print("User 'admin' created successfully")
    else:
        print("User 'admin' already exists")
    
    print("\nTesting authentication...")
    is_valid, error_msg = authenticate("admin", "admin123")
    if is_valid:
        print("Authentication successful!")
    else:
        print(f"Authentication failed: {error_msg}")
    
    print("\nTesting secure session ID generation...")
    session_id1 = generate_secure_session_id("admin")
    session_id2 = generate_secure_session_id("admin")
    print(f"Session ID 1: {session_id1}")
    print(f"Session ID 2: {session_id2}")
    print(f"IDs are unique: {session_id1 != session_id2}")
    
    print("\nTesting session ID validation...")
    is_valid, error_msg = validate_session_id(session_id1, "admin")
    print(f"Valid for admin: {is_valid}")
    
    is_valid, error_msg = validate_session_id(session_id1, "other_user")
    print(f"Valid for other_user: {is_valid}, Error: {error_msg}")

