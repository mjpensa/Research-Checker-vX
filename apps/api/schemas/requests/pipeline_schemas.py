from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PipelineCreate(BaseModel):
    """Request schema for creating a new pipeline"""
    name: Optional[str] = Field(None, max_length=500, description="Optional name for the pipeline")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Research Paper Analysis - Q4 2024",
                "metadata": {
                    "project": "ML Research",
                    "tags": ["machine-learning", "NLP"]
                }
            }
        }

class PipelineUpdate(BaseModel):
    """Request schema for updating a pipeline"""
    name: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, description="pending, processing, completed, failed, cancelled")
    metadata: Optional[dict] = None

class DocumentUploadMetadata(BaseModel):
    """Metadata for document upload"""
    source_llm: Optional[str] = Field(None, description="Source LLM (e.g., gpt-4, claude-3, gemini-pro)")
    source_metadata: Optional[dict] = Field(default_factory=dict)

class ClaimQuery(BaseModel):
    """Query parameters for searching claims"""
    pipeline_id: Optional[str] = None
    claim_type: Optional[str] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    search_text: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
