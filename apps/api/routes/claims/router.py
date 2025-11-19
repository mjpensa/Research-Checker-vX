from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../packages/database'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from core.database import get_db
from models import Claim, Pipeline, Dependency, ClaimType
from schemas.responses.pipeline_schemas import ClaimResponse, DependencyResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_current_user_id() -> str:
    """Get current user ID - placeholder until Clerk auth is added"""
    return "demo_user"

@router.get("/", response_model=List[ClaimResponse])
async def list_claims(
    pipeline_id: Optional[UUID] = None,
    claim_type: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    search_text: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List claims with optional filters"""

    # Build query
    query = select(Claim).join(Pipeline).where(Pipeline.user_id == user_id)

    if pipeline_id:
        query = query.where(Claim.pipeline_id == pipeline_id)

    if claim_type:
        try:
            claim_type_enum = ClaimType[claim_type.upper()]
            query = query.where(Claim.claim_type == claim_type_enum)
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid claim type: {claim_type}"
            )

    if min_confidence is not None:
        query = query.where(Claim.confidence >= min_confidence)

    if search_text:
        query = query.where(Claim.text.ilike(f"%{search_text}%"))

    # Order by importance and limit
    query = query.order_by(desc(Claim.importance_score)).limit(limit).offset(offset)

    result = await db.execute(query)
    claims = result.scalars().all()

    return claims

@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific claim by ID"""

    result = await db.execute(
        select(Claim).join(Pipeline).where(
            and_(
                Claim.id == claim_id,
                Pipeline.user_id == user_id
            )
        )
    )
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim {claim_id} not found"
        )

    return claim

@router.get("/{claim_id}/dependencies", response_model=List[DependencyResponse])
async def get_claim_dependencies(
    claim_id: UUID,
    direction: str = Query("all", regex="^(all|outgoing|incoming)$"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get dependencies for a claim"""

    # Verify claim belongs to user
    result = await db.execute(
        select(Claim).join(Pipeline).where(
            and_(
                Claim.id == claim_id,
                Pipeline.user_id == user_id
            )
        )
    )
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim {claim_id} not found"
        )

    # Get dependencies based on direction
    if direction == "outgoing":
        query = select(Dependency).where(Dependency.source_claim_id == claim_id)
    elif direction == "incoming":
        query = select(Dependency).where(Dependency.target_claim_id == claim_id)
    else:  # all
        query = select(Dependency).where(
            or_(
                Dependency.source_claim_id == claim_id,
                Dependency.target_claim_id == claim_id
            )
        )

    result = await db.execute(query)
    dependencies = result.scalars().all()

    return dependencies

@router.get("/pipeline/{pipeline_id}/stats")
async def get_pipeline_claim_stats(
    pipeline_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get claim statistics for a pipeline"""

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

    # Count total claims
    total_result = await db.execute(
        select(func.count(Claim.id)).where(Claim.pipeline_id == pipeline_id)
    )
    total_claims = total_result.scalar()

    # Count by type
    type_counts = {}
    for claim_type in ClaimType:
        result = await db.execute(
            select(func.count(Claim.id)).where(
                and_(
                    Claim.pipeline_id == pipeline_id,
                    Claim.claim_type == claim_type
                )
            )
        )
        count = result.scalar()
        if count > 0:
            type_counts[claim_type.value] = count

    # Get foundational claims
    foundational_result = await db.execute(
        select(func.count(Claim.id)).where(
            and_(
                Claim.pipeline_id == pipeline_id,
                Claim.is_foundational == True
            )
        )
    )
    foundational_count = foundational_result.scalar()

    # Average confidence
    avg_confidence_result = await db.execute(
        select(func.avg(Claim.confidence)).where(Claim.pipeline_id == pipeline_id)
    )
    avg_confidence = avg_confidence_result.scalar()

    return {
        "pipeline_id": str(pipeline_id),
        "total_claims": total_claims,
        "claims_by_type": type_counts,
        "foundational_claims": foundational_count,
        "average_confidence": float(avg_confidence) if avg_confidence else 0.0
    }
