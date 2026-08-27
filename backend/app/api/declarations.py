from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import ExtractedDeclaration, User
from app.schemas.schemas import ExtractedDeclarationResponse
from app.core.permissions import get_current_user

router = APIRouter(prefix="/inspections", tags=["Extracted Declarations"])

@router.get("/{id}/declarations", response_model=List[ExtractedDeclarationResponse])
def get_extracted_declarations(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ExtractedDeclaration).filter(
        ExtractedDeclaration.inspection_id == id
    ).all()
