"""
Integration tests for the WSGI API.
Tests HTTP endpoints, request handling, and response formatting.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from io import BytesIO

from app import (
    application, 
    create_paste, 
    get_paste, 
    generate_paste_id,
    read_request_body
)
import config


@pytest.mark.unit
class TestHelperFunctions:
    """Test helper functions."""
    
    def test_generate_paste_id(self):
        """Test paste ID generation."""
        paste_id = generate_paste_id()
        
        assert isinstance(paste_id, str)
        assert len(paste_id) == config.PASTE_ID_LENGTH
        assert paste_id.isalnum() or '-' in paste_id or '_' in paste_id
    
    def test_generate_unique_ids(self):
        """Test that generated IDs are unique."""
        ids = set(generate_paste_id() for _ in range(100))
        assert len(ids) == 100  # All should be unique


@pytest.mark.integration
class TestCreatePaste:
    """Test paste creation function."""
    
    def test_create_paste_valid(self, clean_database):
        """Test creating a valid paste."""
        content = "Test content"
        expiry = "1hour"
        
        paste_id = create_paste(content, expiry)
        
        assert paste_id is not None
        assert len(paste_id) == config.PASTE_ID_LENGTH
        
        # Verify in database
        clean_database.execute("SELECT content FROM pastes WHERE id = %s", (paste_id,))
        result = clean_database.fetchone()
        
        assert result is not None
        assert result[0] == content
    
    def test_create_paste_with_different_expiries(self, clean_database):
        """Test creating pastes with different expiry times."""
        expiries = ['10min', '1hour', '1day', '1week', '1month']
        
        for expiry in expiries:
            paste_id = create_paste(f"Content for {expiry}", expiry)
            assert paste_id is not None
            
            # Clean up
            clean_database.execute("DELETE FROM pastes WHERE id = %s", (paste_id,))
    
    def test_create_paste_invalid_expiry_uses_default(self, clean_database):
        """Test that invalid expiry uses default."""
        paste_id = create_paste("Test", "invalid_expiry")
        
        assert paste_id is not None
        
        # Clean up
        clean_database.execute("DELETE FROM pastes WHERE id = %s", (paste_id,))


@pytest.mark.integration
class TestGetPaste:
    """Test paste retrieval function."""
    
    def test_get_existing_paste(self, sample_paste):
        """Test getting an existing, non-expired paste."""
        paste = get_paste(sample_paste['id'])
        
        assert paste is not None
        assert paste['content'] == sample_paste['content']
        assert 'expires_at' in paste
    
    def test_get_expired_paste_returns_none(self, expired_paste):
        """Test that expired pastes return None."""
        paste = get_paste(expired_paste['id'])
        
        assert paste is None
    
    def test_get_nonexistent_paste(self):
        """Test getting a paste that doesn't exist."""
        paste = get_paste("nonexist")
        
        assert paste is None


@pytest.mark.integration
class TestWSGIApplication:
    """Test the WSGI application endpoints."""
    
    def make_request(self, method='GET', path='/', body=None, headers=None):
        """Helper to make WSGI requests."""
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'wsgi.input': BytesIO(body.encode('utf-8') if body else b''),
            'CONTENT_LENGTH': str(len(body.encode('utf-8'))) if body else '0',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8000',
            'wsgi.url_scheme': 'http',
        }
        
        if headers:
            environ.update(headers)
        
        response_status = None
        response_headers = None
        
        def start_response(status, headers):
            nonlocal response_status, response_headers
            response_status = status
            response_headers = headers
        
        response_body = application(environ, start_response)
        
        return {
            'status': response_status,
            'headers': dict(response_headers),
            'body': b''.join(response_body).decode('utf-8')
        }
    
    def test_home_page(self):
        """Test GET / returns HTML."""
        response = self.make_request('GET', '/')
        
        assert '200 OK' in response['status']
        assert 'text/html' in response['headers']['Content-Type']
        assert 'Pastebin' in response['body']
    
    def test_create_paste_endpoint(self, clean_database):
        """Test POST /api/paste creates a paste."""
        data = {
            'content': 'Test paste via API',
            'expiry': '1hour'
        }
        
        response = self.make_request(
            'POST', 
            '/api/paste',
            body=json.dumps(data)
        )
        
        assert '201 Created' in response['status']
        assert 'application/json' in response['headers']['Content-Type']
        
        result = json.loads(response['body'])
        assert result['success'] is True
        assert 'id' in result
        assert 'url' in result
        
        # Clean up
        clean_database.execute("DELETE FROM pastes WHERE id = %s", (result['id'],))
    
    def test_create_paste_empty_content(self):
        """Test POST /api/paste with empty content."""
        data = {
            'content': '',
            'expiry': '1hour'
        }
        
        response = self.make_request(
            'POST',
            '/api/paste',
            body=json.dumps(data)
        )
        
        assert '400 Bad Request' in response['status']
        result = json.loads(response['body'])
        assert 'error' in result
    
    def test_create_paste_invalid_json(self):
        """Test POST /api/paste with invalid JSON."""
        response = self.make_request(
            'POST',
            '/api/paste',
            body='not json'
        )
        
        assert '400 Bad Request' in response['status']
    
    def test_view_paste_endpoint(self, sample_paste):
        """Test GET /v/{id} returns paste."""
        response = self.make_request('GET', f'/v/{sample_paste["id"]}')
        
        assert '200 OK' in response['status']
        assert 'text/html' in response['headers']['Content-Type']
        assert sample_paste['content'] in response['body']
    
    def test_view_expired_paste(self, expired_paste):
        """Test GET /v/{id} for expired paste."""
        response = self.make_request('GET', f'/v/{expired_paste["id"]}')
        
        assert '404 Not Found' in response['status']
    
    def test_view_invalid_paste_id(self):
        """Test GET /v/{id} with invalid ID."""
        response = self.make_request('GET', '/v/invalid')
        
        assert '400 Bad Request' in response['status']
    
    def test_static_file_serving(self):
        """Test GET /static/* serves files."""
        response = self.make_request('GET', '/static/css/style.css')
        
        # This will 404 in test environment without actual files
        # but tests the routing logic
        assert response['status'] in ['200 OK', '404 Not Found']
    
    def test_404_for_unknown_route(self):
        """Test that unknown routes return 404."""
        response = self.make_request('GET', '/unknown/route')
        
        assert '404 Not Found' in response['status']


@pytest.mark.unit
class TestRequestParsing:
    """Test request body parsing."""
    
    def test_read_request_body(self):
        """Test reading request body."""
        body_text = "test content"
        environ = {
            'CONTENT_LENGTH': str(len(body_text)),
            'wsgi.input': BytesIO(body_text.encode('utf-8'))
        }
        
        result = read_request_body(environ)
        assert result == body_text
    
    def test_read_empty_body(self):
        """Test reading empty request body."""
        environ = {
            'CONTENT_LENGTH': '0',
            'wsgi.input': BytesIO(b'')
        }
        
        result = read_request_body(environ)
        assert result == ''
    
    def test_read_oversized_body(self):
        """Test reading body that exceeds max size."""
        environ = {
            'CONTENT_LENGTH': str(config.MAX_CONTENT_LENGTH + 1),
            'wsgi.input': BytesIO(b'x' * (config.MAX_CONTENT_LENGTH + 1))
        }
        
        result = read_request_body(environ)
        assert result is None
