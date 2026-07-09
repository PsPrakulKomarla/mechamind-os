from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.db.database import get_db
from app.db.models import Entity, EntityRelationship, Equipment, Document
from app.models.schemas import (
    EntityResponse, EntityRelationshipResponse,
    KnowledgeGraphQuery, KnowledgeGraphResponse,
)
from app.services.knowledge_graph.extractor import EntityExtractor

router = APIRouter()


@router.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Entity)
    
    if entity_type:
        query = query.where(Entity.type == entity_type)
    if search:
        query = query.where(Entity.name.ilike(f"%{search}%"))
    
    query = query.order_by(Entity.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    db_entity = Entity(**entity)
    db.add(db_entity)
    await db.commit()
    await db.refresh(db_entity)
    return db_entity


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Entity).where(Entity.id == entity_id))
    entity = result.scalar_one_or_none()
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return entity


@router.get("/entities/{entity_id}/neighbors")
async def get_entity_neighbors(
    entity_id: UUID,
    max_depth: int = Query(2, ge=1, le=3),
    relationship_types: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
):
    # Recursive CTE to find neighbors up to max_depth
    cte = select(
        EntityRelationship.source_id,
        EntityRelationship.target_id,
        EntityRelationship.relationship_type,
        EntityRelationship.properties,
        1
    ).where(
        or_(
            EntityRelationship.source_id == entity_id,
            EntityRelationship.target_id == entity_id,
        )
    )
    
    if relationship_types:
        cte = cte.where(EntityRelationship.relationship_type.in_(relationship_types))
    
    cte = cte.cte(name="neighbors", recursive=True)
    
    # This is a simplified version - full recursive CTE would be more complex
    # For now, just get direct relationships
    result = await db.execute(
        select(EntityRelationship, Entity.name, Entity.type)
        .join(Entity, or_(
            and_(Entity.id == EntityRelationship.source_id, Entity.id != entity_id),
            and_(Entity.id == EntityRelationship.target_id, Entity.id != entity_id),
        ))
        .where(
            or_(
                EntityRelationship.source_id == entity_id,
                EntityRelationship.target_id == entity_id,
            )
        )
    )
    
    neighbors = []
    for rel, name, etype in result:
        other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
        direction = "outgoing" if rel.source_id == entity_id else "incoming"
        neighbors.append({
            "entity_id": str(other_id),
            "entity_name": name,
            "entity_type": etype,
            "relationship_type": rel.relationship_type,
            "direction": direction,
            "properties": rel.properties,
        })
    
    return {"neighbors": neighbors}


@router.post("/query", response_model=KnowledgeGraphResponse)
async def query_knowledge_graph(
    query: KnowledgeGraphQuery,
    db: AsyncSession = Depends(get_db),
):
    # Execute a graph query
    # This would use Cypher-like queries against Neo4j in production
    # For now, use SQL recursive queries
    
    if query.start_entity_id:
        # Start from specific entity
        result = await db.execute(
            select(Entity).where(Entity.id == query.start_entity_id)
        )
        start_entity = result.scalar_one_or_none()
        if not start_entity:
            raise HTTPException(status_code=404, detail="Start entity not found")
        
        # Get subgraph
        subgraph = await get_subgraph(db, query.start_entity_id, query.max_depth)
    else:
        # Search by criteria
        pass
    
    return KnowledgeGraphResponse(
        nodes=[],
        edges=[],
        stats={},
    )


async def get_subgraph(db: AsyncSession, start_id: UUID, max_depth: int) -> Dict[str, Any]:
    # Simplified - get neighbors up to max_depth
    nodes = {}
    edges = []
    
    def add_node(entity):
        nodes[str(entity.id)] = {
            "id": str(entity.id),
            "name": entity.name,
            "type": entity.type,
            "properties": entity.properties,
        }
    
    # Get start entity
    result = await db.execute(select(Entity).where(Entity.id == start_id))
    start = result.scalar_one()
    add_node(start)
    
    # Get relationships iteratively
    current_ids = [start_id]
    for depth in range(max_depth):
        rel_result = await db.execute(
            select(EntityRelationship, Entity)
            .join(Entity, or_(
                and_(Entity.id == EntityRelationship.source_id, Entity.id.not_in(current_ids)),
                and_(Entity.id == EntityRelationship.target_id, Entity.id.not_in(current_ids)),
            ))
            .where(
                or_(
                    EntityRelationship.source_id.in_(current_ids),
                    EntityRelationship.target_id.in_(current_ids),
                )
            )
        )
        
        new_ids = []
        for rel, entity in rel_result:
            other_id = rel.target_id if rel.source_id in current_ids else rel.source_id
            if str(other_id) not in nodes:
                add_node(entity)
                new_ids.append(other_id)
            
            edges.append({
                "source": str(rel.source_id),
                "target": str(rel.target_id),
                "type": rel.relationship_type,
                "properties": rel.properties,
            })
        
        if not new_ids:
            break
        current_ids = new_ids
    
    return {"nodes": list(nodes.values()), "edges": edges}


@router.get("/statistics")
async def get_graph_statistics(db: AsyncSession = Depends(get_db)):
    entity_count = await db.execute(select(func.count(Entity.id)))
    
    type_counts = await db.execute(
        select(Entity.type, func.count(Entity.id))
        .group_by(Entity.type)
    )
    
    rel_count = await db.execute(select(func.count(EntityRelationship.id)))
    
    rel_type_counts = await db.execute(
        select(EntityRelationship.relationship_type, func.count(EntityRelationship.id))
        .group_by(EntityRelationship.relationship_type)
    )
    
    return {
        "total_entities": entity_count.scalar(),
        "total_relationships": rel_count.scalar(),
        "entities_by_type": dict(type_counts.all()),
        "relationships_by_type": dict(rel_type_counts.all()),
    }


@router.post("/extract/{document_id}")
async def extract_entities_from_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    extractor = EntityExtractor()
    result = await extractor.extract_from_document(document_id, db)
    return result