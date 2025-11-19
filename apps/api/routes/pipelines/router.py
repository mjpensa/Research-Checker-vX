from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from typing import List, Optional
from uuid import UUID
import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../packages/database'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from core.database import get_db
from models import Pipeline, Document, PipelineStatus
from schemas.requests.pipeline_schemas import PipelineCreate, PipelineUpdate
from schemas.responses.pipeline_schemas import (
    PipelineResponse, PipelineListResponse, DocumentResponse, UploadResponse
)
from services.storage.upload_handler import upload_handler
from services.extraction.text_extractor import text_extractor
from services.queue_service import queue_service
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Temporary user ID (replace with actual auth in Phase 4)
def get_current_user_id() -> str:
    """Get current user ID - placeholder until Clerk auth is added"""
    return "demo_user"

@router.post("/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline: PipelineCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new research synthesis pipeline"""

    new_pipeline = Pipeline(
        user_id=user_id,
        name=pipeline.name,
        status=PipelineStatus.PENDING,
        metadata=pipeline.metadata or {}
    )

    db.add(new_pipeline)
    await db.commit()
    await db.refresh(new_pipeline)

    logger.info(f"Created pipeline {new_pipeline.id} for user {user_id}")

    return new_pipeline

@router.get("/", response_model=PipelineListResponse)
async def list_pipelines(
    user_id: str = Depends(get_current_user_id),
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all pipelines for the current user"""

    # Build query
    query = select(Pipeline).where(Pipeline.user_id == user_id)

    if status_filter:
        try:
            status_enum = PipelineStatus[status_filter.upper()]
            query = query.where(Pipeline.status == status_enum)
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status_filter}"
            )

    # Count total
    count_query = select(Pipeline).where(Pipeline.user_id == user_id)
    if status_filter:
        count_query = count_query.where(Pipeline.status == status_enum)

    # Execute queries
    result = await db.execute(
        query.order_by(desc(Pipeline.created_at)).limit(limit).offset(offset)
    )
    pipelines = result.scalars().all()

    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return PipelineListResponse(
        pipelines=pipelines,
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    include_documents: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific pipeline by ID"""

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

    # Include documents if requested
    if include_documents:
        docs_result = await db.execute(
            select(Document).where(Document.pipeline_id == pipeline_id)
        )
        pipeline.documents = docs_result.scalars().all()

    return pipeline

@router.patch("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: UUID,
    update: PipelineUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a pipeline"""

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

    # Update fields
    if update.name is not None:
        pipeline.name = update.name

    if update.status is not None:
        try:
            pipeline.status = PipelineStatus[update.status.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {update.status}"
            )

    if update.metadata is not None:
        pipeline.metadata = update.metadata

    pipeline.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(pipeline)

    logger.info(f"Updated pipeline {pipeline_id}")

    return pipeline

@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a pipeline and all associated data"""

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

    # Delete uploaded files
    try:
        await upload_handler.delete_pipeline_files(user_id, str(pipeline_id))
    except Exception as e:
        logger.error(f"Error deleting files for pipeline {pipeline_id}: {e}")

    # Delete from database (cascades to related records)
    await db.delete(pipeline)
    await db.commit()

    logger.info(f"Deleted pipeline {pipeline_id}")

    return None

@router.post("/{pipeline_id}/documents", response_model=List[UploadResponse])
async def upload_documents(
    pipeline_id: UUID,
    files: List[UploadFile] = File(...),
    source_llm: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Upload one or more documents to a pipeline"""

    # Verify pipeline exists and belongs to user
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

    responses = []

    for file in files:
        try:
            # Save file
            file_metadata = await upload_handler.save_upload(
                file,
                str(pipeline_id),
                user_id
            )

            # Extract text
            extracted = await text_extractor.extract(
                file_metadata['file_path'],
                file_metadata['mime_type']
            )

            # Create document record
            document = Document(
                pipeline_id=pipeline_id,
                filename=file_metadata['filename'],
                file_path=file_metadata['file_path'],
                file_size=file_metadata['file_size'],
                mime_type=file_metadata['mime_type'],
                source_llm=source_llm,
                source_metadata={'sha256': file_metadata['sha256']},
                status='extracted',
                extracted_text=extracted.text,
                text_length=extracted.word_count
            )

            db.add(document)
            await db.commit()
            await db.refresh(document)

            responses.append(UploadResponse(
                success=True,
                document_id=document.id,
                filename=file.filename,
                file_size=file_metadata['file_size'],
                message=f"Uploaded and extracted {extracted.word_count} words"
            ))

            logger.info(f"Uploaded document {document.id} to pipeline {pipeline_id}")

        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
            responses.append(UploadResponse(
                success=False,
                document_id=None,
                filename=file.filename,
                file_size=0,
                message=f"Upload failed: {str(e)}"
            ))

    return responses

@router.get("/{pipeline_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all documents in a pipeline"""

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

    # Get documents
    docs_result = await db.execute(
        select(Document).where(Document.pipeline_id == pipeline_id)
    )
    documents = docs_result.scalars().all()

    return documents

@router.post("/{pipeline_id}/start", response_model=PipelineResponse)
async def start_pipeline(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Start processing a pipeline (extract claims, analyze dependencies)"""

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

    # Check if pipeline has documents
    docs_result = await db.execute(
        select(Document).where(Document.pipeline_id == pipeline_id)
    )
    documents = docs_result.scalars().all()

    if not documents:
        raise HTTPException(
            status_code=400,
            detail="Cannot start pipeline with no documents"
        )

    # Update status
    pipeline.status = PipelineStatus.PROCESSING
    pipeline.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(pipeline)

    # Enqueue claim extraction jobs for each document
    job_ids = []
    for document in documents:
        job_id = await queue_service.enqueue_claim_extraction(
            str(pipeline_id),
            str(document.id)
        )
        job_ids.append(job_id)

    logger.info(f"Started pipeline {pipeline_id} with {len(documents)} documents, enqueued {len(job_ids)} jobs")

    return pipeline
