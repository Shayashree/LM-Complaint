from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.db.database import get_db
from app.models.models import User, AuditLog
from app.schemas.schemas import LoginRequest, Token, UserResponse, StandardResponse
from app.core.security import verify_password, create_access_token
from app.core.permissions import get_current_user
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Check by employee ID or Email
    user = db.query(User).filter(
        (User.employee_id == request.employee_id) | (User.email == request.employee_id)
    ).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        # Log failed login attempt
        audit = AuditLog(
            user_identity=request.employee_id,
            action="LOGIN_FAILED",
            entity_type="user",
            entity_id=request.employee_id,
            timestamp=datetime.utcnow(),
            action_metadata={"reason": "Invalid credentials"}
        )
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Employee ID / Email or Password"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user profile"
        )

    # Get primary role name
    role_name = user.roles[0].name if user.roles else "INSPECTOR"
    
    access_token = create_access_token(
        subject=user.employee_id, role=role_name, expires_delta=timedelta(hours=4)
    )
    
    # Log audit entry
    audit = AuditLog(
        user_id=user.id,
        user_identity=f"{user.name} ({user.employee_id})",
        action="LOGIN",
        entity_type="user",
        entity_id=str(user.id),
        timestamp=datetime.utcnow(),
        action_metadata={"role": role_name}
    )
    db.add(audit)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role_name,
        "employee_id": user.employee_id,
        "name": user.name
    }

@router.post("/logout", response_model=StandardResponse)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="LOGOUT",
        entity_type="user",
        entity_id=str(current_user.id),
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    return {"success": True, "message": "Session terminated successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
