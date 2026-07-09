"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    equipment_category = postgresql.ENUM(
        'pump', 'compressor', 'boiler', 'turbine', 'heat_exchanger',
        'conveyor', 'valve', 'motor', 'generator', 'transformer',
        'vessel', 'piping', 'instrument', 'control_system', 'safety_system',
        'other',
        name='equipmentcategory',
        create_type=True
    )
    equipment_category.create(op.get_bind())

    equipment_criticality = postgresql.ENUM(
        'critical', 'major', 'minor',
        name='equipmentcriticality',
        create_type=True
    )
    equipment_criticality.create(op.get_bind())

    equipment_status = postgresql.ENUM(
        'operational', 'warning', 'down', 'maintenance', 'unknown',
        name='equipmentstatus',
        create_type=True
    )
    equipment_status.create(op.get_bind())

    document_type = postgresql.ENUM(
        'pdf', 'image', 'spreadsheet', 'video', 'email', 'text', 'cad', 'other',
        name='documenttype',
        create_type=True
    )
    document_type.create(op.get_bind())

    document_status = postgresql.ENUM(
        'uploading', 'processing', 'ready', 'failed',
        name='documentstatus',
        create_type=True
    )
    document_status.create(op.get_bind())

    problem_source = postgresql.ENUM(
        'ai_generated', 'user_submitted', 'document_extracted', 'pre_seeded',
        name='problemsource',
        create_type=True
    )
    problem_source.create(op.get_bind())

    solution_source = postgresql.ENUM(
        'ai_generated', 'user_submitted', 'document_extracted', 'pre_seeded',
        name='solutionsource',
        create_type=True
    )
    solution_source.create(op.get_bind())

    maintenance_type = postgresql.ENUM(
        'preventive', 'corrective', 'predictive',
        name='maintenancetype',
        create_type=True
    )
    maintenance_type.create(op.get_bind())

    # Create tables
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('type', document_type, nullable=False, server_default='other'),
        sa.Column('status', document_status, nullable=False, server_default='uploading'),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('page_count', sa.Integer, nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('tags', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('equipment_tags', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('original_filename', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_type', 'documents', ['type'])
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])

    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('embedding', sa.dialects.postgresql.VECTOR(1536), nullable=True),
        sa.Column('page_number', sa.Integer, nullable=True),
        sa.Column('section_title', sa.String(200), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('token_count', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_chunk_index', 'document_chunks', ['document_id', 'chunk_index'])

    op.create_table(
        'equipment',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('tag_number', sa.String(100), nullable=True, unique=True),
        sa.Column('category', equipment_category, nullable=False),
        sa.Column('criticality', equipment_criticality, nullable=False, server_default='minor'),
        sa.Column('status', equipment_status, nullable=False, server_default='unknown'),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('area', sa.String(200), nullable=True),
        sa.Column('building', sa.String(200), nullable=True),
        sa.Column('floor', sa.String(50), nullable=True),
        sa.Column('coordinates', postgresql.JSONB, nullable=True),
        sa.Column('manufacturer', sa.String(200), nullable=True),
        sa.Column('model', sa.String(200), nullable=True),
        sa.Column('serial_number', sa.String(200), nullable=True),
        sa.Column('installation_date', sa.DateTime, nullable=True),
        sa.Column('last_maintenance_date', sa.DateTime, nullable=True),
        sa.Column('next_maintenance_date', sa.DateTime, nullable=True),
        sa.Column('specifications', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('operating_parameters', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('p_and_id_reference', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_equipment_category', 'equipment', ['category'])
    op.create_index('ix_equipment_criticality', 'equipment', ['criticality'])
    op.create_index('ix_equipment_status', 'equipment', ['status'])
    op.create_index('ix_equipment_location', 'equipment', ['location'])
    op.create_index('ix_equipment_tag', 'equipment', ['tag_number'])

    op.create_table(
        'equipment_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipment.id', ondelete='CASCADE'), nullable=False),
        sa.Column('issue_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('symptoms', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('root_causes', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('severity', sa.Integer, nullable=False, server_default='5'),
        sa.Column('frequency', sa.String(50), nullable=True),
        sa.Column('detection_method', sa.String(200), nullable=True),
        sa.Column('prevention', sa.Text, nullable=True),
        sa.Column('typical_solution', sa.Text, nullable=True),
        sa.Column('estimated_downtime_hours', sa.Float, nullable=True),
        sa.Column('estimated_cost', sa.Float, nullable=True),
        sa.Column('regulatory_impact', sa.Boolean, default=False),
        sa.Column('safety_impact', sa.Boolean, default=False),
        sa.Column('source', problem_source, default='pre_seeded'),
        sa.Column('references', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_equipment_issues_equipment_id', 'equipment_issues', ['equipment_id'])
    op.create_index('ix_equipment_issues_severity', 'equipment_issues', ['severity'])

    op.create_table(
        'problem_solutions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipment.id', ondelete='CASCADE'), nullable=False),
        sa.Column('problem', sa.String(500), nullable=False),
        sa.Column('symptoms', sa.Text, nullable=True),
        sa.Column('root_cause', sa.Text, nullable=True),
        sa.Column('solution', sa.Text, nullable=False),
        sa.Column('solution_steps', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('tools_required', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('parts_required', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('estimated_time_hours', sa.Float, nullable=True),
        sa.Column('estimated_cost', sa.Float, nullable=True),
        sa.Column('safety_precautions', sa.Text, nullable=True),
        sa.Column('source', solution_source, default='ai_generated'),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('upvotes', sa.Integer, default=0),
        sa.Column('downvotes', sa.Integer, default=0),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('replaced_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problem_solutions.id'), nullable=True),
        sa.Column('parent_problem_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('problem_solutions.id'), nullable=True),
        sa.Column('tags', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_problem_solutions_equipment_id', 'problem_solutions', ['equipment_id'])
    op.create_index('ix_problem_solutions_problem', 'problem_solutions', ['problem'])
    op.create_index('ix_problem_solutions_active', 'problem_solutions', ['is_active'])
    op.create_index('ix_problem_solutions_votes', 'problem_solutions', ['upvotes', 'downvotes'])

    op.create_table(
        'maintenance_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipment.id', ondelete='CASCADE'), nullable=False),
        sa.Column('work_order_number', sa.String(100), nullable=True, unique=True),
        sa.Column('maintenance_type', maintenance_type, nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('findings', sa.Text, nullable=True),
        sa.Column('actions_taken', sa.Text, nullable=True),
        sa.Column('parts_replaced', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('labor_hours', sa.Float, nullable=True),
        sa.Column('cost', sa.Float, nullable=True),
        sa.Column('scheduled_date', sa.DateTime, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='planned'),
        sa.Column('priority', sa.String(20), nullable=True),
        sa.Column('attachments', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_maintenance_records_equipment_id', 'maintenance_records', ['equipment_id'])
    op.create_index('ix_maintenance_records_work_order', 'maintenance_records', ['work_order_number'])
    op.create_index('ix_maintenance_records_scheduled_date', 'maintenance_records', ['scheduled_date'])
    op.create_index('ix_maintenance_records_status', 'maintenance_records', ['status'])

    op.create_table(
        'compliance_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('regulation', sa.String(200), nullable=False),
        sa.Column('section', sa.String(100), nullable=True),
        sa.Column('requirement', sa.Text, nullable=False),
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('equipment.id', ondelete='SET NULL'), nullable=True),
        sa.Column('procedure_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('findings', sa.Text, nullable=True),
        sa.Column('evidence_documents', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('corrective_action', sa.Text, nullable=True),
        sa.Column('due_date', sa.DateTime, nullable=True),
        sa.Column('checked_at', sa.DateTime, nullable=True),
        sa.Column('checked_by', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_compliance_checks_regulation', 'compliance_checks', ['regulation'])
    op.create_index('ix_compliance_checks_status', 'compliance_checks', ['status'])
    op.create_index('ix_compliance_checks_equipment_id', 'compliance_checks', ['equipment_id'])

    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(300), nullable=True),
        sa.Column('context', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_updated_at', 'chat_sessions', ['updated_at'])

    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('citations', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('feedback', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])

    op.create_table(
        'user_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('rating', sa.Integer, nullable=True),
        sa.Column('vote', sa.String(10), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_user_feedback_user_id', 'user_feedback', ['user_id'])
    op.create_index('ix_user_feedback_target', 'user_feedback', ['target_type', 'target_id'])
    op.create_index('ix_user_feedback_status', 'user_feedback', ['status'])

    op.create_table(
        'entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(300), nullable=False, unique=True),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('properties', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_entities_type', 'entities', ['type'])
    op.create_index('ix_entities_name', 'entities', ['name'])

    op.create_table(
        'entity_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('properties', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('source', sa.String(50), default='extracted'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_entity_relationships_source', 'entity_relationships', ['source_id'])
    op.create_index('ix_entity_relationships_target', 'entity_relationships', ['target_id'])
    op.create_index('ix_entity_relationships_type', 'entity_relationships', ['relationship_type'])
    op.create_unique_constraint('uq_entity_relationship', 'entity_relationships', ['source_id', 'target_id', 'relationship_type'])


def downgrade() -> None:
    op.drop_table('entity_relationships')
    op.drop_table('entities')
    op.drop_table('user_feedback')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('compliance_checks')
    op.drop_table('maintenance_records')
    op.drop_table('problem_solutions')
    op.drop_table('equipment_issues')
    op.drop_table('equipment')
    op.drop_table('document_chunks')
    op.drop_table('documents')

    # Drop enum types
    for enum_name in [
        'equipmentcategory', 'equipmentcriticality', 'equipmentstatus',
        'documenttype', 'documentstatus', 'problemsource', 'solutionsource',
        'maintenancetype'
    ]:
        op.execute(f'DROP TYPE IF EXISTS {enum_name}')