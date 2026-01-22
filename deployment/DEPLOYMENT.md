# Deployment Guide

This guide covers deploying the pastebin application to a production Linux server.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- PostgreSQL 12+
- Python 3.8+
- sudo access

## Installation Steps

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx

# Create application user (optional but recommended)
sudo useradd -r -s /bin/bash -d /var/www/pastebin pastebin
```

### 2. Application Deployment

```bash
# Create application directory
sudo mkdir -p /var/www/pastebin
sudo chown pastebin:pastebin /var/www/pastebin

# Clone or copy your application
cd /var/www/pastebin
# git clone <your-repo> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE pastebin;
CREATE USER pastebin_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE pastebin TO pastebin_user;
EOF

# Run schema
sudo -u postgres psql -d pastebin -f database/schema.sql

# Grant permissions
sudo -u postgres psql -d pastebin << EOF
GRANT ALL PRIVILEGES ON TABLE pastes TO pastebin_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pastebin_user;
EOF
```

### 4. Environment Configuration

```bash
# Create .env file
cat > /var/www/pastebin/.env << EOF
DB_HOST=localhost
DB_NAME=pastebin
DB_USER=pastebin_user
DB_PASSWORD=your_secure_password
DB_PORT=5432

HOST=0.0.0.0
PORT=8000
DEBUG=False

CLEANUP_INTERVAL=60
EOF

# Secure the .env file
chmod 600 /var/www/pastebin/.env
chown pastebin:pastebin /var/www/pastebin/.env
```

### 5. Create Log Directory

```bash
sudo mkdir -p /var/www/pastebin/logs
sudo chown pastebin:pastebin /var/www/pastebin/logs
sudo chmod 755 /var/www/pastebin/logs
```

## Deployment Options

### Option A: Systemd Services (Recommended)

This approach runs both the app and cleanup service as systemd services.

```bash
# Copy service files
sudo cp deployment/pastebin-app.service /etc/systemd/system/
sudo cp deployment/pastebin-cleanup.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable pastebin-app
sudo systemctl enable pastebin-cleanup

# Start services
sudo systemctl start pastebin-app
sudo systemctl start pastebin-cleanup

# Check status
sudo systemctl status pastebin-app
sudo systemctl status pastebin-cleanup
```

**Managing the services:**

```bash
# View logs
sudo journalctl -u pastebin-app -f
sudo journalctl -u pastebin-cleanup -f

# Restart services
sudo systemctl restart pastebin-app
sudo systemctl restart pastebin-cleanup

# Stop services
sudo systemctl stop pastebin-app
sudo systemctl stop pastebin-cleanup
```

### Option B: Cron Job for Cleanup

Use this if you prefer cron over systemd for the cleanup task.

```bash
# Edit crontab for the pastebin user
sudo -u pastebin crontab -e

# Add one of these lines (choose based on your needs):

# Every minute (development/testing)
* * * * * cd /var/www/pastebin && /var/www/pastebin/venv/bin/python backend/cleanup.py --once >> /var/www/pastebin/logs/cron.log 2>&1

# Every 5 minutes (production)
*/5 * * * * cd /var/www/pastebin && /var/www/pastebin/venv/bin/python backend/cleanup.py --once >> /var/www/pastebin/logs/cron.log 2>&1

# Verify crontab
sudo -u pastebin crontab -l
```

## Nginx Reverse Proxy (Optional)

For production, put Nginx in front of your app:

```bash
# Create Nginx config
sudo tee /etc/nginx/sites-available/pastebin << 'EOF'
server {
    listen 80;
    server_name paste.yourdomain.com;

    client_max_body_size 2M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/pastebin/frontend/static/;
        expires 1d;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/pastebin /etc/nginx/sites-enabled/

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

## Monitoring

### Check Application Health

```bash
# Check if app is responding
curl http://localhost:8000/

# Check database connection
sudo -u pastebin /var/www/pastebin/venv/bin/python backend/db.py
```

### View Logs

```bash
# Application logs (systemd)
sudo journalctl -u pastebin-app -n 100

# Cleanup logs (systemd)
sudo journalctl -u pastebin-cleanup -n 100

# Cleanup logs (file-based)
tail -f /var/www/pastebin/logs/cleanup.log

# Cron logs
tail -f /var/www/pastebin/logs/cron.log
```

### Database Statistics

```bash
# Connect to database
sudo -u postgres psql -d pastebin

# Check paste counts
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE expires_at > NOW()) as active,
    COUNT(*) FILTER (WHERE expires_at <= NOW()) as expired
FROM pastes;

# Check recent pastes
SELECT id, created_at, expires_at 
FROM pastes 
ORDER BY created_at DESC 
LIMIT 10;
```

## Maintenance

### Update Application

```bash
# Pull latest changes
cd /var/www/pastebin
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart services
sudo systemctl restart pastebin-app
sudo systemctl restart pastebin-cleanup
```

### Database Backup

```bash
# Backup database
sudo -u postgres pg_dump pastebin > backup_$(date +%Y%m%d).sql

# Restore database
sudo -u postgres psql pastebin < backup_20240101.sql
```

### Log Rotation

Logs are automatically rotated by the cleanup script (10MB max, 5 backups).

For systemd journal logs:

```bash
# Check journal size
sudo journalctl --disk-usage

# Vacuum old logs (keep last 7 days)
sudo journalctl --vacuum-time=7d
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status pastebin-app
sudo systemctl status pastebin-cleanup

# View detailed logs
sudo journalctl -u pastebin-app -n 50 --no-pager
sudo journalctl -u pastebin-cleanup -n 50 --no-pager

# Check file permissions
ls -la /var/www/pastebin
```

### Database Connection Issues

```bash
# Test database connection
sudo -u pastebin psql -h localhost -U pastebin_user -d pastebin

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

## Security Checklist

- [ ] Changed default database password
- [ ] `.env` file has restricted permissions (600)
- [ ] Firewall configured (ufw/iptables)
- [ ] PostgreSQL only listening on localhost
- [ ] Application running as non-root user
- [ ] Regular security updates applied
- [ ] SSL/TLS configured (use certbot for Let's Encrypt)
- [ ] Rate limiting implemented (via Nginx)
- [ ] Regular backups configured

## Performance Tuning

### PostgreSQL

```sql
-- Add more indexes if needed
CREATE INDEX idx_pastes_created_at ON pastes(created_at DESC);

-- Analyze table statistics
ANALYZE pastes;

-- Vacuum to reclaim space
VACUUM FULL pastes;
```

### Gunicorn Workers

Adjust workers in `pastebin-app.service`:
```
--workers 4  # Use (2 * CPU cores) + 1
```

### Cleanup Interval

Adjust `CLEANUP_INTERVAL` in `.env` based on your traffic:
- High traffic: 60 seconds
- Medium traffic: 300 seconds (5 min)
- Low traffic: 3600 seconds (1 hour)