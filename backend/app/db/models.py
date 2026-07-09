import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, Index, 
    JSON, BigInteger, Boolean, Integer, Float, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, VECTOR, JSONB
from sqlalchemy.orm import relationship, declared_attr
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    IMAGE = "image"
    SPREADSHEET = "spreadsheet"
    VIDEO = "video"
    EMAIL = "email"
    TEXT = "text"
    CAD = "cad"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class EquipmentCategory(str, enum.Enum):
    PUMP = "pump"
    COMPRESSOR = "compressor"
    BOILER = "boiler"
    TURBINE = "turbine"
    CONVEYOR = "conveyor"
    HEAT_EXCHANGER = "heat_exchanger"
    VALVE = "valve"
    MOTOR = "motor"
    GENERATOR = "generator"
    TRANSFORMER = "transformer"
    REACTOR = "reactor"
    TANK = "tank"
    PIPELINE = "pipeline"
    CRANE = "crane"
    OTHER = "other"


class EquipmentCriticality(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class ProblemSource(str, enum.Enum):
    AI_GENERATED = "ai_generated"
    USER_SUBMITTED = "user_submitted"
    DOCUMENT_EXTRACTED = "document_extracted"
    PRE_SEEDED = "pre_seeded"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADING, nullable=False)
    storage_path = Column(String(1000), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    page_count = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # for videos
    metadata = Column(JSONB, default=dict)
    original_filename = Column(String(500), nullable=True)
    mime_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_documents_status", "status"),
        Index("ix_documents_type", "type"),
        Index("ix_documents_created_at", "created_at"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI text-embedding-3-large
    metadata = Column(JSONB, default=dict)  # page_num, timestamp, etc.
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index("ix_document_chunks_document_id", "document_id"),
        Index("ix_document_chunks_chunk_index", "chunk_index"),
    )


class Entity(Base):
    __tablename__ = "entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # equipment, personnel, procedure, regulation, parameter, location
    properties = Column(JSONB, default=dict)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="entities")
    source_relationships = relationship("Relationship", back_populates="source_entity", foreign_keys="Relationship.source_id")
    target_relationships = relationship("Relationship", back_populates="target_entity", foreign_keys="Relationship.target_id")
    
    __table_args__ = (
        Index("ix_entities_document_id", "document_id"),
        Index("ix_entities_name_type", "name", "type"),
        Index("ix_entities_type", "type"),
    )


class Relationship(Base):
    __tablename__ = "relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(50), nullable=False)  # located_in, connected_to, inspected_on, maintained_by, referenced_in, has_parameter
    properties = Column(JSONB, default=dict)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    source_entity = relationship("Entity", back_populates="source_relationships", foreign_keys=[source_id])
    target_entity = relationship("Entity", back_populates="target_relationships", foreign_keys=[target_id])
    
    __table_args__ = (
        Index("ix_relationships_source_id", "source_id"),
        Index("ix_relationships_target_id", "target_id"),
        Index("ix_relationships_type", "relation_type"),
        UniqueConstraint("source_id", "target_id", "relation_type", name="uq_relationship"),
    )


class EquipmentCatalog(Base):
    __tablename__ = "equipment_catalog"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    tag_number = Column(String(50), nullable=True, unique=True)  # e.g., P-101, B-202
    category = Column(Enum(EquipmentCategory), nullable=False)
    criticality = Column(Enum(EquipmentCriticality), default=EquipmentCriticality.MAJOR, nullable=False)
    location = Column(String(200), nullable=True)
    area = Column(String(100), nullable=True)
    unit = Column(String(100), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    model = Column(String(200), nullable=True)
    serial_number = Column(String(100), nullable=True)
    installation_date = Column(DateTime, nullable=True)
    specifications = Column(JSONB, default=dict)  # capacity, pressure, temperature, power, etc.
    operating_parameters = Column(JSONB, default=dict)  # normal ranges
    description = Column(Text, nullable=True)
    p_and_id_reference = Column(String(100), nullable=True)  # P&ID drawing number
    status = Column(String(20), default="operational")  # operational, warning, down, maintenance
    last_maintenance_date = Column(DateTime, nullable=True)
    next_maintenance_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    known_problems = relationship("KnownProblem", back_populates="equipment", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="equipment", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_equipment_catalog_tag", "tag_number"),
        Index("ix_equipment_catalog_category", "category"),
        Index("ix_equipment_catalog_criticality", "criticality"),
        Index("ix_equipment_catalog_area", "area"),
        Index("ix_equipment_catalog_status", "status"),
    )


class KnownProblem(Base):
    __tablename__ = "known_problems"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment_catalog.id", ondelete="CASCADE"), nullable=False)
    problem_name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    symptoms = Column(JSONB, default=list)  # list of symptom strings
    severity = Column(Integer, nullable=False)  # 1-10
    frequency = Column(String(20), nullable=True)  # frequent, occasional, rare
    root_causes = Column(JSONB, default=list)  # list of root cause strings
    detection_methods = Column(JSONB, default=list)  # how to detect
    affected_parameters = Column(JSONB, default=list)  # parameters that deviate
    source = Column(Enum(ProblemSource), default=ProblemSource.PRE_SEEDED, nullable=False)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    equipment = relationship("EquipmentCatalog", back_populates="known_problems")
    solutions = relationship("ProblemSolution", back_populates="problem", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_known_problems_equipment_id", "equipment_id"),
        Index("ix_known_problems_severity", "severity"),
        Index("ix_known_problems_active", "is_active"),
    )


class ProblemSolution(Base):
    __tablename__ = "problem_solutions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("known_problems.id", ondelete="CASCADE"), nullable=False)
    solution_text = Column(Text, nullable=False)
    steps = Column(JSONB, default=list)  # ordered list of steps
    tools_required = Column(JSONB, default=list)
    parts_required = Column(JSONB, default=list)
    estimated_time_minutes = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    safety_notes = Column(Text, nullable=True)
    source = Column(Enum(ProblemSource), default=ProblemSource.USER_SUBMITTED, nullable=False)
    submitted_by = Column(UUID(as_uuid=True), nullable=True)  # user ID
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    replaced_by_id = Column(UUID(as_uuid=True), ForeignKey("problem_solutions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    problem = relationship("KnownProblem", back_populates="solutions")
    replaced_by = relationship("ProblemSolution", remote_side=[id], backref="replaces")
    
    __table_args__ = (
        Index("ix_problem_solutions_problem_id", "problem_id"),
        Index("ix_problem_solutions_active", "is_active"),
        Index("ix_problem_solutions_votes", "upvotes", "downvotes"),
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment_catalog.id", ondelete="CASCADE"), nullable=False)
    work_order_number = Column(String(50), nullable=True)
    maintenance_type = Column(String(20), nullable=False)  # preventive, corrective, predictive
    description = Column(Text, nullable=False)
    findings = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    parts_replaced = Column(JSONB, default=list)
    labor_hours = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    performed_by = Column(String(200), nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    equipment = relationship("EquipmentCatalog", back_populates="maintenance_records")
    
    __table_args__ = (
        Index("ix_maintenance_records_equipment_id", "equipment_id"),
        Index("ix_maintenance_records_type", "maintenance_type"),
        Index("ix_maintenance_records_date", "scheduled_date"),
    )


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulation = Column(String(200), nullable=False)  # Factory Act, OISD, PESO, etc.
    section = Column(String(100), nullable=True)
    requirement = Column(Text, nullable=False)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment_catalog.id", ondelete="SET NULL"), nullable=True)
    procedure_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="pending")  # compliant, gap, pending, non_compliant
    findings = Column(Text, nullable=True)
    evidence_documents = Column(JSONB, default=list)  # list of document IDs
    corrective_action = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    checked_at = Column(DateTime, nullable=True)
    checked_by = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("ix_compliance_checks_regulation", "regulation"),
        Index("ix_compliance_checks_status", "status"),
        Index("ix_compliance_checks_equipment_id", "equipment_id"),
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # from Supabase auth
    title = Column(String(500), nullable=True)
    context = Column(JSONB, default=dict)  # equipment context, filters, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_chat_sessions_user_id", "user_id"),
        Index("ix_chat_sessions_updated_at", "updated_at"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations = Column(JSONB, default=list)  # list of {document_id, chunk_id, excerpt, score}
    metadata = Column(JSONB, default=dict)  # model used, tokens, confidence, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
        Index("ix_chat_messages_created_at", "created_at"),
    )


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 or -1/1 for thumbs down/up
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("ix_user_feedback_message_id", "message_id"),
        Index("ix_user_feedback_user_id", "user_id"),
    )