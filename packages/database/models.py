from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, JSON,
    ForeignKey, Enum as SQLEnum, Text, Boolean, Index
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
import enum

Base = declarative_base()

class PipelineStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ClaimType(enum.Enum):
    FACTUAL = "factual"
    STATISTICAL = "statistical"
    CAUSAL = "causal"
    OPINION = "opinion"
    HYPOTHESIS = "hypothesis"

class DependencyType(enum.Enum):
    CAUSAL = "causal"
    EVIDENTIAL = "evidential"
    TEMPORAL = "temporal"
    PREREQUISITE = "prerequisite"
    CONTRADICTORY = "contradictory"
    REFINES = "refines"
    NONE = "none"

class Pipeline(Base):
    __tablename__ = 'pipelines'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    name = Column(String(500))
    status = Column(SQLEnum(PipelineStatus), default=PipelineStatus.PENDING, index=True)
    file_paths = Column(ARRAY(Text))
    error_message = Column(Text)
    metadata = Column(JSONB, default={})

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    documents = relationship("Document", back_populates="pipeline", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="pipeline", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="pipeline", cascade="all, delete-orphan")

    # Stats
    total_claims = Column(Integer, default=0)
    total_dependencies = Column(Integer, default=0)
    total_contradictions = Column(Integer, default=0)

class Document(Base):
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id', ondelete='CASCADE'), nullable=False)

    filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))

    # Source information
    source_llm = Column(String(100))  # e.g., "gpt-4", "claude-3", "gemini-pro"
    source_metadata = Column(JSONB, default={})

    # Processing
    status = Column(String(50), default='pending')
    extracted_text = Column(Text)
    text_length = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="documents")
    claims = relationship("Claim", back_populates="document")

    __table_args__ = (
        Index('idx_documents_pipeline_status', 'pipeline_id', 'status'),
    )

class Claim(Base):
    __tablename__ = 'claims'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id', ondelete='CASCADE'), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)

    # Claim content
    text = Column(Text, nullable=False)
    claim_type = Column(SQLEnum(ClaimType), nullable=False)

    # Context
    source_span_start = Column(Integer)  # Character position in document
    source_span_end = Column(Integer)
    surrounding_context = Column(Text)

    # Metadata
    confidence = Column(Float)  # 0.0 to 1.0
    evidence_type = Column(String(50))  # empirical, theoretical, anecdotal
    importance_score = Column(Float, default=0.0)

    # Graph metrics (calculated later)
    pagerank = Column(Float)
    centrality = Column(Float)
    is_foundational = Column(Boolean, default=False)

    # Embeddings for semantic search
    embedding = Column(ARRAY(Float))  # Will store vector embeddings

    extracted_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, default={})

    # Relationships
    pipeline = relationship("Pipeline", back_populates="claims")
    document = relationship("Document", back_populates="claims")
    outgoing_dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.source_claim_id",
        back_populates="source_claim"
    )
    incoming_dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.target_claim_id",
        back_populates="target_claim"
    )

    __table_args__ = (
        Index('idx_claims_pipeline_type', 'pipeline_id', 'claim_type'),
        Index('idx_claims_importance', 'importance_score'),
    )

class Dependency(Base):
    __tablename__ = 'dependencies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id', ondelete='CASCADE'), nullable=False)

    source_claim_id = Column(UUID(as_uuid=True), ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)
    target_claim_id = Column(UUID(as_uuid=True), ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)

    # Dependency details
    relationship_type = Column(SQLEnum(DependencyType), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    strength = Column(String(20))  # weak, moderate, strong

    # Analysis
    explanation = Column(Text)
    semantic_markers = Column(ARRAY(String))

    # Validation
    is_validated = Column(Boolean, default=False)
    validation_score = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, default={})

    # Relationships
    source_claim = relationship("Claim", foreign_keys=[source_claim_id], back_populates="outgoing_dependencies")
    target_claim = relationship("Claim", foreign_keys=[target_claim_id], back_populates="incoming_dependencies")

    __table_args__ = (
        Index('idx_dependencies_source', 'source_claim_id'),
        Index('idx_dependencies_target', 'target_claim_id'),
        Index('idx_dependencies_type', 'relationship_type'),
    )

class Contradiction(Base):
    __tablename__ = 'contradictions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id', ondelete='CASCADE'), nullable=False)

    claim_a_id = Column(UUID(as_uuid=True), ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)
    claim_b_id = Column(UUID(as_uuid=True), ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)

    # Contradiction details
    contradiction_type = Column(String(50))  # direct, numerical, temporal, scope, definitional
    severity = Column(String(20))  # low, medium, high, critical

    explanation = Column(Text, nullable=False)
    resolution_suggestion = Column(Text)

    # Evidence
    confidence = Column(Float, nullable=False)
    supporting_evidence = Column(JSONB)

    # Status
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)

    detected_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, default={})

class Report(Base):
    __tablename__ = 'reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id', ondelete='CASCADE'), nullable=False)

    report_type = Column(String(50))  # synthesis, contradictions, dependencies
    title = Column(String(500))

    # Content
    content = Column(Text, nullable=False)  # Markdown formatted
    content_html = Column(Text)
    summary = Column(Text)

    # Structured data
    key_findings = Column(JSONB)
    recommendations = Column(JSONB)
    statistics = Column(JSONB)

    # Export
    export_formats = Column(ARRAY(String))  # pdf, docx, html
    export_paths = Column(JSONB)

    generated_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, default={})

    # Relationships
    pipeline = relationship("Pipeline", back_populates="reports")

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(String(100), primary_key=True)  # BullMQ job ID
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey('pipelines.id', ondelete='CASCADE'))

    job_type = Column(String(50), nullable=False)  # extraction, inference, report
    status = Column(String(50), default='queued')  # queued, active, completed, failed

    progress = Column(Integer, default=0)  # 0-100

    data = Column(JSONB)
    result = Column(JSONB)
    error = Column(Text)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_jobs_pipeline_status', 'pipeline_id', 'status'),
        Index('idx_jobs_type_status', 'job_type', 'status'),
    )
