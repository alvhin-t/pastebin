# API Documentation

This document describes the HTTP API for the pastebin application.

## Base URL

```
http://localhost:8000
```

In production, replace with your domain (e.g., `https://paste.example.com`).

## Endpoints

### 1. Create Paste

Create a new paste with automatic expiry.

**Endpoint:** `POST /api/paste`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "Your paste content here",
  "expiry": "1day"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | Yes | The text content to paste (max 1MB) |
| expiry | string | No | Expiry duration (default: "1day") |

**Expiry Options:**
- `10min` - 10 minutes
- `1hour` - 1 hour
- `1day` - 1 day
- `1week` - 1 week
- `1month` - 1 month
- `never` - Never (100 years)

**Success Response (201 Created):**
```json
{
  "success": true,
  "id": "a1b2c3d4",
  "url": "/v/a1b2c3d4"
}
```

**Error Responses:**

400 Bad Request:
```json
{
  "error": "Content cannot be empty"
}
```

429 Too Many Requests:
```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```

**Rate Limits:**
- 10 requests per minute per IP address

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/paste \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, World!",
    "expiry": "1hour"
  }'
```

**Example (Python):**
```python
import requests

response = requests.post('http://localhost:8000/api/paste', json={
    'content': 'Hello, World!',
    'expiry': '1hour'
})

data = response.json()
if data['success']:
    print(f"Paste created: {data['url']}")
```

**Example (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/api/paste', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        content: 'Hello, World!',
        expiry: '1hour'
    })
});

const data = await response.json();
if (data.success) {
    console.log(`Paste created: ${data.url}`);
}
```

---

### 2. View Paste

Retrieve a paste by its ID (if not expired).

**Endpoint:** `GET /v/{paste_id}`

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| paste_id | string | Yes | 8-character paste identifier |

**Success Response (200 OK):**

Returns HTML page with the paste content.

**Error Responses:**

400 Bad Request:
- Invalid paste ID format

404 Not Found:
- Paste does not exist or has expired

429 Too Many Requests:
- Rate limit exceeded (100 requests per minute per IP)

**Example (curl):**
```bash
curl http://localhost:8000/v/a1b2c3d4
```

**Example (Python):**
```python
import requests

paste_id = 'a1b2c3d4'
response = requests.get(f'http://localhost:8000/v/{paste_id}')

if response.status_code == 200:
    print(response.text)
```

---

## Error Handling

All error responses follow this format:

```json
{
  "error": "Error message description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Paste created successfully |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Paste doesn't exist or expired |
| 413 | Payload Too Large - Content exceeds 1MB |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

---

## Security

### Content Security

- All paste content is sanitized before display
- HTML/JavaScript is escaped to prevent XSS attacks
- Content is validated for size and format

### Rate Limiting

- Paste creation: 10 requests per minute per IP
- Paste viewing: 100 requests per minute per IP

### Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`

---

## Best Practices

### 1. Always Check Response Status

```python
response = requests.post(url, json=data)
if response.status_code == 201:
    # Success
    paste_data = response.json()
else:
    # Error
    error = response.json().get('error')
    print(f"Error: {error}")
```

### 2. Handle Rate Limits

```python
import time

def create_paste_with_retry(content, expiry, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json={'content': content, 'expiry': expiry})
        
        if response.status_code == 429:
            # Rate limited, wait and retry
            time.sleep(60)
            continue
        
        return response.json()
    
    raise Exception("Max retries exceeded")
```

### 3. Validate Content Size

```python
MAX_SIZE = 1024 * 1024  # 1MB

def create_paste(content):
    if len(content.encode('utf-8')) > MAX_SIZE:
        raise ValueError("Content too large")
    
    # Create paste...
```

---

## Integration Examples

### Shell Script

```bash
#!/bin/bash

# Create paste from file
create_paste() {
    local file=$1
    local expiry=${2:-1day}
    
    content=$(cat "$file")
    
    curl -X POST http://localhost:8000/api/paste \
        -H "Content-Type: application/json" \
        -d "{\"content\": $(jq -Rs . <<< "$content"), \"expiry\": \"$expiry\"}" \
        | jq -r '.url'
}

# Usage
url=$(create_paste my_code.py 1week)
echo "Paste created: http://localhost:8000$url"
```

### Python CLI Tool

```python
#!/usr/bin/env python3
import sys
import requests
import argparse

def create_paste(content, expiry='1day'):
    response = requests.post(
        'http://localhost:8000/api/paste',
        json={'content': content, 'expiry': expiry}
    )
    
    if response.status_code == 201:
        data = response.json()
        return f"http://localhost:8000{data['url']}"
    else:
        raise Exception(response.json().get('error'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a paste')
    parser.add_argument('file', help='File to paste')
    parser.add_argument('--expiry', default='1day', help='Expiry time')
    
    args = parser.parse_args()
    
    with open(args.file) as f:
        content = f.read()
    
    url = create_paste(content, args.expiry)
    print(url)
```

---

## Changelog

### Version 1.0 (Current)
- Initial release
- Create and view pastes
- Automatic expiry
- Rate limiting
- XSS protection