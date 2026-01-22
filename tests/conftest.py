"""
Pytest configuration and fixtures.
Shared test utilities and setup.
"""

import sys
import os
import pytest
from datetime import datetime, timedelta, timezone

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from db import DatabaseConnection, init_pool, close_pool
import config


@pytest.fixture(scope='session')
def database_pool():
    """Initialize database connection pool for test session."""
    init_pool()
    yield
    close_pool()


@pytest.fixture
def db_connection(database_pool):
    """Provide a database connection for tests."""
    with DatabaseConnection() as cursor:
        yield cursor


@pytest.fixture
def clean_database(db_connection):
    """Clean test data before and after tests."""
    # Clean before test
    db_connection.execute("DELETE FROM pastes WHERE id LIKE 'test_%'")
    
    yield db_connection
    
    # Clean after test
    db_connection.execute("DELETE FROM pastes WHERE id LIKE 'test_%'")


@pytest.fixture
def sample_paste(clean_database):
    """Create a sample paste for testing."""
    paste_id = "test_abc"
    content = "This is a test paste"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    clean_database.execute(
        "INSERT INTO pastes (id, content, expires_at) VALUES (%s, %s, %s)",
        (paste_id, content, expires_at)
    )
    
    return {
        'id': paste_id,
        'content': content,
        'expires_at': expires_at
    }


@pytest.fixture
def expired_paste(clean_database):
    """Create an expired paste for testing."""
    paste_id = "test_exp"
    content = "This paste has expired"
    expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    
    clean_database.execute(
        "INSERT INTO pastes (id, content, expires_at) VALUES (%s, %s, %s)",
        (paste_id, content, expires_at)
    )
    
    return {
        'id': paste_id,
        'content': content,
        'expires_at': expires_at
    }