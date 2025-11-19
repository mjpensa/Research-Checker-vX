# Railway Deployment Guide

This guide covers deploying the Cross-LLM Research Synthesis System to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
3. **GitHub Repository**: Connected to Railway

## Step-by-Step Deployment

### 1. Create New Railway Project

```bash
# Install Railway CLI (optional)
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init
```

Or use the Railway dashboard: https://railway.app/new

### 2. Add Required Services

In Railway dashboard, add these services to your project:

#### PostgreSQL Database
1. Click "New Service" → "Database" → "PostgreSQL"
2. Railway automatically creates and connects it
3. Environment variable `DATABASE_URL` is auto-set

#### Redis
1. Click "New Service" → "Database" → "Redis"
2. Railway automatically creates and connects it
3. Environment variable `REDIS_URL` is auto-set

### 3. Deploy the API Service

#### Option A: Using Railway Dashboard

1. Click "New Service" → "GitHub Repo"
2. Select your repository
3. Configure:
   - **Root Directory**: `apps/api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Option B: Using Railway CLI

```bash
# From project root
cd apps/api
railway up
```

### 4. Configure Environment Variables

In Railway dashboard, go to your API service → Variables tab and add:

```bash
# Railway auto-provides these:
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
PORT=${{PORT}}

# You must add these manually:
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL=models/gemini-2.5-flash-preview-09-2025

# Application settings:
DEBUG=false
ENVIRONMENT=production

# Optional (for Phase 4):
# CLERK_SECRET_KEY=<your-clerk-key>
# CLERK_PUBLISHABLE_KEY=<your-clerk-public-key>

# Optional monitoring:
# SENTRY_DSN=<your-sentry-dsn>
```

### 5. Initialize Database

Once the API is deployed, initialize the database:

**Option A: Using Railway CLI**
```bash
railway run python packages/database/init_db.py
```

**Option B: Using Alembic (recommended for production)**
```bash
# SSH into Railway container
railway run bash

# Run migrations
cd packages/database
alembic upgrade head
```

### 6. Verify Deployment

1. **Check Health Endpoint**:
   ```bash
   curl https://your-app.railway.app/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "environment": "production"
   }
   ```

2. **Check API Docs** (only if DEBUG=true):
   ```
   https://your-app.railway.app/docs
   ```

3. **Check Logs**:
   - In Railway dashboard → Your Service → Deployments → Logs

## Service Configuration

### API Service Settings

```toml
# railway.toml (in project root)
[services.api]
source = "./apps/api"
buildCommand = "pip install -r requirements.txt"
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Scaling Settings

For production, configure:

- **Memory**: 512MB - 1GB
- **CPU**: 0.5 - 1 vCPU
- **Replicas**: 1-2 (for redundancy)
- **Restart Policy**: ON_FAILURE

### Storage Volumes (Phase 2+)

When you reach Phase 2 (file uploads), add persistent volumes:

1. Go to Service → Settings → Volumes
2. Add volumes:
   - `/mnt/uploads` (100GB)
   - `/mnt/exports` (50GB)

## Database Migrations

### Using Alembic

```bash
# Create migration
railway run alembic revision --autogenerate -m "description"

# Apply migrations
railway run alembic upgrade head

# Rollback
railway run alembic downgrade -1
```

### Manual Database Access

```bash
# Connect to PostgreSQL
railway connect Postgres

# Or get credentials
railway variables --service Postgres
```

## Monitoring & Debugging

### View Logs
```bash
railway logs
```

### Run Commands
```bash
railway run <command>
```

### Shell Access
```bash
railway run bash
```

### Check Environment Variables
```bash
railway variables
```

## Common Issues

### Issue: API won't start

**Check:**
1. Environment variables are set correctly
2. DATABASE_URL is accessible
3. REDIS_URL is accessible
4. No Python syntax errors in logs

**Fix:**
```bash
railway logs --service api
```

### Issue: Database connection error

**Check:**
1. PostgreSQL service is running
2. DATABASE_URL is correct format
3. Database migrations are applied

**Fix:**
```bash
railway connect Postgres
# Then check database exists and has tables
```

### Issue: Redis connection error

**Check:**
1. Redis service is running
2. REDIS_URL is correct

**Fix:**
```bash
railway connect Redis
# Test: PING (should return PONG)
```

### Issue: Gemini API errors

**Check:**
1. GEMINI_API_KEY is valid
2. API quota isn't exceeded
3. Model name is correct

**Test locally:**
```bash
python apps/api/test_gemini.py
```

## Cost Optimization

### Development
- Use Hobby plan ($5/month)
- 1 API instance
- Shared PostgreSQL
- Shared Redis

### Production
- Use Pro plan ($20/month+)
- 2+ API instances (redundancy)
- Dedicated database
- Enable auto-scaling

## Security Best Practices

1. **Never commit `.env` files**
2. **Use Railway's secret storage** for API keys
3. **Enable CORS** only for your frontend domain
4. **Use HTTPS** (Railway provides automatically)
5. **Regular security updates**: `pip install --upgrade`

## Next Steps After Deployment

1. **Phase 2**: Deploy worker services for async processing
2. **Phase 3**: Add dependency inference and report generation
3. **Phase 4**: Deploy Next.js frontend
4. **Phase 5**: Add monitoring, metrics, and optimization

## Useful Railway Commands

```bash
# Status
railway status

# Open in browser
railway open

# Environment info
railway environment

# Link to project
railway link

# Unlink
railway unlink

# Deployment history
railway logs --deployment <id>
```

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: https://github.com/mjpensa/Research-Checker-vX/issues

## Railway Template (Future)

Once your project is stable, you can create a Railway template button:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

This allows one-click deployment for others!
