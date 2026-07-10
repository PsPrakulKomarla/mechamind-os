import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, Index,
    JSON, BigInteger, Boolean, Integer, Float, UniqueConstraint, func, UUID
)
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector as _PgVector
    _HAS_PGVECTOR = True
except Exception:
    _HAS_PGVECTOR = False


def vector_type(dim: int):
    if _HAS_PGVECTOR:
        return _PgVector(dim)
    from sqlalchemy import LargeBinary
    return LargeBinary()


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


class EquipmentCategory(str, enum.Enum):
    PUMP = "pump"
    COMPRESSOR = "compressor"
    BOILER = "boiler"
    TURBINE = "turbine"
    HEAT_EXCHANGER = "heat_exchanger"
    CONVEYOR = "conveyor"
    VALVE = "valve"
    MOTOR = "motor"
    GENERATOR = "generator"
    TRANSFORMER = "transformer"
    VESSEL = "vessel"
    PIPING = "piping"
    INSTRUMENT = "instrument"
    CONTROL_SYSTEM = "control_system"
    SAFETY_SYSTEM = "safety_system"
    OTHER = "other"


class EquipmentCriticality(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class EquipmentStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    WARNING = "warning"
    DOWN = "down"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class ProblemSource(str, enum.Enum):
    AI_GENERATED = "ai_generated"
    USER_SUBMITTED = "user_submitted"
    DOCUMENT_EXTRACTED = "document_extracted"
    PRE_SEEDED = "pre_seeded"


class SolutionSource(str, enum.Enum):
    AI_GENERATED = "ai_generated"
    USER_SUBMITTED = "user_submitted"
    DOCUMENT_EXTRACTED = "document_extracted"
    PRE_SEEDED = "pre_seeded"


class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(DocumentType), nullable=False, default=DocumentType.OTHER)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADING)
    storage_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=True)
    page_count = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)  # for videos
    meta = Column("metadata", JSON, nullable=True, default=dict)
    tags = Column(JSON, nullable=True, default=list)
    equipment_tags = Column(JSON, nullable=True, default=list)
    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_documents_status", "status"),
        Index("ix_documents_type", "type"),
        Index("ix_documents_created_at", "created_at"),
        Index("ix_documents_uploaded_by", "uploaded_by"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(vector_type(1536), nullable=True)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(200), nullable=True)
    meta = Column("metadata", JSON, nullable=True, default=dict)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_document_id", "document_id"),
        Index("ix_chunks_chunk_index", "document_id", "chunk_index"),
    )


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    tag_number = Column(String(100), nullable=True, unique=True)
    category = Column(Enum(EquipmentCategory), nullable=False)
    criticality = Column(Enum(EquipmentCriticality), nullable=False, default=EquipmentCriticality.MINOR)
    status = Column(Enum(EquipmentStatus), nullable=False, default=EquipmentStatus.UNKNOWN)
    location = Column(String(200), nullable=True)
    area = Column(String(200), nullable=True)
    building = Column(String(200), nullable=True)
    floor = Column(String(50), nullable=True)
    coordinates = Column(JSON, nullable=True)  # {x, y, z} for 3D plant layout
    manufacturer = Column(String(200), nullable=True)
    model = Column(String(200), nullable=True)
    serial_number = Column(String(200), nullable=True)
    installation_date = Column(DateTime, nullable=True)
    last_maintenance_date = Column(DateTime, nullable=True)
    next_maintenance_date = Column(DateTime, nullable=True)
    specifications = Column(JSON, nullable=True, default=dict)
    operating_parameters = Column(JSON, nullable=True, default=dict)
    description = Column(Text, nullable=True)
    p_and_id_reference = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    common_issues = relationship("EquipmentIssue", back_populates="equipment", cascade="all, delete-orphan")
    problems = relationship("ProblemSolution", back_populates="equipment", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="equipment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_equipment_category", "category"),
        Index("ix_equipment_criticality", "criticality"),
        Index("ix_equipment_status", "status"),
        Index("ix_equipment_location", "location"),
        Index("ix_equipment_tag", "tag_number"),
    )


class EquipmentIssue(Base):
    __tablename__ = "equipment_issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    issue_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    symptoms = Column(JSON, nullable=True, default=list)
    root_causes = Column(JSON, nullable=True, default=list)
    severity = Column(Integer, nullable=False, default=5)  # 1-10
    frequency = Column(String(50), nullable=True)  # frequent, occasional, rare
    detection_method = Column(String(200), nullable=True)
    prevention = Column(Text, nullable=True)
    typical_solution = Column(Text, nullable=True)
    estimated_downtime_hours = Column(Float, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    regulatory_impact = Column(Boolean, default=False)
    safety_impact = Column(Boolean, default=False)
    source = Column(Enum(ProblemSource), default=ProblemSource.PRE_SEEDED)
    references = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    equipment = relationship("Equipment", back_populates="common_issues")

    __table_args__ = (
        Index("ix_equipment_issues_equipment_id", "equipment_id"),
        Index("ix_equipment_issues_severity", "severity"),
    )


class ProblemSolution(Base):
    __tablename__ = "problem_solutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    problem = Column(String(500), nullable=False)
    symptoms = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    solution = Column(Text, nullable=False)
    solution_steps = Column(JSON, nullable=True, default=list)
    tools_required = Column(JSON, nullable=True, default=list)
    parts_required = Column(JSON, nullable=True, default=list)
    estimated_time_hours = Column(Float, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    safety_precautions = Column(Text, nullable=True)
    source = Column(Enum(SolutionSource), default=SolutionSource.AI_GENERATED)
    submitted_by = Column(UUID(as_uuid=True), nullable=True)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    confidence_score = Column(Float, nullable=True)  # for AI-generated
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    replaced_by_id = Column(UUID(as_uuid=True), ForeignKey("problem_solutions.id"), nullable=True)
    parent_problem_id = Column(UUID(as_uuid=True), ForeignKey("problem_solutions.id"), nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    equipment = relationship("Equipment", back_populates="problems")
    replaced_by = relationship("ProblemSolution", foreign_keys=[replaced_by_id], remote_side=[id], backref="replaces")
    parent_problem = relationship("ProblemSolution", foreign_keys=[parent_problem_id], remote_side=[id], backref="alternatives")

    __table_args__ = (
        Index("ix_problem_solutions_equipment_id", "equipment_id"),
        Index("ix_problem_solutions_problem", "problem"),
        Index("ix_problem_solutions_active", "is_active"),
        Index("ix_problem_solutions_votes", "upvotes", "downvotes"),
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    work_order_number = Column(String(100), nullable=True, unique=True)
    maintenance_type = Column(Enum(MaintenanceType), nullable=False, default=MaintenanceType.PREVENTIVE)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    parts_replaced = Column(JSON, nullable=True, default=list)
    labor_hours = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    performed_by = Column(UUID(as_uuid=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), nullable=False, default="planned")
    priority = Column(String(20), nullable=True)
    attachments = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    equipment = relationship("Equipment", back_populates="maintenance_records")

    __table_args__ = (
        Index("ix_maintenance_equipment_id", "equipment_id"),
        Index("ix_maintenance_work_order", "work_order_number"),
        Index("ix_maintenance_scheduled_date", "scheduled_date"),
        Index("ix_maintenance_status", "status"),
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(300), nullable=True)
    context = Column(JSON, nullable=True, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

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
    citations = Column(JSON, nullable=True, default=list)
    meta = Column("metadata", JSON, nullable=True, default=dict)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    feedback = Column(String(20), nullable=True)  # helpful, not_helpful
    created_at = Column(DateTime, nullable=False, default=func.now())

    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
        Index("ix_chat_messages_created_at", "created_at"),
    )


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # problem_report, solution_submission, vote, correction
    target_type = Column(String(50), nullable=False)  # equipment, problem_solution, document, chat_message
    target_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5
    vote = Column(String(10), nullable=True)  # upvote, downvote
    meta = Column("metadata", JSON, nullable=True, default=dict)
    status = Column(String(20), default="pending")  # pending, reviewed, applied, rejected
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_user_feedback_user_id", "user_id"),
        Index("ix_user_feedback_target", "target_type", "target_id"),
        Index("ix_user_feedback_status", "status"),
    )


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulation = Column(String(200), nullable=False)  # Factory Act, OISD, PESO, etc.
    section = Column(String(100), nullable=True)
    requirement = Column(Text, nullable=False)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True)
    procedure_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="pending")  # compliant, gap, pending, non_compliant
    findings = Column(Text, nullable=True)
    evidence_documents = Column(JSON, nullable=True, default=list)  # list of document IDs
    corrective_action = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    checked_at = Column(DateTime, nullable=True)
    checked_by = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_compliance_checks_regulation", "regulation"),
        Index("ix_compliance_checks_status", "status"),
        Index("ix_compliance_checks_equipment_id", "equipment_id"),
    )


class KnownProblem(Base):
    __tablename__ = "known_problems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    problem_name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    symptoms = Column(JSON, nullable=True, default=list)  # list of symptom strings
    severity = Column(Integer, nullable=False)  # 1-10
    frequency = Column(String(20), nullable=True)  # frequent, occasional, rare
    root_causes = Column(JSON, nullable=True, default=list)  # list of root cause strings
    detection_methods = Column(JSON, nullable=True, default=list)  # how to detect
    affected_parameters = Column(JSON, nullable=True, default=list)  # parameters that deviate
    source = Column(Enum(ProblemSource), default=ProblemSource.PRE_SEEDED, nullable=False)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_known_problems_equipment_id", "equipment_id"),
        Index("ix_known_problems_severity", "severity"),
        Index("ix_known_problems_active", "is_active"),
    )


class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False, unique=True)
    type = Column(String(100), nullable=False)  # equipment, personnel, procedure, regulation, parameter, location
    properties = Column(JSON, nullable=True, default=dict)
    description = Column(Text, nullable=True)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_entities_type", "type"),
        Index("ix_entities_name", "name"),
    )


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(100), nullable=False)  # located_in, connected_to, maintained_by, etc.
    properties = Column(JSON, nullable=True, default=dict)
    confidence = Column(Float, default=1.0)
    source = Column(String(50), default="extracted")  # extracted, manual, inferred
    created_at = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_relationships_source", "source_id"),
        Index("ix_relationships_target", "target_id"),
        Index("ix_relationships_type", "relationship_type"),
        UniqueConstraint("source_id", "target_id", "relationship_type", name="uq_relationship"),
    )


# Aliases for backwards compatibility with code that referenced the older names.
EquipmentCatalog = Equipment
Relationship = EntityRelationship
