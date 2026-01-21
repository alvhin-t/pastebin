"""
Database connection and utility functions.
Implements connection pooling for efficient database access.
"""

import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection pool
connection_pool = None


def init_pool(minconn=1, maxconn=10):
    """Initialize the database connection pool."""
    global connection_pool
    
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn,
            maxconn,
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'pastebin'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        
        if connection_pool:
            print("✓ Database connection pool initialized")
            return True
    except Exception as e:
        print(f"✗ Error initializing connection pool: {e}")
        return False


def get_connection():
    """Get a connection from the pool."""
    if connection_pool is None:
        init_pool()
    
    try:
        return connection_pool.getconn()
    except Exception as e:
        print(f"✗ Error getting connection: {e}")
        return None


def return_connection(conn):
    """Return a connection to the pool."""
    if connection_pool and conn:
        connection_pool.putconn(conn)


def close_pool():
    """Close all connections in the pool."""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("✓ Database connection pool closed")


class DatabaseConnection:
    """Context manager for database connections."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        self.conn = get_connection()
        if self.conn:
            self.cursor = self.conn.cursor()
            return self.cursor
        raise Exception("Failed to get database connection")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An error occurred, rollback
            if self.conn:
                self.conn.rollback()
        else:
            # No error, commit
            if self.conn:
                self.conn.commit()
        
        # Close cursor
        if self.cursor:
            self.cursor.close()
        
        # Return connection to pool
        if self.conn:
            return_connection(self.conn)


def test_connection():
    """Test the database connection."""
    try:
        with DatabaseConnection() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✓ Connected to PostgreSQL: {version[0]}")
            return True
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the connection when run directly
    init_pool()
    test_connection()
    close_pool()
