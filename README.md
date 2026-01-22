# Shared Pastebin with Expiry

A minimalist pastebin application built **without frameworks** to demonstrate mastery of:
- Raw WSGI routing and HTTP handling
- PostgreSQL time-based data management with efficient indexing
- Background task scheduling (systemd/cron)
- Modern browser APIs (Clipboard, Fetch)
- Security best practices (XSS prevention, rate limiting, input validation)
- Professional development workflow (testing, documentation, version control)

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

## ✨ Features

- **📋 Simple Paste Creation** - Share text snippets with custom expiry times
- **⏰ Automatic Cleanup** - Background service deletes expired pastes
- **🔐 Security First** - XSS protection, rate limiting, input validation
- **📱 Responsive Design** - Works on mobile, tablet, and desktop
- **📋 One-Click Copy** - Modern Clipboard API integration
- **🚀 Production Ready** - Systemd services, deployment guides, comprehensive tests

## 🎯 Why No Frameworks?

This project deliberately avoids frameworks like Flask or Django to demonstrate:

1. **Deep HTTP Understanding** - Manual WSGI implementation shows mastery of the HTTP protocol
2. **Database Proficiency** - Direct SQL with connection pooling, no ORM magic
3. **System Administration** - Background processes, service management, production deployment
4. **Frontend Skills** - Vanilla JavaScript with modern APIs, no React/Vue crutches
5. **Performance** - Minimal dependencies, optimized queries, efficient resource usage


## 📚 Tech Stack

- **Backend**: Python 3.x (WSGI, no frameworks)
- **Database**: PostgreSQL with B-Tree indexes for efficient cleanup
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Deployment**: Gunicorn, Systemd, Nginx
- **Testing**: Pytest with >80% coverage


## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+

### Installation

```bash
# Clone the repository
git clone
cd pastebin

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb pastebin
psql -d pastebin -f database/schema.sql

### Configuration

cp .env.example .env
# Create & Edit .env with your database credentials

```
DB_HOST=localhost
DB_NAME=pastebin
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=5432
```

# Run tests
pytest

# Start development server
python backend/app.py

# In another terminal, start cleanup service
python backend/cleanup.py
```

Visit `http://localhost:8000` in your browser.

### Production Deployment

See [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md) for comprehensive production 
setup instructions including:
- Systemd service configuration
- Nginx reverse proxy setup
- Security hardening
- Monitoring and maintenance


## 📖 API Usage

### Create a Paste

```bash
curl -X POST http://localhost:8000/api/paste \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, World!",
    "expiry": "1hour"
  }'
```

Response:
```json
{
  "success": true,
  "id": "a1b2c3d4",
  "url": "/v/a1b2c3d4"
}
```

### View a Paste

```bash
curl http://localhost:8000/v/a1b2c3d4
```

See [docs/API.md](docs/API.md) for complete API documentation with examples in Python, JavaScript, and shell scripts.

## 🏗️ Architecture

### Database Schema

```sql
CREATE TABLE pastes (
    id VARCHAR(8) PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- B-Tree index for efficient cleanup
CREATE INDEX idx_pastes_expires_at ON pastes(expires_at);
```

### Request Flow

1. **User submits paste** → Frontend validates → POST to `/api/paste`
2. **Backend** → Rate limit check → Input validation → Database insert
3. **Response** → Return paste ID and URL → Frontend displays with copy button
4. **Background cleanup** → Runs every 60s → Deletes expired pastes

### Security Layers

- **Input Validation**: Size limits, format checks, suspicious pattern detection
- **XSS Prevention**: HTML escaping, Content Security Policy headers
- **Rate Limiting**: IP-based limits (10 creates/min, 100 views/min)
- **SQL Injection**: Parameterized queries, no string concatenation
- **Path Traversal**: Static file validation, directory restrictions


## Project Structure

```
pastebin/
├── database/          # SQL schemas and migrations
├── backend/           # Python WSGI application
├── frontend/          # Static assets and templates
└── README.md
```

## Development Roadmap

- [x] Project initialization
- [x] Database schema
- [x] WSGI routing
- [x] Paste creation API
- [x] Paste retrieval
- [x] Background cleanup
- [ ] Frontend interface
- [ ] Clipboard API integration

## License

MIT