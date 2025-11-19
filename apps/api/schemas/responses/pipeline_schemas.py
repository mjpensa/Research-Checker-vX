from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class DocumentResponse(BaseModel):
    """Response schema for document"""
    id: UUID
    pipeline_id: UUID
    filename: str
    file_size: int
    mime_type: str
    source_llm: Optional[str]
    status: str
    text_length: Optional[int]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True

class PipelineResponse(BaseModel):
    """Response schema for pipeline"""
    id: UUID
    user_id: str
    name: Optional[str]
    status: str
    total_claims: int
    total_dependencies: int
    total_contradictions: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: dict

    # Include related documents if requested
    documents: Optional[List[DocumentResponse]] = None

    class Config:
        from_attributes = True

class PipelineListResponse(BaseModel):
    """Response schema for pipeline list"""
    pipelines: List[PipelineResponse]
    total: int
    limit: int
    offset: int

class ClaimResponse(BaseModel):
    """Response schema for claim"""
    id: UUID
    pipeline_id: UUID
    document_id: UUID
    text: str
    claim_type: str
    confidence: Optional[float]
    evidence_type: Optional[str]
    importance_score: float
    pagerank: Optional[float]
    centrality: Optional[float]
    is_foundational: bool
    extracted_at: datetime

    class Config:
        from_attributes = True

class DependencyResponse(BaseModel):
    """Response schema for dependency"""
    id: UUID
    source_claim_id: UUID
    target_claim_id: UUID
    relationship_type: str
    confidence: float
    strength: str
    explanation: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    """Response for file upload"""
    success: bool
    document_id: Optional[UUID]
    filename: str
    file_size: int
    message: str

class ProcessingStatus(BaseModel):
    """Real-time processing status"""
    pipeline_id: UUID
    status: str
    progress: int  # 0-100
    current_step: str
    documents_processed: int
    claims_extracted: int
    dependencies_inferred: int
    errors: List[str] = Field(default_factory=list)
