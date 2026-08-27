from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import User, Role, AuditLog
from app.schemas.schemas import UserResponse, UserCreate, StandardResponse
from app.core.security import get_password_hash
from app.core.permissions import PermissionChecker, get_current_user
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["SUPER_ADMIN", "DEPT_ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    return db.query(User).all()

@router.post("", response_model=UserResponse)
def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["SUPER_ADMIN", "DEPT_ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    # Verify user exists
    existing = db.query(User).filter(
        (User.employee_id == request.employee_id) | (User.email == request.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this Employee ID or Email already exists"
        )
        
    hashed_pwd = get_password_hash(request.password)
    user = User(
        employee_id=request.employee_id,
        email=request.email,
        name=request.name,
        hashed_password=hashed_pwd,
        department=request.department
    )
    db.add(user)
    db.flush() # get user.id
    
    # Assign Roles
    for role_name in request.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user.roles.append(role)
            
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="USER_CREATED",
        entity_type="user",
        entity_id=str(user.id),
        timestamp=datetime.utcnow(),
        action_metadata={"created_employee_id": user.employee_id}
    )
    db.add(audit)
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/{id}", response_model=UserResponse)
def get_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
