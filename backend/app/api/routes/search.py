from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.db.database import get_db
from app.db.models import Document, DocumentChunk, DocumentType, DocumentStatus
from app.models.schemas import SearchRequest, SearchResponse, SearchResult
from app.services.rag.chain import HybridRetriever
from app.services.vector_store.qdrant_client import QdrantVectorStore
from app.core.config import settings

router = APIRouter()

retriever = HybridRetriever()
vector_store = QdrantVectorStore()


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    import time
    start = time.time()
    
    # Perform hybrid search
    results = await retriever.search(
        query=request.query,
        top_k=request.top_k,
        threshold=request.threshold,
        filters=request.filters,
        search_type=request.search_type,
    )
    
    query_time = int((time.time() - start) * 1000)
    
    return SearchResponse(
        results=results,
        total=len(results),
        query_time_ms=query_time,
    )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    # Get suggestions from document titles and equipment tags
    result = await db.execute(
        select(Document.title)
        .where(Document.title.ilike(f"%{q}%"))
        .where(Document.status == DocumentStatus.READY)
        .limit(limit)
    )
    titles = result.scalars().all()
    
    # Also search equipment
    equip_result = await db.execute(
        select(Equipment.name, Equipment.tag_number)
        .where(or_(
            Equipment.name.ilike(f"%{q}%"),
            Equipment.tag_number.ilike(f"%{q}%"),
        ))
        .where(Equipment.is_active == True)
        .limit(limit)
    )
    equipment = [{"name": name, "tag": tag} for name, tag in equip_result]
    
    return {
        "suggestions": titles,
        "equipment": equipment,
    }


@router.post("/semantic")
async def semantic_search(
    query: str = Body(..., embed=True),
    top_k: int = Body(10, embed=True),
    threshold: float = Body(0.7, embed=True),
    filters: Dict[str, Any] = Body({}, embed=True),
    db: AsyncSession = Depends(get_db),
):
    results = await retriever.semantic_search(
        query=query,
        top_k=top_k,
        threshold=threshold,
        filters=filters,
    )
    return {"results": results}


@router.post("/keyword")
async def keyword_search(
    query: str = Body(..., embed=True),
    top_k: int = Body(10, embed=True),
    filters: Dict[str, Any] = Body({}, embed=True),
    db: AsyncSession = Depends(get_db),
):
    results = await retriever.keyword_search(
        query=query,
        top_k=top_k,
        filters=filters,
    )
    return {"results": results}


@router.post("/hybrid")
async def hybrid_search(
    query: str = Body(..., embed=True),
    top_k: int = Body(10, embed=True),
    threshold: float = Body(0.7, embed=True),
    filters: Dict[str, Any] = Body({}, embed=True),
    alpha: float = Body(0.5, embed=True),  # 0=keyword, 1=semantic
    db: AsyncSession = Depends(get_db),
):
    results = await retriever.hybrid_search(
        query=query,
        top_k=top_k,
        threshold=threshold,
        filters=filters,
        alpha=alpha,
    )
    return {"results": results}


@router.get("/equipment/{equipment_id}/documents")
async def search_equipment_documents(
    equipment_id: UUID,
    query: Optional[str] = None,
    top_k: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    # Search for documents related to specific equipment
    filters = {"equipment_tags": [str(equipment_id)]}
    
    if query:
        results = await retriever.search(
            query=query,
            top_k=top_k,
            filters=filters,
        )
    else:
        # Get all documents tagged with this equipment
        result = await db.execute(
            select(Document)
            .where(Document.meta["equipment_tags"].contains([str(equipment_id)]))
            .where(Document.status == DocumentStatus.READY)
            .order_by(Document.created_at.desc())
            .limit(top_k)
        )
        docs = result.scalars().all()
        results = [
            SearchResult(
                document_id=d.id,
                document_title=d.title,
                chunk_id=d.chunks[0].id if d.chunks else UUID(int=0),
                content=d.chunks[0].content[:500] if d.chunks else "",
                score=1.0,
                page_number=d.chunks[0].meta.get("page_number") if d.chunks else None,
                meta=d.chunks[0].meta if d.chunks else {},
            )
            for d in docs
        ]
    
    return {"results": results}


@router.post("/reindex")
async def reindex_documents(
    document_ids: Optional[List[UUID]] = None,
    db: AsyncSession = Depends(get_db),
):
    # Rebuild vector embeddings for documents
    if document_ids:
        query = select(Document).where(Document.id.in_(document_ids))
    else:
        query = select(Document).where(Document.status == DocumentStatus.READY)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    count = 0
    for doc in documents:
        chunks_result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        )
        chunks = chunks_result.scalars().all()
        
        for chunk in chunks:
            if chunk.embedding:
                await vector_store.upsert_chunk(chunk)
                count += 1
    
    return {"reindexed_chunks": count}