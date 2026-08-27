from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime
from app.db.database import get_db
from app.models.models import Inspection, Violation, Product, User
from app.schemas.schemas import (
    DashboardSummary, DashboardRecentInspection, DashboardTrendPoint
)
from app.core.permissions import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard Statistics"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Total Scans
    total_scans = db.query(Inspection).count()
    
    # Inspection statuses count
    compliant = db.query(Inspection).filter(Inspection.overall_status == "COMPLIANT").count()
    non_compliant = db.query(Inspection).filter(Inspection.overall_status == "POTENTIAL_NON_COMPLIANCE").count()
    manual_review = db.query(Inspection).filter(Inspection.overall_status == "MANUAL_REVIEW").count()
    
    # Violations
    open_violations = db.query(Violation).filter(Violation.status == "OPEN").count()
    closed_violations = db.query(Violation).filter(Violation.status == "CLOSED").count()
    
    # Inspections in current month
    curr_month_str = datetime.utcnow().strftime("%Y-%m")
    inspections_this_month = db.query(Inspection).filter(Inspection.date.like(f"{curr_month_str}%")).count()
    
    return {
        "total_scans": total_scans,
        "compliant": compliant,
        "potential_non_compliance": non_compliant,
        "manual_review": manual_review,
        "open_violations": open_violations,
        "closed_violations": closed_violations,
        "inspections_this_month": inspections_this_month
    }

@router.get("/violations")
def get_violations_by_type(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Group by violation type
    results = db.query(
        Violation.violation_type,
        func.count(Violation.id).label("count")
    ).group_by(Violation.violation_type).all()
    
    return [{"violation_type": r[0], "count": r[1]} for r in results]

@router.get("/trends", response_model=List[DashboardTrendPoint])
def get_compliance_trends(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Pull date groups
    results = db.query(
        Inspection.date,
        func.sum(func.case((Inspection.overall_status == "COMPLIANT", 1), else_=0)).label("compliant"),
        func.sum(func.case((Inspection.overall_status == "POTENTIAL_NON_COMPLIANCE", 1), else_=0)).label("non_compliant"),
        func.sum(func.case((Inspection.overall_status == "MANUAL_REVIEW", 1), else_=0)).label("manual_review")
    ).group_by(Inspection.date).order_by(Inspection.date.asc()).all()
    
    return [
        {
            "date": r[0],
            "compliant": int(r[1] or 0),
            "non_compliant": int(r[2] or 0),
            "manual_review": int(r[3] or 0)
        } for r in results
    ]

@router.get("/recent-inspections", response_model=List[DashboardRecentInspection])
def get_recent_inspections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(Inspection).order_by(Inspection.created_at.desc()).limit(5).all()
    
    out = []
    for ins in results:
        inspector_name = ins.inspector.name if ins.inspector else "System"
        product_name = ins.product.product_name if ins.product else "N/A"
        brand = ins.product.brand if ins.product else "N/A"
        
        out.append({
            "id": ins.id,
            "product_name": product_name,
            "brand": brand,
            "inspector": inspector_name,
            "date": ins.date,
            "status": ins.overall_status
        })
    return out
