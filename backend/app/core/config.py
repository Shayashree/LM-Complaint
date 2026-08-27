import json
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    PROJECT_NAME: str = "Legal Metrology Packaged Commodities Compliance API"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/legal_metrology"
    JWT_SECRET: str = "8e9282fa2c8f8b3b428d08c5c70ea91b2db97561858c2a8684bd30a10f92b7ef"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "reports"
    
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    
    OCR_PROVIDER: str = "mock"  # 'paddleocr' or 'mock'
    STORAGE_PROVIDER: str = "local"  # 'local'

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

settings = Settings()
export_settings = settings
