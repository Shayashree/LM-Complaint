import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.db.database import get_db
from app.models.models import InspectionImage, OCRResult, User, AuditLog
from app.schemas.schemas import ScanUploadResponse, OCRResponse, OCRBoundingBox
from app.core.permissions import PermissionChecker, get_current_user
from app.utils.storage import storage_provider
from app.services.image_service import image_service
from app.services.ocr_service import ocr_service
from datetime import datetime

router = APIRouter(prefix="/scans", tags=["Image Scans"])

# MIME types allowed
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB

@router.post("/upload", response_model=ScanUploadResponse)
def upload_label_image(
    file: UploadFile = File(...),
    image_side: str = "front",
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    # 1. File validation
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension {ext}. Allowed: JPG, JPEG, PNG, WEBP."
        )

    # Temporary write to check size
    try:
        temp_path = storage_provider.save_file(file, subfolder="temp")
        size = os.path.getsize(temp_path)
        if size > MAX_FILE_SIZE:
            storage_provider.delete_file(temp_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum size threshold of 10MB."
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}"
        )

    # 2. Image assessment using OpenCV readability estimator
    assessment = image_service.estimate_readability(temp_path)
    
    # 3. Rename/move out of temp folder
    final_filename = os.path.basename(temp_path)
    final_path = os.path.join(storage_provider.save_file.__self__.UPLOAD_DIR, "scans", final_filename).replace("\\", "/")
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    os.rename(temp_path, final_path)

    # Return scan ID and path
    scan_id = str(uuid.uuid4())
    
    # Log upload action
    audit = AuditLog(
        user_id=current_user.id,
        user_identity=f"{current_user.name} ({current_user.employee_id})",
        action="UPLOAD_IMAGE",
        entity_type="scan",
        entity_id=scan_id,
        timestamp=datetime.utcnow(),
        action_metadata={"quality_score": assessment["quality_score"], "readability": assessment["readability_status"]}
    )
    db.add(audit)
    db.commit()

    return {
        "scan_id": scan_id,
        "image_id": int(datetime.utcnow().timestamp() % 100000), # placeholder ID for temp linking
        "storage_path": final_path,
        "image_quality": assessment["readability_status"]
    }

@router.post("/{image_id}/ocr", response_model=OCRResponse)
def run_ocr_on_scan(
    image_id: int,
    image_path: str, # passed in request parameters/body for simplification of prototype linking
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["INSPECTOR"]))
):
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified image file not found on server storage."
        )

    # Trigger raw OCR
    ocr_out = ocr_service.perform_ocr(image_path)
    
    # Parse bounding boxes
    bbox_list = []
    total_conf = 0.0
    for line in ocr_out:
        bbox_list.append(OCRBoundingBox(
            text=line["text"],
            confidence=line["confidence"],
            bbox=line["bbox"]
        ))
        total_conf += line["confidence"]
        
    avg_conf = round(total_conf / len(ocr_out), 2) if ocr_out else 1.0

    return {
        "image_id": image_id,
        "extracted_text": bbox_list,
        "ocr_confidence": avg_conf
    }
