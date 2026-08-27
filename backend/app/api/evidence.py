from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.models import ViolationEvidence, User, AuditLog
from app.schemas.schemas import ViolationEvidenceResponse
from app.core.permissions import get_current_user
from datetime import datetime

router = APIRouter(prefix="/violations", tags=["Evidence Management"])

@router.get("/{id}/evidence", response_model=List[ViolationEvidenceResponse])
def get_violation_evidences(
    id: int, # Violation ID
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    evidences = db.query(ViolationEvidence).filter(
        ViolationEvidence.violation_id == id
    ).all()
    return evidences

@router.post("/{id}/evidence", response_model=ViolationEvidenceResponse)
def add_violation_evidence(
    id: int,
    original_image_path: str,
    annotated_image_path: Optional[str] = None, # We can map optional below
    ocr_text: str = None,
    confidence: float = 1.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    evidence = ViolationEvidence(
        violation_id=id,
        original_image_path=original_image_path,
        annotated_image_path=annotated_image_path or original_image_path,
        cropped_image_path=original_image_path,
        ocr_text=ocr_text,
        confidence=confidence
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence
