from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.db.database import get_db
from app.db.models import (
    Equipment, EquipmentIssue, ProblemSolution, MaintenanceRecord,
    EquipmentCategory, EquipmentCriticality, EquipmentStatus,
    ProblemSource, SolutionSource
)
from app.models.schemas import (
    EquipmentCreate, EquipmentUpdate, EquipmentResponse, EquipmentListResponse,
    EquipmentIssueCreate, EquipmentIssueResponse,
    ProblemSolutionCreate, ProblemSolutionUpdate, ProblemSolutionResponse,
    ProblemSolutionWithEquipment, ProblemSolutionVote,
    MaintenanceRecordCreate, MaintenanceRecordUpdate, MaintenanceRecordResponse,
    EquipmentCategory as SchemaEquipmentCategory,
    EquipmentCriticality as SchemaEquipmentCriticality,
    EquipmentStatus as SchemaEquipmentStatus,
)

router = APIRouter()


# Equipment CRUD
@router.post("/", response_model=EquipmentResponse)
async def create_equipment(
    equipment: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check tag uniqueness
    if equipment.tag_number:
        existing = await db.execute(
            select(Equipment).where(Equipment.tag_number == equipment.tag_number)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Tag number already exists")
    
    db_equipment = Equipment(**equipment.model_dump())
    db.add(db_equipment)
    await db.commit()
    await db.refresh(db_equipment)
    
    return db_equipment


@router.get("/", response_model=EquipmentListResponse)
async def list_equipment(
    category: Optional[SchemaEquipmentCategory] = None,
    criticality: Optional[SchemaEquipmentCriticality] = None,
    status: Optional[SchemaEquipmentStatus] = None,
    area: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Equipment).where(Equipment.is_active == True)
    
    if category:
        query = query.where(Equipment.category == category)
    if criticality:
        query = query.where(Equipment.criticality == criticality)
    if status:
        query = query.where(Equipment.status == status)
    if area:
        query = query.where(Equipment.area.ilike(f"%{area}%"))
    if search:
        query = query.where(
            or_(
                Equipment.name.ilike(f"%{search}%"),
                Equipment.tag_number.ilike(f"%{search}%"),
                Equipment.description.ilike(f"%{search}%"),
            )
        )
    
    total_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_query)).scalar()
    
    query = query.order_by(Equipment.criticality.desc(), Equipment.name).offset(skip).limit(limit)
    result = await db.execute(query)
    equipment = result.scalars().all()
    
    return EquipmentListResponse(
        equipment=equipment,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/categories", response_model=List[str])
async def get_categories():
    return [c.value for c in EquipmentCategory]


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: UUID,
    include_issues: bool = True,
    include_maintenance: bool = False,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    if include_issues:
        issues_result = await db.execute(
            select(EquipmentIssue)
            .where(EquipmentIssue.equipment_id == equipment_id)
            .order_by(EquipmentIssue.severity.desc())
        )
        equipment.common_issues = issues_result.scalars().all()
    
    if include_maintenance:
        maint_result = await db.execute(
            select(MaintenanceRecord)
            .where(MaintenanceRecord.equipment_id == equipment_id)
            .order_by(MaintenanceRecord.scheduled_date.desc())
            .limit(10)
        )
        equipment.maintenance_records = maint_result.scalars().all()
    
    return equipment


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: UUID,
    update: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(equipment, field, value)
    
    equipment.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(equipment)
    
    return equipment


@router.delete("/{equipment_id}")
async def delete_equipment(
    equipment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    equipment.is_active = False
    await db.commit()
    
    return {"message": "Equipment deactivated"}


# Equipment Issues (Pre-seeded known problems)
@router.get("/{equipment_id}/issues", response_model=List[EquipmentIssueResponse])
async def get_equipment_issues(
    equipment_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(EquipmentIssue).where(EquipmentIssue.equipment_id == equipment_id)
    
    if active_only:
        query = query.where(EquipmentIssue.is_active == True)
    
    query = query.order_by(EquipmentIssue.severity.desc())
    result = await db.execute(query)
    issues = result.scalars().all()
    
    return issues


@router.post("/{equipment_id}/issues", response_model=EquipmentIssueResponse)
async def create_equipment_issue(
    equipment_id: UUID,
    issue: EquipmentIssueCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify equipment exists
    equip_result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    if not equip_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db_issue = EquipmentIssue(
        equipment_id=equipment_id,
        **issue.model_dump()
    )
    db.add(db_issue)
    await db.commit()
    await db.refresh(db_issue)
    
    return db_issue


# Problem Solutions (Crowdsourced knowledge base)
@router.get("/{equipment_id}/solutions", response_model=List[ProblemSolutionResponse])
async def get_equipment_solutions(
    equipment_id: UUID,
    problem: Optional[str] = None,
    active_only: bool = True,
    sort_by: str = Query("votes", pattern="^(votes|recent|confidence)$"),
    db: AsyncSession = Depends(get_db),
):
    query = select(ProblemSolution).where(
        ProblemSolution.equipment_id == equipment_id
    )
    
    if active_only:
        query = query.where(ProblemSolution.is_active == True)
    
    if problem:
        query = query.where(ProblemSolution.problem.ilike(f"%{problem}%"))
    
    if sort_by == "votes":
        query = query.order_by(
            (ProblemSolution.upvotes - ProblemSolution.downvotes).desc(),
            ProblemSolution.confidence_score.desc().nullsl_score.desc().nullslast()
        )
    elif sort_by == "recent":
        query = query.order_by(ProblemSolution.created_at.desc())
    elif sort_by == "confidence":
        query = query.order_by(ProblemSolution.confidence_score.desc().nullslast())
    
    result = await db.execute(query)
    solutions = result.scalars().all()
    
    return solutions


@router.post("/{equipment_id}/solutions", response_model=ProblemSolutionResponse)
async def create_solution(
    equipment_id: UUID,
    solution: ProblemSolutionCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify equipment exists
    equip_result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    if not equip_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db_solution = ProblemSolution(
        equipment_id=equipment_id,
        **solution.model_dump()
    )
    db.add(db_solution)
    await db.commit()
    await db.refresh(db_solution)
    
    return db_solution


@router.post("/solutions/{solution_id}/vote")
async def vote_solution(
    solution_id: UUID,
    vote: ProblemSolutionVote,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProblemSolution).where(ProblemSolution.id == solution_id))
    solution = result.scalar_one_or_none()
    
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")
    
    if vote.vote == "upvote":
        solution.upvotes += 1
    elif vote.vote == "downvote":
        solution.downvotes += 1
    else:
        raise HTTPException(status_code=400, detail="Invalid vote type")
    
    await db.commit()
    
    return {
        "upvotes": solution.upvotes,
        "downvotes": solution.downvotes,
        "score": solution.upvotes - solution.downvotes,
    }


@router.post("/solutions/{solution_id}/verify")
async def verify_solution(
    solution_id: UUID,
    verified_by: UUID,  # From auth
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProblemSolution).where(ProblemSolution.id == solution_id))
    solution = result.scalar_one_or_none()
    
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")
    
    solution.is_verified = True
    solution.verified_by = verified_by
    solution.verified_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Solution verified", "solution_id": solution_id}


@router.post("/solutions/{solution_id}/replace")
async def replace_solution(
    solution_id: UUID,
    new_solution: ProblemSolutionCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProblemSolution).where(ProblemSolution.id == solution_id))
    old_solution = result.scalar_one_or_none()
    
    if not old_solution:
        raise HTTPException(status_code=404, detail="Solution not found")
    
    # Create new solution
    db_new = ProblemSolution(
        equipment_id=old_solution.equipment_id,
        **new_solution.model_dump(),
        parent_problem_id=old_solution.id,
    )
    db.add(db_new)
    
    # Mark old as replaced
    old_solution.is_active = False
    old_solution.replaced_by_id = db_new.id
    
    await db.commit()
    await db.refresh(db_new)
    
    return db_new


# Maintenance Records
@router.get("/{equipment_id}/maintenance", response_model=List[MaintenanceRecordResponse])
async def get_maintenance_records(
    equipment_id: UUID,
    maintenance_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(MaintenanceRecord).where(MaintenanceRecord.equipment_id == equipment_id)
    
    if maintenance_type:
        query = query.where(MaintenanceRecord.maintenance_type == maintenance_type)
    if status:
        query = query.where(MaintenanceRecord.status == status)
    
    query = query.order_by(MaintenanceRecord.scheduled_date.desc()).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()
    
    return records


@router.post("/{equipment_id}/maintenance", response_model=MaintenanceRecordResponse)
async def create_maintenance_record(
    equipment_id: UUID,
    record: MaintenanceRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify equipment exists
    equip_result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    if not equip_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db_record = MaintenanceRecord(
        equipment_id=equipment_id,
        **record.model_dump()
    )
    db.add(db_record)
    
    # Update equipment last/next maintenance dates
    equip = equip_result.scalar_one()
    if record.completed_at:
        equip.last_maintenance_date = record.completed_at
    if record.scheduled_date:
        equip.next_maintenance_date = record.scheduled_date
    
    await db.commit()
    await db.refresh(db_record)
    
    return db_record


@router.get("/dashboard/summary")
async def get_equipment_dashboard(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(Equipment.id)).where(Equipment.is_active == True))
    
    by_status = await db.execute(
        select(Equipment.status, func.count(Equipment.id))
        .where(Equipment.is_active == True)
        .group_by(Equipment.status)
    )
    
    by_criticality = await db.execute(
        select(Equipment.criticality, func.count(Equipment.id))
        .where(Equipment.is_active == True)
        .group_by(Equipment.criticality)
    )
    
    by_category = await db.execute(
        select(Equipment.category, func.count(Equipment.id))
        .where(Equipment.is_active == True)
        .group_by(Equipment.category)
    )
    
    # Equipment needing maintenance
    from datetime import datetime, timedelta
    overdue = await db.execute(
        select(func.count(Equipment.id))
        .where(
            Equipment.is_active == True,
            Equipment.next_maintenance_date < datetime.utcnow()
        )
    )
    
    # Recent problems reported
    recent_problems = await db.execute(
        select(func.count(ProblemSolution.id))
        .where(ProblemSolution.created_at > datetime.utcnow() - timedelta(days=7))
    )
    
    return {
        "total_equipment": total.scalar(),
        "by_status": dict(by_status.all()),
        "by_criticality": dict(by_criticality.all()),
        "by_category": dict(by_category.all()),
        "overdue_maintenance": overdue.scalar() or 0,
        "recent_problems_reported": recent_problems.scalar() or 0,
    }