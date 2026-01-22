"""
Unit tests for database operations.
Tests connection pooling, CRUD operations, and expiry logic.
"""

import pytest
from datetime import datetime, timedelta, timezone
from db import DatabaseConnection, get_connection, return_connection


@pytest.mark.unit
class TestDatabaseConnection:
    """Test database connection pooling."""
    
    def test_connection_pool_initialized(self, database_pool):
        """Test that connection pool is properly initialized."""
        conn = get_connection()
        assert conn is not None
        assert not conn.closed
        return_connection(conn)
    
    def test_context_manager(self, database_pool):
        """Test DatabaseConnection context manager."""
        with DatabaseConnection() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_context_manager_rollback_on_error(self, database_pool):
        """Test that errors trigger rollback."""
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("SELECT 1")
                raise Exception("Test error")
        except Exception:
            pass  # Expected
        
        # Connection should be returned to pool despite error
        conn = get_connection()
        assert conn is not None
        return_connection(conn)


@pytest.mark.integration
class TestPasteCRUD:
    """Test paste CRUD operations."""
    
    def test_create_paste(self, clean_database):
        """Test creating a new paste."""
        paste_id = "test_001"
        content = "Hello, World!"
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        
        clean_database.execute(
            "INSERT INTO pastes (id, content, expires_at) VALUES (%s, %s, %s)",
            (paste_id, content, expires_at)
        )
        
        # Verify insertion
        clean_database.execute("SELECT content FROM pastes WHERE id = %s", (paste_id,))
        result = clean_database.fetchone()
        
        assert result is not None
        assert result[0] == content
    
    def test_read_paste(self, sample_paste, db_connection):
        """Test reading an existing paste."""
        db_connection.execute(
            "SELECT content, expires_at FROM pastes WHERE id = %s AND expires_at > NOW()",
            (sample_paste['id'],)
        )
        result = db_connection.fetchone()
        
        assert result is not None
        assert result[0] == sample_paste['content']
    
    def test_read_expired_paste_returns_nothing(self, expired_paste, db_connection):
        """Test that expired pastes are not returned."""
        db_connection.execute(
            "SELECT content FROM pastes WHERE id = %s AND expires_at > NOW()",
            (expired_paste['id'],)
        )
        result = db_connection.fetchone()
        
        assert result is None
    
    def test_delete_paste(self, sample_paste, db_connection):
        """Test deleting a paste."""
        db_connection.execute("DELETE FROM pastes WHERE id = %s", (sample_paste['id'],))
        
        # Verify deletion
        db_connection.execute("SELECT COUNT(*) FROM pastes WHERE id = %s", (sample_paste['id'],))
        count = db_connection.fetchone()[0]
        
        assert count == 0
    
    def test_cleanup_expired_pastes(self, expired_paste, db_connection):
        """Test cleanup of expired pastes."""
        # Delete expired pastes
        db_connection.execute("DELETE FROM pastes WHERE expires_at < NOW()")
        deleted_count = db_connection.rowcount
        
        assert deleted_count >= 1
        
        # Verify the expired paste is gone
        db_connection.execute("SELECT COUNT(*) FROM pastes WHERE id = %s", (expired_paste['id'],))
        count = db_connection.fetchone()[0]
        
        assert count == 0


@pytest.mark.integration
class TestPasteConstraints:
    """Test database constraints and validation."""
    
    def test_duplicate_id_rejected(self, sample_paste, clean_database):
        """Test that duplicate IDs are rejected."""
        with pytest.raises(Exception):  # Should raise IntegrityError
            clean_database.execute(
                "INSERT INTO pastes (id, content, expires_at) VALUES (%s, %s, %s)",
                (sample_paste['id'], "Different content", sample_paste['expires_at'])
            )
    
    def test_expiry_must_be_after_creation(self, clean_database):
        """Test that expires_at must be after created_at."""
        paste_id = "test_002"
        content = "Invalid expiry"
        
        # Try to create paste with expires_at before created_at
        with pytest.raises(Exception):  # Should raise CheckConstraint error
            clean_database.execute(
                """
                INSERT INTO pastes (id, content, created_at, expires_at) 
                VALUES (%s, %s, NOW(), NOW() - INTERVAL '1 hour')
                """,
                (paste_id, content)
            )
    
    def test_content_cannot_be_null(self, clean_database):
        """Test that content is required."""
        paste_id = "test_003"
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        
        with pytest.raises(Exception):  # Should raise NotNullViolation
            clean_database.execute(
                "INSERT INTO pastes (id, content, expires_at) VALUES (%s, %s, %s)",
                (paste_id, None, expires_at)
            )


@pytest.mark.integration
class TestDatabaseIndexes:
    """Test that database indexes are working."""
    
    def test_expires_at_index_exists(self, db_connection):
        """Test that index on expires_at exists."""
        db_connection.execute(
            """
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'pastes' AND indexname = 'idx_pastes_expires_at'
            """
        )
        result = db_connection.fetchone()
        
        assert result is not None
        assert result[0] == 'idx_pastes_expires_at'
    
    def test_created_at_index_exists(self, db_connection):
        """Test that index on created_at exists."""
        db_connection.execute(
            """
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'pastes' AND indexname = 'idx_pastes_created_at'
            """
        )
        result = db_connection.fetchone()
        
        assert result is not None
        assert result[0] == 'idx_pastes_created_at'
