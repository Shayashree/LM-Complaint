from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User
from app.core.config import settings
from app.schemas.schemas import TokenData

security = HTTPBearer()

def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        employee_id: str = payload.get("sub")
        role: str = payload.get("role")
        if employee_id is None:
            raise credentials_exception
        token_data = TokenData(employee_id=employee_id, role=role)
    except Exception:
        raise credentials_exception
        
    user = db.query(User).filter(User.employee_id == token_data.employee_id).first()
    if user is None:
        raise credentials_exception
    return user

class PermissionChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        user_roles = [r.name for r in current_user.roles]
        # Super Admins bypass checks
        if "SUPER_ADMIN" in user_roles:
            return current_user
        
        has_access = any(role in self.allowed_roles for role in user_roles)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Action forbidden: Sufficient permissions not met"
            )
        return current_user
