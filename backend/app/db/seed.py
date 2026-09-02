from app.db.database import SessionLocal, Base, engine
from app.models.models import Role, User, Product, Rule, RuleVersion, Inspection, InspectionImage, ExtractedDeclaration, Violation, ViolationEvidence, AuditLog
from app.core.security import get_password_hash
from datetime import datetime

def seed_db():
    # Recreate tables (convenient fallback if Alembic isn't run first)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Role).count() > 0:
            print("Database already seeded. Skipping.")
            return

        print("Seeding roles and permissions...")
        roles = {
            "SUPER_ADMIN": Role(name="SUPER_ADMIN", description="Complete system administration", permissions=["*"]),
            "INSPECTOR": Role(name="INSPECTOR", description="Field scans and manual verification", permissions=["scan", "verify", "upload"]),
            "SUPERVISOR": Role(name="SUPERVISOR", description="Escalations and approvals", permissions=["approve", "verify", "view_all"]),
            "DEPT_ADMIN": Role(name="DEPT_ADMIN", description="Department Administrator - management views", permissions=["view_dashboard", "view_history"]),
            "RULE_ADMIN": Role(name="RULE_ADMIN", description="Manages regulatory thresholds", permissions=["create_rules", "amend_rules"]),
            "ANALYST": Role(name="ANALYST", description="Analytical views and reports exports", permissions=["view_analytics", "export"]),
            "AUDITOR": Role(name="AUDITOR", description="Read-only access to audit logs and records", permissions=["view_logs", "view_records"]),
            "CONSUMER": Role(name="CONSUMER", description="Public/Consumer access portal", permissions=["view_basic_compliance"])
        }
        for r in roles.values():
            db.add(r)
        db.flush()

        print("Seeding default user profiles...")
        users = [
            User(employee_id="LMI-00000", email="admin@example.com", name="Super Admin", hashed_password=get_password_hash("Password123")),
            User(employee_id="LMI-88902", email="inspector@example.com", name="Rajesh Kumar", hashed_password=get_password_hash("Password123"), department="Enforcement - Zone I"),
            User(employee_id="LMS-77102", email="supervisor@example.com", name="A. K. Shastri", hashed_password=get_password_hash("Password123"), department="Directorate of Legal Metrology"),
            User(employee_id="LMD-88092", email="deptadmin@example.com", name="Vikas Swarup", hashed_password=get_password_hash("Password123"), department="Enforcement HQ"),
            User(employee_id="LMA-44390", email="ruleadmin@example.com", name="Manoj Dwivedi", hashed_password=get_password_hash("Password123"), department="Rules & Policy Section"),
            User(employee_id="LMD-12903", email="analyst@example.com", name="Neha Goel", hashed_password=get_password_hash("Password123"), department="Data Operations"),
            User(employee_id="LMA-99021", email="auditor@example.com", name="Sanjay Swamy", hashed_password=get_password_hash("Password123"), department="Internal Audit Division"),
            User(employee_id="LMC-11029", email="consumer@example.com", name="Aravind Sharma", hashed_password=get_password_hash("Password123"), department="Public Portal User")
        ]
        
        # Link user roles
        users[0].roles.append(roles["SUPER_ADMIN"])
        users[1].roles.append(roles["INSPECTOR"])
        users[2].roles.append(roles["SUPERVISOR"])
        users[3].roles.append(roles["DEPT_ADMIN"])
        users[4].roles.append(roles["RULE_ADMIN"])
        users[5].roles.append(roles["ANALYST"])
        users[6].roles.append(roles["AUDITOR"])
        users[7].roles.append(roles["CONSUMER"])

        for u in users:
            db.add(u)
        db.flush()

        print("Seeding sample product SKUs...")
        products = [
            Product(
                product_name="Parle-G Gluco Biscuits", brand="Parle", category="Food",
                manufacturer="Parle Products Pvt. Ltd.", barcode="8901234567890",
                net_quantity="800 g", mrp="₹50.00 (inclusive of all taxes)",
                manufacturing_date="06/2026", consumer_care="Ph: 1800-22-7753, Email: customercare@parle.biz"
            ),
            Product(
                product_name="Surf Excel Easy Wash Detergent Powder", brand="HUL", category="Household",
                manufacturer="Hindustan Unilever Limited (HUL)", barcode="8901234567891",
                net_quantity="1 kg", mrp="₹140.00", # missing taxes clause
                manufacturing_date="05/2026", consumer_care="Not Detected"
            ),
            Product(
                product_name="Haldiram's Bhujia Sev", brand="Haldiram", category="Food",
                manufacturer="Haldiram Foods International Pvt. Ltd.", barcode="8901234567892",
                net_quantity="400 g", mrp="₹110.00 (inclusive of all taxes)",
                manufacturing_date="07/2026", consumer_care="support@haldirams.com"
            )
        ]
        for p in products:
            db.add(p)
        db.flush()

        print("Seeding Legal Metrology PC Rules database...")
        rules = [
            Rule(rule_code="RULE_NAME_001", title="Rule 6(1)(a) - Generic Commodity Name", description="Every package must declare the common or generic name of the commodity.", category="General", requirement_type="presence", field="product_name", validation_type="presence", status="Active", version="1.0", created_by_id=users[3].id),
            Rule(rule_code="RULE_MFG_002", title="Rule 6(1)(b) - Manufacturer Details", description="Must print name and address of the manufacturer/packer/importer.", category="General", requirement_type="presence", field="manufacturer", validation_type="presence", status="Active", version="1.0", created_by_id=users[3].id),
            Rule(rule_code="RULE_QTY_003", title="Rule 6(1)(c) - Declared Net Quantity", description="Must print net quantity in metric standard units.", category="General", requirement_type="presence", field="net_quantity", validation_type="presence", status="Active", version="1.0", created_by_id=users[3].id),
            Rule(rule_code="RULE_DATE_004", title="Rule 6(1)(d) - Manufacture Date", description="Month and Year of packing must be clearly legible.", category="General", requirement_type="presence", field="manufacturing_date", validation_type="presence", status="Active", version="1.0", created_by_id=users[3].id),
            Rule(rule_code="RULE_MRP_005", title="Rule 6(1)(e) - Maximum Retail Price (MRP)", description="Price must state 'incl. of all taxes'.", category="General", requirement_type="format", field="mrp", validation_type="regex", status="Active", version="1.0", created_by_id=users[3].id),
            Rule(rule_code="RULE_CARE_006", title="Rule 6(1)(da) - Consumer Helpline", description="Must list postal, email, and phone contact details.", category="General", requirement_type="presence", field="consumer_care", validation_type="presence", status="Active", version="1.0", created_by_id=users[3].id),
            Rule(rule_code="RULE_ORIGIN_007", title="Rule 6(1)(f) - Country of Origin", description="Must state the country of origin or manufacture for imported commodities.", category="General", requirement_type="presence", field="country_of_origin", validation_type="presence", status="Active", version="1.0", created_by_id=users[3].id),
            Rule(rule_code="RULE_UNIT_008", title="Rule 6(1)(g) - Unit Sale Price", description="Must declare the unit sale price in Rupees per gram, ml, or unit.", category="General", requirement_type="presence", field="unit_sale_price", validation_type="presence", status="Active", version="1.0", created_by_id=users[3].id),
            Rule(rule_code="RULE_FONT_009", title="Rule 13 - Font Size & Height", description="Mandatory declarations must satisfy minimum letter/numeral height based on PDP area.", category="General", requirement_type="format", field="net_quantity", validation_type="format", status="Active", version="1.0", created_by_id=users[3].id)
        ]
        for r in rules:
            db.add(r)
        db.flush()

        print("Seeding pre-packaged Inspections history...")
        # 1. Compliant Inspection (Parle-G)
        ins1 = Inspection(
            id="LM-2026-00121", product_id=products[0].id, inspector_id=users[1].id,
            date="2026-08-26", overall_status="COMPLIANT", image_quality="Excellent",
            ocr_confidence=98.0, detection_confidence=97.0, overall_confidence=97.5,
            officer_remarks="Verified compliant under Rule 7 standards.",
            verification_status="Verified", verified_by_id=users[1].id, verified_date=datetime.utcnow()
        )
        db.add(ins1)
        db.flush()
        
        img1 = InspectionImage(inspection_id=ins1.id, storage_path="uploads/scans/parleg_front.jpg", image_side="front", quality_score=0.98, readability_status="GOOD")
        db.add(img1)
        db.flush()

        decls1 = [
            ExtractedDeclaration(inspection_id=ins1.id, field_name="product_name", value="PARLE-G GLUCO BISCUITS", confidence=0.99, source_image_id=img1.id, bounding_box=[10, 35, 80, 15], extraction_method="heuristic"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="brand", value="Parle", confidence=0.99, source_image_id=img1.id, bounding_box=[10, 35, 80, 15], extraction_method="heuristic"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="net_quantity", value="800 g", confidence=0.98, source_image_id=img1.id, bounding_box=[10, 60, 35, 10], extraction_method="regex"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="mrp", value="MRP Rs 50.00 (incl. of all taxes)", confidence=0.97, source_image_id=img1.id, bounding_box=[50, 60, 42, 10], extraction_method="regex"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="manufacturer", value="Parle Products Pvt. Ltd., Mumbai - 400057", confidence=0.96, source_image_id=img1.id, bounding_box=[8, 73, 84, 11], extraction_method="regex"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="consumer_care", value="Ph: 1800-22-7753, email: customercare@parle.biz", confidence=0.98, source_image_id=img1.id, bounding_box=[8, 86, 84, 11], extraction_method="regex"),
            ExtractedDeclaration(inspection_id=ins1.id, field_name="manufacturing_date", value="06/2026", confidence=0.99, source_image_id=img1.id, bounding_box=[42, 51, 24, 7], extraction_method="regex")
        ]
        for d in decls1:
            db.add(d)

        # 2. Non-Compliant Inspection (Surf Excel)
        ins2 = Inspection(
            id="LM-2026-00122", product_id=products[1].id, inspector_id=users[1].id,
            date="2026-08-25", overall_status="POTENTIAL_NON_COMPLIANCE", image_quality="Good",
            ocr_confidence=94.0, detection_confidence=92.0, overall_confidence=93.0,
            officer_remarks="AI flagged missing consumer care and non-conforming MRP taxes clause. Confirmed.",
            verification_status="Verified", verified_by_id=users[1].id, verified_date=datetime.utcnow()
        )
        db.add(ins2)
        db.flush()

        img2 = InspectionImage(inspection_id=ins2.id, storage_path="uploads/scans/surfexcel_front.jpg", image_side="front", quality_score=0.88, readability_status="GOOD")
        db.add(img2)
        db.flush()

        decls2 = [
            ExtractedDeclaration(inspection_id=ins2.id, field_name="product_name", value="Surf Excel Easy Wash Detergent Powder", confidence=0.98, source_image_id=img2.id, bounding_box=[8, 12, 84, 16], extraction_method="heuristic"),
            ExtractedDeclaration(inspection_id=ins2.id, field_name="brand", value="HUL", confidence=0.98, source_image_id=img2.id, bounding_box=[8, 12, 84, 16], extraction_method="heuristic"),
            ExtractedDeclaration(inspection_id=ins2.id, field_name="net_quantity", value="1 kg", confidence=0.97, source_image_id=img2.id, bounding_box=[10, 80, 38, 10], extraction_method="regex"),
            ExtractedDeclaration(inspection_id=ins2.id, field_name="mrp", value="MRP Rs 140.00", confidence=0.95, source_image_id=img2.id, bounding_box=[50, 80, 42, 10], extraction_method="regex"),
            ExtractedDeclaration(inspection_id=ins2.id, field_name="manufacturer", value="Hindustan Unilever Limited, Mumbai - 400099", confidence=0.96, source_image_id=img2.id, bounding_box=[8, 62, 84, 12], extraction_method="regex"),
            ExtractedDeclaration(inspection_id=ins2.id, field_name="manufacturing_date", value="05/2026", confidence=0.93, source_image_id=img2.id, bounding_box=[12, 32, 28, 8], extraction_method="regex")
        ]
        for d in decls2:
            db.add(d)
        db.flush()

        # Add violations for Surf Excel
        v1 = Violation(inspection_id=ins2.id, rule_id=rules[5].id, violation_type="Missing Consumer Care Details", description="No consumer care helpline phone/email/address detected.", severity="HIGH", confidence=0.91, status="OPEN")
        v2 = Violation(inspection_id=ins2.id, rule_id=rules[4].id, violation_type="MRP Format Violation", description="MRP tag missing taxes statement.", severity="MEDIUM", confidence=0.95, status="OPEN")
        db.add(v1)
        db.add(v2)
        db.flush()

        ev1 = ViolationEvidence(violation_id=v1.id, original_image_path="uploads/scans/surfexcel_front.jpg", annotated_image_path="uploads/scans/surfexcel_front.jpg", cropped_image_path="uploads/scans/surfexcel_front.jpg", bounding_box=[8, 48, 84, 10], ocr_text="Not Detected", confidence=0.91)
        ev2 = ViolationEvidence(violation_id=v2.id, original_image_path="uploads/scans/surfexcel_front.jpg", annotated_image_path="uploads/scans/surfexcel_front.jpg", cropped_image_path="uploads/scans/surfexcel_front.jpg", bounding_box=[50, 80, 42, 10], ocr_text="MRP Rs 140.00", confidence=0.95)
        db.add(ev1)
        db.add(ev2)

        # Audit logs seeding
        db.add(AuditLog(user_identity="Rajesh Kumar (LMI-88902)", action="CREATE_INSPECTION", entity_type="inspection", entity_id=ins1.id, timestamp=datetime.utcnow()))
        db.add(AuditLog(user_identity="Rajesh Kumar (LMI-88902)", action="CREATE_INSPECTION", entity_type="inspection", entity_id=ins2.id, timestamp=datetime.utcnow()))

        db.commit()
        print("Database seeded successfully with all sample data.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
