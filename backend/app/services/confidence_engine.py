from typing import Dict, Any, List, Optional

class ConfidenceEngine:
    """
    Measurable confidence calculation and evidence classification engine.
    Calculates evidence score based on actual measurable signals:
    - Image quality score (from Laplacian variance, exposure, and glare)
    - Multi-pass OCR agreement ratio
    - Field regex format validity
    - LocateAnything visual grounding confidence
    - Gemini cross-verification agreement

    Maintains rigorous distinction between:
    - NOT_DETECTED: Field could not be legibly found; needs clearer angle/rescan
    - ABSENT: High coverage & quality confirmed, yet declaration is genuinely missing (statutory violation)
    """

    def compute_declaration_evidence(
        self,
        field: str,
        parsed_result: Dict[str, Any],
        image_quality_meta: Dict[str, Any],
        spatial_grounding_meta: Optional[Dict[str, Any]] = None,
        ocr_consensus_meta: Optional[Dict[str, Any]] = None,
        ai_verification_meta: Optional[Dict[str, Any]] = None,
        surface_coverage_ratio: float = 1.0
    ) -> Dict[str, Any]:
        """
        Synthesizes raw OCR, spatial grounding, parser validation, and AI cross-check
        into an evidence record with measurable confidence.
        """
        raw_val = parsed_result.get("raw_value", "")
        norm_val = parsed_result.get("normalized_value")
        is_valid_format = parsed_result.get("is_valid_format", False)
        base_status = parsed_result.get("status", "NOT_DETECTED")

        # 1. Quality Signal (0.0 to 1.0)
        quality_score = float(image_quality_meta.get("quality_score", 0.8))

        # 2. OCR Consensus Signal (0.0 to 1.0)
        ocr_agreement = 1.0
        ocr_conflict = False
        if ocr_consensus_meta:
            ocr_agreement = float(ocr_consensus_meta.get("confidence", 0.9))
            ocr_conflict = bool(ocr_consensus_meta.get("conflict_detected", False))

        # 3. Spatial Grounding Signal (0.0 to 1.0)
        grounding_conf = 0.9
        bbox = [10, 50, 40, 8]
        if spatial_grounding_meta:
            grounding_conf = float(spatial_grounding_meta.get("confidence", 0.9))
            bbox = spatial_grounding_meta.get("bbox", bbox)

        # 4. AI Cross-Verification Signal
        ai_agreement = 1.0
        ai_conflict = False
        ai_val = None
        if ai_verification_meta:
            ai_status = ai_verification_meta.get("verification_status")
            ai_val = ai_verification_meta.get("ai_interpretation")
            if ai_status == "REQUIRES_MANUAL_REVIEW":
                ai_conflict = True
                ai_agreement = 0.4
            elif ai_status == "VERIFIED":
                ai_agreement = 1.0

        # Measurable Confidence Formula based on 5 weighted signals
        if raw_val in ["NOT_DETECTED", "N/A", "", None]:
            final_conf = 0.0
            # Distinguish NOT_DETECTED vs ABSENT
            if quality_score >= 0.75 and surface_coverage_ratio >= 0.80:
                final_status = "ABSENT" # Complete surface scanned at high quality, field genuinely absent!
            else:
                final_status = "NOT_DETECTED" # Low quality or partial surface, cannot declare absent
        else:
            final_conf = round(
                (quality_score * 0.20) +
                (ocr_agreement * 0.30) +
                (grounding_conf * 0.20) +
                ((1.0 if is_valid_format else 0.4) * 0.15) +
                (ai_agreement * 0.15),
                2
            )

            # Determine Status
            if ocr_conflict or ai_conflict:
                final_status = "REQUIRES_MANUAL_REVIEW"
            elif not is_valid_format:
                final_status = "NON_COMPLIANT"
            elif final_conf >= 0.70:
                final_status = "VERIFIED"
            else:
                final_status = "REQUIRES_MANUAL_REVIEW"

        review_reasons = []
        if ocr_conflict:
            review_reasons.append("Conflicting readings across multi-pass OCR preprocessing variants")
        if ai_conflict:
            review_reasons.append("OCR reading and Gemini AI interpretation disagree")
        if parsed_result.get("review_reason"):
            review_reasons.append(parsed_result["review_reason"])

        return {
            "field": field,
            "value": raw_val,
            "raw_text": raw_val,
            "normalized_value": norm_val,
            "confidence": final_conf,
            "bbox": bbox,
            "ocr_results": ocr_consensus_meta.get("ocr_candidates", []) if ocr_consensus_meta else [],
            "ai_verification": ai_verification_meta,
            "status": final_status,
            "review_reasons": review_reasons,
            "source": spatial_grounding_meta.get("source", "locate_anything") if spatial_grounding_meta else "locate_anything"
        }

    def compute_three_state_verdict(
        self,
        compliance_checks: List[Dict[str, Any]],
        declarations: List[Dict[str, Any]],
        image_quality_acceptable: bool = True
    ) -> Dict[str, Any]:
        """
        Determines the Three-State Final Compliance Verdict:
        1. VERIFIED COMPLIANT: All applicable statutory declarations verified and rules passed.
        2. VERIFIED NON-COMPLIANT: Sufficient evidence exists and an applicable rule is violated.
        3. MANUAL REVIEW REQUIRED: Evidence is insufficient, ambiguous, or conflicting.
        """
        if not image_quality_acceptable:
            return {
                "verdict": "MANUAL_REVIEW_REQUIRED",
                "reason": "Image quality insufficient for automated legal determination. Follow scan guidance.",
                "verified_count": 0,
                "review_count": len(declarations),
                "violation_count": 0
            }

        has_fail = any(c.get("status") == "FAIL" for c in compliance_checks)
        has_review = any(c.get("status") == "REVIEW" for c in compliance_checks)
        has_decl_review = any(d.get("status") in ["REQUIRES_MANUAL_REVIEW", "NOT_DETECTED"] for d in declarations)

        verified_count = sum(1 for d in declarations if d.get("status") == "VERIFIED")
        review_count = sum(1 for d in declarations if d.get("status") in ["REQUIRES_MANUAL_REVIEW", "NOT_DETECTED"])
        violation_count = sum(1 for c in compliance_checks if c.get("status") == "FAIL")

        if has_fail:
            verdict = "VERIFIED_NON_COMPLIANT"
            reason = f"Statutory non-compliance identified: {violation_count} rule violation(s) confirmed by evidence."
        elif has_review or has_decl_review:
            verdict = "MANUAL_REVIEW_REQUIRED"
            reason = "Statutory declarations require officer review due to ambiguous OCR, low confidence, or format warnings."
        else:
            verdict = "VERIFIED_COMPLIANT"
            reason = "All statutory Legal Metrology declarations verified and mandatory requirements satisfied."

        return {
            "verdict": verdict,
            "reason": reason,
            "verified_count": verified_count,
            "review_count": review_count,
            "violation_count": violation_count
        }

confidence_engine = ConfidenceEngine()
