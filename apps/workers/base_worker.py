"""
Base worker class for background job processing
Uses Redis as a simple queue (BullMQ Python binding has limited support)
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import config
import sentry_sdk

logger = logging.getLogger(__name__)

class BaseWorker:
    """Base class for background workers"""

    def __init__(self, worker_name: str, queue_name: str = None):
        self.worker_name = worker_name
        self.queue_name = queue_name or config.QUEUE_NAME
        self.redis_client: Optional[redis.Redis] = None
        self.db_engine = None
        self.SessionLocal = None
        self.running = False

        # Initialize Sentry if configured
        if config.SENTRY_DSN:
            sentry_sdk.init(dsn=config.SENTRY_DSN)

    async def connect(self):
        """Connect to Redis and Database"""

        # Connect to Redis
        self.redis_client = await redis.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await self.redis_client.ping()
        logger.info(f"Worker {self.worker_name} connected to Redis")

        # Connect to Database
        database_url = config.DATABASE_URL.replace(
            'postgresql://',
            'postgresql+asyncpg://'
        )

        self.db_engine = create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )

        self.SessionLocal = async_sessionmaker(
            self.db_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        logger.info(f"Worker {self.worker_name} connected to database")

    async def disconnect(self):
        """Disconnect from Redis and Database"""

        if self.redis_client:
            await self.redis_client.close()

        if self.db_engine:
            await self.db_engine.dispose()

        logger.info(f"Worker {self.worker_name} disconnected")

    async def get_db(self):
        """Get database session"""
        async with self.SessionLocal() as session:
            yield session

    async def enqueue_job(self, job_type: str, data: Dict[str, Any]) -> str:
        """Enqueue a job to the queue"""

        job_id = f"{job_type}:{datetime.utcnow().timestamp()}"

        job = {
            'id': job_id,
            'type': job_type,
            'data': data,
            'status': 'queued',
            'created_at': datetime.utcnow().isoformat(),
            'attempts': 0
        }

        # Push to queue (Redis list)
        queue_key = f"queue:{self.queue_name}:{job_type}"
        await self.redis_client.lpush(queue_key, json.dumps(job))

        logger.info(f"Enqueued job {job_id} to {queue_key}")

        return job_id

    async def dequeue_job(self, job_type: str, timeout: int = 5) -> Optional[Dict]:
        """Dequeue a job from the queue"""

        queue_key = f"queue:{self.queue_name}:{job_type}"

        # Blocking pop from queue
        result = await self.redis_client.brpop(queue_key, timeout=timeout)

        if result:
            _, job_data = result
            job = json.loads(job_data)
            logger.info(f"Dequeued job {job['id']} from {queue_key}")
            return job

        return None

    async def update_job_status(self, job_id: str, status: str, progress: int = 0, error: str = None):
        """Update job status in Redis"""

        status_key = f"job:status:{job_id}"

        status_data = {
            'job_id': job_id,
            'status': status,
            'progress': progress,
            'updated_at': datetime.utcnow().isoformat()
        }

        if error:
            status_data['error'] = error

        await self.redis_client.set(
            status_key,
            json.dumps(status_data),
            ex=86400  # Expire after 24 hours
        )

        logger.debug(f"Updated job {job_id} status: {status} ({progress}%)")

    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status from Redis"""

        status_key = f"job:status:{job_id}"
        result = await self.redis_client.get(status_key)

        if result:
            return json.loads(result)

        return None

    async def process_job(self, job: Dict) -> Any:
        """Process a job - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_job")

    async def run(self, job_type: str):
        """Run the worker loop"""

        self.running = True
        logger.info(f"Worker {self.worker_name} started, processing {job_type} jobs")

        try:
            while self.running:
                try:
                    # Get job from queue
                    job = await self.dequeue_job(job_type, timeout=5)

                    if not job:
                        continue

                    job_id = job['id']

                    # Update status to active
                    await self.update_job_status(job_id, 'active', progress=0)

                    try:
                        # Process job
                        result = await self.process_job(job)

                        # Mark as completed
                        await self.update_job_status(job_id, 'completed', progress=100)

                        logger.info(f"Job {job_id} completed successfully")

                    except Exception as e:
                        logger.error(f"Job {job_id} failed: {e}", exc_info=True)

                        # Mark as failed
                        await self.update_job_status(
                            job_id,
                            'failed',
                            progress=0,
                            error=str(e)
                        )

                        # Re-queue if attempts < max_retries
                        if job.get('attempts', 0) < 3:
                            job['attempts'] = job.get('attempts', 0) + 1
                            await self.enqueue_job(job['type'], job['data'])
                            logger.info(f"Re-queued job {job_id} (attempt {job['attempts']})")

                except Exception as e:
                    logger.error(f"Error in worker loop: {e}", exc_info=True)
                    await asyncio.sleep(1)

        finally:
            logger.info(f"Worker {self.worker_name} stopped")

    def stop(self):
        """Stop the worker"""
        self.running = False
