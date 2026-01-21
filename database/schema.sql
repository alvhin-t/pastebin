-- Shared Pastebin Database Schema
-- Time-aware design with automatic expiry

-- Drop existing objects if they exist
DROP TABLE IF EXISTS pastes CASCADE;
DROP INDEX IF EXISTS idx_pastes_expires_at;

-- Create the pastes table
CREATE TABLE pastes (
    id VARCHAR(8) PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Create B-Tree index on expires_at for efficient cleanup queries
-- This allows the cleanup script to find expired rows without full table scans
CREATE INDEX idx_pastes_expires_at ON pastes(expires_at);

-- Optional: Create index on created_at for analytics
CREATE INDEX idx_pastes_created_at ON pastes(created_at);

-- View for active pastes (not expired)
CREATE OR REPLACE VIEW active_pastes AS
SELECT id, content, created_at, expires_at
FROM pastes
WHERE expires_at > NOW();

-- Function to clean up expired pastes (can be called manually or via cron)
CREATE OR REPLACE FUNCTION cleanup_expired_pastes()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM pastes WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON TABLE pastes TO your_username;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_username;

COMMENT ON TABLE pastes IS 'Stores text pastes with automatic expiry';
COMMENT ON COLUMN pastes.id IS 'Non-sequential 8-character identifier';
COMMENT ON COLUMN pastes.expires_at IS 'Timestamp when paste should be deleted';
COMMENT ON INDEX idx_pastes_expires_at IS 'Enables fast cleanup of expired pastes';
