import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

connection_pool = None

def init_pool(minconn=1, maxconn=10):
    global connection_pool
    try:
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            connection_pool = psycopg2.pool.SimpleConnectionPool(minconn, maxconn, db_url)
        else:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn, maxconn,
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'pastebin'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                port=os.getenv('DB_PORT', '5432')
            )
        
        if connection_pool:
            print("✓ Database connection pool initialized")
            ensure_tables_exist()
            return True
    except Exception as e:
        print(f"✗ Error initializing connection pool: {e}")
        return False

def get_connection():
    if connection_pool is None:
        init_pool()
    try:
        return connection_pool.getconn()
    except Exception as e:
        print(f"✗ Error getting connection: {e}")
        return None

def return_connection(conn):
    if connection_pool and conn:
        connection_pool.putconn(conn)

def close_pool():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("✓ Database connection pool closed")


class DatabaseConnection:
    """Enhanced Context manager for database connections."""
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.last_query = None

    def __enter__(self):
        self.conn = get_connection()
        if self.conn:
            self.cursor = self.conn.cursor()
            return self # Returns the class instance
        raise Exception("Failed to get database connection")

    def execute(self, query, vars=None):
        self.last_query = query
        return self.cursor.execute(query, vars)

    def fetchone(self):
        return self.cursor.fetchone()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.conn: self.conn.rollback()
            print(f"❌ SQL Error: {exc_val}")
            print(f"📍 Failed Query: {self.last_query}")
        else:
            if self.conn: self.conn.commit()
        if self.cursor: self.cursor.close()
        if self.conn: return_connection(self.conn)


def ensure_tables_exist():
    try:
        # Note: We call db.execute() now, not cursor.execute()
        with DatabaseConnection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS pastes (
                    id VARCHAR(10) PRIMARY KEY,
                    content TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✓ Database table 'pastes' verified/created")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")

def cleanup_expired_pastes():
    """Delete all pastes that have reached their expiration time."""
    try:
        with DatabaseConnection() as db:
            db.execute("DELETE FROM pastes WHERE expires_at < NOW()")
            # In PostgreSQL, rowcount tells us how many rows were deleted
            deleted_count = db.cursor.rowcount 
            if deleted_count > 0:
                print(f"🧹 Cleanup: Removed {deleted_count} expired pastes.")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")

def test_connection():
    try:
        with DatabaseConnection() as db:
            db.execute("SELECT version();")
            version = db.fetchone()
            print(f"✓ Connected to PostgreSQL: {version[0]}")
            return True
    except Exception as e:
        return False

if __name__ == "__main__":
    init_pool()
    test_connection()
    close_pool()