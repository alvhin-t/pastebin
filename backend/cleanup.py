"""
Background cleanup service for expired pastes.
Runs continuously and removes expired entries from the database.

Can be run as:
1. A standalone Python script (for development)
2. A systemd service (for production)
3. A cron job (alternative production approach)
"""

import time
import signal
import sys
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

import config
from db import DatabaseConnection, init_pool, close_pool


# Global flag for graceful shutdown
running = True


def setup_logging():
    """Configure logging with rotation."""
    # Create logs directory if it doesn't exist
    import os
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'cleanup.log')
    
    # Create logger
    logger = logging.getLogger('cleanup')
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def cleanup_expired_pastes(logger):
    """
    Delete all expired pastes from the database.
    
    Returns:
        Number of pastes deleted, or -1 on error
    """
    try:
        with DatabaseConnection() as cursor:
            # Delete expired pastes
            cursor.execute(
                """
                DELETE FROM pastes 
                WHERE expires_at < NOW()
                """
            )
            
            # Get count of deleted rows
            deleted_count = cursor.rowcount
            
            return deleted_count
    
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return -1


def get_database_stats(logger):
    """
    Get statistics about the database.
    
    Returns:
        Dictionary with stats or None on error
    """
    try:
        with DatabaseConnection() as cursor:
            # Get total paste count
            cursor.execute("SELECT COUNT(*) FROM pastes")
            total = cursor.fetchone()[0]
            
            # Get active paste count
            cursor.execute(
                "SELECT COUNT(*) FROM pastes WHERE expires_at > NOW()"
            )
            active = cursor.fetchone()[0]
            
            # Get expired paste count
            cursor.execute(
                "SELECT COUNT(*) FROM pastes WHERE expires_at <= NOW()"
            )
            expired = cursor.fetchone()[0]
            
            return {
                'total': total,
                'active': active,
                'expired': expired
            }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger = logging.getLogger('cleanup')
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    running = False


def run_cleanup_loop(interval=None):
    """
    Main cleanup loop.
    
    Args:
        interval: Cleanup interval in seconds (default: from config)
    """
    global running
    
    if interval is None:
        interval = config.CLEANUP_INTERVAL
    
    logger = setup_logging()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("Paste Cleanup Service Starting")
    logger.info(f"Cleanup interval: {interval} seconds")
    logger.info("=" * 60)
    
    # Initialize database connection pool
    if not init_pool():
        logger.error("Failed to initialize database connection pool")
        sys.exit(1)
    
    # Get initial stats
    stats = get_database_stats(logger)
    if stats:
        logger.info(f"Initial stats - Total: {stats['total']}, "
                   f"Active: {stats['active']}, "
                   f"Expired: {stats['expired']}")
    
    cleanup_count = 0
    total_deleted = 0
    
    try:
        while running:
            cleanup_count += 1
            start_time = time.time()
            
            logger.info(f"Starting cleanup run #{cleanup_count}")
            
            # Perform cleanup
            deleted = cleanup_expired_pastes(logger)
            
            if deleted >= 0:
                total_deleted += deleted
                elapsed = time.time() - start_time
                
                if deleted > 0:
                    logger.info(f"✓ Deleted {deleted} expired paste(s) "
                              f"in {elapsed:.2f}s")
                else:
                    logger.debug(f"No expired pastes found "
                               f"(checked in {elapsed:.2f}s)")
                
                # Log stats every 10 runs
                if cleanup_count % 10 == 0:
                    stats = get_database_stats(logger)
                    if stats:
                        logger.info(
                            f"Stats (run #{cleanup_count}) - "
                            f"Total: {stats['total']}, "
                            f"Active: {stats['active']}, "
                            f"Lifetime deleted: {total_deleted}"
                        )
            else:
                logger.error(f"Cleanup run #{cleanup_count} failed")
            
            # Sleep until next cleanup (interruptible)
            for _ in range(interval):
                if not running:
                    break
                time.sleep(1)
    
    except Exception as e:
        logger.error(f"Unexpected error in cleanup loop: {e}")
    
    finally:
        logger.info("=" * 60)
        logger.info("Paste Cleanup Service Stopping")
        logger.info(f"Total cleanup runs: {cleanup_count}")
        logger.info(f"Total pastes deleted: {total_deleted}")
        logger.info("=" * 60)
        
        close_pool()


def run_once():
    """
    Run cleanup once and exit.
    Useful for cron jobs.
    """
    logger = setup_logging()
    logger.info("Running one-time cleanup")
    
    if not init_pool():
        logger.error("Failed to initialize database connection pool")
        return 1
    
    try:
        deleted = cleanup_expired_pastes(logger)
        if deleted >= 0:
            logger.info(f"✓ Deleted {deleted} expired paste(s)")
            return 0
        else:
            logger.error("Cleanup failed")
            return 1
    finally:
        close_pool()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pastebin cleanup service'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run cleanup once and exit (for cron)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        help=f'Cleanup interval in seconds (default: {config.CLEANUP_INTERVAL})'
    )
    
    args = parser.parse_args()
    
    if args.once:
        sys.exit(run_once())
    else:
        run_cleanup_loop(args.interval)
