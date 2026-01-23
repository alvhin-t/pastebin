"""
WSGI Application - No Framework
Handles HTTP routing and request processing manually.
"""

import json
import secrets
import html
import os
import mimetypes
from datetime import datetime, timezone
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from . import config
from .db import DatabaseConnection, init_pool, close_pool
from security import (
    paste_rate_limiter,
    view_rate_limiter,
    validate_paste_content,
    validate_paste_id,
    get_client_ip,
    add_security_headers,
    check_suspicious_content
)


def generate_paste_id():
    """Generate a random 8-character paste ID."""
    return secrets.token_urlsafe(6)[:config.PASTE_ID_LENGTH]


def create_paste(content, expiry_key):
    """
    Create a new paste in the database.
    
    Args:
        content: The paste content
        expiry_key: Expiry duration key (e.g., '1hour', '1day')
    
    Returns:
        Paste ID if successful, None otherwise
    """
    # Validate expiry
    if not config.is_valid_expiry(expiry_key):
        expiry_key = config.DEFAULT_EXPIRY
    
    # Calculate expiry time
    expiry_delta = config.get_expiry_timedelta(expiry_key)
    expires_at = datetime.now(timezone.utc) + expiry_delta
    
    # Generate unique ID
    paste_id = generate_paste_id()
    
    try:
        with DatabaseConnection() as cursor:
            cursor.execute(
                """
                INSERT INTO pastes (id, content, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (paste_id, content, expires_at)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error creating paste: {e}")
        return None


def get_paste(paste_id):
    """
    Retrieve a paste by ID if it hasn't expired.
    
    Args:
        paste_id: The paste ID
    
    Returns:
        Paste content if found and not expired, None otherwise
    """
    try:
        with DatabaseConnection() as cursor:
            cursor.execute(
                """
                SELECT content, expires_at 
                FROM pastes 
                WHERE id = %s AND expires_at > NOW()
                """,
                (paste_id,)
            )
            result = cursor.fetchone()
            if result:
                return {'content': result[0], 'expires_at': result[1]}
            return None
    except Exception as e:
        print(f"Error retrieving paste: {e}")
        return None


def read_request_body(environ):
    """Read and parse the request body."""
    try:
        content_length = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        content_length = 0
    
    if content_length > config.MAX_CONTENT_LENGTH:
        return None
    
    if content_length > 0:
        body = environ['wsgi.input'].read(content_length)
        return body.decode('utf-8')
    
    return ''


def json_response(start_response, data, status='200 OK'):
    """Helper to create JSON responses."""
    response_body = json.dumps(data).encode('utf-8')
    headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body)))
    ]
    headers = add_security_headers(headers)
    start_response(status, headers)
    return [response_body]


def html_response(start_response, html_content, status='200 OK'):
    """Helper to create HTML responses."""
    response_body = html_content.encode('utf-8')
    headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(response_body)))
    ]
    headers = add_security_headers(headers)
    start_response(status, headers)
    return [response_body]


def serve_static_file(start_response, path):
    """Serve static files (CSS, JS, images)."""
    
    relative_path = path.replace('/static/', '', 1).lstrip('/')

    # Security: prevent directory traversal
    if '..' in relative_path or relative_path.startswith('/'):
        return html_response(start_response, '<h1>403 Forbidden</h1>', '403 Forbidden')
    
    # Construct full path
    base_dir = os.path.dirname(os.path.dirname(__file__))
    full_path = os.path.join(base_dir, 'frontend', 'static', relative_path)
    
    # Extra security: Ensure the resolved path is actually inside the frontend folder
    if not full_path.startswith(os.path.join(base_dir, 'frontend')):
         return html_response(start_response, '<h1>403 Forbidden</h1>', '403     Forbidden')

    # Check if file exists
    if not os.path.isfile(full_path):
        print(f"DEBUG: File not found at {full_path}") # This will show in Render logs
        return html_response(start_response, '<h1>404 Not Found</h1>', '404 Not Found')
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(full_path)
    if content_type is None:
        content_type = 'application/octet-stream'
    
    try:
        with open(full_path, 'rb') as f:
            content = f.read()
        
        headers = [
            ('Content-Type', content_type),
            ('Content-Length', str(len(content))),
            ('Cache-Control', 'public, max-age=86400')  # Cache for 1 day
        ]
        start_response('200 OK', headers)
        return [content]
    
    except Exception as e:
        print(f"Error serving static file {filepath}: {e}")
        return html_response(start_response, '<h1>500 Internal Server Error</h1>', '500 Internal Server Error')


def render_template(template_name, context=None):
    """
    Simple template rendering with variable substitution.
    Supports {variable_name} syntax.
    """
    if context is None:
        context = {}
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, 'frontend', 'templates', template_name)
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Simple variable substitution
        for key, value in context.items():
            template = template.replace(f'{{{key}}}', str(value))
        
        return template
    
    except FileNotFoundError:
        return f"<h1>Template not found: {template_name}</h1>"
    except Exception as e:
        print(f"Error rendering template {template_name}: {e}")
        return "<h1>Error rendering template</h1>"


def application(environ, start_response):
    """
    WSGI application entry point.
    Manually routes requests based on PATH_INFO.
    """
    
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Route: Home page (GET /)
    if path == '/' and method == 'GET':
        html = render_template('index.html')
        return html_response(start_response, html)
    
    # Route: Create paste (POST /api/paste)
    elif path == '/api/paste' and method == 'POST':
        # Rate limiting
        client_ip = get_client_ip(environ)
        if not paste_rate_limiter.is_allowed(client_ip):
            return json_response(
                start_response,
                {'error': 'Rate limit exceeded. Please try again later.'},
                '429 Too Many Requests'
            )
        
        body = read_request_body(environ)
        if not body:
            return json_response(
                start_response,
                {'error': 'No content provided'},
                '400 Bad Request'
            )
        
        try:
            data = json.loads(body)
            content = data.get('content', '').strip()
            expiry = data.get('expiry', config.DEFAULT_EXPIRY)
            
            # Validate content
            is_valid, error_msg = validate_paste_content(content)
            if not is_valid:
                return json_response(
                    start_response,
                    {'error': error_msg},
                    '400 Bad Request'
                )
            
            # Check for suspicious content
            is_suspicious, reason = check_suspicious_content(content)
            if is_suspicious:
                return json_response(
                    start_response,
                    {'error': f'Content rejected: {reason}'},
                    '400 Bad Request'
                )
            
            paste_id = create_paste(content, expiry)
            
            if paste_id:
                return json_response(
                    start_response,
                    {
                        'success': True,
                        'id': paste_id,
                        'url': f'/v/{paste_id}'
                    },
                    '201 Created'
                )
            else:
                return json_response(
                    start_response,
                    {'error': 'Failed to create paste'},
                    '500 Internal Server Error'
                )
        
        except json.JSONDecodeError:
            return json_response(
                start_response,
                {'error': 'Invalid JSON'},
                '400 Bad Request'
            )
    
    # Route: View paste (GET /v/{id})
    elif path.startswith('/v/') and method == 'GET':
        # Rate limiting
        client_ip = get_client_ip(environ)
        if not view_rate_limiter.is_allowed(client_ip):
            return html_response(
                start_response,
                '<h1>429 Too Many Requests</h1><p>Please slow down.</p>',
                '429 Too Many Requests'
            )
        
        paste_id = path[3:]  # Remove '/v/' prefix
        
        # Validate paste ID
        if not validate_paste_id(paste_id):
            html = render_template('view.html', {
                'paste_id': 'Invalid',
                'content': 'Invalid paste ID format',
                'expires_at': 'N/A'
            })
            return html_response(start_response, html, '400 Bad Request')
        
        paste = get_paste(paste_id)
        
        if paste:
            # Escape content to prevent XSS
            safe_content = html.escape(paste['content'])
            html_content = render_template('view.html', {
                'paste_id': html.escape(paste_id),
                'content': safe_content,
                'expires_at': paste['expires_at'].strftime('%Y-%m-%d %H:%M:%S UTC')
            })
            return html_response(start_response, html_content)
        else:
            html_content = render_template('view.html', {
                'paste_id': 'Not Found',
                'content': 'This paste does not exist or has expired.',
                'expires_at': 'N/A'
            })
            return html_response(start_response, html_content, '404 Not Found')
    
    # Route: Static files (GET /static/*)
    elif path.startswith('/static/') and method == 'GET':
        return serve_static_file(start_response, path)
    
    # Route: 404 for everything else
    else:
        return html_response(
            start_response,
            '<h1>404 Not Found</h1>',
            '404 Not Found'
        )


def run_server():
    """Start the WSGI server."""
    init_pool()
    
    try:
        with make_server(config.HOST, config.PORT, application) as httpd:
            print(f"🚀 Server running on http://{config.HOST}:{config.PORT}")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹ Shutting down server...")
    finally:
        close_pool()


if __name__ == '__main__':
    run_server()