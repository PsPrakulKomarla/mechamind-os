from typing import List, Dict, Any, Optional
from uuid import UUID
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition,
    MatchValue, MatchAny, SearchRequest, PayloadSchemaType
)
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings

logger = structlog.get_logger()


class QdrantVectorStore:
    """Qdrant vector database client."""
    
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30,
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._initialized = False
    
    async def initialize(self):
        """Initialize collection if not exists."""
        if self._initialized:
            return
        
        try:
            collections = self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI text-embedding-3-large
                        distance=Distance.COSINE,
                    ),
                )
                # Create payload indexes for filtering
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="metadata.equipment_tags",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            
            self._initialized = True
            
        except Exception as e:
            logger.error("Failed to initialize Qdrant", error=str(e))
            raise
    
    async def upsert_chunk(self, chunk: Dict[str, Any]) -> bool:
        """Upsert a single chunk."""
        await self.initialize()
        
        point = PointStruct(
            id=chunk.get("id") or str(UUID(bytes=hash(chunk["content"].encode())[:16])),
            vector=chunk["embedding"],
            payload=chunk.get("payload", {}),
        )
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
            return True
        except Exception as e:
            logger.error("Failed to upsert chunk", error=str(e))
            return False
    
    async def upsert_batch(self, points: List[Dict[str, Any]]) -> int:
        """Upsert multiple chunks."""
        await self.initialize()
        
        point_structs = [
            PointStruct(
                id=p.get("id") or str(UUID(bytes=hash(p["content"].encode())[:16])),
                vector=p["vector"],
                payload=p.get("payload", {}),
            )
            for p in points
        ]
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=point_structs,
            )
            return len(point_structs)
        except Exception as e:
            logger.error("Failed to upsert batch", error=str(e))
            return 0
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search vectors with optional filtering."""
        await self.initialize()
        
        # Build Qdrant filter
        qdrant_filter = None
        if filter_conditions:
            conditions = []
            for key, value in filter_conditions.items():
                if isinstance(value, list):
                    conditions.append(
                        FieldCondition(key=key, match=MatchAny(any=value))
                    )
                else:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
            if conditions:
                qdrant_filter = Filter(must=conditions)
        
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=qdrant_filter,
                with_payload=True,
                with_vectors=False,
            )
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "payload": r.payload,
                    "vector": r.vector,
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error("Qdrant search failed", error=str(e))
            return []
    
    async def delete_document_chunks(self, document_id: UUID) -> bool:
        """Delete all chunks for a document."""
        await self.initialize()
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id)),
                        )
                    ]
                ),
            )
            return True
        except Exception as e:
            logger.error("Failed to delete document chunks", error=str(e))
            return False
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        await self.initialize()
        
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error("Failed to get collection info", error=str(e))
            return {}
    
    async def scroll_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Scroll through all points (for debugging)."""
        await self.initialize()
        
        try:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            return [
                {"id": str(p.id), "payload": p.payload}
                for p in points
            ]
        except Exception as e:
            logger.error("Failed to scroll", error=str(e))
            return []


# Global instance
qdrant_vector_store = QdrantVectorStore()