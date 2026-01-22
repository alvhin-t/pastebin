# Contributing to Pastebin

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git

### Setup Steps

1. **Fork and Clone**

```bash
git fork <repository-url>
git clone <your-fork-url>
cd pastebin
```

2. **Create Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Set Up Database**

```bash
# Create database
createdb pastebin_dev

# Run schema
psql -d pastebin_dev -f database/schema.sql
```

5. **Configure Environment**

Create `.env`:
```bash
DB_HOST=localhost
DB_NAME=pastebin_dev
DB_USER=your_username
DB_PASSWORD=your_password
DEBUG=True
```

6. **Run Tests**

```bash
pytest
```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `refactor/*` - Code refactoring

### Commit Messages

Follow the conventional commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(api): add rate limiting to paste creation

Implement in-memory rate limiter that allows 10 requests per minute
per IP address to prevent abuse.

Closes #42
```

```bash
fix(cleanup): handle database connection errors gracefully

Add try-except block around cleanup operations to prevent service
crashes when database is temporarily unavailable.
```

### Making Changes

1. **Create Feature Branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make Changes**

- Write clean, readable code
- Follow PEP 8 for Python code
- Add docstrings to functions
- Keep functions small and focused

3. **Write Tests**

```bash
# Add tests to tests/
pytest tests/test_your_feature.py
```

4. **Run Full Test Suite**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html
```

5. **Update Documentation**

- Update README.md if needed
- Update API.md for API changes
- Add docstrings to new functions

6. **Commit Changes**

```bash
git add .
git commit -m "feat(scope): description"
```

7. **Push and Create PR**

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Python

- Follow PEP 8
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use type hints where appropriate

```python
def create_paste(content: str, expiry: str) -> Optional[str]:
    """
    Create a new paste.
    
    Args:
        content: The paste content
        expiry: Expiry duration key
    
    Returns:
        Paste ID if successful, None otherwise
    """
    # Implementation...
```

### JavaScript

- Use ES6+ features
- Use 2 spaces for indentation
- Use single quotes for strings
- Use semicolons

```javascript
async function createPaste(content, expiry) {
  const response = await fetch('/api/paste', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, expiry })
  });
  
  return response.json();
}
```

### CSS

- Use kebab-case for class names
- Group related properties
- Use CSS custom properties for colors

```css
.paste-form {
  /* Layout */
  display: flex;
  flex-direction: column;
  
  /* Spacing */
  padding: var(--spacing-lg);
  
  /* Visual */
  background: var(--bg-primary);
  border-radius: var(--radius-md);
}
```

## Testing Guidelines

### Unit Tests

Test individual functions in isolation:

```python
def test_validate_paste_content():
    """Test paste content validation."""
    # Valid content
    is_valid, error = validate_paste_content("Hello, World!")
    assert is_valid is True
    assert error is None
    
    # Empty content
    is_valid, error = validate_paste_content("")
    assert is_valid is False
    assert "empty" in error.lower()
```

### Integration Tests

Test interactions between components:

```python
@pytest.mark.integration
def test_create_and_retrieve_paste(clean_database):
    """Test creating and retrieving a paste."""
    paste_id = create_paste("Test content", "1hour")
    assert paste_id is not None
    
    paste = get_paste(paste_id)
    assert paste is not None
    assert paste['content'] == "Test content"
```

### Test Coverage

- Aim for >80% code coverage
- Test edge cases and error conditions
- Test security features (XSS, rate limiting, etc.)

## Pull Request Process

1. **Update Documentation**
   - Update README if functionality changes
   - Update API docs for API changes
   - Add docstrings to new code

2. **Ensure Tests Pass**
   ```bash
   pytest
   ```

3. **Check Code Quality**
   ```bash
   # Run linter (if available)
   flake8 backend/
   
   # Check test coverage
   pytest --cov=backend --cov-report=term-missing
   ```

4. **Create Pull Request**
   - Use descriptive title
   - Reference related issues
   - Describe what changed and why
   - Add screenshots for UI changes

5. **Address Review Comments**
   - Respond to all comments
   - Make requested changes
   - Push updates to your branch

6. **Merge**
   - Squash commits if needed
   - Delete feature branch after merge

## Feature Requests

To suggest a new feature:

1. Check existing issues first
2. Create new issue with:
   - Clear description
   - Use case / motivation
   - Proposed implementation (optional)
3. Tag as `enhancement`

## Bug Reports

To report a bug:

1. Check if already reported
2. Create new issue with:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details
   - Error messages / logs
3. Tag as `bug`

## Questions

For questions:

1. Check existing documentation
2. Search closed issues
3. Create discussion or issue with `question` tag

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing! 🎉