# Phase 2: Core Pipeline - Complete! 🎉

Phase 2 implements the core document processing pipeline with file uploads, background workers, and claim extraction.

## What's New in Phase 2

### 1. **File Upload & Storage** ✅
- Multi-format document upload (PDF, DOCX, TXT, MD, JSON)
- Text extraction from uploaded files
- SHA-256 hash calculation for integrity
- Organized storage by user and pipeline

### 2. **API Routes** ✅

#### Pipeline Management
- `POST /api/v1/pipelines/` - Create a new pipeline
- `GET /api/v1/pipelines/` - List all pipelines
- `GET /api/v1/pipelines/{id}` - Get pipeline details
- `PATCH /api/v1/pipelines/{id}` - Update pipeline
- `DELETE /api/v1/pipelines/{id}` - Delete pipeline
- `POST /api/v1/pipelines/{id}/start` - Start processing

#### Document Operations
- `POST /api/v1/pipelines/{id}/documents` - Upload documents
- `GET /api/v1/pipelines/{id}/documents` - List documents

#### Claims & Analysis
- `GET /api/v1/claims/` - List claims with filters
- `GET /api/v1/claims/{id}` - Get specific claim
- `GET /api/v1/claims/{id}/dependencies` - Get claim relationships
- `GET /api/v1/claims/pipeline/{id}/stats` - Get statistics

### 3. **Background Workers** ✅
- Redis-based job queue
- Claim extraction worker using Gemini 2.5 Flash
- Automatic retry on failures
- Job status tracking

### 4. **WebSocket Support** ✅
- Real-time pipeline status updates
- Connect at: `ws://localhost:8000/ws/pipelines/{pipeline_id}`
- Heartbeat and status messages

## Quick Start

### 1. Start the API

```bash
cd apps/api
python main.py
```

API will be available at: `http://localhost:8000`

### 2. Start the Worker

In a separate terminal:

```bash
cd apps/workers
python worker_extraction.py
```

### 3. Run the Test

```bash
cd apps/api
python test_phase2.py
```

This will:
1. Create a test pipeline
2. Upload a sample document
3. Start processing
4. Monitor claim extraction
5. Display extracted claims

## API Usage Examples

### Create a Pipeline

```bash
curl -X POST http://localhost:8000/api/v1/pipelines/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Research Analysis",
    "metadata": {"project": "AI Research"}
  }'
```

### Upload Documents

```bash
curl -X POST http://localhost:8000/api/v1/pipelines/{pipeline_id}/documents \
  -F "files=@research_paper.pdf" \
  -F "source_llm=gpt-4"
```

### Start Processing

```bash
curl -X POST http://localhost:8000/api/v1/pipelines/{pipeline_id}/start
```

### List Claims

```bash
curl http://localhost:8000/api/v1/claims/?pipeline_id={pipeline_id}&limit=10
```

## API Documentation

When running in DEBUG mode, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

```
┌─────────────┐       ┌──────────┐       ┌─────────────┐
│   Frontend  │──────▶│   API    │──────▶│  PostgreSQL │
│  (Phase 4)  │       │ (FastAPI)│       │  Database   │
└─────────────┘       └──────────┘       └─────────────┘
                            │
                            ▼
                      ┌──────────┐
                      │  Redis   │
                      │  Queue   │
                      └──────────┘
                            │
                            ▼
                      ┌──────────┐       ┌─────────────┐
                      │  Worker  │──────▶│   Gemini    │
                      │  Process │       │  2.5 Flash  │
                      └──────────┘       └─────────────┘
```

## Worker Details

### Claim Extraction Worker

Located in: `apps/workers/worker_extraction.py`

**What it does:**
1. Pulls jobs from Redis queue
2. Reads document text from database
3. Sends to Gemini for claim extraction
4. Saves extracted claims to database
5. Updates pipeline statistics

**How to run:**
```bash
cd apps/workers
python worker_extraction.py
```

**Environment variables needed:**
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `GEMINI_API_KEY` - Google AI API key

## Troubleshooting

### Worker not processing jobs

1. Check worker is running:
   ```bash
   ps aux | grep worker_extraction
   ```

2. Check Redis connection:
   ```bash
   redis-cli ping
   ```

3. Check queue length:
   ```bash
   redis-cli llen queue:llm_synthesis:claim_extraction
   ```

### Claims not appearing

1. Check worker logs for errors
2. Verify Gemini API key is valid
3. Check database for saved claims:
   ```sql
   SELECT COUNT(*) FROM claims;
   ```

### Upload failures

1. Check file size (max 100MB)
2. Verify supported format (PDF, DOCX, TXT, MD, JSON)
3. Ensure upload directory exists and is writable

## What's Next: Phase 3

Phase 3 will add:
- **Dependency Inference**: Analyze relationships between claims
- **Contradiction Detection**: Find conflicting statements
- **Report Generation**: Create synthesis reports
- **Graph Analysis**: Calculate PageRank and centrality
- **Advanced Workers**: Inference and report generation workers

## File Structure

```
apps/
├── api/
│   ├── routes/
│   │   ├── pipelines/router.py  # Pipeline endpoints
│   │   ├── claims/router.py     # Claims endpoints
│   │   └── websocket/router.py  # WebSocket handler
│   ├── services/
│   │   ├── storage/upload_handler.py  # File uploads
│   │   ├── extraction/text_extractor.py  # Text extraction
│   │   └── queue_service.py     # Job queue management
│   ├── schemas/
│   │   ├── requests/pipeline_schemas.py
│   │   └── responses/pipeline_schemas.py
│   ├── main.py                  # FastAPI app
│   └── test_phase2.py           # Phase 2 tests
│
└── workers/
    ├── base_worker.py           # Base worker class
    ├── worker_extraction.py     # Claim extraction worker
    ├── config.py                # Worker configuration
    └── requirements.txt
```

## Performance Notes

- **Concurrent Workers**: Run multiple workers for faster processing
- **Batch Size**: Adjust worker concurrency in config
- **Caching**: Gemini responses are cached in Redis
- **Database Pooling**: Configured for optimal connections

## Railway Deployment

To deploy Phase 2 to Railway:

1. API service already configured in `railway.toml`
2. Add worker service:
   ```toml
   [services.worker-extraction]
   source = "./apps/workers"
   buildCommand = "pip install -r requirements.txt"
   startCommand = "python worker_extraction.py"
   replicas = 2
   ```

3. Ensure environment variables are set in Railway dashboard

## Support

- Check `TESTING.md` for testing procedures
- Review `RAILWAY_DEPLOYMENT.md` for deployment
- See `Implementation Plan` for full roadmap

---

**Status**: Phase 2 Complete ✅
**Next**: Phase 3 - Advanced Features (Dependency Analysis & Reports)
