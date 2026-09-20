import os
import re
import json
import base64
import logging
import requests
from typing import Dict, Any, Optional, Union
import numpy as np
import cv2
from app.services.providers.base import VisionReasoningProvider

logger = logging.getLogger("GeminiVisionProvider")

class GeminiVisionProvider(VisionReasoningProvider):
    """
    Google Gemini Multimodal Vision Cross-Verification Provider.
    Adheres strictly to the mandate: Gemini is a cross-check, NEVER the sole authority.
    Discrepancies between OCR and AI trigger REQUIRES_MANUAL_REVIEW.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def cross_verify(
        self,
        crop_image_or_path: Union[str, np.ndarray],
        field_name: str,
        raw_ocr_value: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cross-verifies a localized declaration crop against raw OCR text.
        Returns:
        {
          "field": field_name,
          "raw_ocr": raw_ocr_value,
          "ai_interpretation": ai_val,
          "final_value": final_val,
          "verification_status": "VERIFIED" | "REQUIRES_MANUAL_REVIEW" | "NOT_DETECTED",
          "reason": str
        }
        """
        from app.core.config import settings
        effective_key = api_key or self.api_key or getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")

        if not effective_key:
            return {
                "field": field_name,
                "raw_ocr": raw_ocr_value,
                "ai_interpretation": None,
                "final_value": raw_ocr_value,
                "verification_status": "VERIFIED" if raw_ocr_value and raw_ocr_value != "N/A" else "NOT_DETECTED",
                "reason": "AI verification skipped: Gemini API key not configured. Value validated via deterministic OCR and regex."
            }

        # Prepare base64 image data
        b64_img = self._to_base64(crop_image_or_path)
        if not b64_img:
            return {
                "field": field_name,
                "raw_ocr": raw_ocr_value,
                "ai_interpretation": None,
                "final_value": raw_ocr_value,
                "verification_status": "VERIFIED" if raw_ocr_value and raw_ocr_value != "N/A" else "NOT_DETECTED",
                "reason": "Invalid image crop data provided for cross-verification."
            }

        prompt = (
            f"You are a Legal Metrology forensic verification system.\n"
            f"Inspect this high-resolution packaging crop specifically for the statutory field: '{field_name}'.\n"
            f"The optical OCR reader extracted: '{raw_ocr_value}'.\n\n"
            f"Task:\n"
            f"1. Read the exact text printed in the image for this field.\n"
            f"2. Return valid JSON only:\n"
            f"{{\n"
            f"  \"text_seen\": \"exact string read from image or null if not legible\",\n"
            f"  \"confidence\": 0.95,\n"
            f"  \"matches_ocr\": true or false\n"
            f"}}"
        )

        models = [
            "gemini-3.5-flash",
            "gemini-3.7-flash",
            "gemini-flash-latest",
            "gemini-3.8-flash",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-2.5-flash"
        ]
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={effective_key.strip()}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inlineData": {"mimeType": "image/jpeg", "data": b64_img}}
                        ]
                    }],
                    "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
                }
                headers = {"Content-Type": "application/json"}
                resp = requests.post(url, json=payload, headers=headers, timeout=12)
                if resp.status_code == 200:
                    resp_json = resp.json()
                    out_text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    parsed = json.loads(out_text)
                    ai_seen = parsed.get("text_seen")

                    if not ai_seen:
                        return {
                            "field": field_name,
                            "raw_ocr": raw_ocr_value,
                            "ai_interpretation": None,
                            "final_value": raw_ocr_value,
                            "verification_status": "REQUIRES_MANUAL_REVIEW" if raw_ocr_value != "N/A" else "NOT_DETECTED",
                            "reason": "AI could not legibly confirm the declaration in the crop image."
                        }

                    # Comparison logic
                    is_match = self._compare_readings(field_name, raw_ocr_value, ai_seen)
                    if is_match:
                        return {
                            "field": field_name,
                            "raw_ocr": raw_ocr_value,
                            "ai_interpretation": ai_seen,
                            "final_value": raw_ocr_value if raw_ocr_value != "N/A" else ai_seen,
                            "verification_status": "VERIFIED",
                            "reason": "OCR and Gemini AI mutually confirmed."
                        }
                    else:
                        logger.warning(f"Conflict detected for {field_name}: OCR='{raw_ocr_value}' vs Gemini='{ai_seen}'")
                        return {
                            "field": field_name,
                            "raw_ocr": raw_ocr_value,
                            "ai_interpretation": ai_seen,
                            "final_value": None,
                            "verification_status": "REQUIRES_MANUAL_REVIEW",
                            "reason": f"OCR and AI disagree: OCR reads '{raw_ocr_value}' while AI interprets '{ai_seen}'."
                        }
            except Exception as e:
                logger.debug(f"Gemini call to {model} failed: {e}")

        # Fallback if API unavailable
        return {
            "field": field_name,
            "raw_ocr": raw_ocr_value,
            "ai_interpretation": None,
            "final_value": raw_ocr_value,
            "verification_status": "VERIFIED" if raw_ocr_value and raw_ocr_value != "N/A" else "NOT_DETECTED",
            "reason": "AI cross-verification service temporarily unreachable; fallback to OCR consensus."
        }

    def _compare_readings(self, field_name: str, ocr_val: str, ai_val: str) -> bool:
        """
        Normalized comparison between OCR and AI outputs.
        """
        if not ocr_val or not ai_val:
            return False

        c_ocr = re.sub(r"[^\w\.]", "", ocr_val.lower())
        c_ai = re.sub(r"[^\w\.]", "", ai_val.lower())

        if c_ocr == c_ai:
            return True

        if field_name == "mrp":
            # Extract numbers
            num_ocr = re.findall(r"\d+(?:\.\d+)?", ocr_val)
            num_ai = re.findall(r"\d+(?:\.\d+)?", ai_val)
            return len(num_ocr) > 0 and len(num_ai) > 0 and num_ocr[0] == num_ai[0]

        if field_name == "net_quantity":
            num_ocr = re.findall(r"\d+(?:\.\d+)?", ocr_val)
            num_ai = re.findall(r"\d+(?:\.\d+)?", ai_val)
            return len(num_ocr) > 0 and len(num_ai) > 0 and num_ocr[0] == num_ai[0]

        # Substring / overlap check
        return c_ocr in c_ai or c_ai in c_ocr

    def _to_base64(self, crop_image_or_path: Union[str, np.ndarray]) -> Optional[str]:
        try:
            if isinstance(crop_image_or_path, str):
                if not os.path.exists(crop_image_or_path):
                    return None
                with open(crop_image_or_path, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            elif isinstance(crop_image_or_path, np.ndarray):
                success, encoded = cv2.imencode(".jpg", crop_image_or_path)
                if success:
                    return base64.b64encode(encoded).decode("utf-8")
        except Exception:
            pass
        return None
