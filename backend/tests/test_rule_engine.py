from app.models.models import Rule, ExtractedDeclaration
from app.services.rule_engine import rule_engine

def test_evaluate_rules_missing_field():
    rules = [
        Rule(id=1, rule_code="R1", title="MRP check", field="mrp", status="Active")
    ]
    declarations = []
    
    results = rule_engine.evaluate_rules(rules, declarations)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "not detected" in results[0]["message"]

def test_evaluate_rules_mrp_incl_taxes():
    rules = [
        Rule(id=1, rule_code="R1", title="MRP check", field="mrp", status="Active")
    ]
    declarations = [
        ExtractedDeclaration(field_name="mrp", value="MRP Rs 50.00 (incl. of all taxes)", confidence=0.95)
    ]
    
    results = rule_engine.evaluate_rules(rules, declarations)
    assert len(results) == 1
    assert results[0]["status"] == "PASS"

def test_evaluate_rules_mrp_missing_taxes():
    rules = [
        Rule(id=1, rule_code="R1", title="MRP check", field="mrp", status="Active")
    ]
    declarations = [
        ExtractedDeclaration(field_name="mrp", value="MRP Rs 140.00", confidence=0.95)
    ]
    
    results = rule_engine.evaluate_rules(rules, declarations)
    assert len(results) == 1
    assert results[0]["status"] == "REVIEW"
    assert "missing mandatory phrase" in results[0]["message"]

def test_evaluate_rules_net_quantity_invalid_units():
    rules = [
        Rule(id=1, rule_code="R2", title="Qty Check", field="net_quantity", status="Active")
    ]
    declarations = [
        ExtractedDeclaration(field_name="net_quantity", value="100 boxes", confidence=0.95)
    ]
    
    results = rule_engine.evaluate_rules(rules, declarations)
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "non-standard" in results[0]["message"]

def test_evaluate_rules_low_ocr_confidence():
    rules = [
        Rule(id=1, rule_code="R1", title="MRP check", field="mrp", status="Active")
    ]
    declarations = [
        ExtractedDeclaration(field_name="mrp", value="MRP Rs 50.00 (incl. of all taxes)", confidence=0.60)
    ]
    
    results = rule_engine.evaluate_rules(rules, declarations)
    assert len(results) == 1
    assert results[0]["status"] == "REVIEW"
    assert "low character confidence" in results[0]["message"]
