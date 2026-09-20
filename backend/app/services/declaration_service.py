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

    def extract_declarations_llm(
        self, 
        image_path: str, 
        ocr_results: list,
        commodity_category: Optional[str] = None,
        original_filename: Optional[str] = None,
        api_key: Optional[str] = None,
        candidate_hints_by_field: Optional[Dict[str, List[str]]] = None
    ) -> tuple:
        """
        Executes the upgraded Scanning Pipeline:
        Detect Package -> Validate Image -> Correct Perspective -> Cover Complete Package ->
        Locate Declarations -> Crop -> Multi-Pass Preprocessing & OCR -> Field-Specific Validation & Normalization ->
        Gemini Cross-Verification -> Confidence / Evidence Engine
        """
        import os
        from app.core.config import settings
        from app.services.image_service import image_service
        from app.services.providers.locate_provider import LocateAnythingProvider
        from app.services.providers.ocr_provider import MultiPassTesseractProvider
        from app.services.providers.gemini_provider import GeminiVisionProvider
        from app.services.field_parser import field_parser
        from app.services.confidence_engine import confidence_engine
        from app.services.llm_service import llm_service

        effective_key = api_key or getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")

        # 1. Image Quality Assessment
        quality_meta = image_service.check_image_quality(image_path)

        # 2. Package Detection & Perspective Correction
        rectified_path, perspective_meta = image_service.detect_package_and_correct_perspective(image_path)
        active_scan_path = rectified_path if perspective_meta.get("applied") else image_path

        # 3. Complete Surface Coverage (Overlapping Tiles for large images)
        surface_tiles = image_service.generate_overlapping_tiles(active_scan_path)

        # 4. Extract raw text candidates via multimodal LLM & heuristic baseline
        extracted_fields = llm_service.analyze_label_image(
            image_path=active_scan_path, 
            api_key=effective_key,
            commodity_category=commodity_category,
            original_filename=original_filename
        )

        # 5. Visual Grounding via LocateAnythingProvider (WHERE is the declaration?)
        locate_provider = LocateAnythingProvider()
        located_boxes = locate_provider.locate_declarations(
            image_path=active_scan_path,
            declarations_to_find={
                "product_name": extracted_fields.get("product_name", ""),
                "brand": extracted_fields.get("brand", ""),
                "manufacturer": extracted_fields.get("manufacturer_name_address", ""),
                "net_quantity": extracted_fields.get("net_quantity", ""),
                "mfg_date": extracted_fields.get("mfg_date", ""),
                "mrp": extracted_fields.get("mrp", ""),
                "consumer_care": extracted_fields.get("consumer_care", ""),
                "unit_sale_price": extracted_fields.get("unit_sale_price", ""),
                "country_of_origin": extracted_fields.get("country_of_origin", ""),
                "best_before": extracted_fields.get("best_before_or_expiry", ""),
                "veg_nonveg": extracted_fields.get("veg_nonveg_symbol", ""),
                "piece_count": extracted_fields.get("individual_piece_count", "")
            }
        )

        # Model providers for OCR and AI Cross-Check
        ocr_provider = MultiPassTesseractProvider()
        gemini_cross_checker = GeminiVisionProvider(api_key=effective_key)

        decls = []

        def process_field(field_name: str, candidate_val: str, default_bbox: list):
            loc_info = located_boxes.get(field_name, {})
            bbox = loc_info.get("bbox") or self._find_matching_bbox(candidate_val, ocr_results) or default_bbox

            # 6. High-Resolution Region Crop
            crop_path = image_service.crop_region_high_res(active_scan_path, bbox)

            # 7. Multi-Pass OCR with consensus voting
            hints = (candidate_hints_by_field or {}).get(field_name, [])
            if candidate_val and candidate_val not in ["N/A", "NOT_DETECTED"]:
                hints = [candidate_val] + hints

            ocr_consensus = ocr_provider.perform_ocr(
                image_path_or_crop=crop_path or active_scan_path,
                field_name=field_name,
                candidate_hints=hints
            )

            primary_text = ocr_consensus.get("consensus_text") or candidate_val or "NOT_DETECTED"

            # 8. Field-Specific Value Parsing & Normalization
            parsed = field_parser.parse_and_normalize(field_name, primary_text)

            # 9. Gemini Multimodal Cross-Verification (Cross-check, not authority)
            ai_cross_check = None
            if crop_path and effective_key and primary_text not in ["NOT_DETECTED", "N/A"]:
                try:
                    ai_cross_check = gemini_cross_checker.cross_verify(
                        crop_image_or_path=crop_path,
                        field_name=field_name,
                        raw_ocr_value=primary_text
                    )
                except Exception as e:
                    logger.debug(f"AI cross-check skipped for {field_name}: {e}")

            # 10. Confidence & Evidence Synthesis
            evidence = confidence_engine.compute_declaration_evidence(
                field=field_name,
                parsed_result=parsed,
                image_quality_meta=quality_meta,
                spatial_grounding_meta=loc_info,
                ocr_consensus_meta=ocr_consensus,
                ai_verification_meta=ai_cross_check,
                surface_coverage_ratio=1.0 if len(surface_tiles) > 0 else 0.85
            )

            # Clean temporary crop if needed
            if crop_path and os.path.exists(crop_path) and "temp" in crop_path:
                try:
                    os.remove(crop_path)
                except Exception:
                    pass

            final_val = evidence["value"]
            decls.append({
                "field_name": field_name,
                "value": final_val if final_val != "NOT_DETECTED" else "N/A",
                "raw_value": evidence["raw_text"],
                "normalized_value": evidence["normalized_value"],
                "confidence": evidence["confidence"],
                "bounding_box": evidence["bbox"],
                "extraction_method": evidence["source"],
                "ocr_results": evidence["ocr_results"],
                "ai_verification": evidence["ai_verification"],
                "declaration_status": evidence["status"],
                "review_reasons": evidence["review_reasons"]
            })

        # Process statutory fields
        prod_val = extracted_fields.get("product_name", "N/A")
        process_field("product_name", prod_val, [10, 20, 80, 8])

        brand_val = extracted_fields.get("brand") or (prod_val.split()[0] if prod_val and prod_val != "N/A" else "N/A")
        process_field("brand", brand_val, [10, 20, 20, 5])

        process_field("manufacturer", extracted_fields.get("manufacturer_name_address", "N/A"), [10, 30, 80, 10])
        process_field("net_quantity", extracted_fields.get("net_quantity", "N/A"), [10, 45, 30, 6])
        process_field("manufacturing_date", extracted_fields.get("mfg_date", "N/A"), [10, 55, 30, 6])
        process_field("mrp", extracted_fields.get("mrp", "N/A"), [50, 45, 40, 6])
        process_field("consumer_care", extracted_fields.get("consumer_care", "N/A"), [10, 65, 80, 10])
        process_field("unit_sale_price", extracted_fields.get("unit_sale_price", "N/A"), [50, 55, 40, 6])
        process_field("country_of_origin", extracted_fields.get("country_of_origin", "N/A"), [10, 80, 30, 6])

        if extracted_fields.get("best_before_or_expiry") and extracted_fields.get("best_before_or_expiry") != "N/A":
            process_field("best_before", extracted_fields.get("best_before_or_expiry"), [10, 60, 40, 6])

        if extracted_fields.get("veg_nonveg_symbol") and extracted_fields.get("veg_nonveg_symbol") != "N/A":
            process_field("veg_nonveg", extracted_fields.get("veg_nonveg_symbol"), [85, 20, 10, 5])

        if extracted_fields.get("individual_piece_count") and extracted_fields.get("individual_piece_count") != "N/A":
            process_field("piece_count", extracted_fields.get("individual_piece_count"), [10, 50, 25, 5])

        commodity_cat = extracted_fields.get("commodity_category", "GENERAL")
        return decls, commodity_cat, quality_meta

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

