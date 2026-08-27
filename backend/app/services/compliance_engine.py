from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Inspection, Rule, ComplianceCheck, Violation, ViolationEvidence, AuditLog
from app.services.rule_engine import rule_engine

class ComplianceEngine:
    def run_compliance_check(self, db: Session, inspection_id: str) -> Inspection:
        """
        Executes rules engine against inspection declarations and logs violations.
        """
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            raise ValueError(f"Inspection {inspection_id} not found.")

        # Clear existing checks for this run
        db.query(ComplianceCheck).filter(ComplianceCheck.inspection_id == inspection_id).delete()
        db.query(Violation).filter(Violation.inspection_id == inspection_id).delete()

        # Query all active rules
        rules = db.query(Rule).filter(Rule.status == "Active").all()
        
        # Evaluate using rule engine
        results = rule_engine.evaluate_rules(rules, inspection.declarations, inspection.product)

        # Store Compliance Checks & find potential violations
        has_fail = False
        has_review = False
        violations_count = 0
        
        for res in results:
            check = ComplianceCheck(
                inspection_id=inspection_id,
                rule_id=res["rule_id"],
                rule_version="1.0",
                field=res["field"],
                status=res["status"],
                confidence=res["confidence"],
                message=res["message"]
            )
            db.add(check)
            
            if res["status"] in ["FAIL", "REVIEW"]:
                if res["status"] == "FAIL":
                    has_fail = True
                    severity = "HIGH"
                else:
                    has_review = True
                    severity = "MEDIUM"
                
                # Fetch declarations to map evidence bounding box
                linked_decl = next((d for d in inspection.declarations if d.field_name == res["field"]), None)
                
                violation = Violation(
                    inspection_id=inspection_id,
                    rule_id=res["rule_id"],
                    violation_type=f"Non-compliant {res['field'].replace('_', ' ').title()}",
                    description=res["message"],
                    severity=severity,
                    confidence=res["confidence"],
                    status="OPEN"
                )
                db.add(violation)
                db.flush() # Flush to get violation.id
                violations_count += 1
                
                # Create mock or real evidence
                original_img = inspection.images[0].storage_path if inspection.images else "uploads/default.png"
                evidence = ViolationEvidence(
                    violation_id=violation.id,
                    original_image_path=original_img,
                    annotated_image_path=original_img,
                    cropped_image_path=original_img,
                    bounding_box=linked_decl.bounding_box if linked_decl else [0, 0, 100, 100],
                    ocr_text=linked_decl.value if linked_decl else None,
                    confidence=res["confidence"]
                )
                db.add(evidence)

        # Determine overall status
        if has_fail:
            overall_status = "POTENTIAL_NON_COMPLIANCE"
        elif has_review:
            overall_status = "MANUAL_REVIEW"
        else:
            overall_status = "COMPLIANT"

        # Update inspection
        inspection.overall_status = overall_status
        inspection.violationsCount = violations_count # Match model field spelling or mapping
        
        # Calculate overall confidence
        confs = [d.confidence for d in inspection.declarations]
        avg_conf = round(sum(confs) / len(confs), 2) if confs else 0.0
        inspection.overall_confidence = avg_conf
        inspection.ocr_confidence = avg_conf
        inspection.detection_confidence = avg_conf

        # Log system action
        audit = AuditLog(
            user_identity="AI System Engine",
            action="COMPLIANCE_CHECKED",
            entity_type="inspection",
            entity_id=inspection_id,
            timestamp=datetime.utcnow(),
            action_metadata={"overall_status": overall_status, "violations_flagged": violations_count},
            ip_address="localhost"
        )
        db.add(audit)
        
        db.commit()
        db.refresh(inspection)
        return inspection

compliance_engine = ComplianceEngine()
