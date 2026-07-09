"""
Safety Intelligence Agent
Detects compound risks, analyzes incidents, and manages emergency response.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.db.models import (
    Equipment, ProblemSolution, MaintenanceRecord,
    EquipmentCategory, EquipmentCriticality, EquipmentStatus
)
from app.services.rag.llm_provider import LLMProviderFactory
from app.config import settings


class SafetyAgent:
    """AI agent for safety intelligence."""
    
    def __init__(self):
        self.llm = LLMProviderFactory.get_provider()
    
    async def detect_compound_risks(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Detect compound risk conditions across the plant."""
        
        # Get equipment with risk factors
        result = await db.execute(
            select(Equipment).where(
                Equipment.is_active == True,
                Equipment.status.in_([EquipmentStatus.WARNING, EquipmentStatus.DOWN, EquipmentStatus.MAINTENANCE])
            )
        )
        at_risk_equipment = result.scalars().all()
        
        # Get active maintenance
        maint_result = await db.execute(
            select(MaintenanceRecord)
            .where(MaintenanceRecord.status.in_(["in_progress", "scheduled"]))
        )
        active_maintenance = maint_result.scalars().all()
        
        # Get open safety issues
        safety_issues = await db.execute(
            select(ProblemSolution)
            .where(
                ProblemSolution.is_active == True,
                ProblemSolution.safety_precautions.is_not(None)
            )
        )
        
        # Build risk analysis
        risks = []
        
        # Risk 1: Maintenance on critical equipment during abnormal conditions
        for equip in at_risk_equipment:
            if equip.criticality == EquipmentCriticality.CRITICAL:
                # Check if there's active maintenance
                active_maint = [m for m in active_maintenance if m.equipment_id == equip.id]
                if active_maint:
                    risks.append({
                        "type": "critical_equipment_maintenance",
                        "severity": "high",
                        "equipment_id": str(equip.id),
                        "equipment_name": equip.name,
                        "equipment_tag": equip.tag_number,
                        "description": f"Critical equipment {equip.name} ({equip.tag_number}) is under maintenance while in {equip.status.value} status",
                        "factors": [
                            f"Equipment criticality: {equip.criticality.value}",
                            f"Current status: {equip.status.value}",
                            "Active maintenance in progress",
                        ],
                        "recommended_action": "Review maintenance safety plan. Verify LOTO. Confirm no simultaneous operations in hazardous areas.",
                        "detected_at": datetime.utcnow().isoformat(),
                    })
        
        # Risk 2: Multiple maintenance in same area
        area_maintenance = {}
        for m in active_maintenance:
            equip_result = await db.execute(
                select(Equipment).where(Equipment.id == m.equipment_id)
            )
            equip = equip_result.scalar_one_or_none()
            if equip and equip.area:
                if equip.area not in area_maintenance:
                    area_maintenance[equip.area] = []
                area_maintenance[equip.area].append((equip, m))
        
        for area, items in area_maintenance.items():
            if len(items) > 1:
                risks.append({
                    "type": "simultaneous_operations",
                    "severity": "medium",
                    "area": area,
                    "description": f"Multiple simultaneous maintenance activities in {area}",
                    "equipment": [{"name": e.name, "tag": e.tag_number, "task": m.title} for e, m in items],
                    "recommended_action": "Review SIMOPS (Simultaneous Operations) permit. Verify isolation boundaries. Coordinate with area supervisor.",
                    "detected_at": datetime.utcnow().isoformat(),
                })
        
        # Risk 3: Overdue maintenance on safety-critical equipment
        overdue_result = await db.execute(
            select(MaintenanceRecord, Equipment)
            .join(Equipment, MaintenanceRecord.equipment_id == Equipment.id)
            .where(
                MaintenanceRecord.scheduled_date < datetime.utcnow(),
                MaintenanceRecord.status.in_(["planned", "scheduled"]),
                Equipment.criticality.in_([EquipmentCriticality.CRITICAL, EquipmentCriticality.MAJOR]),
            )
        )
        overdue = overdue_result.all()
        
        for record, equip in overdue:
            days_overdue = (datetime.utcnow() - record.scheduled_date).days
            severity = "high" if days_overdue > 30 else "medium" if days_overdue > 7 else "low"
            risks.append({
                "type": "overdue_safety_maintenance",
                "severity": severity,
                "equipment_id": str(equip.id),
                "equipment_name": equip.name,
                "equipment_tag": equip.tag_number,
                "task": record.title,
                "days_overdue": days_overdue,
                "description": f"Safety-critical maintenance overdue by {days_overdue} days on {equip.name}",
                "recommended_action": "Escalate to maintenance manager. Prioritize scheduling. Assess interim risk controls.",
                "detected_at": datetime.utcnow().isoformat(),
            })
        
        return risks
    
    async def check_permit_conflicts(
        self,
        permit_data: Dict[str, Any],
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """Check permit-to-work for conflicts."""
        
        conflicts = []
        
        permit_type = permit_data.get("type")  # hot_work, confined_space, working_at_height, etc.
        location = permit_data.get("location")
        equipment_tags = permit_data.get("equipment_tags", [])
        start_time = permit_data.get("start_time")
        end_time = permit_data.get("end_time")
        
        # Check 1: Conflicting permits in same area
        # Would query permit database in production
        
        # Check 2: Equipment status conflicts
        for tag in equipment_tags:
            equip_result = await db.execute(
                select(Equipment).where(Equipment.tag_number == tag)
            )
            equip = equip_result.scalar_one_or_none()
            
            if equip:
                if equip.status == EquipmentStatus.DOWN:
                    conflicts.append({
                        "type": "equipment_down",
                        "severity": "high",
                        "message": f"Equipment {equip.name} ({tag}) is DOWN - verify permit validity",
                    })
                elif equip.status == EquipmentStatus.MAINTENANCE:
                    conflicts.append({
                        "type": "equipment_under_maintenance",
                        "severity": "medium",
                        "message": f"Equipment {equip.name} ({tag}) is under maintenance - check SIMOPS",
                    })
                
                # Hot work near hazardous areas
                if permit_type == "hot_work" and equip.category in [
                    EquipmentCategory.VESSEL, EquipmentCategory.PIPING,
                    EquipmentCategory.TANK, EquipmentCategory.REACTOR
                ]:
                    conflicts.append({
                        "type": "hot_work_near_hazardous",
                        "severity": "high",
                        "message": f"Hot work on {equip.category.value} equipment {equip.name} - verify gas-free, fire watch",
                    })
        
        # Check 3: Weather/environmental (placeholder)
        # Would integrate with weather API
        
        return conflicts
    
    async def analyze_incident_patterns(
        self,
        regulation: Optional[str] = None,
        equipment_category: Optional[str] = None,
        db: AsyncSession = None,
    ) -> Dict[str, Any]:
        """Analyze incident patterns for prevention."""
        
        # Get safety-related problems
        query = select(ProblemSolution).where(
            ProblemSolution.is_active == True,
            ProblemSolution.safety_precautions.is_not(None)
        )
        
        if equipment_category:
            query = query.join(Equipment).where(Equipment.category == equipment_category)
        
        result = await db.execute(query)
        safety_problems = result.scalars().all()
        
        # Group by category
        by_category = {}
        for p in safety_problems:
            cat = "unknown"
            equip_result = await db.execute(
                select(Equipment).where(Equipment.id == p.equipment_id)
            )
            equip = equip_result.scalar_one_or_none()
            if equip:
                cat = equip.category.value
            
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(p)
        
        # Generate pattern analysis
        prompt = f"""Analyze these safety incident patterns:

Total safety-related problems: {len(safety_problems)}
Categories affected: {list(by_category.keys())}

Top problems by category:
{chr(10).join([f"{cat}: {len(probs)} problems" for cat, probs in by_category.items()])}

Provide:
1. Recurring incident types
2. Systemic root causes
3. Prevention priorities
4. Leading indicators to monitor
5. Training/competency gaps"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are a process safety expert analyzing incident patterns for prevention."},
            {"role": "user", "content": prompt},
        ], temperature=0.1)
        
        return {
            "total_problems": len(safety_problems),
            "by_category": {cat: len(probs) for cat, probs in by_category.items()},
            "analysis": response,
        }
    
    async def trigger_emergency_response(
        self,
        trigger_type: str,
        location: str,
        equipment_ids: List[UUID],
        details: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Initiate emergency response protocol."""
        
        # Get affected equipment
        equipments = []
        for eid in equipment_ids:
            result = await db.execute(select(Equipment).where(Equipment.id == eid))
            equip = result.scalar_one_or_none()
            if equip:
                equipments.append(equip)
        
        prompt = f"""Generate emergency response plan for:

Trigger: {trigger_type}
Location: {location}
Details: {details}
Affected Equipment: {[f"{e.name} ({e.tag_number})" for e in equipments]}

Provide:
1. Immediate actions (first 5 minutes)
2. Evacuation routes and assembly points
3. Emergency contacts
4. Communication protocol
5. Evidence preservation steps
6. Regulatory notification requirements
7. Post-incident investigation plan"""
        
        response = await self.llm.chat([
            {"role": "system", "content": "You are an emergency response coordinator for industrial facilities."},
            {"role": "user", "content": prompt},
        ], temperature=0.0)
        
        return {
            "incident_id": str(UUID()),
            "trigger_type": trigger_type,
            "location": location,
            "equipment_ids": [str(e) for e in equipment_ids],
            "response_plan": response,
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "active",
        }
    
    async def get_safety_dashboard_data(self, db: AsyncSession) -> Dict[str, Any]:
        """Get safety dashboard statistics."""
        
        # Critical equipment status
        critical_down = await db.execute(
            select(func.count(Equipment.id))
            .where(
                Equipment.criticality == EquipmentCriticality.CRITICAL,
                Equipment.status == EquipmentStatus.DOWN,
            )
        )
        
        # Overdue maintenance on critical
        overdue_critical = await db.execute(
            select(func.count(MaintenanceRecord.id))
            .join(Equipment, MaintenanceRecord.equipment_id == Equipment.id)
            .where(
                Equipment.criticality == EquipmentCriticality.CRITICAL,
                MaintenanceRecord.scheduled_date < datetime.utcnow(),
                MaintenanceRecord.status.in_(["planned", "scheduled"]),
            )
        )
        
        # Open safety issues
        safety_issues = await db.execute(
            select(func.count(ProblemSolution.id))
            .where(
                ProblemSolution.is_active == True,
                ProblemSolution.safety_precautions.is_not(None),
            )
        )
        
        return {
            "critical_equipment_down": critical_down.scalar() or 0,
            "overdue_critical_maintenance": overdue_critical.scalar() or 0,
            "open_safety_issues": safety_issues.scalar() or 0,
            "timestamp": datetime.utcnow().isoformat(),
        }


safety_agent = SafetyAgent()