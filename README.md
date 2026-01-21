 # Shared Pastebin with Expiry

A minimalist pastebin application built without frameworks to demonstrate:
- Raw WSGI routing
- PostgreSQL time-based data management
- Background task scheduling
- Modern browser APIs

## Features

- Share text snippets with custom expiry times
- Automatic cleanup of expired pastes
- One-click URL copying
- XSS-safe paste rendering

## Tech Stack

- Backend: Python 3.x (WSGI, no frameworks)
- Database: PostgreSQL
- Frontend: Vanilla JavaScript, HTML5, CSS3

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd pastebin

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
psql -U postgres -f database/schema.sql
```

### Configuration

Create a `.env` file in the project root:

```
DB_HOST=localhost
DB_NAME=pastebin
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=5432
```

## Running the Application

```bash
# Start the WSGI server
python backend/app.py

# In a separate terminal, start the cleanup service
python backend/cleanup.py
```

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
- [ ] Database schema
- [ ] WSGI routing
- [ ] Paste creation API
- [ ] Paste retrieval
- [ ] Background cleanup
- [ ] Frontend interface
- [ ] Clipboard API integration

## License

MIT