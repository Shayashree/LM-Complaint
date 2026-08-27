from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import AuditLog, User
from app.schemas.schemas import AuditLogResponse
from app.core.permissions import PermissionChecker

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse])
def get_system_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["AUDITOR", "SUPER_ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return logs
