from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import (
    Equipment, MaintenanceRecord, MaintenanceType, 
    ProblemSolution, EquipmentCategory, EquipmentCriticality
)
from app.models.schemas import (
    MaintenanceRecordCreate, MaintenanceRecordUpdate, MaintenanceRecordResponse,
)
from app.services.agents.maintenance_agent import MaintenanceAgent

router = APIRouter()


@router.get("/records", response_model=List[MaintenanceRecordResponse])
async def list_maintenance_records(
    equipment_id: Optional[UUID] = None,
    maintenance_type: Optional[MaintenanceType] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(MaintenanceRecord)
    
    if equipment_id:
        query = query.where(MaintenanceRecord.equipment_id == equipment_id)
    if maintenance_type:
        query = query.where(MaintenanceRecord.maintenance_type == maintenance_type)
    if status:
        query = query.where(MaintenanceRecord.status == status)
    if start_date:
        query = query.where(MaintenanceRecord.scheduled_date >= start_date)
    if end_date:
        query = query.where(MaintenanceRecord.scheduled_date <= end_date)
    
    query = query.order_by(MaintenanceRecord.scheduled_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()
    
    return records


@router.post("/records", response_model=MaintenanceRecordResponse, status_code=201)
async def create_maintenance_record(
    record: MaintenanceRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify equipment
    equip_result = await db.execute(select(Equipment).where(Equipment.id == record.equipment_id))
    if not equip_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db_record = MaintenanceRecord(**record.model_dump())
    db.add(db_record)
    
    # Update equipment dates
    equip = equip_result.scalar_one()
    if record.completed_at:
        equip.last_maintenance_date = record.completed_at
    if record.scheduled_date:
        equip.next_maintenance_date = record.scheduled_date
    
    await db.commit()
    await db.refresh(db_record)
    
    return db_record


@router.get("/records/{record_id}", response_model=MaintenanceRecordResponse)
async def get_maintenance_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    return record


@router.patch("/records/{record_id}", response_model=MaintenanceRecordResponse)
async def update_maintenance_record(
    record_id: UUID,
    update: MaintenanceRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    
    record.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(record)
    
    return record


@router.get("/schedule/upcoming")
async def get_upcoming_maintenance(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    end_date = datetime.utcnow() + timedelta(days=days)
    
    result = await db.execute(
        select(MaintenanceRecord, Equipment.name, Equipment.tag_number)
        .join(Equipment, MaintenanceRecord.equipment_id == Equipment.id)
        .where(
            MaintenanceRecord.scheduled_date <= end_date,
            MaintenanceRecord.scheduled_date >= datetime.utcnow(),
            MaintenanceRecord.status.in_(["planned", "scheduled", "in_progress"]),
        )
        .order_by(MaintenanceRecord.scheduled_date)
    )
    
    return [
        {
            "record_id": r.id,
            "equipment_name": name,
            "equipment_tag": tag,
            "title": r.title,
            "type": r.maintenance_type,
            "scheduled_date": r.scheduled_date,
            "priority": r.priority,
            "status": r.status,
        }
        for r, name, tag in result
    ]


@router.get("/schedule/overdue")
async def get_overdue_maintenance(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MaintenanceRecord, Equipment.name, Equipment.tag_number)
        .join(Equipment, MaintenanceRecord.equipment_id == Equipment.id)
        .where(
            MaintenanceRecord.scheduled_date < datetime.utcnow(),
            MaintenanceRecord.status.in_(["planned", "scheduled", "in_progress"]),
        )
        .order_by(MaintenanceRecord.scheduled_date)
    )
    
    return [
        {
            "record_id": r.id,
            "equipment_name": name,
            "equipment_tag": tag,
            "title": r.title,
            "type": r.maintenance_type,
            "scheduled_date": r.scheduled_date,
            "days_overdue": (datetime.utcnow() - r.scheduled_date).days,
            "priority": r.priority,
            "status": r.status,
        }
        for r, name, tag in result
    ]


@router.post("/predict/{equipment_id}")
async def predict_maintenance(
    equipment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    agent = MaintenanceAgent()
    prediction = await agent.predict_maintenance(equipment_id, db)
    return prediction


@router.get("/analytics/failure-patterns")
async def get_failure_patterns(
    equipment_category: Optional[EquipmentCategory] = None,
    days: int = Query(365, ge=30, le=1095),
    db: AsyncSession = Depends(get_db),
):
    # Analyze maintenance records for failure patterns
    from datetime import datetime
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(
            Equipment.category,
            MaintenanceRecord.maintenance_type,
            func.count(MaintenanceRecord.id).label("count"),
            func.avg(MaintenanceRecord.labor_hours).label("avg_hours"),
            func.avg(MaintenanceRecord.cost).label("avg_cost"),
        )
        .join(Equipment, MaintenanceRecord.equipment_id == Equipment.id)
        .where(MaintenanceRecord.completed_at >= cutoff)
        .group_by(Equipment.category, MaintenanceRecord.maintenance_type)
    )
    
    if equipment_category:
        query = query.where(Equipment.category == equipment_category)
    
    result = await db.execute(query)
    
    return [
        {
            "category": cat,
            "maintenance_type": mtype,
            "count": count,
            "avg_labor_hours": float(avg_hours) if avg_hours else 0,
            "avg_cost": float(avg_cost) if avg_cost else 0,
        }
        for cat, mtype, count, avg_hours, avg_cost in result
    ]


@router.get("/analytics/mtbf/{equipment_id}")
async def get_mtbf(
    equipment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # Mean Time Between Failures
    result = await db.execute(
        select(MaintenanceRecord)
        .where(
            MaintenanceRecord.equipment_id == equipment_id,
            MaintenanceRecord.maintenance_type == "corrective",
            MaintenanceRecord.completed_at.is_not(None),
        )
        .order_by(MaintenanceRecord.completed_at)
    )
    records = result.scalars().all()
    
    if len(records) < 2:
        return {"mtbf_hours": None, "failure_count": len(records), "message": "Insufficient data"}
    
    intervals = []
    for i in range(1, len(records)):
        delta = records[i].completed_at - records[i-1].completed_at
        intervals.append(delta.total_seconds() / 3600)
    
    mtbf = sum(intervals) / len(intervals) if intervals else 0
    
    return {
        "mtbf_hours": round(mtbf, 2),
        "failure_count": len(records),
        "intervals_hours": intervals,
        "last_failure": records[-1].completed_at if records else None,
    }


@router.post("/rca")
async def run_rca(
    equipment_id: UUID,
    problem_description: str,
    db: AsyncSession = Depends(get_db),
):
    agent = MaintenanceAgent()
    rca = await agent.perform_rca(equipment_id, problem_description, db)
    return rca