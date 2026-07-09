"""
Knowledge Graph Entity Extractor
Extracts entities and relationships from documents using NLP and LLMs.
"""

import re
import json
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Document, DocumentChunk, Entity, EntityRelationship
from app.services.rag.llm_provider import LLMProviderFactory
from app.config import settings

# Industrial equipment patterns
EQUIPMENT_PATTERNS = [
    r'\b([A-Z]{1,3}-\d{3,4}[A-Z]?)\b',  # P-101, B-202, TG-301
    r'\b(Pump|Compressor|Turbine|Boiler|Heat Exchanger|Fan|Blower|Motor|Generator|Transformer|Valve|Vessel|Tank|Reactor)\s+[A-Z]?\d{3,4}\b',
    r'\b(P-\d{3,4}|B-\d{3,4}|TG-\d{3,4}|C-\d{3,4}|HE-\d{3,4}|V-\d{3,4}|TK-\d{3,4}|R-\d{3,4}|MOV-\d{3,4}|CV-\d{3,4})\b',
]

PARAMETER_PATTERNS = [
    r'(\d+(?:\.\d+)?)\s*(bar|barg|bara|psi|kPa|MPa|°C|deg\s*C|Celsius|Fahrenheit|K|RPM|Hz|kW|MW|HP|m3/h|t/h|kg/s|ppm|%|volts?|amps?|A\b)',
    r'(pressure|temperature|flow|level|vibration|speed|power|current|voltage|frequency)\s*:?\s*(\d+(?:\.\d+)?)\s*(\w+)',
]

REGULATION_PATTERNS = [
    r'\b(IBR|OISD|PESO|API|ASME|ASTM|ISO|IEC|IEEE|NFPA|OSHA|DGMS|Factory Act|Environmental Protection Act|Air Act|Water Act|Hazardous Waste Rules)\b',
    r'\b(Section|Clause|Rule|Regulation|Standard)\s+\d+[A-Z]?\b',
]

PERSONNEL_PATTERNS = [
    r'\b(Operator|Engineer|Supervisor|Manager|Technician|Inspector|Auditor)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
    r'\b(Mr\.|Ms\.|Dr\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
]


class EntityExtractor:
    """Extracts entities and relationships from documents."""
    
    def __init__(self):
        self.llm = LLMProviderFactory.get_provider()
        self.equipment_regex = [re.compile(p, re.IGNORECASE) for p in EQUIPMENT_PATTERNS]
        self.parameter_regex = [re.compile(p, re.IGNORECASE) for p in PARAMETER_PATTERNS]
        self.regulation_regex = [re.compile(p, re.IGNORECASE) for r in REGULATION_PATTERNS for p in [r]]
        self.personnel_regex = [re.compile(p, re.IGNORECASE) for p in PERSONNEL_PATTERNS]
    
    async def extract_from_document(self, document_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Extract entities from a document's chunks."""
        
        # Get document chunks
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .limit(50)  # Limit for LLM context
        )
        chunks = result.scalars().all()
        
        if not chunks:
            return {"entities": [], "relationships": []}
        
        # Combine chunk texts
        full_text = "\n\n".join([
            f"[Chunk {c.chunk_index}] {c.content[:2000]}"
            for c in chunks
        ])
        
        # Extract using regex first (fast)
        regex_entities = self._extract_regex(full_text)
        
        # Extract using LLM (comprehensive)
        llm_entities = await self._extract_llm(full_text[:15000])
        
        # Merge and deduplicate
        all_entities = self._merge_entities(regex_entities, llm_entities)
        
        # Extract relationships
        relationships = await self._extract_relationships(full_text[:15000], all_entities)
        
        # Save to database
        saved_entities = await self._save_entities(document_id, all_entities, db)
        saved_relationships = await self._save_relationships(document_id, relationships, db)
        
        return {
            "entities": saved_entities,
            "relationships": saved_relationships,
        }
    
    def _extract_regex(self, text: str) -> List[Dict[str, Any]]:
        """Fast regex-based extraction."""
        entities = []
        
        # Equipment tags
        for regex in self.equipment_regex:
            for match in regex.finditer(text):
                entities.append({
                    "name": match.group(1) if match.groups() else match.group(0),
                    "type": "equipment",
                    "source": "regex",
                    "confidence": 0.8,
                    "context": text[max(0, match.start()-50):match.end()+50],
                })
        
        # Parameters
        for regex in self.parameter_regex:
            for match in regex.finditer(text):
                entities.append({
                    "name": match.group(0),
                    "type": "parameter",
                    "source": "regex",
                    "confidence": 0.7,
                    "context": text[max(0, match.start()-50):match.end()+50],
                })
        
        # Regulations
        for regex in self.regulation_regex:
            for match in regex.finditer(text):
                entities.append({
                    "name": match.group(0),
                    "type": "regulation",
                    "source": "regex",
                    "confidence": 0.9,
                    "context": text[max(0, match.start()-50):match.end()+50],
                })
        
        # Personnel
        for regex in self.personnel_regex:
            for match in regex.finditer(text):
                entities.append({
                    "name": match.group(0),
                    "type": "personnel",
                    "source": "regex",
                    "confidence": 0.7,
                    "context": text[max(0, match.start()-50):match.end()+50],
                })
        
        return entities
    
    async def _extract_llm(self, text: str) -> List[Dict[str, Any]]:
        """LLM-based entity extraction."""
        
        prompt = f"""Extract industrial entities from this text. Return JSON array of entities.

Entity types: equipment, procedure, parameter, regulation, personnel, location, material, chemical

For each entity, provide:
- name: exact name/tag from text
- type: one of the types above
- properties: relevant attributes (e.g., for equipment: tag, location, capacity; for parameter: value, unit; for regulation: section, standard)
- confidence: 0.0-1.0

Text:
{text}

Return only valid JSON array."""
        
        try:
            response = await self.llm.chat([
                {"role": "system", "content": "You are an industrial NLP expert. Extract entities precisely."},
                {"role": "user", "content": prompt},
            ], temperature=0.1)
            
            # Parse JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                entities = json.loads(response[json_start:json_end])
                for e in entities:
                    e["source"] = "llm"
                return entities
        except Exception as e:
            print(f"LLM extraction failed: {e}")
        
        return []
    
    def _merge_entities(self, regex_entities: List, llm_entities: List) -> List:
        """Merge and deduplicate entities."""
        merged = {}
        
        for e in regex_entities + llm_entities:
            key = (e["name"].lower(), e["type"])
            if key not in merged or e["confidence"] > merged[key]["confidence"]:
                merged[key] = e
        
        return list(merged.values())
    
    async def _extract_relationships(
        self,
        text: str,
        entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract relationships between entities."""
        
        entity_names = [e["name"] for e in entities]
        
        prompt = f"""Given these entities found in the text, identify relationships between them.

Entities: {', '.join(entity_names[:30])}

Relationship types:
- located_in (equipment -> location)
- connected_to (equipment -> equipment)
- has_parameter (equipment -> parameter)
- maintained_by (equipment -> personnel)
- inspected_on (equipment -> date)
- references (procedure -> equipment)
- requires (procedure -> parameter)
- regulates (regulation -> equipment/procedure)
- specified_in (parameter -> document)

Return JSON array of: {{"source": "entity_name", "target": "entity_name", "type": "relationship_type", "confidence": 0.0-1.0, "context": "snippet"}}

Text:
{text[:8000]}"""
        
        try:
            response = await self.llm.chat([
                {"role": "system", "content": "Extract relationships between industrial entities. Return only JSON array."},
                {"role": "user", "content": prompt},
            ], temperature=0.1)
            
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except Exception as e:
            print(f"Relationship extraction failed: {e}")
        
        return []
    
    async def _save_entities(
        self,
        document_id: UUID,
        entities: List[Dict[str, Any]],
        db: AsyncSession,
    ) -> List[Entity]:
        """Save entities to database."""
        saved = []
        
        for e in entities:
            # Check if entity exists
            result = await db.execute(
                select(Entity).where(Entity.name == e["name"], Entity.type == e["type"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update
                existing.properties = e.get("properties", {})
                existing.confidence = max(existing.confidence, e.get("confidence", 1.0))
                existing.updated_at = datetime.utcnow()
                saved.append(existing)
            else:
                # Create new
                entity = Entity(
                    name=e["name"],
                    type=e["type"],
                    properties=e.get("properties", {}),
                    description=e.get("context", "")[:500],
                    source_document_id=document_id,
                    confidence=e.get("confidence", 1.0),
                )
                db.add(entity)
                saved.append(entity)
        
        await db.commit()
        return saved
    
    async def _save_relationships(
        self,
        document_id: UUID,
        relationships: List[Dict[str, Any]],
        db: AsyncSession,
    ) -> List[EntityRelationship]:
        """Save relationships to database."""
        saved = []
        
        # Build entity name to ID map
        result = await db.execute(select(Entity.id, Entity.name))
        entity_map = {name: id for id, name in result}
        
        for rel in relationships:
            source_id = entity_map.get(rel["source"])
            target_id = entity_map.get(rel["target"])
            
            if not source_id or not target_id:
                continue
            
            # Check if relationship exists
            result = await db.execute(
                select(EntityRelationship).where(
                    EntityRelationship.source_id == source_id,
                    EntityRelationship.target_id == target_id,
                    EntityRelationship.relationship_type == rel["type"],
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                relationship = EntityRelationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=rel["type"],
                    properties={"context": rel.get("context", "")},
                    confidence=rel.get("confidence", 0.8),
                    source="extracted",
                )
                db.add(relationship)
                saved.append(relationship)
        
        await db.commit()
        return saved


# Global instance
entity_extractor = EntityExtractor()