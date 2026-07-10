from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from uuid import UUID
import enum


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


class LLMProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class DocumentBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    type: DocumentType = DocumentType.OTHER
    tags: List[str] = []
    equipment_tags: List[str] = []


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    equipment_tags: Optional[List[str]] = None


class DocumentResponse(DocumentBase):
    id: UUID
    status: DocumentStatus
    file_size: int
    mime_type: Optional[str] = None
    page_count: Optional[int] = None
    duration_seconds: Optional[float] = None
    meta: Dict[str, Any] = Field(default={}, alias="metadata")
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    meta: Dict[str, Any] = Field(default={}, alias="metadata")
    token_count: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentSearchResult(BaseModel):
    document: DocumentResponse
    chunks: List[DocumentChunkResponse]
    score: float


# Equipment Models
class EquipmentBase(BaseModel):
    name: str = Field(..., max_length=200)
    tag_number: Optional[str] = Field(None, max_length=100)
    category: EquipmentCategory
    criticality: EquipmentCriticality = EquipmentCriticality.MINOR
    location: Optional[str] = None
    area: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    specifications: Dict[str, Any] = {}
    operating_parameters: Dict[str, Any] = {}
    description: Optional[str] = None
    p_and_id_reference: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    tag_number: Optional[str] = None
    category: Optional[EquipmentCategory] = None
    criticality: Optional[EquipmentCriticality] = None
    status: Optional[EquipmentStatus] = None
    location: Optional[str] = None
    area: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    operating_parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    p_and_id_reference: Optional[str] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class EquipmentIssueBase(BaseModel):
    issue_name: str = Field(..., max_length=200)
    description: Optional[str] = None
    symptoms: List[str] = []
    root_causes: List[str] = []
    severity: int = Field(..., ge=1, le=10)
    frequency: Optional[str] = None
    detection_method: Optional[str] = None
    prevention: Optional[str] = None
    typical_solution: Optional[str] = None
    estimated_downtime_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    regulatory_impact: bool = False
    safety_impact: bool = False
    references: List[str] = []


class EquipmentIssueCreate(EquipmentIssueBase):
    pass


class EquipmentIssueResponse(EquipmentIssueBase):
    id: UUID
    equipment_id: UUID
    source: ProblemSource
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class EquipmentResponse(EquipmentBase):
    id: UUID
    tag_number: Optional[str] = None
    status: EquipmentStatus
    installation_date: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    common_issues: List[EquipmentIssueResponse] = []
    
    class Config:
        from_attributes = True
        populate_by_name = True


class EquipmentListResponse(BaseModel):
    equipment: List[EquipmentResponse]
    total: int
    page: int
    page_size: int


# Problem/Solution Models
class ProblemSolutionBase(BaseModel):
    problem: str = Field(..., max_length=500)
    symptoms: Optional[str] = None
    root_cause: Optional[str] = None
    solution: str
    solution_steps: List[str] = []
    tools_required: List[str] = []
    parts_required: List[str] = []
    estimated_time_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    safety_precautions: Optional[str] = None
    tags: List[str] = []


class ProblemSolutionCreate(ProblemSolutionBase):
    equipment_id: UUID


class ProblemSolutionUpdate(BaseModel):
    problem: Optional[str] = None
    symptoms: Optional[str] = None
    root_cause: Optional[str] = None
    solution: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    tools_required: Optional[List[str]] = None
    parts_required: Optional[List[str]] = None
    estimated_time_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    safety_precautions: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class ProblemSolutionResponse(ProblemSolutionBase):
    id: UUID
    equipment_id: UUID
    source: SolutionSource
    submitted_by: Optional[UUID] = None
    upvotes: int
    downvotes: int
    confidence_score: Optional[float] = None
    is_active: bool
    is_verified: bool
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    replaced_by_id: Optional[UUID] = None
    parent_problem_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class ProblemSolutionVote(BaseModel):
    vote: str  # "upvote" or "downvote"


class ProblemSolutionWithEquipment(ProblemSolutionResponse):
    equipment_name: str
    equipment_tag: Optional[str] = None
    equipment_category: EquipmentCategory


# Chat Models
class ChatMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Citation(BaseModel):
    document_id: UUID
    chunk_id: UUID
    excerpt: str
    score: float
    document_title: str
    page_number: Optional[int] = None


class ChatMessageBase(BaseModel):
    role: ChatMessageRole
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: UUID
    session_id: UUID
    citations: List[Citation] = []
    meta: Dict[str, Any] = Field(default={}, alias="metadata")
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class ChatSessionBase(BaseModel):
    title: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ChatSessionResponse(ChatSessionBase):
    id: UUID
    user_id: UUID
    context: Dict[str, Any] = {}
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True
        populate_by_name = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    provider: Optional[LLMProvider] = None
    model: Optional[str] = None
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    use_rag: bool = True
    top_k: int = Field(default=10, ge=1, le=50)
    filters: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    message: ChatMessageResponse
    session_id: UUID
    suggested_followups: List[str] = []


class ChatStreamChunk(BaseModel):
    type: str  # "token", "citation", "done", "error"
    content: Optional[str] = None
    citation: Optional[Citation] = None
    done: bool = False
    error: Optional[str] = None


class FeedbackCreate(BaseModel):
    message_id: UUID
    rating: Optional[int] = None
    feedback_text: Optional[str] = None
    vote: Optional[str] = None
    meta: Dict[str, Any] = Field(default={}, alias="metadata")


class FeedbackResponse(BaseModel):
    id: UUID
    user_id: UUID
    feedback_type: Optional[str] = None
    target_type: Optional[str] = None
    target_id: UUID
    content: Optional[str] = None
    rating: Optional[int] = None
    vote: Optional[str] = None
    meta: Dict[str, Any] = Field(default={}, alias="metadata")
    status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# Knowledge Graph Models
class EntityResponse(BaseModel):
    id: UUID
    name: str
    type: str
    properties: Dict[str, Any] = {}
    description: Optional[str] = None
    source_document_id: Optional[UUID] = None
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class EntityRelationshipResponse(BaseModel):
    id: UUID
    source_id: UUID
    target_id: UUID
    relationship_type: str
    properties: Dict[str, Any] = {}
    confidence: float = 1.0
    source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class KnowledgeGraphQuery(BaseModel):
    start_entity_id: Optional[UUID] = None
    query: Optional[str] = None
    max_depth: int = 2
    relationship_types: Optional[List[str]] = None


class KnowledgeGraphResponse(BaseModel):
    nodes: List[Any] = []
    edges: List[Any] = []
    stats: Dict[str, Any] = {}


# Safety Models
class SafetyZoneResponse(BaseModel):
    equipment_id: str
    equipment_name: str
    equipment_tag: Optional[str] = None
    category: Optional[str] = None
    location: Optional[Any] = None
    area: Optional[str] = None
    hazard_classification: Optional[str] = None
    risk_level: Optional[str] = None


class PermitResponse(BaseModel):
    pass


class IncidentResponse(BaseModel):
    pass


# Compliance Models
class ComplianceCheckBase(BaseModel):
    regulation: str
    section: Optional[str] = None
    requirement: str
    equipment_id: Optional[UUID] = None
    procedure_id: Optional[UUID] = None
    status: Optional[str] = None
    findings: Optional[str] = None
    evidence_documents: List[Any] = []
    corrective_action: Optional[str] = None
    due_date: Optional[datetime] = None


class ComplianceCheckCreate(ComplianceCheckBase):
    pass


class ComplianceCheckUpdate(BaseModel):
    regulation: Optional[str] = None
    section: Optional[str] = None
    requirement: Optional[str] = None
    equipment_id: Optional[UUID] = None
    procedure_id: Optional[UUID] = None
    status: Optional[str] = None
    findings: Optional[str] = None
    evidence_documents: Optional[List[Any]] = None
    corrective_action: Optional[str] = None
    due_date: Optional[datetime] = None


class ComplianceCheckResponse(ComplianceCheckBase):
    id: UUID
    checked_at: Optional[datetime] = None
    checked_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# Search Models
class SearchRequest(BaseModel):
    query: str
    filters: Dict[str, Any] = {}
    top_k: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    search_type: str = "hybrid"  # semantic, keyword, hybrid


class SearchResult(BaseModel):
    document_id: UUID
    document_title: str
    chunk_id: UUID
    content: str
    score: float
    page_number: Optional[int] = None
    meta: Dict[str, Any] = Field(default={}, alias="metadata")


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query_time_ms: int


# Maintenance Models
class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"


class MaintenanceRecordBase(BaseModel):
    work_order_number: Optional[str] = None
    maintenance_type: MaintenanceType
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    findings: Optional[str] = None
    actions_taken: Optional[str] = None
    parts_replaced: List[str] = []
    labor_hours: Optional[float] = None
    cost: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    priority: Optional[str] = None


class MaintenanceRecordCreate(MaintenanceRecordBase):
    equipment_id: UUID


class MaintenanceRecordUpdate(BaseModel):
    work_order_number: Optional[str] = None
    maintenance_type: Optional[MaintenanceType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    findings: Optional[str] = None
    actions_taken: Optional[str] = None
    parts_replaced: Optional[List[str]] = None
    labor_hours: Optional[float] = None
    cost: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    performed_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class MaintenanceRecordResponse(MaintenanceRecordBase):
    id: UUID
    equipment_id: UUID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    performed_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    status: str
    attachments: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


# User Feedback Models
class FeedbackType(str, enum.Enum):
    PROBLEM_REPORT = "problem_report"
    SOLUTION_SUBMISSION = "solution_submission"
    VOTE = "vote"
    CORRECTION = "correction"


class UserFeedbackCreate(BaseModel):
    feedback_type: FeedbackType
    target_type: str
    target_id: UUID
    content: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    vote: Optional[str] = None
    meta: Dict[str, Any] = Field(default={}, alias="metadata")


class UserFeedbackResponse(BaseModel):
    id: UUID
    user_id: UUID
    feedback_type: FeedbackType
    target_type: str
    target_id: UUID
    content: Optional[str] = None
    rating: Optional[int] = None
    vote: Optional[str] = None
    meta: Dict[str, Any] = Field(default={}, alias="metadata")
    status: str
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


# RAG Models
class RAGConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OPENAI
    model: Optional[str] = None
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    top_k: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_context_length: int = Field(default=8000, ge=1000, le=32000)
    use_reranker: bool = True


# Health Check
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    vector_db: str
    graph_db: str
    redis: str
    timestamp: datetime