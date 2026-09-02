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

def test_commodity_category_food_perishable():
    rules = [
        Rule(id=1, rule_code="R1", title="MRP check", field="mrp", status="Active")
    ]
    # Food item missing best before date
    decls_no_expiry = [
        ExtractedDeclaration(field_name="mrp", value="MRP Rs 50.00 (incl. of all taxes)", confidence=0.95)
    ]
    res = rule_engine.evaluate_rules(rules, decls_no_expiry, commodity_category="FOOD_PERISHABLE")
    food_check = next((c for c in res if c["rule_code"] == "RULE_FOOD_EXPIRY_010"), None)
    assert food_check is not None
    assert food_check["status"] == "FAIL"

    # Food item with best before date
    decls_with_expiry = [
        ExtractedDeclaration(field_name="mrp", value="MRP Rs 50.00 (incl. of all taxes)", confidence=0.95),
        ExtractedDeclaration(field_name="best_before", value="Best Before 6 months from packaging", confidence=0.98)
    ]
    res2 = rule_engine.evaluate_rules(rules, decls_with_expiry, commodity_category="FOOD_PERISHABLE")
    food_check2 = next((c for c in res2 if c["rule_code"] == "RULE_FOOD_EXPIRY_010"), None)
    assert food_check2 is not None
    assert food_check2["status"] == "PASS"

def test_rule_26_small_package_exemption():
    rules = [
        Rule(id=1, rule_code="RULE_QTY_003", title="Qty Check", field="net_quantity", status="Active")
    ]
    # 5g sachet - small pack exempt under Rule 26 (<10g)
    decls = [
        ExtractedDeclaration(field_name="net_quantity", value="5 g", confidence=0.95, bounding_box=[10, 10, 50, 0.005]) # tiny font
    ]
    res = rule_engine.evaluate_rules(rules, decls, pdp_area_cm2=450.0) # Even on large area, exemption applies
    assert res[0]["status"] == "PASS"
    assert "Exempt under Rule 26" in res[0]["message"]

def test_font_calibration_vernier_override():
    rules = [
        Rule(id=1, rule_code="RULE_QTY_003", title="Qty Check", field="net_quantity", status="Active")
    ]
    decls = [
        ExtractedDeclaration(field_name="net_quantity", value="500 g", confidence=0.95, bounding_box=[10, 10, 50, 0.005]) # optical is small
    ]
    # Officer measures with digital vernier caliper: 4.5 mm (above required 4.0 mm for 450 cm2)
    res = rule_engine.evaluate_rules(rules, decls, pdp_area_cm2=450.0, caliper_override_mm=4.5)
    assert res[0]["status"] == "PASS"
    assert res[0]["measured_font_height_mm"] == 4.5
