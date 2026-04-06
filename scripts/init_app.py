"""
Initialize the application database and create a default admin user.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import init_database
from modules.auth import create_user


def main():
    """Initialize database and create default user."""
    print("Initializing database...")
    init_database()
    
    print("\nCreating default admin user...")
    username = "admin"
    password = "admin123"
    
    if create_user(username, password):
        print(f"User '{username}' created successfully")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print("\nWARNING: Please change the default password after first login!")
    else:
        print(f"User '{username}' already exists")
    
    print("\nApplication initialization complete!")
    print("\nTo start the application, run:")
    print("  streamlit run streamlit_app.py")


if __name__ == "__main__":
    main()
