"""
Maintenance Intelligence Agent
Performs RCA, predictive maintenance, and failure analysis.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.db.models import (
    Equipment, MaintenanceRecord, ProblemSolution,
    EquipmentCategory, EquipmentCriticality, MaintenanceType
)
from app.services.rag.llm_provider import LLMProviderFactory
from app.config import settings


class MaintenanceAgent:
    """AI agent for maintenance intelligence."""
    
    def __init__(self):
        self.llm = LLMProviderFactory.get_provider()
    
    async def predict_maintenance(self, equipment_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Predict next maintenance needs based on history."""
        
        # Get equipment
        result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
        equipment = result.scalar_one_or_none()
        
        if not equipment:
            return {"error": "Equipment not found"}
        
        # Get maintenance history
        maint_result = await db.execute(
            select(MaintenanceRecord)
            .where(
                MaintenanceRecord.equipment_id == equipment_id,
                MaintenanceRecord.completed_at.is_not(None)
            )
            .order_by(MaintenanceRecord.completed_at.desc())
            .limit(20)
        )
        history = maint_result.scalars().all()
        
        # Get known issues
        issues_result = await db.execute(
            select(ProblemSolution)
            .where(
                ProblemSolution.equipment_id == equipment_id,
                ProblemSolution.is_active == True
            )
            .order_by(ProblemSolution.upvotes.desc())
            .limit(10)
        )
        issues = issues_result.scalars().all()
        
        # Build prompt
        history_text = "\n".join([
            f"- {r.completed_at.strftime('%Y-%m-%d')}: {r.maintenance_type} - {r.title} ({r.labor_hours or 0}h, ${r.cost or 0})"
            for r in history
        ])
        
        issues_text = "\n".join([
            f"- {p.problem}: {p.solution[:100]}... (Votes: {p.upvotes - p.downvotes})"
            for p in issues
        ])
        
        prompt = f"""Analyze maintenance history for {equipment.name} ({equipment.tag_number}) and predict next maintenance needs.

Equipment: {equipment.name} ({equipment.category.value})
Criticality: {equipment.criticality.value}
Last maintenance: {equipment.last_maintenance_date}
Next scheduled: {equipment.next_maintenance_date}

Recent History:
{history_text or "No history available"}

Known Issues:
{issues_text or "No issues recorded"}

Operating Parameters: {equipment.operating_parameters}

Provide:
1. Predicted next failure mode (if any)
2. Recommended preventive actions
3. Optimal maintenance window
4. Parts to pre-order
5. Risk level (Low/Medium/High)"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are a predictive maintenance expert for industrial equipment."},
            {"role": "user", "content": prompt},
        ], temperature=0.2)
        
        return {
            "equipment_id": str(equipment_id),
            "equipment_name": equipment.name,
            "prediction": response,
            "generated_at": datetime.utcnow().isoformat(),
            "based_on_records": len(history),
            "known_issues_count": len(issues),
        }
    
    async def perform_rca(self, equipment_id: UUID, problem_description: str, db: AsyncSession) -> Dict[str, Any]:
        """Perform Root Cause Analysis."""
        
        # Get equipment details
        result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
        equipment = result.scalar_one_or_none()
        
        # Get relevant maintenance records
        maint_result = await db.execute(
            select(MaintenanceRecord)
            .where(MaintenanceRecord.equipment_id == equipment_id)
            .order_by(MaintenanceRecord.completed_at.desc())
            .limit(10)
        )
        history = maint_result.scalars().all()
        
        # Get known problems and solutions
        prob_result = await db.execute(
            select(ProblemSolution)
            .where(
                ProblemSolution.equipment_id == equipment_id,
                ProblemSolution.is_active == True
            )
            .order_by(ProblemSolution.upvotes.desc())
            .limit(5)
        )
        problems = prob_result.scalars().all()
        
        # Build RCA prompt
        prompt = f"""Perform Root Cause Analysis for the following problem:

Equipment: {equipment.name if equipment else 'Unknown'} ({equipment.tag_number if equipment else ''})
Category: {equipment.category.value if equipment else 'Unknown'}
Criticality: {equipment.criticality.value if equipment else 'Unknown'}

Problem: {problem_description}

Recent Maintenance History:
{chr(10).join([f"- {r.completed_at.strftime('%Y-%m-%d')}: {r.maintenance_type} - {r.title} - {r.findings or 'N/A'}" for r in history]) or "No history"}

Known Problems & Solutions:
{chr(10).join([f"- {p.problem}: {p.solution[:200]}" for p in problems]) or "None recorded"}

Provide structured RCA:
1. Problem Statement
2. Timeline of Events
3. Possible Causes (rank by likelihood)
4. Most Probable Root Cause
5. Contributing Factors
6. Recommended Corrective Actions
7. Preventive Measures
8. Verification Steps"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are an expert in industrial Root Cause Analysis (RCA) using 5 Whys, Fishbone, and Fault Tree methods."},
            {"role": "user", "content": prompt},
        ], temperature=0.1)
        
        return {
            "equipment_id": str(equipment_id),
            "problem": problem_description,
            "rca": response,
            "performed_at": datetime.utcnow().isoformat(),
            "methodology": "5 Whys + Fault Tree + Historical Pattern Matching",
        }
    
    async def analyze_failure_patterns(
        self,
        category: Optional[EquipmentCategory] = None,
        days: int = 365,
        db: AsyncSession = None,
    ) -> Dict[str, Any]:
        """Analyze failure patterns across equipment."""
        
        # Get maintenance records
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = select(MaintenanceRecord).where(
            MaintenanceRecord.completed_at >= cutoff,
            MaintenanceRecord.maintenance_type == "corrective"
        )
        
        if category:
            query = query.join(Equipment).where(Equipment.category == category)
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        # Analyze patterns
        failure_by_equipment = {}
        for r in records:
            key = str(r.equipment_id)
            if key not in failure_by_equipment:
                failure_by_equipment[key] = {"count": 0, "total_hours": 0, "total_cost": 0}
            failure_by_equipment[key]["count"] += 1
            failure_by_equipment[key]["total_hours"] += r.labor_hours or 0
            failure_by_equipment[key]["total_cost"] += r.cost or 0
        
        # Sort by frequency
        sorted_failures = sorted(
            failure_by_equipment.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        # Generate insights
        prompt = f"""Analyze these failure patterns and provide insights:

Total corrective maintenance events: {len(records)}
Equipment with failures: {len(failure_by_equipment)}
Top failing equipment: {sorted_failures[:5]}

Provide:
1. Common failure modes
2. Seasonal/temporal patterns
3. Equipment categories most affected
4. Recommended preventive program changes
5. Spare parts stocking recommendations"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are a reliability engineer analyzing failure patterns."},
            {"role": "user", "content": prompt},
        ], temperature=0.2)
        
        return {
            "analysis_period_days": days,
            "total_failures": len(records),
            "unique_equipment_failed": len(failure_by_equipment),
            "top_failures": sorted_failures[:10],
            "insights": response,
        }
    
    async def optimize_maintenance_schedule(self, equipment_id: UUID, db: AsyncSession) -> Dict[str, Any]:
        """Optimize preventive maintenance schedule."""
        
        result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
        equipment = result.scalar_one_or_none()
        
        # Get PM history
        pm_result = await db.execute(
            select(MaintenanceRecord)
            .where(
                MaintenanceRecord.equipment_id == equipment_id,
                MaintenanceRecord.maintenance_type == "preventive"
            )
            .order_by(MaintenanceRecord.completed_at.desc())
            .limit(20)
        )
        pm_history = pm_result.scalars().all()
        
        # Get CM history
        cm_result = await db.execute(
            select(MaintenanceRecord)
            .where(
                MaintenanceRecord.equipment_id == equipment_id,
                MaintenanceRecord.maintenance_type == "corrective"
            )
            .order_by(MaintenanceRecord.completed_at.desc())
            .limit(10)
        )
        cm_history = cm_result.scalars().all()
        
        prompt = f"""Optimize preventive maintenance schedule for:

Equipment: {equipment.name if equipment else 'Unknown'} ({equipment.tag_number if equipment else ''})
Criticality: {equipment.criticality.value if equipment else 'Unknown'}
Current PM interval: {equipment.next_maintenance_date}

PM History ({len(pm_history)} records):
{chr(10).join([f"- {r.completed_at.strftime('%Y-%m-%d')}: {r.title} ({r.labor_hours or 0}h)" for r in pm_history])}

CM History ({len(cm_history)} records):
{chr(10).join([f"- {r.completed_at.strftime('%Y-%m-%d')}: {r.title}" for r in cm_history])}

Operating Context: {equipment.operating_parameters if equipment else 'N/A'}

Provide:
1. Recommended PM interval
2. PM task list with frequencies
3. Condition-based monitoring points
4. Spare parts for PM kit
5. Estimated annual PM cost vs CM risk reduction"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are a maintenance optimization expert using RCM (Reliability Centered Maintenance) principles."},
            {"role": "user", "content": prompt},
        ], temperature=0.2)
        
        return {
            "equipment_id": str(equipment_id),
            "optimization": response,
            "current_pm_count": len(pm_history),
            "current_cm_count": len(cm_history),
        }


maintenance_agent = MaintenanceAgent()