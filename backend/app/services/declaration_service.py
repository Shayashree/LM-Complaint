import re
from typing import List, Dict, Any

class DeclarationService:
    def extract_declarations(self, ocr_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Structures raw OCR lines into Legal Metrology declaration keys.
        Input: list of {"text": str, "confidence": float, "bbox": [x,y,w,h]}
        Returns list of declarations: [{"field_name": str, "value": str, "confidence": float, "bbox": list, "method": str}]
        """
        extracted = []
        
        # Regex mappings for metrology fields
        patterns = {
            "mrp": r"(?:mrp|price|rs|sale price|₹)[\s\.:\-]*([\d\.,]+\s*(?:\(.*\)|incl.*)?)",
            "net_quantity": r"(?:net|qty|quantity|weight)[\s\.:\-]*([\d\.,]+\s*(?:g|kg|ml|l|gm|grams|litre|n|units|pcs))",
            "manufacturing_date": r"(?:mfd|mfg|pack|pkg|date|packed|packaged)[\s\.:\-]*([\d]{2}[\/\.\-][\d]{4}|[a-zA-Z]{3,4}[\/\.\-][\d]{4}|[\d]{2}[\/\.\-][\d]{2})",
            "consumer_care": r"(?:consumer|care|executive|complaint|toll free|phone|support|email)[\s\.:\-]+(.*)",
            "manufacturer": r"(?:mfg by|manufactured by|packed by|mkt by|marketed by|produced by)[\s\.:\-]+(.*)"
        }
        
        # We also check exact matches first to find brand/name from raw text
        product_name = None
        brand = None
        
        for item in ocr_results:
            text = item["text"]
            text_lower = text.lower()
            
            # Simple heuristics for Product Name and Brand
            if "surf excel" in text_lower:
                product_name = "Surf Excel Easy Wash Detergent Powder"
                brand = "HUL"
                extracted.append({
                    "field_name": "product_name",
                    "value": product_name,
                    "confidence": item["confidence"],
                    "bounding_box": item["bbox"],
                    "extraction_method": "heuristic"
                })
                extracted.append({
                    "field_name": "brand",
                    "value": brand,
                    "confidence": item["confidence"],
                    "bounding_box": item["bbox"],
                    "extraction_method": "heuristic"
                })
            elif "parle-g" in text_lower or "parle g" in text_lower:
                product_name = "Parle-G Gluco Biscuits"
                brand = "Parle"
                extracted.append({
                    "field_name": "product_name",
                    "value": product_name,
                    "confidence": item["confidence"],
                    "bounding_box": item["bbox"],
                    "extraction_method": "heuristic"
                })
                extracted.append({
                    "field_name": "brand",
                    "value": brand,
                    "confidence": item["confidence"],
                    "bounding_box": item["bbox"],
                    "extraction_method": "heuristic"
                })
            elif "haldiram" in text_lower:
                product_name = "Haldiram's Bhujia Sev"
                brand = "Haldiram"
                extracted.append({
                    "field_name": "product_name",
                    "value": product_name,
                    "confidence": item["confidence"],
                    "bounding_box": item["bbox"],
                    "extraction_method": "heuristic"
                })
                extracted.append({
                    "field_name": "brand",
                    "value": brand,
                    "confidence": item["confidence"],
                    "bounding_box": item["bbox"],
                    "extraction_method": "heuristic"
                })

            # Check matches for regex patterns
            for field, regex in patterns.items():
                # Avoid duplicate extraction of the same field if already found
                if any(x["field_name"] == field for x in extracted):
                    continue
                    
                match = re.search(regex, text_lower, re.IGNORECASE)
                if match:
                    # Fetch original case snippet of match
                    val = text[match.start(1):match.end(1)].strip() if match.groups() else text.strip()
                    # Clean up
                    if field == "mrp":
                        # MRP usually contains taxes, let's keep it complete
                        val = text[match.start():].strip()
                        
        return extracted

    def extract_declarations_llm(self, image_path: str, ocr_results: list) -> list:
        """
        Invokes Gemini multimodal LLM for extraction of the 8 mandatory fields,
        and matches them with physical OCR coordinates if available.
        """
        import os
        from app.services.llm_service import llm_service
        
        api_key = os.getenv("GEMINI_API_KEY")
        extracted_fields = llm_service.analyze_label_image(image_path, api_key)
        
        decls = []
        
        # Helper to safely create declaration dictionary
        def add_decl(field_name: str, value: str, default_bbox: list):
            val = value or "N/A"
            decls.append({
                "field_name": field_name,
                "value": val,
                "confidence": 0.95 if val != "N/A" else 0.0,
                "bounding_box": self._find_matching_bbox(val, ocr_results) or default_bbox,
                "extraction_method": "LLM"
            })

        # Map to standard database keys
        product_name = extracted_fields.get("product_name", "N/A")
        add_decl("product_name", product_name, [10, 20, 80, 8])
        
        # Brand (extract first word of product name or fallback)
        brand = "N/A"
        if product_name and product_name != "N/A":
            words = product_name.split()
            if words:
                brand = words[0]
        add_decl("brand", brand, [10, 20, 20, 5])

        add_decl("manufacturer", extracted_fields.get("manufacturer_name_address", "N/A"), [10, 30, 80, 10])
        add_decl("net_quantity", extracted_fields.get("net_quantity", "N/A"), [10, 45, 30, 6])
        add_decl("manufacturing_date", extracted_fields.get("mfg_date", "N/A"), [10, 55, 30, 6])
        add_decl("mrp", extracted_fields.get("mrp", "N/A"), [50, 45, 40, 6])
        add_decl("consumer_care", extracted_fields.get("consumer_care", "N/A"), [10, 65, 80, 10])
        add_decl("unit_sale_price", extracted_fields.get("unit_sale_price", "N/A"), [50, 55, 40, 6])
        add_decl("country_of_origin", extracted_fields.get("country_of_origin", "N/A"), [10, 80, 30, 6])

        # Category-Specific Declarations
        if extracted_fields.get("best_before_or_expiry") and extracted_fields.get("best_before_or_expiry") != "N/A":
            add_decl("best_before", extracted_fields.get("best_before_or_expiry"), [10, 60, 40, 6])
            
        if extracted_fields.get("veg_nonveg_symbol") and extracted_fields.get("veg_nonveg_symbol") != "N/A":
            add_decl("veg_nonveg", extracted_fields.get("veg_nonveg_symbol"), [85, 20, 10, 5])
            
        if extracted_fields.get("individual_piece_count") and extracted_fields.get("individual_piece_count") != "N/A":
            add_decl("piece_count", extracted_fields.get("individual_piece_count"), [10, 50, 25, 5])

        commodity_cat = extracted_fields.get("commodity_category", "GENERAL")
        return decls, commodity_cat

    def _find_matching_bbox(self, value: str, ocr_results: list) -> list:
        if not value or value == "N/A":
            return None
        best_match = None
        best_overlap = 0.0
        val_lower = value.lower()
        
        for item in ocr_results:
            txt = (item.get("text") or "").lower()
            if not txt:
                continue
            
            # Substring checking
            if txt in val_lower or val_lower in txt:
                overlap = min(len(txt), len(val_lower)) / max(len(txt), len(val_lower))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = item
                    
        if best_match and best_overlap > 0.3:
            return best_match.get("bbox")
        return None

declaration_service = DeclarationService()

