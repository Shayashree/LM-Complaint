import os
import tempfile
import numpy as np
import cv2
import pytest
from app.services.image_service import image_service

def test_image_quality_sharp_good():
    img = np.ones((600, 600, 3), dtype=np.uint8) * 200
    cv2.putText(img, "LEGAL METROLOGY SCAN TEST", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
    cv2.rectangle(img, (40, 40), (560, 560), (30, 30, 30), 3)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        cv2.imwrite(tmp_path, img)

    try:
        res = image_service.check_image_quality(tmp_path)
        assert res["is_acceptable"] is True
        assert res["readability_status"] in ["GOOD", "MANUAL_VERIFICATION_REQUIRED"]
        assert res["blur_score"] > 30.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_image_quality_blurry_detection():
    img = np.ones((500, 500, 3), dtype=np.uint8) * 128
    blurred = cv2.GaussianBlur(img, (51, 51), 0)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        cv2.imwrite(tmp_path, blurred)

    try:
        res = image_service.check_image_quality(tmp_path)
        assert any("blurry" in issue.lower() or "focus" in issue.lower() for issue in res["issues"])
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_perspective_correction_and_cropping():
    img = np.zeros((800, 800, 3), dtype=np.uint8) + 240
    pts = np.array([[120, 100], [680, 150], [650, 700], [150, 660]], np.int32)
    cv2.fillPoly(img, [pts], (40, 60, 90))
    cv2.putText(img, "NET QTY 500g", (200, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        cv2.imwrite(tmp_path, img)

    try:
        corrected_path, meta = image_service.detect_package_and_correct_perspective(tmp_path)
        assert meta["applied"] is True
        assert os.path.exists(corrected_path)

        crop_path = image_service.crop_region_high_res(corrected_path, [20, 40, 50, 20])
        assert crop_path is not None
        assert os.path.exists(crop_path)

        variants = image_service.generate_preprocessing_variants(crop_path)
        assert "original" in variants
        assert "grayscale" in variants
        assert "contrast_enhanced" in variants
        assert "sharpened" in variants
        assert "adaptive_threshold" in variants

        if os.path.exists(crop_path):
            os.remove(crop_path)
        if corrected_path != tmp_path and os.path.exists(corrected_path):
            os.remove(corrected_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
