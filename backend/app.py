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
from .db import DatabaseConnection, init_pool, close_pool, ensure_tables_exist, cleanup_expired_pastes
from security import (
    paste_rate_limiter,
    view_rate_limiter,
    validate_paste_content,
    validate_paste_id,
    get_client_ip,
    add_security_headers,
    check_suspicious_content
)

# --- UTILITY FUNCTIONS ---

def generate_paste_id():
    """Generate a random 8-character paste ID."""
    return secrets.token_urlsafe(6)[:config.PASTE_ID_LENGTH]

def create_paste(content, expiry_key):
    """Create a new paste in the database."""
    if not config.is_valid_expiry(expiry_key):
        expiry_key = config.DEFAULT_EXPIRY
    
    expiry_delta = config.get_expiry_timedelta(expiry_key)
    expires_at = datetime.now(timezone.utc) + expiry_delta
    paste_id = generate_paste_id()
    
    try:
        with DatabaseConnection() as db:
            db.execute(
                "INSERT INTO pastes (id, content, expires_at) VALUES (%s, %s, %s) RETURNING id",
                (paste_id, content, expires_at)
            )
            result = db.fetchone()
            return result[0] if result else None
    except Exception:
        return None

def get_paste(paste_id):
    """Retrieve a paste by ID if it hasn't expired."""
    try:
        with DatabaseConnection() as db:
            db.execute(
                "SELECT content, expires_at FROM pastes WHERE id = %s AND expires_at > NOW()",
                (paste_id,)
            )
            result = db.fetchone()
            if result:
                return {'content': result[0], 'expires_at': result[1]}
            return None
    except Exception:
        return None

# --- RESPONSE HELPERS ---

def read_request_body(environ):
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
    response_body = json.dumps(data).encode('utf-8')
    headers = [('Content-Type', 'application/json'), ('Content-Length', str(len(response_body)))]
    headers = add_security_headers(headers)
    start_response(status, headers)
    return [response_body]

def html_response(start_response, html_content, status='200 OK'):
    response_body = html_content.encode('utf-8')
    headers = [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(response_body)))]
    headers = add_security_headers(headers)
    start_response(status, headers)
    return [response_body]

def render_template(template_name, context=None):
    if context is None: context = {}
    base_dir = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, 'frontend', 'templates', template_name)
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        for key, value in context.items():
            template = template.replace(f'{{{key}}}', str(value))
        return template
    except Exception:
        return "<h1>Template Error</h1>"

def serve_static_file(start_response, path):
    relative_path = path.replace('/static/', '', 1).lstrip('/')
    if '..' in relative_path or relative_path.startswith('/'):
        return html_response(start_response, '<h1>403 Forbidden</h1>', '403 Forbidden')
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    full_path = os.path.join(project_root, 'frontend', 'static', relative_path)
    
    if not os.path.isfile(full_path):
        return html_response(start_response, '<h1>404 Not Found</h1>', '404 Not Found')
    
    content_type, _ = mimetypes.guess_type(full_path)
    with open(full_path, 'rb') as f:
        content = f.read()
    
    headers = [('Content-Type', content_type or 'application/octet-stream'), ('Content-Length', str(len(content)))]
    start_response('200 OK', headers)
    return [content]

# --- APP STARTUP ---

def setup_app():
    """Perform all one-time startup tasks."""
    if init_pool():
        ensure_tables_exist()
        cleanup_expired_pastes()
        print("🚀 Startup tasks completed successfully")
    else:
        print("⚠️ Startup failed: Database connection error")

# Execute startup
setup_app()

# --- WSGI APPLICATION ---

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if path == '/' and method == 'GET':
        return html_response(start_response, render_template('index.html'))
    
    elif path == '/api/paste' and method == 'POST':
        client_ip = get_client_ip(environ)
        if not paste_rate_limiter.is_allowed(client_ip):
            return json_response(start_response, {'error': 'Too many requests'}, '429 Too Many Requests')
        
        body = read_request_body(environ)
        if not body: return json_response(start_response, {'error': 'No content'}, '400 Bad Request')
        
        try:
            data = json.loads(body)
            content = data.get('content', '').strip()
            expiry = data.get('expiry', config.DEFAULT_EXPIRY)
            
            is_valid, error_msg = validate_paste_content(content)
            if not is_valid: return json_response(start_response, {'error': error_msg}, '400 Bad Request')
            
            is_suspicious, reason = check_suspicious_content(content)
            if is_suspicious: return json_response(start_response, {'error': f'Rejected: {reason}'}, '400 Bad Request')
            
            paste_id = create_paste(content, expiry)
            return json_response(start_response, {'success': True, 'id': paste_id, 'url': f'/v/{paste_id}'}, '201 Created') if paste_id else json_response(start_response, {'error': 'Database error'}, '500 Internal Server Error')
        except Exception:
            return json_response(start_response, {'error': 'Invalid request'}, '400 Bad Request')

    elif path.startswith('/v/') and method == 'GET':
        paste_id = path[3:]
        if not validate_paste_id(paste_id):
            return html_response(start_response, render_template('view.html', {'paste_id': 'Error', 'content': 'Invalid ID', 'expires_at': 'N/A'}), '400 Bad Request')
        
        paste = get_paste(paste_id)
        if paste:
            return html_response(start_response, render_template('view.html', {
                'paste_id': html.escape(paste_id),
                'content': html.escape(paste['content']),
                'expires_at': paste['expires_at'].strftime('%Y-%m-%d %H:%M:%S UTC')
            }))
        return html_response(start_response, render_template('view.html', {'paste_id': '404', 'content': 'Paste expired or not found', 'expires_at': 'N/A'}), '404 Not Found')

    elif path.startswith('/static/') and method == 'GET':
        return serve_static_file(start_response, path)
    
    return html_response(start_response, '<h1>404 Not Found</h1>', '404 Not Found')

if __name__ == '__main__':
    with make_server(config.HOST, config.PORT, application) as httpd:
        print(f"🚀 Dev server: http://{config.HOST}:{config.PORT}")
        httpd.serve_forever()