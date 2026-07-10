from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.db.database import get_db
from app.db.models import (
    Equipment, Document, EquipmentCategory
)
from app.models.schemas import (
    SafetyZoneResponse, PermitResponse, IncidentResponse,
)
from app.services.agents.safety_agent import SafetyAgent

router = APIRouter()


# Phase 2: Safety Intelligence endpoints


@router.get("/zones", response_model=List[SafetyZoneResponse])
async def get_safety_zones(
    area: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    # Get equipment with safety zones
    query = select(Equipment).where(
        Equipment.is_active == True,
        Equipment.coordinates.is_not(None)
    )
    
    if area:
        query = query.where(Equipment.area == area)
    
    result = await db.execute(query)
    equipment = result.scalars().all()
    
    zones = []
    for eq in equipment:
        if eq.coordinates:
            zones.append({
                "equipment_id": str(eq.id),
                "equipment_name": eq.name,
                "equipment_tag": eq.tag_number,
                "category": eq.category,
                "location": eq.coordinates,
                "area": eq.area,
                "hazard_classification": eq.meta.get("hazard_classification") if eq.meta else None,
                "risk_level": eq.status,  # Use status as proxy
            })
    
    return zones


@router.get("/heatmap")
async def get_risk_heatmap(
    area: Optional[str] = None,
    time_range: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
):
    # Return risk heatmap data for frontend visualization
    # This would integrate with sensor data in Phase 2
    return {
        "areas": [],
        "timestamp": datetime.utcnow().isoformat(),
        "time_range": time_range,
    }


@router.get("/permits", response_model=List[PermitResponse])
async def get_active_permits(
    area: Optional[str] = None,
    permit_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    # This would integrate with permit-to-work system
    # For now, return mock data structure
    return []


@router.post("/permits/check-conflicts")
async def check_permit_conflicts(
    permit_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    agent = SafetyAgent()
    result = await agent.check_permit_conflicts(permit_data)
    return result


@router.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    severity: Optional[str] = None,
    equipment_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    # This would query incident database
    return []


@router.get("/incidents/patterns")
async def get_incident_patterns(
    regulation: Optional[str] = None,
    equipment_category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    agent = SafetyAgent()
    patterns = await agent.analyze_incident_patterns(
        regulation=regulation,
        equipment_category=equipment_category,
    )
    return patterns


@router.post("/emergency/trigger")
async def trigger_emergency_response(
    trigger_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    agent = SafetyAgent()
    result = await agent.trigger_emergency_response(trigger_data)
    return result


@router.get("/sensors/status")
async def get_sensor_status(
    area: Optional[str] = None,
    sensor_type: Optional[str] = None,  # gas, pressure, temperature, vibration
    db: AsyncSession = Depends(get_db),
):
    # This would integrate with SCADA/IoT in Phase 2
    return {
        "sensors": [],
        "last_updated": datetime.utcnow().isoformat(),
    }


@router.get("/sensors/{sensor_id}/readings")
async def get_sensor_readings(
    sensor_id: str,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    # Return time-series data for a sensor
    return {
        "sensor_id": sensor_id,
        "readings": [],
        "period_hours": hours,
    }