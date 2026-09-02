from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any, Dict
from datetime import datetime

# ==========================================
# AUTH SCHEMAS
# ==========================================
class LoginRequest(BaseModel):
    employee_id: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    employee_id: str
    name: str

class TokenData(BaseModel):
    employee_id: Optional[str] = None
    role: Optional[str] = None

# ==========================================
# USER SCHEMAS
# ==========================================
class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[str]

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    employee_id: str
    email: EmailStr
    name: str
    department: Optional[str] = None
    is_active: bool
    roles: List[RoleResponse] = []

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    employee_id: str
    email: EmailStr
    name: str
    password: str
    department: Optional[str] = None
    roles: List[str] = ["INSPECTOR"]

# ==========================================
# PRODUCT SCHEMAS
# ==========================================
class ProductImageResponse(BaseModel):
    id: int
    storage_path: str
    image_side: Optional[str] = None
    quality_score: float

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    manufacturer: Optional[str] = None
    packer: Optional[str] = None
    importer: Optional[str] = None
    barcode: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    manufacturing_date: Optional[str] = None
    packing_date: Optional[str] = None
    consumer_care: Optional[str] = None
    created_at: datetime
    images: List[ProductImageResponse] = []

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    manufacturer: Optional[str] = None
    packer: Optional[str] = None
    importer: Optional[str] = None
    barcode: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    manufacturing_date: Optional[str] = None
    packing_date: Optional[str] = None
    consumer_care: Optional[str] = None

# ==========================================
# SCAN UPLOAD SCHEMAS
# ==========================================
class ScanUploadResponse(BaseModel):
    scan_id: str
    image_id: int
    storage_path: str
    image_quality: str

class OCRBoundingBox(BaseModel):
    text: str
    confidence: float
    bbox: List[float] # [x, y, w, h] in percentages

class OCRResponse(BaseModel):
    image_id: int
    extracted_text: List[OCRBoundingBox]
    ocr_confidence: float

# ==========================================
# DECLARATION SCHEMAS
# ==========================================
class ExtractedDeclarationResponse(BaseModel):
    id: int
    field_name: str
    value: Optional[str] = None
    confidence: float
    source_image_id: Optional[int] = None
    bounding_box: Optional[List[float]] = None
    extraction_method: str

    class Config:
        from_attributes = True

# ==========================================
# RULE SCHEMAS
# ==========================================
class RuleResponse(BaseModel):
    id: int
    rule_code: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    requirement_type: Optional[str] = None
    field: Optional[str] = None
    validation_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: str
    version: str

    class Config:
        from_attributes = True

class RuleCreate(BaseModel):
    rule_code: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    requirement_type: Optional[str] = None
    field: Optional[str] = None
    validation_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = "Active"
    version: Optional[str] = "1.0"

# ==========================================
# COMPLIANCE CHECK & VIOLATION SCHEMAS
# ==========================================
class ComplianceCheckResponse(BaseModel):
    id: int
    rule_id: int
    rule_code: str
    field: Optional[str] = None
    status: str
    confidence: float
    message: Optional[str] = None
    measured_font_height_mm: Optional[float] = None
    required_font_height_mm: Optional[float] = None

    class Config:
        from_attributes = True

class ViolationEvidenceResponse(BaseModel):
    id: int
    original_image_path: str
    annotated_image_path: Optional[str] = None
    cropped_image_path: Optional[str] = None
    bounding_box: Optional[List[float]] = None
    ocr_text: Optional[str] = None
    confidence: float

    class Config:
        from_attributes = True

class ViolationCreate(BaseModel):
    inspection_id: str
    violation_type: str
    description: Optional[str] = None
    severity: str
    rule_id: int

class ViolationResponse(BaseModel):
    id: int
    inspection_id: str
    violation_type: str
    description: Optional[str] = None
    severity: str
    confidence: float
    status: str
    officer_comment: Optional[str] = None
    created_at: datetime
    rule: RuleResponse
    evidence: List[ViolationEvidenceResponse] = []

    class Config:
        from_attributes = True

# ==========================================
# REPORT SCHEMAS
# ==========================================
class ReportResponse(BaseModel):
    id: int
    inspection_id: str
    generated_by_id: Optional[int] = None
    storage_path: str
    rule_version_used: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# INSPECTION SCHEMAS
# ==========================================
class InspectionCommentResponse(BaseModel):
    id: int
    user_id: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True

class InspectionImageResponse(BaseModel):
    id: int
    storage_path: str
    image_side: Optional[str] = None
    is_processed: bool
    processed_path: Optional[str] = None
    quality_score: float
    readability_status: str

    class Config:
        from_attributes = True

class InspectionResponse(BaseModel):
    id: str
    product_id: Optional[int] = None
    inspector_id: int
    date: str
    overall_status: str
    image_quality: str
    ocr_confidence: float
    detection_confidence: float
    overall_confidence: float
    officer_remarks: Optional[str] = None
    verification_status: str
    verified_by_id: Optional[int] = None
    verified_date: Optional[datetime] = None
    supervisor_status: str
    supervisor_remarks: Optional[str] = None
    supervisor_id: Optional[int] = None
    supervisor_date: Optional[datetime] = None
    created_at: datetime
    
    # Category and Calibration Fields
    commodity_category: Optional[str] = "GENERAL"
    pdp_width_mm: Optional[float] = None
    pdp_height_mm: Optional[float] = None
    pdp_area_cm2: Optional[float] = None
    calibration_method: Optional[str] = "AUTO_HEURISTIC"
    calibration_scale_ppm: Optional[float] = None
    calibrated_font_height_mm: Optional[float] = None
    caliper_override_mm: Optional[float] = None

    product: Optional[ProductResponse] = None
    images: List[InspectionImageResponse] = []
    declarations: List[ExtractedDeclarationResponse] = []
    compliance_checks: List[ComplianceCheckResponse] = []
    violations: List[ViolationResponse] = []
    comments: List[InspectionCommentResponse] = []
    reports: List[ReportResponse] = []

    class Config:
        from_attributes = True

class InspectionCreate(BaseModel):
    product_id: Optional[int] = None
    officer_remarks: Optional[str] = None
    commodity_category: Optional[str] = None
    pdp_width_mm: Optional[float] = None
    pdp_height_mm: Optional[float] = None
    calibration_method: Optional[str] = None

class InspectionVerifyRequest(BaseModel):
    decision: str # CONFIRM, MARK_COMPLIANT, SEND_FOR_MANUAL_REVIEW, REQUEST_REINSPECTION
    remarks: str
    caliper_override_mm: Optional[float] = None
    commodity_category_override: Optional[str] = None

class SupervisorReviewRequest(BaseModel):
    decision: str # APPROVE, REJECT, REQUEST_REINSPECTION
    remarks: str

# ==========================================
# DASHBOARD SCHEMAS
# ==========================================
class DashboardSummary(BaseModel):
    total_scans: int
    compliant: int
    potential_non_compliance: int
    manual_review: int
    open_violations: int
    closed_violations: int
    inspections_this_month: int

class DashboardViolationTypeCount(BaseModel):
    violation_type: str
    count: int

class DashboardTrendPoint(BaseModel):
    date: str
    compliant: int
    non_compliant: int
    manual_review: int

class DashboardRecentInspection(BaseModel):
    id: str
    product_name: str
    brand: Optional[str] = None
    inspector: str
    date: str
    status: str

# ==========================================
# AUDIT LOG SCHEMAS
# ==========================================
class AuditLogResponse(BaseModel):
    id: int
    user_identity: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    timestamp: datetime
    action_metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True

# ==========================================
# STANDARD RESPONSE ENVELOPES
# ==========================================
class StandardResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None

class StandardErrorDetails(BaseModel):
    code: str
    message: str

class StandardErrorResponse(BaseModel):
    success: bool = False
    error: StandardErrorDetails
