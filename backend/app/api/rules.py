from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import Rule, RuleVersion, User, AuditLog
from app.schemas.schemas import RuleResponse, RuleCreate
from app.core.permissions import PermissionChecker, get_current_user
from datetime import datetime

router = APIRouter(prefix="/rules", tags=["Rules Repository"])

@router.get("", response_model=List[RuleResponse])
def list_rules(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Rule)
    if category:
        query = query.filter(Rule.category == category)
    return query.all()

@router.post("", response_model=RuleResponse)
def create_rule(
    request: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["RULE_ADMIN"]))
):
    # Verify unique code
    existing = db.query(Rule).filter(Rule.rule_code == request.rule_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rule with code {request.rule_code} already exists"
        )
        
    rule = Rule(
        rule_code=request.rule_code,
        title=request.title,
        description=request.description,
        category=request.category,
        requirement_type=request.requirement_type,
        field=request.field,
        validation_type=request.validation_type,
        parameters=request.parameters,
        status=request.status,
        version=request.version,
        created_by_id=current_user.id
    )
    db.add(rule)
    db.flush()
    
    # Set default version 1.0 entry
    ver = RuleVersion(
        rule_id=rule.id,
        version=rule.version,
        status="Active",
        effective_from=datetime.utcnow().strftime("%Y-%m-%d"),
        approved_by_id=current_user.id
    )
    db.add(ver)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="RULE_CREATED",
        entity_type="rule",
        entity_id=str(rule.id),
        timestamp=datetime.utcnow(),
        action_metadata={"rule_code": rule.rule_code}
    )
    db.add(audit)
    db.commit()
    db.refresh(rule)
    
    return rule

@router.put("/{id}", response_model=RuleResponse)
def update_rule(
    id: int,
    request: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["RULE_ADMIN"]))
):
    rule = db.query(Rule).filter(Rule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule reference not found")
        
    # Apply modifications
    for k, v in request.dict(exclude_unset=True).items():
        setattr(rule, k, v)
        
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="RULE_UPDATED",
        entity_type="rule",
        entity_id=str(id),
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(rule)
    return rule
