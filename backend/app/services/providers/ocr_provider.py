import os
import re
import logging
from collections import Counter
from typing import Dict, Any, List, Optional, Union
import numpy as np
from app.services.providers.base import OCRProvider
from app.services.image_service import image_service

logger = logging.getLogger("MultiPassTesseractProvider")

PYTESSERACT_AVAILABLE = False
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

class MultiPassTesseractProvider(OCRProvider):
    """
    Multi-pass OCR Provider that executes multiple preprocessing variants
    on high-resolution declaration crops and derives a verified consensus value.
    If OCR results conflict significantly, marks the field as REQUIRES_MANUAL_REVIEW.
    """

    def perform_ocr(
        self,
        image_path_or_crop: Union[str, np.ndarray],
        field_name: Optional[str] = None,
        candidate_hints: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes multi-pass OCR on image crop across multiple preprocessing variants.
        Returns:
        {
          "consensus_text": str,
          "confidence": float,
          "ocr_candidates": List[Dict[str, Any]],
          "conflict_detected": bool,
          "status": "VERIFIED" | "REQUIRES_MANUAL_REVIEW" | "NOT_DETECTED"
        }
        """
        variants = image_service.generate_preprocessing_variants(image_path_or_crop)
        ocr_results = []

        # Run OCR on each preprocessing variant
        for variant_name, var_img in variants.items():
            text_candidate = self._recognize_single_variant(var_img, field_name)
            if text_candidate:
                ocr_results.append({
                    "variant": variant_name,
                    "text": text_candidate["text"],
                    "confidence": text_candidate["confidence"]
                })

        # Include any external candidate hints passed from client/Tesseract.js
        if candidate_hints:
            for idx, hint in enumerate(candidate_hints):
                if hint and hint.strip():
                    ocr_results.append({
                        "variant": f"client_tesseract_pass_{idx+1}",
                        "text": hint.strip(),
                        "confidence": 0.90
                    })

        if not ocr_results:
            return {
                "consensus_text": "",
                "confidence": 0.0,
                "ocr_candidates": [],
                "conflict_detected": False,
                "status": "NOT_DETECTED"
            }

        # Consensus Evaluation
        return self._evaluate_consensus(ocr_results, field_name)

    def _recognize_single_variant(self, img_variant: np.ndarray, field_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Runs OCR on a single preprocessed variant.
        """
        if PYTESSERACT_AVAILABLE:
            try:
                # Configure PSM for single-line vs block
                config = "--psm 6" if field_name in ["mrp", "net_quantity", "mfg_date", "unit_sale_price"] else "--psm 3"
                txt = pytesseract.image_to_string(img_variant, config=config).strip()
                if txt:
                    return {"text": txt, "confidence": 0.92}
            except Exception:
                pass
        return None

    def _evaluate_consensus(self, candidates: List[Dict[str, Any]], field_name: Optional[str]) -> Dict[str, Any]:
        """
        Derives a consensus result from multi-pass OCR outputs.
        Detects significant conflicts (e.g. ?249 vs ?349).
        """
        raw_texts = [c["text"].strip() for c in candidates if c["text"].strip()]
        if not raw_texts:
            return {
                "consensus_text": "",
                "confidence": 0.0,
                "ocr_candidates": candidates,
                "conflict_detected": False,
                "status": "NOT_DETECTED"
            }

        # Check for numeric/price conflicts if field is MRP or Net Quantity
        if field_name == "mrp":
            prices = []
            for t in raw_texts:
                match = re.search(r"(\d+(?:\.\d{1,2})?)", t.replace(",", ""))
                if match:
                    prices.append(float(match.group(1)))
            unique_prices = set(prices)
            if len(unique_prices) > 1 and max(unique_prices) - min(unique_prices) > 1.0:
                # Meaningful conflict in price detected!
                counts = Counter(prices)
                most_common_price, freq = counts.most_common(1)[0]
                return {
                    "consensus_text": f"? {most_common_price}",
                    "confidence": round(freq / len(prices), 2),
                    "ocr_candidates": candidates,
                    "conflict_detected": True,
                    "status": "REQUIRES_MANUAL_REVIEW",
                    "review_reason": f"Conflicting price values detected across OCR passes: {sorted(list(unique_prices))}"
                }

        # General consensus by voting
        counts = Counter(raw_texts)
        best_text, best_count = counts.most_common(1)[0]
        agreement_ratio = round(best_count / float(len(raw_texts)), 2)

        conflict = agreement_ratio < 0.5 and len(raw_texts) > 2
        status = "REQUIRES_MANUAL_REVIEW" if conflict else "VERIFIED"

        return {
            "consensus_text": best_text,
            "confidence": agreement_ratio,
            "ocr_candidates": candidates,
            "conflict_detected": conflict,
            "status": status,
            "agreement_ratio": agreement_ratio
        }
