from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../packages/database'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from core.database import get_db
from models import Report, Pipeline, Contradiction
from services.queue_service import queue_service
from services.contradiction_detector import contradiction_detector
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_current_user_id() -> str:
    """Get current user ID - placeholder until Clerk auth is added"""
    return "demo_user"

@router.post("/{pipeline_id}/generate")
async def generate_report(
    pipeline_id: UUID,
    report_type: str = "synthesis",
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate a new report for a pipeline"""

    # Verify pipeline belongs to user
    result = await db.execute(
        select(Pipeline).where(
            and_(
                Pipeline.id == pipeline_id,
                Pipeline.user_id == user_id
            )
        )
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline {pipeline_id} not found"
        )

    # Enqueue report generation job
    job_id = await queue_service.enqueue_report_generation(
        str(pipeline_id),
        report_type
    )

    logger.info(f"Enqueued report generation job {job_id} for pipeline {pipeline_id}")

    return {
        "message": "Report generation started",
        "job_id": job_id,
        "pipeline_id": str(pipeline_id),
        "report_type": report_type
    }

@router.get("/{pipeline_id}")
async def list_reports(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all reports for a pipeline"""

    # Verify pipeline belongs to user
    result = await db.execute(
        select(Pipeline).where(
            and_(
                Pipeline.id == pipeline_id,
                Pipeline.user_id == user_id
            )
        )
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline {pipeline_id} not found"
        )

    # Get reports
    reports_result = await db.execute(
        select(Report)
        .where(Report.pipeline_id == pipeline_id)
        .order_by(desc(Report.generated_at))
    )
    reports = reports_result.scalars().all()

    return reports

@router.get("/{pipeline_id}/latest")
async def get_latest_report(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get the most recent report for a pipeline"""

    # Verify pipeline belongs to user
    result = await db.execute(
        select(Pipeline).where(
            and_(
                Pipeline.id == pipeline_id,
                Pipeline.user_id == user_id
            )
        )
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline {pipeline_id} not found"
        )

    # Get latest report
    report_result = await db.execute(
        select(Report)
        .where(Report.pipeline_id == pipeline_id)
        .order_by(desc(Report.generated_at))
        .limit(1)
    )
    report = report_result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=404,
            detail="No reports found for this pipeline"
        )

    return report

@router.get("/report/{report_id}")
async def get_report(
    report_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific report by ID"""

    result = await db.execute(
        select(Report).join(Pipeline).where(
            and_(
                Report.id == report_id,
                Pipeline.user_id == user_id
            )
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report {report_id} not found"
        )

    return report

@router.post("/{pipeline_id}/detect-contradictions")
async def detect_contradictions(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Detect contradictions in pipeline claims"""

    # Verify pipeline belongs to user
    result = await db.execute(
        select(Pipeline).where(
            and_(
                Pipeline.id == pipeline_id,
                Pipeline.user_id == user_id
            )
        )
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline {pipeline_id} not found"
        )

    # Run contradiction detection
    contradictions = await contradiction_detector.detect_contradictions(
        str(pipeline_id),
        db,
        max_claims=50
    )

    # Save contradictions
    saved_count = await contradiction_detector.save_contradictions(
        str(pipeline_id),
        contradictions,
        db
    )

    logger.info(f"Detected and saved {saved_count} contradictions for pipeline {pipeline_id}")

    return {
        "message": f"Detected {saved_count} contradictions",
        "pipeline_id": str(pipeline_id),
        "contradictions_found": saved_count
    }

@router.get("/{pipeline_id}/contradictions")
async def list_contradictions(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all contradictions for a pipeline"""

    # Verify pipeline belongs to user
    result = await db.execute(
        select(Pipeline).where(
            and_(
                Pipeline.id == pipeline_id,
                Pipeline.user_id == user_id
            )
        )
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline {pipeline_id} not found"
        )

    # Get contradictions
    contras_result = await db.execute(
        select(Contradiction)
        .where(Contradiction.pipeline_id == pipeline_id)
        .order_by(desc(Contradiction.confidence))
    )
    contradictions = contras_result.scalars().all()

    return contradictions

@router.post("/{pipeline_id}/analyze-dependencies")
async def analyze_dependencies(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Start dependency analysis for a pipeline"""

    # Verify pipeline belongs to user
    result = await db.execute(
        select(Pipeline).where(
            and_(
                Pipeline.id == pipeline_id,
                Pipeline.user_id == user_id
            )
        )
    )
    pipeline = result.scalar_one_or_none()

    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail=f"Pipeline {pipeline_id} not found"
        )

    # Enqueue dependency inference job
    job_id = await queue_service.enqueue_dependency_inference(str(pipeline_id))

    logger.info(f"Enqueued dependency inference job {job_id} for pipeline {pipeline_id}")

    return {
        "message": "Dependency analysis started",
        "job_id": job_id,
        "pipeline_id": str(pipeline_id)
    }
