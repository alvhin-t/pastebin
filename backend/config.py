"""
Configuration management for the pastebin application.
Centralizes all configuration values and expiry durations.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'pastebin'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432')
}

# Paste Configuration
PASTE_ID_LENGTH = 8
MAX_PASTE_SIZE = 1024 * 1024  # 1MB in bytes

# Expiry durations mapping
# Maps user-friendly labels to timedelta objects
EXPIRY_OPTIONS = {
    '10min': timedelta(minutes=10),
    '1hour': timedelta(hours=1),
    '1day': timedelta(days=1),
    '1week': timedelta(weeks=1),
    '1month': timedelta(days=30),
    'never': timedelta(days=365 * 100)  # 100 years ~ never
}

# Default expiry if none specified
DEFAULT_EXPIRY = '1day'

# Cleanup Configuration
CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', 60))  # seconds

# Security
MAX_CONTENT_LENGTH = MAX_PASTE_SIZE

# CORS (if needed for API access)
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')


def get_expiry_timedelta(expiry_key):
    """
    Get timedelta for an expiry key.
    
    Args:
        expiry_key: String key like '1hour', '1day', etc.
    
    Returns:
        timedelta object or None if invalid
    """
    return EXPIRY_OPTIONS.get(expiry_key, EXPIRY_OPTIONS[DEFAULT_EXPIRY])


def is_valid_expiry(expiry_key):
    """Check if an expiry key is valid."""
    return expiry_key in EXPIRY_OPTIONS


def get_expiry_choices():
    """Get list of available expiry choices for frontend."""
    return [
        {'key': '10min', 'label': '10 Minutes'},
        {'key': '1hour', 'label': '1 Hour'},
        {'key': '1day', 'label': '1 Day'},
        {'key': '1week', 'label': '1 Week'},
        {'key': '1month', 'label': '1 Month'},
        {'key': 'never', 'label': 'Never (100 years)'}
    ]


if __name__ == "__main__":
    # Display configuration when run directly
    print("=== Pastebin Configuration ===")
    print(f"Server: {HOST}:{PORT}")
    print(f"Debug: {DEBUG}")
    print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    print(f"Max paste size: {MAX_PASTE_SIZE / 1024}KB")
    print(f"Cleanup interval: {CLEANUP_INTERVAL}s")
    print("\nExpiry Options:")
    for choice in get_expiry_choices():
        print(f"  - {choice['label']} ({choice['key']})")
