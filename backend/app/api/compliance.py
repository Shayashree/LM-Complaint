from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import ComplianceCheck, User, Inspection
from app.schemas.schemas import ComplianceCheckResponse, InspectionResponse
from app.core.permissions import PermissionChecker, get_current_user
from app.services.compliance_engine import compliance_engine

router = APIRouter(prefix="/compliance", tags=["Compliance Engine"])

@router.post("/check/{inspection_id}", response_model=InspectionResponse)
def trigger_compliance_check(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    try:
        inspection = compliance_engine.run_compliance_check(db, inspection_id)
        return inspection
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal engine processing error: {e}")

@router.get("/{inspection_id}", response_model=List[ComplianceCheckResponse])
def get_compliance_checks(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    checks = db.query(ComplianceCheck).filter(ComplianceCheck.inspection_id == inspection_id).all()
    return checks
