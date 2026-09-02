from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Float, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

# Association Table for User-Role Many-to-Many
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False) # e.g. SUPER_ADMIN, INSPECTOR
    description = Column(String(200))
    permissions = Column(JSON, default=list) # List of permission keys (e.g. ['scan', 'verify'])

    users = relationship("User", secondary=user_roles, back_populates="roles")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    inspections = relationship("Inspection", foreign_keys="Inspection.inspector_id", back_populates="inspector")
    supervised_inspections = relationship("Inspection", foreign_keys="Inspection.supervisor_id", back_populates="supervisor")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(150), index=True, nullable=False)
    brand = Column(String(100), index=True)
    category = Column(String(50), index=True) # e.g. Food, Cosmetics
    subcategory = Column(String(50))
    manufacturer = Column(String(150))
    packer = Column(String(150))
    importer = Column(String(150))
    barcode = Column(String(50), unique=True, index=True)
    net_quantity = Column(String(50))
    mrp = Column(String(50))
    manufacturing_date = Column(String(50))
    packing_date = Column(String(50))
    consumer_care = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    inspections = relationship("Inspection", back_populates="product")

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    storage_path = Column(String(255), nullable=False)
    image_side = Column(String(20)) # e.g. front, back, side
    quality_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="images")

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String(50), primary_key=True, index=True) # e.g. LM-2026-00001
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(20), index=True, nullable=False) # Date stamp e.g. '2026-08-26'
    
    # AI Screening results
    overall_status = Column(String(30), default="MANUAL_REVIEW", index=True) # COMPLIANT, POTENTIAL_NON_COMPLIANCE, MANUAL_REVIEW
    image_quality = Column(String(20), default="Good") # Excellent, Good, Poor
    ocr_confidence = Column(Float, default=0.0)
    detection_confidence = Column(Float, default=0.0)
    overall_confidence = Column(Float, default=0.0)
    
    # Inspector Decision
    officer_remarks = Column(String(500))
    verification_status = Column(String(30), default="Pending", index=True) # Pending, Verified, Escalated
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_date = Column(DateTime, nullable=True)
    
    # Supervisor Review
    supervisor_status = Column(String(30), default="Pending") # Pending, Approved, Rejected
    supervisor_remarks = Column(String(500))
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    supervisor_date = Column(DateTime, nullable=True)
    
    # Commodity Category & Calibration Fields
    commodity_category = Column(String(50), default="GENERAL") # FOOD_PERISHABLE, COSMETICS, ELECTRONICS, TEXTILE, MULTI_PIECE, GENERAL
    pdp_width_mm = Column(Float, nullable=True) # Calibrated PDP Width in mm
    pdp_height_mm = Column(Float, nullable=True) # Calibrated PDP Height in mm
    pdp_area_cm2 = Column(Float, nullable=True) # Principal Display Panel Area in cm2
    calibration_method = Column(String(50), default="AUTO_HEURISTIC") # MANUAL_PDP, REFERENCE_CARD, AUTO_HEURISTIC
    calibration_scale_ppm = Column(Float, nullable=True) # Scale in Pixels Per mm
    calibrated_font_height_mm = Column(Float, nullable=True) # Measured physical font height in mm
    caliper_override_mm = Column(Float, nullable=True) # Officer physical vernier caliper override in mm
    
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="inspections")
    inspector = relationship("User", foreign_keys=[inspector_id], back_populates="inspections")
    supervisor = relationship("User", foreign_keys=[supervisor_id], back_populates="supervised_inspections")
    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    declarations = relationship("ExtractedDeclaration", back_populates="inspection", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="inspection", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="inspection", cascade="all, delete-orphan")
    comments = relationship("InspectionComment", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")

class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    storage_path = Column(String(255), nullable=False)
    image_side = Column(String(20)) # front, back, etc.
    is_processed = Column(Boolean, default=False)
    processed_path = Column(String(255))
    quality_score = Column(Float, default=1.0)
    estimated_text_height = Column(Float)
    readability_status = Column(String(30), default="GOOD") # GOOD, POOR, MANUAL_VERIFICATION_REQUIRED
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="images")
    ocr_results = relationship("OCRResult", back_populates="inspection_image", cascade="all, delete-orphan")

class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, index=True)
    inspection_image_id = Column(Integer, ForeignKey("inspection_images.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(1000), nullable=False)
    confidence = Column(Float, default=1.0)
    bounding_box = Column(JSON) # [x, y, w, h] as percentages
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection_image = relationship("InspectionImage", back_populates="ocr_results")

class ExtractedDeclaration(Base):
    __tablename__ = "extracted_declarations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(50), nullable=False) # e.g. net_quantity, mrp
    value = Column(String(500))
    confidence = Column(Float, default=1.0)
    source_image_id = Column(Integer, ForeignKey("inspection_images.id", ondelete="SET NULL"), nullable=True)
    bounding_box = Column(JSON) # [x, y, w, h]
    extraction_method = Column(String(50), default="regex")
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="declarations")

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. RULE_MRP_ taxes
    title = Column(String(150), nullable=False)
    description = Column(String(500))
    category = Column(String(50), index=True) # Food, Cosmetics, General
    requirement_type = Column(String(50)) # e.g. presence, font_size, format
    field = Column(String(50)) # e.g. mrp, net_quantity
    validation_type = Column(String(50)) # e.g. regex, presence, math
    parameters = Column(JSON) # Configurable regex list, thresholds
    status = Column(String(20), default="Active") # Active, Inactive
    version = Column(String(20), default="1.0")
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(20), nullable=False)
    status = Column(String(20), default="Active")
    effective_from = Column(String(20)) # MFD date stamp
    effective_to = Column(String(20))
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    rule_version = Column(String(20))
    field = Column(String(50))
    status = Column(String(30), default="REVIEW") # PASS, FAIL, REVIEW, NOT_APPLICABLE
    confidence = Column(Float, default=1.0)
    message = Column(String(500))
    measured_font_height_mm = Column(Float, nullable=True)
    required_font_height_mm = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="compliance_checks")
    rule = relationship("Rule")

    @property
    def rule_code(self) -> str:
        return self.rule.rule_code if self.rule else "N/A"

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    violation_type = Column(String(100), index=True, nullable=False) # e.g. Missing Consumer Care
    description = Column(String(500))
    severity = Column(String(20), default="MEDIUM") # HIGH, MEDIUM, LOW
    confidence = Column(Float, default=1.0)
    status = Column(String(30), default="OPEN", index=True) # OPEN, UNDER_REVIEW, CONFIRMED, DISMISSED, CLOSED
    officer_comment = Column(String(550))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="violations")
    rule = relationship("Rule")
    evidence = relationship("ViolationEvidence", back_populates="violation", cascade="all, delete-orphan")

class ViolationEvidence(Base):
    __tablename__ = "violation_evidence"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id", ondelete="CASCADE"), nullable=False)
    original_image_path = Column(String(255), nullable=False)
    annotated_image_path = Column(String(255))
    cropped_image_path = Column(String(255))
    bounding_box = Column(JSON) # BBox coordinates of infraction
    ocr_text = Column(String(500))
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    violation = relationship("Violation", back_populates="evidence")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    generated_by_id = Column(Integer, ForeignKey("users.id"))
    storage_path = Column(String(255), nullable=False)
    rule_version_used = Column(String(30))
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="reports")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_identity = Column(String(100), nullable=False) # Rajesh Kumar (LMI-88902)
    action = Column(String(50), index=True, nullable=False) # LOGIN, UPLOAD_IMAGE, etc.
    entity_type = Column(String(50)) # e.g. inspection, rule
    entity_id = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    action_metadata = Column(JSON) # Additional context, changed parameters
    ip_address = Column(String(50))

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_role = Column(String(50), index=True) # e.g. SUPERVISOR
    title = Column(String(150), nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class InspectionComment(Base):
    __tablename__ = "inspection_comments"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    inspection = relationship("Inspection", back_populates="comments")
