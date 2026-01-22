"""
Test script for the cleanup service.
Demonstrates that expired pastes are properly deleted.
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from db import DatabaseConnection, init_pool, close_pool
from cleanup import cleanup_expired_pastes, setup_logging


def create_test_paste(paste_id, content, expires_in_seconds):
    """Create a test paste with specific expiry time."""
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
    
    with DatabaseConnection() as cursor:
        cursor.execute(
            "INSERT INTO pastes (id, content, expires_at) VALUES (%s, %s, %s)",
            (paste_id, content, expires_at)
        )


def get_paste_count():
    """Get total number of pastes."""
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) FROM pastes")
        return cursor.fetchone()[0]


def get_active_paste_count():
    """Get number of active (non-expired) pastes."""
    with DatabaseConnection() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM pastes WHERE expires_at > NOW()"
        )
        return cursor.fetchone()[0]


def paste_exists(paste_id):
    """Check if a paste exists."""
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) FROM pastes WHERE id = %s", (paste_id,))
        return cursor.fetchone()[0] > 0


def run_tests():
    """Run cleanup tests."""
    logger = setup_logging()
    
    print("=" * 60)
    print("CLEANUP SERVICE TEST")
    print("=" * 60)
    
    # Initialize database
    init_pool()
    
    try:
        # Clean up any existing test data
        with DatabaseConnection() as cursor:
            cursor.execute("DELETE FROM pastes WHERE id LIKE 'test_%'")
        
        print("\n1. Creating test pastes...")
        
        # Create pastes with different expiry times
        create_test_paste("test_001", "This expires in 5 seconds", 5)
        create_test_paste("test_002", "This expires in 10 seconds", 10)
        create_test_paste("test_003", "This expired 5 seconds ago", -5)
        create_test_paste("test_004", "This expires in 1 hour", 3600)
        
        initial_count = get_paste_count()
        initial_active = get_active_paste_count()
        
        print(f"   ✓ Created 4 test pastes")
        print(f"   Total pastes: {initial_count}")
        print(f"   Active pastes: {initial_active}")
        
        # Verify the already-expired paste
        print("\n2. Checking already-expired paste...")
        assert paste_exists("test_003"), "test_003 should exist initially"
        print("   ✓ Expired paste exists in database")
        
        # Run cleanup
        print("\n3. Running cleanup...")
        deleted = cleanup_expired_pastes(logger)
        print(f"   ✓ Deleted {deleted} expired paste(s)")
        
        # Verify cleanup removed the expired paste
        print("\n4. Verifying cleanup results...")
        assert not paste_exists("test_003"), "test_003 should be deleted"
        assert paste_exists("test_001"), "test_001 should still exist"
        assert paste_exists("test_002"), "test_002 should still exist"
        assert paste_exists("test_004"), "test_004 should still exist"
        print("   ✓ Only expired pastes were deleted")
        
        after_cleanup_count = get_paste_count()
        after_cleanup_active = get_active_paste_count()
        
        print(f"   Total pastes: {after_cleanup_count}")
        print(f"   Active pastes: {after_cleanup_active}")
        
        # Wait and test time-based expiry
        print("\n5. Testing time-based expiry...")
        print("   Waiting 6 seconds for test_001 to expire...")
        
        import time
        time.sleep(6)
        
        deleted = cleanup_expired_pastes(logger)
        print(f"   ✓ Deleted {deleted} expired paste(s)")
        
        assert not paste_exists("test_001"), "test_001 should now be deleted"
        assert paste_exists("test_002"), "test_002 should still exist"
        print("   ✓ Time-based expiry works correctly")
        
        # Clean up test data
        print("\n6. Cleaning up test data...")
        with DatabaseConnection() as cursor:
            cursor.execute("DELETE FROM pastes WHERE id LIKE 'test_%'")
        print("   ✓ Test data removed")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        
        return 0
    
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        close_pool()


if __name__ == '__main__':
    sys.exit(run_tests())
