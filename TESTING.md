# Testing Guide - Phase 1

This guide covers testing the Phase 1 foundation before deploying to Railway.

## Local Testing (Optional)

If you want to test locally before deploying to Railway:

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Setup

1. **Create local database**:
```bash
createdb llm_synthesis
```

2. **Start Redis**:
```bash
redis-server
```

3. **Set up environment**:
```bash
cd apps/api
cp .env.example .env

# Edit .env and set:
DATABASE_URL=postgresql://localhost/llm_synthesis
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_actual_gemini_key
DEBUG=true
```

4. **Install dependencies**:
```bash
cd apps/api
pip install -r requirements.txt
```

5. **Initialize database**:
```bash
cd packages/database
pip install -r requirements.txt
python init_db.py
```

### Run Tests

#### Test API Startup
```bash
cd apps/api
python test_api.py
```

Expected output:
```
✅ Configuration loaded
✅ Database connection established
✅ Redis connection established
✅ Module imports successful
```

#### Test Gemini Integration
```bash
cd apps/api
python test_gemini.py
```

Expected output:
```
✅ Response received
✅ JSON response received
✅ Cache is working
✅ Token estimation working
```

#### Start API Server
```bash
cd apps/api
python main.py

# Or with uvicorn:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Test Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Root
curl http://localhost:8000/

# API Docs (if DEBUG=true)
open http://localhost:8000/docs
```

## Railway Testing (Recommended)

### Quick Start

1. **Create Railway project** with:
   - PostgreSQL service
   - Redis service
   - API service (from GitHub)

2. **Set environment variables** in Railway:
   ```
   GEMINI_API_KEY=<your-key>
   DEBUG=true
   ENVIRONMENT=development
   ```

3. **Initialize database**:
   ```bash
   railway run python packages/database/init_db.py
   ```

4. **Test health endpoint**:
   ```bash
   curl https://your-app.railway.app/health
   ```

### Verification Checklist

- [ ] Railway project created
- [ ] PostgreSQL service running
- [ ] Redis service running
- [ ] API service deployed
- [ ] Environment variables set
- [ ] Database initialized
- [ ] Health check returns 200 OK
- [ ] Logs show no errors

## Troubleshooting

### Database Connection Issues

**Error**: `connection refused`
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
railway run psql $DATABASE_URL
```

**Fix**: Ensure PostgreSQL service is running in Railway

### Redis Connection Issues

**Error**: `redis.exceptions.ConnectionError`
```bash
# Check REDIS_URL
echo $REDIS_URL

# Test connection
railway run redis-cli -u $REDIS_URL ping
```

**Fix**: Ensure Redis service is running in Railway

### Gemini API Issues

**Error**: `API key not valid`
```bash
# Check API key is set
railway variables | grep GEMINI
```

**Fix**:
1. Get key from https://aistudio.google.com/app/apikey
2. Set in Railway: `railway variables --set GEMINI_API_KEY=<your-key>`

### Import Errors

**Error**: `ModuleNotFoundError`
```bash
# Check dependencies installed
railway run pip list

# Reinstall
railway run pip install -r requirements.txt
```

## Performance Tests

### Database Query Performance
```python
# Test in Railway shell
railway run python

>>> import asyncio
>>> from core.database import get_db
>>> # Run test queries
```

### Redis Cache Performance
```python
# Test cache hit rates
railway run python

>>> from core.redis import redis_client
>>> # Test cache operations
```

### Gemini API Response Time
```bash
# Run Gemini test
railway run python apps/api/test_gemini.py
```

## Next Steps

Once all tests pass:

1. ✅ Phase 1 is complete
2. → Proceed to Phase 2: Core Pipeline
3. → Implement file upload system
4. → Add background workers
5. → Create API endpoints

## Test Results Log

Document your test results:

```
Date: _______________
Environment: Railway / Local
Database: ✅ / ❌
Redis: ✅ / ❌
API: ✅ / ❌
Gemini: ✅ / ❌
Notes: _______________
```

## Automated Testing (Future)

In Phase 5, we'll add:
- Unit tests with pytest
- Integration tests
- API endpoint tests
- Load testing
- CI/CD pipeline

For now, manual testing is sufficient for Phase 1.
