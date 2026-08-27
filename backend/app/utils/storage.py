import os
import uuid
import shutil
from fastapi import UploadFile
from app.core.config import settings

class LocalStorageProvider:
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.REPORT_DIR, exist_ok=True)

    def save_file(self, file: UploadFile, subfolder: str = "") -> str:
        ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
        filename = f"{uuid.uuid4()}{ext}"
        
        target_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        
        file_path = os.path.join(target_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Normalize to forward slashes for clean REST API path returns
        return file_path.replace("\\", "/")

    def delete_file(self, file_path: str):
        normalized_path = file_path.replace("/", os.sep)
        if os.path.exists(normalized_path):
            os.remove(normalized_path)

storage_provider = LocalStorageProvider()
