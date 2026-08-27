from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.products import router as products_router
from app.api.scans import router as scans_router
from app.api.inspections import router as inspections_router
from app.api.declarations import router as declarations_router
from app.api.compliance import router as compliance_router
from app.api.violations import router as violations_router
from app.api.evidence import router as evidence_router
from app.api.reports import router as reports_router
from app.api.rules import router as rules_router
from app.api.dashboard import router as dashboard_router
from app.api.audit_logs import router as audit_logs_router
from app.api.ecom import router as ecom_router

# Ensure local directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "temp"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "scans"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "inspections"), exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API services supporting Computer Vision & rules validation under Legal Metrology PC Rules, 2011",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Error Handlers
@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please consult the system logs."
            }
        }
    )

# Static file serving
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/reports", StaticFiles(directory=settings.REPORT_DIR), name="reports")

# Include Routers under standard /api prefix
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(scans_router, prefix=settings.API_V1_STR)
app.include_router(inspections_router, prefix=settings.API_V1_STR)
app.include_router(declarations_router, prefix=settings.API_V1_STR)
app.include_router(compliance_router, prefix=settings.API_V1_STR)
app.include_router(violations_router, prefix=settings.API_V1_STR)
app.include_router(evidence_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(rules_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(audit_logs_router, prefix=settings.API_V1_STR)
app.include_router(ecom_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "success": True,
        "message": "Welcome to the Legal Metrology PC Rules API Portal",
        "docs_url": "/docs"
    }
