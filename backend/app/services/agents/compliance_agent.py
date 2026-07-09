"""
Compliance Intelligence Agent
Analyzes regulatory compliance gaps and generates audit evidence.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import (
    ComplianceCheck, Equipment, Document,
    EquipmentCategory, EquipmentCriticality
)
from app.services.rag.llm_provider import LLMProviderFactory
from app.config import settings


class ComplianceAgent:
    """AI agent for compliance intelligence."""
    
    def __init__(self):
        self.llm = LLMProviderFactory.get_provider()
    
    async def analyze_gaps(
        self,
        regulation: str,
        equipment_ids: Optional[List[UUID]] = None,
        db: AsyncSession = None,
    ) -> Dict[str, Any]:
        """Analyze compliance gaps for a regulation."""
        
        # Build query
        query = select(ComplianceCheck).where(
            ComplianceCheck.regulation.ilike(f"%{regulation}%")
        )
        
        if equipment_ids:
            query = query.where(ComplianceCheck.equipment_id.in_(equipment_ids))
        
        result = await db.execute(query)
        checks = result.scalars().all()
        
        # Get related equipment and documents
        equipment_map = {}
        doc_map = {}
        
        for check in checks:
            if check.equipment_id:
                equip_result = await db.execute(
                    select(Equipment).where(Equipment.id == check.equipment_id)
                )
                equip = equip_result.scalar_one_or_none()
                if equip:
                    equipment_map[str(check.equipment_id)] = equip
            
            if check.evidence_documents:
                for doc_id in check.evidence_documents:
                    doc_result = await db.execute(
                        select(Document).where(Document.id == doc_id)
                    )
                    doc = doc_result.scalar_one_or_none()
                    if doc:
                        doc_map[str(doc_id)] = doc
        
        # Build analysis
        gap_checks = [c for c in checks if c.status in ["gap", "non_compliant", "pending"]]
        compliant_checks = [c for c in checks if c.status == "compliant"]
        
        prompt = f"""Analyze compliance gaps for: {regulation}

Total Checks: {len(checks)}
Compliant: {len(compliant_checks)}
Gaps/Non-compliant: {len(gap_checks)}
Pending: {len([c for c in checks if c.status == 'pending'])}

Gap Details:
{chr(10).join([f"- {c.requirement[:200]} (Equipment: {equipment_map.get(str(c.equipment_id), {}).name if c.equipment_id else 'N/A'})" for c in gap_checks[:10]])}

Compliant Details:
{chr(10).join([f"- {c.requirement[:200]}" for c in compliant_checks[:5]])}

Provide:
1. Priority gaps requiring immediate action
2. Root causes of non-compliance
3. Recommended corrective actions with timelines
4. Required documentation
5. Risk assessment (regulatory, operational, safety)"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are a regulatory compliance expert for Indian industrial regulations (Factories Act, OISD, PESO, IBR, Environmental Act)."},
            {"role": "user", "content": prompt},
        ], temperature=0.1)
        
        return {
            "regulation": regulation,
            "summary": {
                "total_checks": len(checks),
                "compliant": len(compliant_checks),
                "gaps": len(gap_checks),
                "pending": len([c for c in checks if c.status == "pending"]),
            },
            "analysis": response,
            "gap_details": [
                {
                    "id": str(c.id),
                    "requirement": c.requirement,
                    "status": c.status,
                    "equipment": equipment_map.get(str(c.equipment_id), {}).name if c.equipment_id else None,
                    "findings": c.findings,
                    "due_date": c.due_date.isoformat() if c.due_date else None,
                }
                for c in gap_checks
            ],
        }
    
    async def generate_audit_package(
        self,
        regulation: str,
        equipment_ids: Optional[List[UUID]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: AsyncSession = None,
    ) -> Dict[str, Any]:
        """Generate compliance evidence package for audit."""
        
        query = select(ComplianceCheck).where(
            ComplianceCheck.regulation.ilike(f"%{regulation}%")
        )
        
        if equipment_ids:
            query = query.where(ComplianceCheck.equipment_id.in_(equipment_ids))
        if start_date:
            query = query.where(ComplianceCheck.due_date >= start_date)
        if end_date:
            query = query.where(ComplianceCheck.due_date <= end_date)
        
        result = await db.execute(query)
        checks = result.scalars().all()
        
        # Group by equipment
        by_equipment = {}
        for check in checks:
            equip_id = str(check.equipment_id) if check.equipment_id else "general"
            if equip_id not in by_equipment:
                by_equipment[equip_id] = []
            by_equipment[equip_id].append(check)
        
        prompt = f"""Generate audit evidence package structure for {regulation}.

Regulation: {regulation}
Period: {start_date} to {end_date}
Total checks: {len(checks)}
Equipment covered: {len(by_equipment)}

Provide:
1. Executive summary template
2. Evidence matrix (requirement -> documents)
3. Gap register with corrective actions
4. Compliance status dashboard
5. Auditor interview preparation notes
6. Document checklist"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are an audit preparation expert for Indian industrial compliance audits."},
            {"role": "user", "content": prompt},
        ], temperature=0.1)
        
        return {
            "package_structure": response,
            "regulation": regulation,
            "period": {"start": start_date, "end": end_date},
            "checks_included": len(checks),
        }
    
    async def auto_check_procedure(
        self,
        procedure_doc_id: UUID,
        regulation: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Auto-check a procedure document against regulation."""
        
        # Get procedure document
        result = await db.execute(select(Document).where(Document.id == procedure_doc_id))
        procedure = result.scalar_one_or_none()
        
        if not procedure:
            return {"error": "Procedure document not found"}
        
        # Get procedure chunks
        chunks_result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == procedure_doc_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = chunks_result.scalars().all()
        
        procedure_text = "\n\n".join([c.content for c in chunks])
        
        prompt = f"""Check this procedure against {regulation} requirements:

Procedure: {procedure.title}
Document Type: {procedure.type.value}

Procedure Content (excerpt):
{procedure_text[:10000]}

Provide:
1. Requirements covered
2. Requirements missing
3. Ambiguous or weak sections
4. Recommended additions/modifications
5. Compliance score (0-100%)"""
        
        response = await self.llm.chat([
            {"role": "system", "content": f"You are a {regulation} compliance auditor reviewing procedures."},
            {"role": "user", "content": prompt},
        ], temperature=0.1)
        
        return {
            "procedure_id": str(procedure_doc_id),
            "regulation": regulation,
            "analysis": response,
        }
    
    async def track_regulatory_changes(
        self,
        regulation: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Track recent regulatory changes (would need external API in production)."""
        
        # This is a placeholder - in production would integrate with regulatory databases
        prompt = f"""Provide a template for tracking regulatory changes for {regulation}.

Include:
1. Sources to monitor (gazettes, authority websites, industry bodies)
2. Change detection process
3. Impact assessment framework
4. Communication protocol
5. Implementation timeline template"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are a regulatory change management expert."},
            {"role": "user", "content": prompt},
        ], temperature=0.2)
        
        return {
            "regulation": regulation,
            "change_management_framework": response,
        }


compliance_agent = ComplianceAgent()