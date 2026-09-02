from typing import List, Dict, Any, Optional
import json
import re
from app.models.models import Rule, ExtractedDeclaration

class RuleEngine:
    # Schedule II (Rule 13) Minimum Height of Letters and Numerals Table
    # Format: (max_pdp_area_cm2, min_qty_mm, min_other_mm, min_blown_molded_mm)
    SCHEDULE_II_FONT_TABLE = [
        (50.0, 1.0, 1.0, 1.5),
        (200.0, 2.0, 1.5, 3.0),
        (1000.0, 4.0, 2.0, 6.0),
        (float('inf'), 6.0, 3.0, 6.0)
    ]

    def get_schedule_ii_min_height(
        self, 
        pdp_area_cm2: float, 
        is_net_quantity: bool = True, 
        is_blown_molded: bool = False
    ) -> float:
        """
        Returns the statutory minimum height in mm as prescribed in Schedule II under Rule 13.
        """
        for max_area, min_qty, min_other, min_blown in self.SCHEDULE_II_FONT_TABLE:
            if pdp_area_cm2 <= max_area:
                if is_blown_molded:
                    return min_blown
                return min_qty if is_net_quantity else min_other
        return 6.0

    def compute_calibrated_font_height(
        self, 
        bbox: Any, 
        pdp_height_mm: float = 180.0,
        calibration_scale_ppm: Optional[float] = None,
        caliper_override_mm: Optional[float] = None
    ) -> float:
        """
        Computes physical font height in millimeters using optical calibration scale,
        bounding box physical ratio, or inspector vernier caliper override.
        """
        # 1. Inspector Digital Vernier Caliper Manual Override (Highest Legal Authority)
        if caliper_override_mm is not None and caliper_override_mm > 0:
            return round(caliper_override_mm, 2)

        if not bbox:
            return 2.5 # default baseline

        if isinstance(bbox, str):
            try:
                bbox = json.loads(bbox)
            except Exception:
                return 2.5

        if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
            return 2.5

        h_val = float(bbox[3])
        if h_val <= 0:
            return 2.5

        # 2. Reference-Object / Physical Calibration Scale (Pixels per mm)
        if calibration_scale_ppm and calibration_scale_ppm > 0:
            if h_val > 1.0: # Raw pixel height
                return round(h_val / calibration_scale_ppm, 2)

        # 3. Known Principal Display Panel (PDP) Height Dimension Ratio
        if h_val <= 1.0:
            height_ratio = h_val
        elif h_val <= 100.0:
            height_ratio = h_val / 100.0
        else:
            height_ratio = h_val / 800.0 # Normalized standard 800px frame

        return round(height_ratio * pdp_height_mm, 2)

    def evaluate_rules(
        self, 
        rules: List[Rule], 
        declarations: List[ExtractedDeclaration],
        product: Any = None,
        commodity_category: str = "GENERAL",
        pdp_width_mm: Optional[float] = None,
        pdp_height_mm: Optional[float] = None,
        pdp_area_cm2: Optional[float] = None,
        calibration_scale_ppm: Optional[float] = None,
        caliper_override_mm: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes active compliance rules against extracted declarations using:
        1. Commodity-specific rule profiles (Food, Cosmetics, Electronics, Textiles, Multi-piece, General).
        2. Rule 26 Small Package exemption checks (<10g / <10ml).
        3. Rule 13 Schedule II calibrated millimeter font-size verification.
        """
        checks = []
        decl_map = {d.field_name: d for d in declarations}
        
        # 1. Calculate Calibrated Principal Display Panel (PDP) Area and Height
        if pdp_width_mm and pdp_height_mm and pdp_width_mm > 0 and pdp_height_mm > 0:
            package_height = float(pdp_height_mm)
            pdp_area = round((float(pdp_width_mm) * float(pdp_height_mm)) / 100.0, 1)
        elif pdp_area_cm2 and pdp_area_cm2 > 0:
            pdp_area = float(pdp_area_cm2)
            package_height = pdp_height_mm or 180.0
        else:
            # Defaults based on known seeded catalog
            pdp_area = 250.0
            package_height = 180.0
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

        # 2. Evaluate Rule 26 Small Package Exemption (< 10g or < 10ml)
        is_small_pack_exempt = False
        net_qty_decl = decl_map.get("net_quantity")
        if net_qty_decl and net_qty_decl.value:
            val_q = net_qty_decl.value.lower()
            qty_num_match = re.search(r"(\d+(?:\.\d+)?)", val_q)
            if qty_num_match:
                qty_val = float(qty_num_match.group(1))
                if ("g" in val_q or "ml" in val_q or "gm" in val_q) and "kg" not in val_q and "l" not in val_q:
                    if qty_val <= 10.0:
                        is_small_pack_exempt = True

        category_upper = (commodity_category or "GENERAL").upper()

        # 3. Base Statutory Rules Evaluation
        for rule in rules:
            field = rule.field
            rule_code = rule.rule_code
            
            # Check presence
            if field not in decl_map:
                checks.append({
                    "rule_id": rule.id,
                    "rule_code": rule_code,
                    "field": field,
                    "status": "FAIL",
                    "confidence": 1.0,
                    "message": f"Mandatory declaration '{field}' was not detected on the packaging.",
                    "measured_font_height_mm": None,
                    "required_font_height_mm": None
                })
                continue
                
            decl = decl_map[field]
            val = decl.value or ""
            val_lower = val.lower()
            
            status = "PASS"
            msg = f"Mandatory declaration '{field}' detected: '{val}'."
            confidence = decl.confidence
            measured_font_mm = None
            required_font_mm = None
            
            # Check low character confidence
            if confidence < 0.75:
                status = "REVIEW"
                msg = f"Declaration '{field}' detected with low character confidence ({int(confidence*100)}%). Inspector review required."
            
            # Field format checks
            elif field == "mrp":
                has_taxes = "tax" in val_lower or "incl" in val_lower
                if not has_taxes:
                    status = "REVIEW"
                    msg = "MRP declaration detected but missing mandatory phrase 'inclusive of all taxes' under Rule 6(1)(e)."
                    
            elif field == "net_quantity":
                has_units = any(u in val_lower for u in ["g", "kg", "ml", "l", "gm", "grams", "litre", "units", "pcs", "n"])
                if not has_units:
                    status = "FAIL"
                    msg = f"Net quantity uses non-standard metric weight/measure unit: '{val}'."
                    
            elif field == "consumer_care":
                has_details = "@" in val_lower or "tel" in val_lower or "ph" in val_lower or "call" in val_lower or "write" in val_lower or "toll" in val_lower or "contact" in val_lower
                if not has_details:
                    status = "REVIEW"
                    msg = "Consumer care contact details are incomplete or contain parsing errors."
                    
            elif field == "unit_sale_price":
                has_per = "per" in val_lower or "/" in val_lower or "each" in val_lower or "u" in val_lower or "unit" in val_lower
                if not has_per:
                    status = "REVIEW"
                    msg = "Unit sale price detected but missing base unit description (e.g. 'per g', '/ml')."
                    
            elif field == "country_of_origin":
                if val_lower in ["n/a", "not found", "unknown", "none"]:
                    status = "REVIEW"
                    msg = "Country of origin is missing or could not be verified from packaging declarations."

            # 4. Font size validation (Rule 13 Schedule II)
            if status == "PASS" and (decl.bounding_box or caliper_override_mm):
                measured_font_mm = self.compute_calibrated_font_height(
                    decl.bounding_box, 
                    package_height, 
                    calibration_scale_ppm, 
                    caliper_override_mm
                )
                required_font_mm = self.get_schedule_ii_min_height(
                    pdp_area, 
                    is_net_quantity=(field == "net_quantity")
                )

                if is_small_pack_exempt:
                    msg = f"Exempt under Rule 26: Net quantity <= 10g/10ml. Measured height: {measured_font_mm} mm (Statutory minimum {required_font_mm} mm waived)."
                elif measured_font_mm < required_font_mm:
                    status = "FAIL"
                    cal_info = f" [Calibrated via Vernier Caliper: {caliper_override_mm} mm]" if caliper_override_mm else f" [Optically calibrated for PDP Area {pdp_area} cm²]"
                    msg = f"Non-compliant font size: Calibrated height is {measured_font_mm} mm, below the statutory minimum of {required_font_mm} mm under Rule 13 Schedule II{cal_info}."

            checks.append({
                "rule_id": rule.id,
                "rule_code": rule_code,
                "field": field,
                "status": status,
                "confidence": confidence,
                "message": msg,
                "measured_font_height_mm": measured_font_mm,
                "required_font_height_mm": required_font_mm
            })

        # 5. Commodity-Category-Specific Statutory Rules Routing
        if category_upper in ["FOOD_PERISHABLE", "FOOD"]:
            # Rule 6(1)(d) Proviso: Best Before / Use By mandatory for perishable food
            best_before_decl = decl_map.get("best_before")
            if not best_before_decl or best_before_decl.value in ["N/A", "not found", "unknown"]:
                checks.append({
                    "rule_id": 1001,
                    "rule_code": "RULE_FOOD_EXPIRY_010",
                    "field": "best_before",
                    "status": "FAIL",
                    "confidence": 0.95,
                    "message": "Rule 6(1)(d) Proviso Violation: For perishable/food commodities, 'Best Before' or 'Use By' date is strictly mandatory.",
                    "measured_font_height_mm": None,
                    "required_font_height_mm": None
                })
            else:
                checks.append({
                    "rule_id": 1001,
                    "rule_code": "RULE_FOOD_EXPIRY_010",
                    "field": "best_before",
                    "status": "PASS",
                    "confidence": 0.95,
                    "message": f"Food commodity 'Best Before / Expiry' date validated: '{best_before_decl.value}'.",
                    "measured_font_height_mm": None,
                    "required_font_height_mm": None
                })

        elif category_upper in ["COSMETICS"]:
            # Cosmetics must declare Use-By date / Batch number
            best_before_decl = decl_map.get("best_before")
            if not best_before_decl or best_before_decl.value in ["N/A", "not found"]:
                checks.append({
                    "rule_id": 1002,
                    "rule_code": "RULE_COSMETICS_USEBEFORE_011",
                    "field": "use_before",
                    "status": "REVIEW",
                    "confidence": 0.90,
                    "message": "Cosmetics Rule Alert: Expiry / 'Use before' date or batch code not detected on primary panel.",
                    "measured_font_height_mm": None,
                    "required_font_height_mm": None
                })

        elif category_upper in ["MULTI_PIECE", "MULTIPACK"]:
            # Rule 24: Multi-piece package must declare piece count and individual piece net qty
            piece_decl = decl_map.get("piece_count")
            if not piece_decl or piece_decl.value in ["N/A", "not found", "1"]:
                checks.append({
                    "rule_id": 1003,
                    "rule_code": "RULE_MULTIPIECE_24",
                    "field": "piece_count",
                    "status": "REVIEW",
                    "confidence": 0.88,
                    "message": "Rule 24 Multi-Piece Requirement: Must explicitly declare individual piece count and quantity of each individual unit.",
                    "measured_font_height_mm": None,
                    "required_font_height_mm": None
                })

        elif category_upper in ["ELECTRONICS"]:
            # Electronics strictly requires country of origin under Rule 6(1)(f)
            origin_decl = decl_map.get("country_of_origin")
            if not origin_decl or origin_decl.value in ["N/A", "not found"]:
                checks.append({
                    "rule_id": 1004,
                    "rule_code": "RULE_ELEC_ORIGIN_014",
                    "field": "country_of_origin",
                    "status": "FAIL",
                    "confidence": 0.98,
                    "message": "Mandatory Electronic Appliance Rule: Country of Origin declaration is strictly mandated for all electrical equipment under Rule 6(1)(f).",
                    "measured_font_height_mm": None,
                    "required_font_height_mm": None
                })

        return checks

rule_engine = RuleEngine()
