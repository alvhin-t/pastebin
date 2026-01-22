# Cloud Deployment Guide (No Linux Server Needed)

This guide shows how to deploy the pastebin application using free cloud platforms.

## Recommended: Render.com (Easiest)

### Why Render?
- ✅ Free tier (no credit card required)
- ✅ Automatic deployments from GitHub
- ✅ Free PostgreSQL database
- ✅ HTTPS automatically configured
- ✅ Background workers supported
- ✅ Great for portfolios

### Step-by-Step Deployment

#### 1. Prepare Your Repository

```bash
# Make sure render.yaml is committed
git add render.yaml Procfile
git commit -m "Add Render deployment configuration"
git push origin main
```

#### 2. Sign Up for Render

1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

#### 3. Deploy Using render.yaml

1. Click **"New +"** → **"Blueprint"**
2. Connect your repository
3. Render will automatically detect `render.yaml`
4. Click **"Apply"**

Render will:
- Create a PostgreSQL database
- Create the web service
- Create the cleanup worker
- Connect everything automatically

#### 4. Run Database Schema

After deployment:

1. Go to your database in Render dashboard
2. Click **"Connect"** → **"External Connection"**
3. Copy the `psql` command
4. Run locally:
   ```bash
   # Paste the psql command from Render
   psql postgresql://user:pass@host/db
   
   # Then paste the schema
   \i database/schema.sql
   \q
   ```

Or use the Render Shell:
1. Go to your database → **"Shell"**
2. Paste the contents of `database/schema.sql`

#### 5. Verify Deployment

Your app will be live at: `https://pastebin-app.onrender.com`

**Test it:**
```bash
# Create a paste
curl -X POST https://pastebin-app.onrender.com/api/paste \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello from Render!", "expiry": "1hour"}'
```

### Troubleshooting Render

**App won't start:**
- Check logs: Dashboard → Your service → **"Logs"**
- Common issues:
  - Database not initialized (run schema)
  - Environment variables missing

**Database connection failed:**
- Verify DB_HOST uses internal hostname (not external)
- Check all env vars are set correctly

---

## Alternative: Railway.app

### Quick Deploy

1. **Sign up**: https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. **Add PostgreSQL**: Click **"+ New"** → **"Database"** → **"PostgreSQL"**
4. **Configure App**:
   - In Variables, Railway auto-sets `DATABASE_URL`
   - Add: `PORT=8000`
5. **Add Worker**:
   - New service → Same repo
   - Command: `python backend/cleanup.py`

Railway auto-detects Python and installs dependencies.

---

## Alternative: Heroku

### Setup

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create your-pastebin-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# Run schema
heroku pg:psql < database/schema.sql

# Scale worker
heroku ps:scale worker=1

# Open app
heroku open
```

**Note:** Heroku free tier was discontinued in November 2022. You'll need a paid plan (~$5/month).

---

## Docker Local Testing

Want to test locally without deploying? Use Docker:

### Prerequisites

- Install Docker Desktop: https://www.docker.com/products/docker-desktop

### Run Locally

```bash
# Build and start all services
docker-compose up --build

# Visit http://localhost:8000

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

This runs:
- PostgreSQL database
- Web application
- Cleanup worker

All automatically configured!

### Test the Deployment

```bash
# Create paste
curl -X POST http://localhost:8000/api/paste \
  -H "Content-Type: application/json" \
  -d '{"content": "Test paste", "expiry": "1hour"}'

# Check cleanup logs
docker-compose logs cleanup
```

---

## For Portfolio/Demo

### Option 1: Deploy to Render (Best)

- Live URL you can share
- Shows deployment skills
- Free hosting
- Professional presentation

### Option 2: Video Demo

Can't deploy? Record a video:

```bash
# Run locally with Docker
docker-compose up

# Record screen showing:
1. Creating a paste
2. Viewing the paste
3. Checking database (docker-compose exec db psql ...)
4. Showing cleanup logs
5. Paste expiring
```

### Option 3: Local + Screenshots

1. Run with Docker locally
2. Take screenshots of:
   - Creating paste
   - Viewing paste
   - API response
   - Database entries
   - Cleanup logs
3. Add to README

---

## Updating Deployment

### Render
```bash
# Just push to GitHub
git push origin main
# Render auto-deploys
```

### Railway
```bash
# Just push to GitHub
git push origin main
# Railway auto-deploys
```

### Heroku
```bash
# Push to Heroku
git push heroku main
```

### Docker
```bash
# Rebuild and restart
docker-compose up --build -d
```

---

## Monitoring

### Render
- Dashboard → Service → **"Metrics"**
- View logs in real-time
- Set up alerts

### Railway
- Dashboard → Service → **"Deployments"**
- Live logs
- Resource usage

### Docker Local
```bash
# View logs
docker-compose logs -f web
docker-compose logs -f cleanup

# Check status
docker-compose ps

# Database
docker-compose exec db psql -U pastebin_user -d pastebin
```

---

## Cost Comparison

| Platform | Free Tier | Paid (if needed) |
|----------|-----------|------------------|
| Render | ✅ 750 hours/month | $7/month |
| Railway | ✅ $5 credit/month | $5/month usage-based |
| Heroku | ❌ (discontinued) | $5/month minimum |
| Docker Local | ✅ Free forever | N/A |

**Recommendation for Portfolio:** Start with Render's free tier.

---

## Security for Production

If deploying publicly:

1. **Change Default Secrets**
   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

2. **Set Environment Variables** in platform dashboard:
   - `DB_PASSWORD` - Strong password
   - `DEBUG` - Set to `False`

3. **Enable HTTPS** - Automatic on Render/Railway/Heroku

4. **Monitor Logs** - Check for suspicious activity

---

## Next Steps

1. ✅ Choose a platform (Render recommended)
2. ✅ Push code to GitHub
3. ✅ Deploy using guide above
4. ✅ Test the deployment
5. ✅ Add live URL to your resume/portfolio

Questions? Check the logs first, then open an issue!