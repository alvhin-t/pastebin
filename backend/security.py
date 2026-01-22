"""
Security utilities for the pastebin application.
Includes rate limiting, input validation, and XSS protection.
"""

import re
import time
from collections import defaultdict
from datetime import datetime, timedelta


class RateLimiter:
    """
    Simple in-memory rate limiter.
    In production, use Redis for distributed rate limiting.
    """
    
    def __init__(self, max_requests=10, window_seconds=60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier):
        """
        Check if request is allowed for the given identifier.
        
        Args:
            identifier: Usually an IP address
        
        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier):
        """Get remaining requests for identifier."""
        now = time.time()
        window_start = now - self.window_seconds
        
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(recent_requests))
    
    def cleanup(self):
        """Remove old entries to prevent memory bloat."""
        now = time.time()
        window_start = now - self.window_seconds
        
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
            
            # Remove empty entries
            if not self.requests[identifier]:
                del self.requests[identifier]


# Global rate limiter instances
paste_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
view_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


def validate_paste_content(content):
    """
    Validate paste content.
    
    Args:
        content: The paste content to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not content:
        return False, "Content cannot be empty"
    
    if not isinstance(content, str):
        return False, "Content must be a string"
    
    # Check length
    if len(content.strip()) == 0:
        return False, "Content cannot be only whitespace"
    
    # Check byte size
    byte_size = len(content.encode('utf-8'))
    if byte_size > 1024 * 1024:  # 1MB
        return False, f"Content too large ({byte_size} bytes, max 1MB)"
    
    # Check for null bytes
    if '\x00' in content:
        return False, "Content contains invalid null bytes"
    
    return True, None


def validate_paste_id(paste_id):
    """
    Validate paste ID format.
    
    Args:
        paste_id: The paste ID to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not paste_id:
        return False
    
    if not isinstance(paste_id, str):
        return False
    
    # Check length
    if len(paste_id) != 8:  # Expected length
        return False
    
    # Check characters (alphanumeric, dash, underscore only)
    if not re.match(r'^[A-Za-z0-9_-]+$', paste_id):
        return False
    
    return True


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal.
    
    Args:
        filename: The filename to sanitize
    
    Returns:
        Sanitized filename or None if invalid
    """
    if not filename:
        return None
    
    # Remove path components
    filename = filename.replace('\\', '/').split('/')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Prevent hidden files
    if filename.startswith('.'):
        return None
    
    # Prevent empty filename
    if not filename:
        return None
    
    return filename


def get_client_ip(environ):
    """
    Extract client IP from WSGI environ.
    Handles proxies via X-Forwarded-For header.
    
    Args:
        environ: WSGI environment dict
    
    Returns:
        Client IP address
    """
    # Check for proxy headers
    forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(',')[0].strip()
    
    # Fall back to REMOTE_ADDR
    return environ.get('REMOTE_ADDR', '0.0.0.0')


def add_security_headers(headers):
    """
    Add security headers to response.
    
    Args:
        headers: List of (name, value) tuples
    
    Returns:
        Updated headers list
    """
    security_headers = [
        ('X-Content-Type-Options', 'nosniff'),
        ('X-Frame-Options', 'DENY'),
        ('X-XSS-Protection', '1; mode=block'),
        ('Referrer-Policy', 'strict-origin-when-cross-origin'),
        ('Content-Security-Policy', 
         "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"),
    ]
    
    # Add security headers if not already present
    header_names = {name.lower() for name, _ in headers}
    
    for name, value in security_headers:
        if name.lower() not in header_names:
            headers.append((name, value))
    
    return headers


def check_suspicious_content(content):
    """
    Check for suspicious patterns in content.
    This is a basic check - in production, use more sophisticated methods.
    
    Args:
        content: The content to check
    
    Returns:
        tuple: (is_suspicious, reason)
    """
    # Check for very long lines (potential DoS)
    lines = content.split('\n')
    max_line_length = 10000
    
    for i, line in enumerate(lines):
        if len(line) > max_line_length:
            return True, f"Line {i+1} exceeds maximum length"
    
    # Check for excessive newlines (potential DoS)
    if content.count('\n') > 100000:
        return True, "Too many newlines"
    
    # Check for common malware patterns (very basic)
    suspicious_patterns = [
        r'eval\s*\(',
        r'exec\s*\(',
        r'<script[^>]*>.*?</script>',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            return True, "Suspicious content pattern detected"
    
    return False, None


# Periodic cleanup task
def cleanup_rate_limiters():
    """Clean up old rate limiter entries."""
    paste_rate_limiter.cleanup()
    view_rate_limiter.cleanup()
