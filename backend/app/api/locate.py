from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Optional, Dict, Any, List
import json
import os
import shutil
import tempfile
from app.services.nvidia_locate_service import nvidia_locate_service

router = APIRouter(prefix="/locate", tags=["NVIDIA LocateAnything Spatial Grounding"])

@router.post("/ground")
async def ground_declarations(
    file: UploadFile = File(...),
    declarations_json: str = Form(..., description="JSON dict mapping field_name to target text description"),
    nvidia_api_key: Optional[str] = Form(None),
    endpoint_url: Optional[str] = Form(None)
):
    """
    Accepts a packaging image and a dictionary of declarations to locate.
    Uses NVIDIA LocateAnything-3B (or NIM microservice) with Parallel Box Decoding
    to return pinpoint spatial bounding boxes [x, y, w, h] (0-100%).
    """
    try:
        decl_dict = json.loads(declarations_json)
        if not isinstance(decl_dict, dict):
            raise ValueError("declarations_json must be a JSON object")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid declarations_json: {e}")

    # Save temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "img.jpg")[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        results = nvidia_locate_service.locate_declarations(
            image_path=tmp_path,
            declarations_to_find=decl_dict,
            api_key=nvidia_api_key,
            endpoint_url=endpoint_url
        )
        return {
            "success": True,
            "engine": "NVIDIA LocateAnything-3B",
            "located_declarations": results
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
