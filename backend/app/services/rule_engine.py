from typing import List, Dict, Any
import json
from app.models.models import Rule, ExtractedDeclaration

class RuleEngine:
    def estimate_font_height(self, bbox: Any, package_height_mm: float = 180.0) -> float:
        """
        Estimates the physical font height of a declaration in millimeters from its bounding box.
        """
        if not bbox:
            return 2.5 # reasonable fallback height in mm
            
        # Parse JSON string if bounding box is stored as a serialized string
        if isinstance(bbox, str):
            try:
                bbox = json.loads(bbox)
            except Exception:
                return 2.5
                
        if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
            return 2.5
            
        h_val = float(bbox[3])
        
        # Determine scale of bounding box height
        if h_val <= 0:
            return 2.5
        elif h_val <= 1.0:
            # normalized 0-1
            height_ratio = h_val
        elif h_val <= 100.0:
            # normalized 0-100 (percentage)
            height_ratio = h_val / 100.0
        else:
            # pixel value (assume standard label scanning height is 800px)
            height_ratio = h_val / 800.0
            
        estimated_mm = height_ratio * package_height_mm
        return round(estimated_mm, 2)

    def evaluate_rules(
        self, 
        rules: List[Rule], 
        declarations: List[ExtractedDeclaration],
        product: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Executes active compliance rules against extracted declarations,
        including presence, format, and font size compliance checks (Rule 13).
        """
        checks = []
        decl_map = {d.field_name: d for d in declarations}
        
        # Determine PDP Area and Package Height (Rule 13 defaults)
        pdp_area = 250.0       # sq cm (default medium package size)
        package_height = 180.0  # mm (default height)
        
        if product:
            prod_name = (product.product_name or "").lower()
            if "surf" in prod_name:
                pdp_area = 450.0
                package_height = 250.0
            elif "parle" in prod_name:
                pdp_area = 180.0
                package_height = 120.0
            elif "haldiram" in prod_name:
                pdp_area = 220.0
                package_height = 180.0
                
        for rule in rules:
            field = rule.field
            rule_code = rule.rule_code
            
            # 1. Check if the field is present when required
            if field not in decl_map:
                checks.append({
                    "rule_id": rule.id,
                    "rule_code": rule_code,
                    "field": field,
                    "status": "FAIL",
                    "confidence": 1.0,
                    "message": f"Mandatory declaration '{field}' was not detected on the packaging."
                })
                continue
                
            decl = decl_map[field]
            val = decl.value or ""
            val_lower = val.lower()
            
            # Set default pass state
            status = "PASS"
            msg = f"Mandatory declaration '{field}' detected: '{val}'."
            confidence = decl.confidence
            
            # 2. Check low OCR confidence
            if confidence < 0.75:
                status = "REVIEW"
                msg = f"Declaration '{field}' detected but with low character confidence ({int(confidence*100)}%). Verification required."
            
            # 3. Format validation
            elif field == "mrp":
                has_taxes = "tax" in val_lower or "incl" in val_lower
                if not has_taxes:
                    status = "REVIEW"
                    msg = "MRP declaration detected but missing mandatory phrase 'inclusive of all taxes'."
                    
            elif field == "net_quantity":
                has_units = any(u in val_lower for u in ["g", "kg", "ml", "l", "gm", "grams", "litre", "units", "pcs"])
                if not has_units:
                    status = "FAIL"
                    msg = f"Net quantity uses non-standard weight/measure unit: '{val}'."
                    
            elif field == "consumer_care":
                has_details = "@" in val_lower or "tel" in val_lower or "ph" in val_lower or "call" in val_lower or "write" in val_lower or "toll" in val_lower or "contact" in val_lower
                if not has_details:
                    status = "REVIEW"
                    msg = "Consumer care contact details are incomplete or contain parsing errors."
                    
            # 4. Font size validation (Rule 13 of Legal Metrology PC Rules, 2011)
            # Standard minimum heights of letters and numerals:
            if status == "PASS":
                actual_height = self.estimate_font_height(decl.bounding_box, package_height)
                
                # Minimum height rules
                if field == "net_quantity":
                    # Table I: Net Quantity minimum heights
                    if pdp_area <= 50:
                        min_height = 1.0
                    elif pdp_area <= 100:
                        min_height = 1.5
                    elif pdp_area <= 500:
                        min_height = 2.0
                    elif pdp_area <= 2000:
                        min_height = 4.0
                    else:
                        min_height = 6.0
                else:
                    # Table II: All other declarations (MRP, MFD, Address, Helpline)
                    if pdp_area <= 100:
                        min_height = 1.0
                    elif pdp_area <= 500:
                        min_height = 1.5
                    elif pdp_area <= 2000:
                        min_height = 2.0
                    else:
                        min_height = 3.0
                
                # Check font size compliance
                if actual_height < min_height:
                    status = "FAIL"
                    msg = f"Non-compliant font size: detected height is {actual_height} mm, which is below the minimum legal requirement of {min_height} mm under Legal Metrology Rule 13 (PDP area: {pdp_area} sq cm)."

            checks.append({
                "rule_id": rule.id,
                "rule_code": rule_code,
                "field": field,
                "status": status,
                "confidence": confidence,
                "message": msg
            })
            
        return checks

rule_engine = RuleEngine()
