from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import (
    Equipment, ComplianceCheck, Document, EquipmentCategory, EquipmentCriticality
)
from app.models.schemas import (
    ComplianceCheckResponse, ComplianceCheckCreate, ComplianceCheckUpdate,
)
from app.services.agents.compliance_agent import ComplianceAgent

router = APIRouter()


@router.get("/checks", response_model=List[ComplianceCheckResponse])
async def list_compliance_checks(
    regulation: Optional[str] = None,
    status: Optional[str] = None,
    equipment_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(ComplianceCheck)
    
    if regulation:
        query = query.where(ComplianceCheck.regulation.ilike(f"%{regulation}%"))
    if status:
        query = query.where(ComplianceCheck.status == status)
    if equipment_id:
        query = query.where(ComplianceCheck.equipment_id == equipment_id)
    if start_date:
        query = query.where(ComplianceCheck.due_date >= start_date)
    if end_date:
        query = query.where(ComplianceCheck.due_date <= end_date)
    
    query = query.order_by(ComplianceCheck.due_date.asc().nullslast()).offset(skip).limit(limit)
    result = await db.execute(query)
    checks = result.scalars().all()
    
    return checks


@router.get("/checks/{check_id}", response_model=ComplianceCheckResponse)
async def get_compliance_check(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ComplianceCheck).where(ComplianceCheck.id == check_id))
    check = result.scalar_one_or_none()
    
    if not check:
        raise HTTPException(status_code=404, detail="Compliance check not found")
    
    return check


@router.post("/checks", response_model=ComplianceCheckResponse, status_code=201)
async def create_compliance_check(
    check: ComplianceCheckCreate,
    db: AsyncSession = Depends(get_db),
):
    db_check = ComplianceCheck(**check.model_dump())
    db.add(db_check)
    await db.commit()
    await db.refresh(db_check)
    
    return db_check


@router.patch("/checks/{check_id}", response_model=ComplianceCheckResponse)
async def update_compliance_check(
    check_id: UUID,
    update: ComplianceCheckUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ComplianceCheck).where(ComplianceCheck.id == check_id))
    check = result.scalar_one_or_none()
    
    if not check:
        raise HTTPException(status_code=404, detail="Compliance check not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(check, field, value)
    
    check.updated_at = datetime.utcnow()
    if update.status == "compliant" and not check.checked_at:
        check.checked_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(check)
    
    return check


@router.get("/regulations")
async def get_regulations(db: AsyncSession = Depends(get_db)):
    # Get unique regulations from checks
    result = await db.execute(
        select(ComplianceCheck.regulation).distinct()
    )
    regulations = result.scalars().all()
    
    # Also return standard Indian industrial regulations
    standard_regulations = [
        "Factories Act, 1948",
        "OISD Standards (Oil Industry Safety Directorate)",
        "PESO Rules (Petroleum and Explosives Safety Organisation)",
        "Environmental Protection Act, 1986",
        "Air (Prevention and Control of Pollution) Act, 1981",
        "Water (Prevention and Control of Pollution) Act, 1974",
        "Hazardous Waste Management Rules, 2016",
        "Indian Boiler Regulations (IBR)",
        "Central Electricity Authority Regulations",
        "Petroleum Act, 1934",
        "Gas Cylinders Rules, 2016",
        "Static and Mobile Pressure Vessels Rules (SMPV)",
    ]
    
    return {
        "custom": regulations,
        "standard": standard_regulations,
    }


@router.get("/equipment/{equipment_id}/checks", response_model=List[ComplianceCheckResponse])
async def get_equipment_compliance(
    equipment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ComplianceCheck)
        .where(ComplianceCheck.equipment_id == equipment_id)
        .order_by(ComplianceCheck.due_date.asc().nullslast())
    )
    checks = result.scalars().all()
    
    return checks


@router.get("/dashboard/summary")
async def get_compliance_dashboard(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(ComplianceCheck.id)))
    
    by_status = await db.execute(
        select(ComplianceCheck.status, func.count(ComplianceCheck.id))
        .group_by(ComplianceCheck.status)
    )
    
    by_regulation = await db.execute(
        select(ComplianceCheck.regulation, func.count(ComplianceCheck.id))
        .group_by(ComplianceCheck.regulation)
    )
    
    # Overdue checks
    overdue = await db.execute(
        select(func.count(ComplianceCheck.id))
        .where(
            ComplianceCheck.due_date < datetime.utcnow(),
            ComplianceCheck.status.in_(["pending", "gap"])
        )
    )
    
    # Due this week
    next_week = datetime.utcnow() + timedelta(days=7)
    due_soon = await db.execute(
        select(func.count(ComplianceCheck.id))
        .where(
            ComplianceCheck.due_date <= next_week,
            ComplianceCheck.due_date >= datetime.utcnow(),
            ComplianceCheck.status.in_(["pending", "gap"])
        )
    )
    
    return {
        "total_checks": total.scalar(),
        "by_status": dict(by_status.all()),
        "by_regulation": dict(by_regulation.all()),
        "overdue": overdue.scalar() or 0,
        "due_this_week": due_soon.scalar() or 0,
    }


@router.post("/audit/evidence-package")
async def generate_evidence_package(
    regulation: str,
    equipment_ids: Optional[List[UUID]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    # Build query for relevant checks and documents
    query = select(ComplianceCheck).where(ComplianceCheck.regulation.ilike(f"%{regulation}%"))
    
    if equipment_ids:
        query = query.where(ComplianceCheck.equipment_id.in_(equipment_ids))
    if start_date:
        query = query.where(ComplianceCheck.due_date >= start_date)
    if end_date:
        query = query.where(ComplianceCheck.due_date <= end_date)
    
    result = await db.execute(query)
    checks = result.scalars().all()
    
    # Gather evidence documents
    doc_ids = set()
    for check in checks:
        if check.evidence_documents:
            doc_ids.update(check.evidence_documents)
        if check.procedure_id:
            doc_ids.add(check.procedure_id)
    
    docs = []
    if doc_ids:
        docs_result = await db.execute(
            select(Document).where(Document.id.in_(doc_ids))
        )
        docs = docs_result.scalars().all()
    
    package = {
        "regulation": regulation,
        "generated_at": datetime.utcnow().isoformat(),
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None,
        },
        "summary": {
            "total_checks": len(checks),
            "compliant": sum(1 for c in checks if c.status == "compliant"),
            "gaps": sum(1 for c in checks if c.status == "gap"),
            "pending": sum(1 for c in checks if c.status == "pending"),
            "non_compliant": sum(1 for c in checks if c.status == "non_compliant"),
        },
        "checks": [
            {
                "id": str(c.id),
                "requirement": c.requirement,
                "status": c.status,
                "findings": c.findings,
                "evidence_documents": c.evidence_documents,
                "corrective_action": c.corrective_action,
                "due_date": c.due_date.isoformat() if c.due_date else None,
                "checked_at": c.checked_at.isoformat() if c.checked_at else None,
                "checked_by": c.checked_by,
            }
            for c in checks
        ],
        "documents": [
            {
                "id": str(d.id),
                "title": d.title,
                "type": d.type,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
    }
    
    return package


@router.post("/agent/check-gaps")
async def run_compliance_gap_analysis(
    regulation: str,
    equipment_ids: Optional[List[UUID]] = None,
    db: AsyncSession = Depends(get_db),
):
    agent = ComplianceAgent()
    result = await agent.analyze_gaps(
        regulation=regulation,
        equipment_ids=equipment_ids,
    )
    return result