from app.models.models import Inspection, Product, Rule, ExtractedDeclaration, Violation, ComplianceCheck
from app.services.compliance_engine import compliance_engine

def test_run_compliance_check_compliant(db_session):
    db = db_session
    
    # 1. Create a product
    product = Product(product_name="Sample Biscuit", brand="Test", net_quantity="100 g", mrp="₹10 (incl. of taxes)")
    db.add(product)
    db.flush()
    
    # 2. Create Rules
    rule1 = Rule(rule_code="R1", title="MRP check", field="mrp", status="Active")
    rule2 = Rule(rule_code="R2", title="Qty Check", field="net_quantity", status="Active")
    db.add(rule1)
    db.add(rule2)
    db.flush()
    
    # 3. Create Inspection & Declarations
    inspection = Inspection(id="LM-TEST-01", product_id=product.id, inspector_id=1, date="2026-08-26", overall_status="MANUAL_REVIEW")
    db.add(inspection)
    db.flush()
    
    decl1 = ExtractedDeclaration(inspection_id="LM-TEST-01", field_name="mrp", value="MRP ₹10 (incl of taxes)", confidence=0.98)
    decl2 = ExtractedDeclaration(inspection_id="LM-TEST-01", field_name="net_quantity", value="100 g", confidence=0.95)
    db.add(decl1)
    db.add(decl2)
    db.commit()
    
    # 4. Execute check
    updated_ins = compliance_engine.run_compliance_check(db, "LM-TEST-01")
    
    assert updated_ins.overall_status == "COMPLIANT"
    assert updated_ins.violationsCount == 0
    
    # Assert checks were stored
    checks = db.query(ComplianceCheck).filter(ComplianceCheck.inspection_id == "LM-TEST-01").all()
    assert len(checks) == 2
    assert all(c.status == "PASS" for c in checks)

def test_run_compliance_check_non_compliant(db_session):
    db = db_session
    
    # 1. Create a product
    product = Product(product_name="Sample Detergent", brand="Test", net_quantity="1 kg", mrp="₹150")
    db.add(product)
    db.flush()
    
    # 2. Create Rules
    rule1 = Rule(rule_code="R1", title="MRP check", field="mrp", status="Active")
    rule2 = Rule(rule_code="R2", title="Qty Check", field="net_quantity", status="Active")
    db.add(rule1)
    db.add(rule2)
    db.flush()
    
    # 3. Create Inspection & Declarations (MRP missing taxes clause)
    inspection = Inspection(id="LM-TEST-02", product_id=product.id, inspector_id=1, date="2026-08-26", overall_status="MANUAL_REVIEW")
    db.add(inspection)
    db.flush()
    
    decl1 = ExtractedDeclaration(inspection_id="LM-TEST-02", field_name="mrp", value="MRP ₹150", confidence=0.98)
    decl2 = ExtractedDeclaration(inspection_id="LM-TEST-02", field_name="net_quantity", value="1 kg", confidence=0.95)
    db.add(decl1)
    db.add(decl2)
    db.commit()
    
    # 4. Execute check
    updated_ins = compliance_engine.run_compliance_check(db, "LM-TEST-02")
    
    # MRP check should fail/review taxes check, making overall status MANUAL_REVIEW or non-compliant
    assert updated_ins.overall_status == "MANUAL_REVIEW"
    assert updated_ins.violationsCount == 1
    
    # Assert violation is logged in DB
    violation = db.query(Violation).filter(Violation.inspection_id == "LM-TEST-02").first()
    assert violation is not None
    assert violation.severity == "MEDIUM"
    assert violation.status == "OPEN"
