from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import (
    Inspection, InspectionImage, Product, User, ExtractedDeclaration, 
    OCRResult, AuditLog, InspectionComment, Violation
)
from app.schemas.schemas import (
    InspectionResponse, StandardResponse, InspectionVerifyRequest, SupervisorReviewRequest
)
from app.core.permissions import PermissionChecker, get_current_user
from app.utils.storage import storage_provider
from app.services.image_service import image_service
from app.services.ocr_service import ocr_service
from app.services.declaration_service import declaration_service
from app.services.compliance_engine import compliance_engine
from app.services.report_service import report_service
from datetime import datetime
import uuid

router = APIRouter(prefix="/inspections", tags=["Inspections"])

def run_background_compliance(db_session_factory, inspection_id: str):
    """
    Background worker task to trigger compliance check pipelines.
    """
    db = db_session_factory()
    try:
        compliance_engine.run_compliance_check(db, inspection_id)
    except Exception as e:
        print(f"Compliance pipeline background error: {e}")
    finally:
        db.close()

@router.post("", response_model=InspectionResponse)
def create_inspection(
    background_tasks: BackgroundTasks,
    product_id: Optional[int] = Form(None),
    image_side: str = Form("front"),
    file: UploadFile = File(...),
    commodity_category: Optional[str] = Form(None),
    calibration_method: Optional[str] = Form("AUTO_HEURISTIC"),
    pdp_width_mm: Optional[float] = Form(None),
    pdp_height_mm: Optional[float] = Form(None),
    caliper_override_mm: Optional[float] = Form(None),
    gemini_api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    # 1. Save original image
    try:
        storage_path = storage_provider.save_file(file, subfolder="inspections")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save packaging upload image: {e}"
        )

    # 2. Preprocess image
    processed_path = image_service.preprocess_image(storage_path)
    assessment = image_service.estimate_readability(storage_path)

    # 3. Calculate Calibrated Scale & PDP Area
    pdp_area = round((float(pdp_width_mm) * float(pdp_height_mm)) / 100.0, 1) if (pdp_width_mm and pdp_height_mm) else None
    calibration_scale_ppm = None
    if calibration_method == "REFERENCE_CARD":
        # Standard ID-1 ISO Card is 85.60 mm wide. Default calibrated optical ratio
        calibration_scale_ppm = 4.82
    elif pdp_height_mm and pdp_height_mm > 0:
        calibration_scale_ppm = round(800.0 / float(pdp_height_mm), 2)

    # Create inspection record
    inspection_id = f"LM-2026-{uuid.uuid4().hex[:5].upper()}"
    inspection = Inspection(
        id=inspection_id,
        product_id=product_id,
        inspector_id=current_user.id,
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        overall_status="MANUAL_REVIEW",
        image_quality=assessment["readability_status"],
        verification_status="Pending",
        supervisor_status="Pending",
        commodity_category=commodity_category or "GENERAL",
        calibration_method=calibration_method or "AUTO_HEURISTIC",
        pdp_width_mm=pdp_width_mm,
        pdp_height_mm=pdp_height_mm,
        pdp_area_cm2=pdp_area,
        calibration_scale_ppm=calibration_scale_ppm,
        caliper_override_mm=caliper_override_mm
    )
    db.add(inspection)
    db.flush()

    # Create Inspection Image entry
    ins_image = InspectionImage(
        inspection_id=inspection_id,
        storage_path=storage_path,
        image_side=image_side,
        is_processed=(processed_path != storage_path),
        processed_path=processed_path,
        quality_score=assessment["quality_score"],
        readability_status=assessment["readability_status"]
    )
    db.add(ins_image)
    db.flush()

    # 4. Trigger OCR & Extractor synchronously for instant feedback in prototype
    ocr_out = ocr_service.perform_ocr(processed_path)
    total_conf = 0.0
    for line in ocr_out:
        res = OCRResult(
            inspection_image_id=ins_image.id,
            text=line["text"],
            confidence=line["confidence"],
            bounding_box=line["bbox"]
        )
        db.add(res)
        total_conf += line["confidence"]
        
    avg_conf = round(total_conf / len(ocr_out), 2) if ocr_out else 1.0
    db.flush()

    # Extract structured fields and category classification
    decls, detected_category = declaration_service.extract_declarations_llm(
        processed_path, 
        ocr_out,
        commodity_category=commodity_category,
        original_filename=file.filename,
        api_key=gemini_api_key
    )
    if not commodity_category and detected_category:
        inspection.commodity_category = detected_category

    for decl in decls:
        db_decl = ExtractedDeclaration(
            inspection_id=inspection_id,
            field_name=decl["field_name"],
            value=decl["value"],
            confidence=decl["confidence"],
            source_image_id=ins_image.id,
            bounding_box=decl["bounding_box"],
            extraction_method=decl["extraction_method"]
        )
        db.add(db_decl)
    db.flush()

    # Connect to a default product if not supplied, based on name heuristic
    if not product_id:
        detected_name_decl = next((d for d in decls if d["field_name"] == "product_name"), None)
        if detected_name_decl:
            name_val = detected_name_decl["value"]
            matched_prod = db.query(Product).filter(Product.product_name.like(f"%{name_val}%")).first()
            if matched_prod:
                inspection.product_id = matched_prod.id

    # 5. Run Compliance check pipeline
    db.commit() # Commit declarations and files
    
    # Run compliance engine calculation (run synchronously for the demo flow, or queue in BackgroundTasks)
    compliance_engine.run_compliance_check(db, inspection_id)

    # 6. Automatically compile official PDF compliance report for this product scan
    try:
        report_service.generate_compliance_report(db, inspection_id, current_user.id)
    except Exception as e:
        print(f"Auto-generation of PDF report failed for {inspection_id}: {e}")
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="CREATE_INSPECTION",
        entity_type="inspection",
        entity_id=inspection_id,
        timestamp=datetime.utcnow(),
        action_metadata={"overall_status": inspection.overall_status}
    )
    db.add(audit)
    db.commit()
    db.refresh(inspection)

    return inspection

@router.get("", response_model=List[InspectionResponse])
def list_inspections(
    status: Optional[str] = None,
    product_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR", "SUPERVISOR", "AUDITOR", "ANALYST", "DEPT_ADMIN", "CONSUMER"]))
):
    query = db.query(Inspection)
    if status:
        query = query.filter(Inspection.overall_status == status)
    if product_name:
        query = query.join(Product).filter(Product.product_name.like(f"%{product_name}%"))
        
    return query.order_by(Inspection.created_at.desc()).all()

@router.get("/{id}", response_model=InspectionResponse)
def get_inspection(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inspection = db.query(Inspection).filter(Inspection.id == id).first()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection record not found"
        )
    return inspection

@router.post("/{id}/verify", response_model=InspectionResponse)
def verify_inspection(
    id: str,
    request: InspectionVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    inspection = db.query(Inspection).filter(Inspection.id == id).first()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection record not found"
        )

    # Record decision
    inspection.verification_status = "Verified" if request.decision in ["CONFIRM", "MARK_COMPLIANT"] else "Escalated"
    inspection.verified_by_id = current_user.id
    inspection.verified_date = datetime.utcnow()
    inspection.officer_remarks = request.remarks

    # Apply Caliper Manual Override or Category Override if provided by Inspector
    needs_reeval = False
    if request.caliper_override_mm is not None and request.caliper_override_mm > 0:
        inspection.caliper_override_mm = request.caliper_override_mm
        needs_reeval = True
    if request.commodity_category_override:
        inspection.commodity_category = request.commodity_category_override
        needs_reeval = True

    if needs_reeval:
        db.flush()
        compliance_engine.run_compliance_check(db, id)
        try:
            report_service.generate_compliance_report(db, id, current_user.id)
        except Exception as e:
            print(f"Report re-generation warning: {e}")

    # If CONFIRM (violation confirmed), confirm open violations status
    if request.decision == "CONFIRM":
        db.query(Violation).filter(Violation.inspection_id == id).update({"status": "CONFIRMED"})
    elif request.decision == "MARK_COMPLIANT":
        db.query(Violation).filter(Violation.inspection_id == id).update({"status": "DISMISSED"})

    # Add Comment
    comment = InspectionComment(
        inspection_id=id,
        user_id=current_user.id,
        comment=f"Officer Verdict ({request.decision}): {request.remarks}"
    )
    db.add(comment)

    # Log action
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="OFFICER_VERIFIED",
        entity_type="inspection",
        entity_id=id,
        timestamp=datetime.utcnow(),
        action_metadata={"decision": request.decision}
    )
    db.add(audit)
    db.commit()
    db.refresh(inspection)
    return inspection

@router.post("/{id}/supervisor-review", response_model=InspectionResponse)
def supervisor_review_inspection(
    id: str,
    request: SupervisorReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["SUPERVISOR"]))
):
    inspection = db.query(Inspection).filter(Inspection.id == id).first()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection record not found"
        )

    # Record supervisor decision
    inspection.supervisor_status = "Approved" if request.decision == "APPROVE" else "Rejected"
    inspection.supervisor_remarks = request.remarks
    inspection.supervisor_id = current_user.id
    inspection.supervisor_date = datetime.utcnow()

    # Update violation statuses based on supervisor approval
    if request.decision == "APPROVE":
        # Supervisor approved violations, keep confirmed
        pass
    else:
        # Supervisor rejected the violation filing, close them
        db.query(Violation).filter(Violation.inspection_id == id).update({"status": "CLOSED"})

    comment = InspectionComment(
        inspection_id=id,
        user_id=current_user.id,
        comment=f"Supervisor Decision ({request.decision}): {request.remarks}"
    )
    db.add(comment)

    # Log action
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="SUPERVISOR_REVIEWED",
        entity_type="inspection",
        entity_id=id,
        timestamp=datetime.utcnow(),
        action_metadata={"decision": request.decision}
    )
    db.add(audit)
    db.commit()
    db.refresh(inspection)
    return inspection
