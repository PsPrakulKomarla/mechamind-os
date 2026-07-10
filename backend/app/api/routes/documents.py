from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List
from uuid import UUID
import os
import shutil
from datetime import datetime

from app.db.database import get_db
from app.db.models import Document, DocumentChunk, DocumentType, DocumentStatus
from app.models.schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentChunkResponse, DocumentSearchResult,
    DocumentType as SchemaDocumentType, DocumentStatus as SchemaDocumentStatus
)
from app.services.ingestion.pipeline import IngestionPipeline
from app.config import settings

router = APIRouter()

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

ingestion_pipeline = IngestionPipeline()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    type: SchemaDocumentType = Form(SchemaDocumentType.OTHER),
    tags: Optional[str] = Form(None),
    equipment_tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Determine document type from extension if not provided
    if type == SchemaDocumentType.OTHER:
        ext = os.path.splitext(file.filename)[1].lower()
        type_map = {
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.WORD,
            ".doc": DocumentType.WORD,
            ".jpg": DocumentType.IMAGE,
            ".jpeg": DocumentType.IMAGE,
            ".png": DocumentType.IMAGE,
            ".tiff": DocumentType.IMAGE,
            ".xlsx": DocumentType.SPREADSHEET,
            ".xls": DocumentType.SPREADSHEET,
            ".csv": DocumentType.SPREADSHEET,
            ".mp4": DocumentType.VIDEO,
            ".avi": DocumentType.VIDEO,
            ".mov": DocumentType.VIDEO,
            ".eml": DocumentType.EMAIL,
            ".msg": DocumentType.EMAIL,
            ".txt": DocumentType.TEXT,
            ".md": DocumentType.TEXT,
        }
        type = type_map.get(ext, DocumentType.OTHER)
    
    # Save file
    file_id = UUID()
    file_ext = os.path.splitext(file.filename)[1]
    storage_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
    
    with open(storage_path, "wb") as f:
        f.write(file_content)
    
    # Versioning logic: check if a document with the same title exists
    version = 1
    version_group_id = None
    
    if title:
        result = await db.execute(
            select(Document)
            .where(Document.title == title)
            .order_by(Document.version.desc())
            .limit(1)
        )
        latest_doc = result.scalar_one_or_none()
        if latest_doc:
            version = latest_doc.version + 1
            version_group_id = latest_doc.version_group_id or latest_doc.id

    # Create document record
    doc = Document(
        id=file_id,
        title=title or file.filename,
        description=description,
        type=type,
        status=DocumentStatus.UPLOADING,
        storage_path=storage_path,
        file_size=len(file_content),
        mime_type=file.content_type,
        version=version,
        version_group_id=version_group_id,
        meta={
            "tags": tags.split(",") if tags else [],
            "equipment_tags": equipment_tags.split(",") if equipment_tags else [],
        },
    )
    
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    # Process in background
    background_tasks.add_task(ingestion_pipeline.process_document, doc.id)
    
    return doc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    status: Optional[SchemaDocumentStatus] = None,
    type: Optional[SchemaDocumentType] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Document)
    
    if status:
        query = query.where(Document.status == status)
    if type:
        query = query.where(Document.type == type)
    if search:
        query = query.where(
            or_(
                Document.title.ilike(f"%{search}%"),
                Document.description.ilike(f"%{search}%"),
            )
        )
    
    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    # Verify document exists
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    if not doc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Document not found")
    
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .offset(skip)
        .limit(limit)
    )
    chunks = result.scalars().all()
    
    return chunks


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    update: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    document.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(document)
    
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    if os.path.exists(document.storage_path):
        os.remove(document.storage_path)
    
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.status = DocumentStatus.PROCESSING
    document.error_message = None
    await db.commit()
    
    background_tasks.add_task(ingestion_pipeline.process_document, document_id)
    
    return {"message": "Reprocessing started"}


@router.get("/stats/overview")
async def get_document_stats(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(Document.id)))
    total_count = total.scalar()
    
    by_status = await db.execute(
        select(Document.status, func.count(Document.id))
        .group_by(Document.status)
    )
    status_counts = dict(by_status.all())
    
    by_type = await db.execute(
        select(Document.type, func.count(Document.id))
        .group_by(Document.type)
    )
    type_counts = dict(by_type.all())
    
    total_size = await db.execute(select(func.sum(Document.file_size)))
    
    return {
        "total_documents": total_count,
        "by_status": status_counts,
        "by_type": type_counts,
        "total_size_bytes": total_size.scalar() or 0,
    }