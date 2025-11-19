"""
Queue Service for managing background jobs
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from core.redis import redis_client
from core.config import settings

logger = logging.getLogger(__name__)

class QueueService:
    """Service for managing background job queues"""

    def __init__(self):
        self.queue_name = settings.QUEUE_NAME

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
        await redis_client.redis.lpush(queue_key, json.dumps(job))

        # Set initial status
        await self.update_job_status(job_id, 'queued', progress=0)

        logger.info(f"Enqueued job {job_id} to {queue_key}")

        return job_id

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

        await redis_client.set_json(status_key, status_data)

        # Set expiration (24 hours)
        await redis_client.redis.expire(status_key, 86400)

        logger.debug(f"Updated job {job_id} status: {status} ({progress}%)")

    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status from Redis"""

        status_key = f"job:status:{job_id}"
        return await redis_client.get_json(status_key)

    async def enqueue_claim_extraction(self, pipeline_id: str, document_id: str) -> str:
        """Enqueue a claim extraction job"""

        return await self.enqueue_job(
            'claim_extraction',
            {
                'pipeline_id': pipeline_id,
                'document_id': document_id
            }
        )

    async def enqueue_dependency_inference(self, pipeline_id: str) -> str:
        """Enqueue a dependency inference job"""

        return await self.enqueue_job(
            'dependency_inference',
            {
                'pipeline_id': pipeline_id
            }
        )

    async def enqueue_report_generation(self, pipeline_id: str, report_type: str = 'synthesis') -> str:
        """Enqueue a report generation job"""

        return await self.enqueue_job(
            'report_generation',
            {
                'pipeline_id': pipeline_id,
                'report_type': report_type
            }
        )

    async def get_queue_length(self, job_type: str) -> int:
        """Get the number of jobs in a queue"""

        queue_key = f"queue:{self.queue_name}:{job_type}"
        return await redis_client.redis.llen(queue_key)

    async def get_all_queue_stats(self) -> Dict[str, int]:
        """Get statistics for all queues"""

        stats = {}

        for job_type in ['claim_extraction', 'dependency_inference', 'report_generation']:
            queue_key = f"queue:{self.queue_name}:{job_type}"
            length = await redis_client.redis.llen(queue_key)
            stats[job_type] = length

        return stats

queue_service = QueueService()
