from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
import structlog

from app.services.rag.llm_provider import LLMProviderFactory, EmbeddingService
from app.services.vector_store.qdrant_client import QdrantVectorStore
from app.config import settings

logger = structlog.get_logger()


class HybridRetriever:
    """Hybrid retriever combining semantic and keyword search."""
    
    def __init__(self):
        self.vector_store = QdrantVectorStore()
        self.embedding_service = EmbeddingService()
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        search_type: str = "hybrid",
        alpha: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search."""
        
        if search_type == "semantic":
            return await self._semantic_search(query, top_k, threshold, filters)
        elif search_type == "keyword":
            return await self._keyword_search(query, top_k, filters)
        else:
            return await self._hybrid_search(query, top_k, threshold, filters, alpha)
    
    async def _semantic_search(
        self,
        query: str,
        top_k: int,
        threshold: float,
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        query_embedding = await self.embedding_service.get_embedding(query)
        
        results = await self.vector_store.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=threshold,
            filter_conditions=filters,
        )
        
        return results
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        # Keyword search would use PostgreSQL full-text search
        # For now, delegate to vector store with payload filtering
        return await self.vector_store.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=[0.0] * 1536,  # Dummy vector
            limit=top_k,
            filter_conditions=filters,
        )
    
    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        threshold: float,
        filters: Optional[Dict[str, Any]],
        alpha: float,
    ) -> List[Dict[str, Any]]:
        # Get semantic results
        semantic_results = await self._semantic_search(query, top_k * 2, threshold * 0.8, filters)
        
        # For hybrid, we'd combine with keyword results
        # For now, return semantic results with score adjustment
        for r in semantic_results:
            r["search_type"] = "semantic"
        
        return semantic_results[:top_k]
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return await self._semantic_search(query, top_k, threshold, filters)
    
    async def keyword_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return await self._keyword_search(query, top_k, filters)


class RAGChain:
    """Main RAG chain for question answering."""
    
    def __init__(self):
        self.retriever = HybridRetriever()
        self.llm = LLMProviderFactory.get_provider()
    
    async def query(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        equipment_id: Optional[UUID] = None,
        top_k: int = 10,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Execute RAG query."""
        
        # Build filters
        filters = {}
        if equipment_id:
            filters["equipment_tags"] = [str(equipment_id)]
        if context:
            filters.update(context.get("filters", {}))
        
        # Retrieve relevant chunks
        chunks = await self.retriever.search(
            query=question,
            top_k=top_k,
            threshold=settings.SIMILARITY_THRESHOLD,
            filters=filters,
            search_type="hybrid",
        )
        
        # Build context from chunks
        context_text = self._build_context(chunks)
        
        # Generate answer
        answer = await self._generate_answer(question, context_text, temperature)
        
        # Prepare citations
        citations = self._prepare_citations(chunks)
        
        return {
            "answer": answer,
            "chunks": chunks,
            "citations": citations,
            "context_used": context_text,
        }
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks):
            source = chunk.get("payload", {}).get("source", "Unknown")
            content = chunk.get("payload", {}).get("content", "")
            context_parts.append(f"[Source {i+1}: {source}]\n{content}")
        return "\n\n---\n\n".join(context_parts)
    
    def _prepare_citations(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare citation metadata."""
        citations = []
        for chunk in chunks:
            payload = chunk.get("payload", {})
            citations.append({
                "document_id": payload.get("document_id"),
                "chunk_id": payload.get("chunk_id"),
                "excerpt": payload.get("content", "")[:200],
                "score": chunk.get("score", 0),
                "source": payload.get("source"),
                "page_number": payload.get("metadata", {}).get("page_number"),
            })
        return citations
    
    async def _generate_answer(
        self,
        question: str,
        context: str,
        temperature: float,
    ) -> str:
        """Generate answer using LLM."""
        
        system_prompt = """You are an expert industrial knowledge assistant for Mechamind OS.
You help engineers, operators, and maintenance personnel with questions about equipment, procedures, and operations.

Guidelines:
- Be precise and technical
- Always cite sources when using context
- If context doesn't contain enough information, say so clearly
- Prioritize safety in all responses
- Reference equipment tags, procedures, and standards when relevant
- Provide actionable guidance"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
        
        return await self.llm.chat(messages, temperature)


# Global instances
hybrid_retriever = HybridRetriever()
rag_chain = RAGChain()