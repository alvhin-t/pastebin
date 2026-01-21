"""
WSGI Application - No Framework
Handles HTTP routing and request processing manually.
"""

import json
import secrets
import html
from datetime import datetime, timezone
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

import config
from db import DatabaseConnection, init_pool, close_pool


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
    start_response(status, headers)
    return [response_body]


def html_response(start_response, html_content, status='200 OK'):
    """Helper to create HTML responses."""
    response_body = html_content.encode('utf-8')
    headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(response_body)))
    ]
    start_response(status, headers)
    return [response_body]


def application(environ, start_response):
    """
    WSGI application entry point.
    Manually routes requests based on PATH_INFO.
    """
    
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # Route: Home page (GET /)
    if path == '/' and method == 'GET':
        # For now, return a simple HTML page
        # We'll enhance this in later commits
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pastebin - Share Text with Expiry</title>
        </head>
        <body>
            <h1>Pastebin</h1>
            <p>API Endpoints:</p>
            <ul>
                <li>POST /api/paste - Create new paste</li>
                <li>GET /v/{id} - View paste</li>
            </ul>
        </body>
        </html>
        """
        return html_response(start_response, html)
    
    # Route: Create paste (POST /api/paste)
    elif path == '/api/paste' and method == 'POST':
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
            
            if not content:
                return json_response(
                    start_response,
                    {'error': 'Content cannot be empty'},
                    '400 Bad Request'
                )
            
            if len(content.encode('utf-8')) > config.MAX_PASTE_SIZE:
                return json_response(
                    start_response,
                    {'error': 'Content too large'},
                    '413 Payload Too Large'
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
        paste_id = path[3:]  # Remove '/v/' prefix
        
        if not paste_id or len(paste_id) != config.PASTE_ID_LENGTH:
            return html_response(
                start_response,
                '<h1>Invalid paste ID</h1>',
                '400 Bad Request'
            )
        
        paste = get_paste(paste_id)
        
        if paste:
            # Escape content to prevent XSS
            safe_content = html.escape(paste['content'])
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Paste {paste_id}</title>
                <style>
                    body {{ font-family: monospace; margin: 20px; }}
                    pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h2>Paste {paste_id}</h2>
                <p>Expires: {paste['expires_at']}</p>
                <pre>{safe_content}</pre>
            </body>
            </html>
            """
            return html_response(start_response, html_content)
        else:
            return html_response(
                start_response,
                '<h1>404 Not Found</h1><p>This paste does not exist or has expired.</p>',
                '404 Not Found'
            )
    
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
