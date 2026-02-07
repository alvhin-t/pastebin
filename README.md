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

### Development Setup

```bash
# Clone repository
git clone <your-repo-url>
cd pastebin

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb pastebin
psql -d pastebin -f database/schema.sql

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run tests
pytest

# Start development server
python backend/app.py

# In another terminal, start cleanup service
python backend/cleanup.py
```

Visit `http://localhost:8000` in your browser.

### Production Deployment

See [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md) for comprehensive production setup instructions including:
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

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run only unit tests
pytest -m unit

# Run only integration tests  
pytest -m integration
```

Test coverage: >80% across all modules

## 📁 Project Structure

```
pastebin/
|── backend/
|   |── app.py              # WSGI application & routing
│   |── db.py               # Database connection pooling
|   |── config.py           # Configuration management
|   |── cleanup.py          # Background cleanup service
|   |── security.py         # Rate limiting & validation
|── frontend/
|   |── templates/          # HTML templates
|   │   |── index.html
|   |   |── view.html
|   |── static/
|       |── css/
|       │   └── style.css
|       |── js/
|           |── app.js      # Paste creation logic
│           |── view.js     # Paste viewing logic
|── database/
|   |── schema.sql          # Database schema
|── deployment/
|   |── pastebin-app.service
|   |── pastebin-cleanup.service
|   |── crontab.example
|   |── DEPLOYMENT.md
|── tests/
|   |── conftest.py
|   |── test_database.py
|   |── test_api.py
|   |── test_config.py
|   |── test_cleanup.py
|── docs/
│   |── API.md
|── .env.example
|── .gitignore
|── requirements.txt
|── pytest.ini
|── CONTRIBUTING.md
|── README.md
```

## 🎓 What This Demonstrates

### Backend Skills
- ✅ Manual WSGI implementation (no Flask/Django)
- ✅ SQL with connection pooling and indexes
- ✅ Background processes and daemon management
- ✅ Security best practices (rate limiting, validation, XSS prevention)
- ✅ Comprehensive error handling

### Frontend Skills
- ✅ Vanilla JavaScript with modern APIs (Fetch, Clipboard)
- ✅ Progressive enhancement and accessibility
- ✅ Responsive CSS without frameworks
- ✅ Client-side validation and UX polish

### DevOps Skills
- ✅ Systemd service configuration
- ✅ Production deployment documentation
- ✅ Database management and migrations
- ✅ Logging and monitoring setup

### Professional Practices
- ✅ Comprehensive testing (unit + integration)
- ✅ Git workflow with meaningful commits
- ✅ API documentation
- ✅ Contributing guidelines
- ✅ Security considerations