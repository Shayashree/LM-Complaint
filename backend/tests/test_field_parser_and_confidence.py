import pytest
from app.services.field_parser import field_parser
from app.services.confidence_engine import confidence_engine

def test_mrp_parsing_and_taxes():
    # Test valid MRP with taxes
    res1 = field_parser.parse_mrp("MRP Rs 249.00 (incl. of all taxes)")
    assert res1["is_valid_format"] is True
    assert res1["normalized_value"]["amount"] == 249.0
    assert res1["normalized_value"]["inclusive_of_taxes"] is True
    assert res1["status"] == "VERIFIED"

    # Test MRP lacking tax phrase -> REQUIRES_MANUAL_REVIEW under Rule 6(1)(e)
    res2 = field_parser.parse_mrp("MRP Rs 140.00")
    assert res2["is_valid_format"] is True
    assert res2["status"] == "REQUIRES_MANUAL_REVIEW"

def test_net_quantity_normalization():
    # 0.5 kg -> 500 g
    q1 = field_parser.parse_net_quantity("Net Wt. 0.5 kg")
    assert q1["is_valid_format"] is True
    assert q1["normalized_value"]["value"] == 500.0
    assert q1["normalized_value"]["unit"] == "g"

    # 1 kg -> 1000 g
    q2 = field_parser.parse_net_quantity("Net Qty: 1 kg")
    assert q2["normalized_value"]["value"] == 1000.0
    assert q2["normalized_value"]["unit"] == "g"

    # 1000 ml -> 1 L
    q3 = field_parser.parse_net_quantity("Net Volume: 1000 ml")
    assert q3["normalized_value"]["value"] == 1.0
    assert q3["normalized_value"]["unit"] == "L"

    # Nutrition facts exclusion
    q4 = field_parser.parse_net_quantity("Carbohydrate: 7g per serve")
    assert q4["status"] == "REQUIRES_MANUAL_REVIEW"

def test_date_parsing():
    d1 = field_parser.parse_date("MFD 05/2026")
    assert d1["is_valid_format"] is True
    assert d1["normalized_value"]["month"] == "05"
    assert d1["normalized_value"]["year"] == 2026

def test_country_of_origin_territory_stripping():
    # Should strip 'For sale in India, Nepal' and resolve to India
    c1 = field_parser.parse_country_of_origin("Made in India. For sale in India, Nepal, and Bhutan only.")
    assert c1["normalized_value"]["country"] == "India"

def test_confidence_engine_conflict_and_three_state():
    # Simulating conflicting OCR and AI
    parsed = field_parser.parse_mrp("MRP Rs 249.00 (incl. of all taxes)")
    evidence = confidence_engine.compute_declaration_evidence(
        field="mrp",
        parsed_result=parsed,
        image_quality_meta={"quality_score": 0.9},
        spatial_grounding_meta={"bbox": [50, 60, 40, 10], "confidence": 0.95},
        ocr_consensus_meta={"confidence": 0.95, "conflict_detected": False},
        ai_verification_meta={"verification_status": "REQUIRES_MANUAL_REVIEW", "reason": "OCR and AI disagree"}
    )
    assert evidence["status"] == "REQUIRES_MANUAL_REVIEW"
    assert any("disagree" in r for r in evidence["review_reasons"])

    # Test three-state verdict
    verdict1 = confidence_engine.compute_three_state_verdict(
        compliance_checks=[{"status": "PASS"}, {"status": "PASS"}],
        declarations=[{"status": "VERIFIED"}, {"status": "VERIFIED"}]
    )
    assert verdict1["verdict"] == "VERIFIED_COMPLIANT"

    verdict2 = confidence_engine.compute_three_state_verdict(
        compliance_checks=[{"status": "FAIL"}],
        declarations=[{"status": "VERIFIED"}]
    )
    assert verdict2["verdict"] == "VERIFIED_NON_COMPLIANT"

    verdict3 = confidence_engine.compute_three_state_verdict(
        compliance_checks=[{"status": "PASS"}],
        declarations=[{"status": "REQUIRES_MANUAL_REVIEW"}]
    )
    assert verdict3["verdict"] == "MANUAL_REVIEW_REQUIRED"
