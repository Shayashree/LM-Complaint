from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from app.db.database import get_db
from app.models.models import Report, User, Inspection
from app.schemas.schemas import ReportResponse
from app.core.permissions import PermissionChecker, get_current_user
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Reports Archive"])

@router.post("/{inspection_id}/generate", response_model=ReportResponse)
def generate_inspection_report(
    inspection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR", "SUPERVISOR", "AUDITOR", "ANALYST", "DEPT_ADMIN", "SUPER_ADMIN"]))
):
    try:
        pdf_path = report_service.generate_compliance_report(db, inspection_id, current_user.id)
        report = db.query(Report).filter(Report.storage_path == pdf_path).first()
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF compiler failure: {e}")

@router.get("/{id}", response_model=ReportResponse)
def get_report_metadata(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = db.query(Report).filter(Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report record not found")
    return report

@router.get("/{id}/download")
def download_pdf_report(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR", "SUPERVISOR", "AUDITOR", "ANALYST", "DEPT_ADMIN", "SUPER_ADMIN", "CONSUMER"]))
):
    report = db.query(Report).filter(Report.id == id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report record not found")
        
    normalized_path = report.storage_path.replace("/", os.sep)
    if not os.path.exists(normalized_path):
        # Auto-regenerate on demand if deleted
        try:
            new_path = report_service.generate_compliance_report(db, report.inspection_id, current_user.id)
            normalized_path = new_path.replace("/", os.sep)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="The requested PDF report document file was deleted from system storage."
            )
        
    return FileResponse(
        path=normalized_path,
        media_type="application/pdf",
        filename=os.path.basename(normalized_path)
    )

@router.get("/analytics/download")
def download_analytics_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR", "SUPERVISOR", "AUDITOR", "ANALYST", "DEPT_ADMIN"]))
):
    try:
        pdf_path = report_service.generate_analytics_report(db, current_user.id)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Analytics report PDF generation failed")
            
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename="Legal_Metrology_Analytics_Report.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF compiler failure: {e}")
