from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import Violation, User, AuditLog
from app.schemas.schemas import ViolationResponse, ViolationCreate
from app.core.permissions import PermissionChecker, get_current_user
from datetime import datetime

router = APIRouter(prefix="/violations", tags=["Violations Board"])

@router.get("", response_model=List[ViolationResponse])
def list_violations(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR", "SUPERVISOR", "AUDITOR", "DEPT_ADMIN", "CONSUMER"]))
):
    query = db.query(Violation)
    if status:
        query = query.filter(Violation.status == status)
    if severity:
        query = query.filter(Violation.severity == severity)
    return query.order_by(Violation.created_at.desc()).all()

@router.get("/{id}", response_model=ViolationResponse)
def get_violation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    violation = db.query(Violation).filter(Violation.id == id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation record not found")
    return violation

@router.put("/{id}", response_model=ViolationResponse)
def update_violation_comment(
    id: int,
    comment: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    violation = db.query(Violation).filter(Violation.id == id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation record not found")
        
    violation.officer_comment = comment
    violation.status = "UNDER_REVIEW"
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="VIOLATION_UPDATED",
        entity_type="violation",
        entity_id=str(id),
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(violation)
    return violation

@router.post("", response_model=ViolationResponse)
def create_violation(
    payload: ViolationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    from app.models.models import Inspection
    inspection = db.query(Inspection).filter(Inspection.id == payload.inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Associated Inspection not found")
        
    violation = Violation(
        inspection_id=payload.inspection_id,
        violation_type=payload.violation_type,
        description=payload.description,
        severity=payload.severity,
        confidence=1.0,
        status="OPEN",
        rule_id=payload.rule_id
    )
    db.add(violation)
    db.flush()
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="VIOLATION_CREATED",
        entity_type="violation",
        entity_id=str(violation.id),
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(violation)
    return violation
