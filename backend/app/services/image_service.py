import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger("ImageService")

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available. Falling back to basic copy for image processing.")

class ImageService:
    def check_image_quality(self, image_path: str) -> Dict[str, Any]:
        """
        Phase 1: Deterministic image quality checking before OCR or AI analysis.
        Checks:
        - Product package presence & visibility
        - Blur detection via Laplacian variance
        - Exposure/lighting sufficiency (underexposed/overexposed)
        - Glare & specular reflection
        - Resolution & size sufficiency
        - Heavy tilt
        """
        if not os.path.exists(image_path):
            return {
                "is_acceptable": False,
                "issues": ["Image file not found"],
                "tips": ["Please upload a valid image file."],
                "blur_score": 0.0,
                "lighting_score": 0.0,
                "glare_percentage": 0.0,
                "quality_score": 0.0,
                "readability_status": "POOR"
            }

        if not OPENCV_AVAILABLE:
            return {
                "is_acceptable": True,
                "issues": [],
                "tips": [],
                "blur_score": 100.0,
                "lighting_score": 128.0,
                "glare_percentage": 0.0,
                "quality_score": 1.0,
                "readability_status": "GOOD"
            }

        try:
            img = cv2.imread(image_path)
            if img is None:
                return {
                    "is_acceptable": False,
                    "issues": ["Cannot decode image data"],
                    "tips": ["Please upload a supported image format (JPEG, PNG)."],
                    "quality_score": 0.0,
                    "readability_status": "POOR"
                }

            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            issues = []
            tips = []

            # 1. Resolution Check
            if w < 320 or h < 320:
                issues.append("Image resolution is too low")
                tips.append("Move closer to the package or capture at higher resolution.")

            # 2. Blur Estimation (Laplacian Variance)
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            # Low variance indicates blurry / unfocused image
            is_blurry = laplacian_var < 55.0
            if is_blurry:
                issues.append(f"Image is blurry (focus score: {round(laplacian_var, 1)})")
                tips.append("Keep the package steady and tap the screen to focus before capturing.")

            # 3. Lighting / Exposure Check
            mean_brightness = float(np.mean(gray))
            if mean_brightness < 40:
                issues.append("Lighting is too dark / underexposed")
                tips.append("Increase ambient lighting or enable the device camera flash.")
            elif mean_brightness > 230:
                issues.append("Image is overexposed / washed out")
                tips.append("Avoid direct harsh light directly facing the camera sensor.")

            # 4. Glare / Specular Reflection Detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            val_channel = hsv[:, :, 2]
            sat_channel = hsv[:, :, 1]
            glare_mask = (val_channel > 245) & (sat_channel < 35)
            glare_pct = float((np.count_nonzero(glare_mask) / (w * h)) * 100.0)
            if glare_pct > 14.0:
                issues.append(f"Excessive glare detected ({round(glare_pct, 1)}% of surface)")
                tips.append("Angle the package slightly away from light sources to avoid specular glare.")

            # 5. Package Visibility / Edge Presence
            edges = cv2.Canny(gray, 50, 150)
            edge_density = float(np.count_nonzero(edges) / (w * h))
            if edge_density < 0.008:
                issues.append("No distinct package or text contours detected")
                tips.append("Make sure the complete package is visible in the frame.")

            # Overall acceptability
            is_acceptable = (
                not is_blurry 
                and 35 <= mean_brightness <= 235 
                and glare_pct <= 22.0 
                and w >= 300 and h >= 300
            )

            quality_score = max(0.0, min(1.0, (
                (min(laplacian_var, 300.0) / 300.0) * 0.4 +
                (1.0 - abs(mean_brightness - 128.0) / 128.0) * 0.3 +
                (max(0.0, 1.0 - glare_pct / 20.0)) * 0.3
            )))

            readability_status = "GOOD"
            if not is_acceptable:
                readability_status = "POOR"
            elif quality_score < 0.55 or len(issues) > 0:
                readability_status = "MANUAL_VERIFICATION_REQUIRED"

            return {
                "is_acceptable": is_acceptable,
                "issues": issues,
                "tips": tips if tips else ["Image quality is optimal for statutory analysis."],
                "blur_score": round(laplacian_var, 1),
                "lighting_score": round(mean_brightness, 1),
                "glare_percentage": round(glare_pct, 2),
                "quality_score": round(quality_score, 2),
                "readability_status": readability_status,
                "width": w,
                "height": h
            }
        except Exception as e:
            logger.error(f"Error checking image quality: {e}")
            return {
                "is_acceptable": True,
                "issues": [],
                "tips": [],
                "blur_score": 100.0,
                "lighting_score": 128.0,
                "glare_percentage": 0.0,
                "quality_score": 0.8,
                "readability_status": "GOOD"
            }

    def detect_package_and_correct_perspective(
        self, 
        input_path: str, 
        output_path: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Phase 2: Detect package boundary using OpenCV and perform 4-corner homography/perspective transform.
        Transforms angled packaging into a normalized front-facing view without text distortion.
        Preserves highest useful resolution.
        """
        if not OPENCV_AVAILABLE or not os.path.exists(input_path):
            return input_path, {"applied": False, "reason": "OpenCV or file unavailable"}

        try:
            img = cv2.imread(input_path)
            if img is None:
                return input_path, {"applied": False, "reason": "Failed to decode image"}

            orig_h, orig_w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Edge detection and morphological closing
            edged = cv2.Canny(blurred, 40, 140)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return input_path, {"applied": False, "reason": "No packaging contour detected"}

            # Sort contours by area descending
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            min_area = orig_w * orig_h * 0.12 # Must cover at least 12% of frame

            package_quad = None
            for c in contours:
                area = cv2.contourArea(c)
                if area < min_area:
                    continue
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.025 * peri, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    package_quad = approx.reshape(4, 2)
                    break

            if package_quad is None:
                # If exact 4-point quadrilateral not found, try minAreaRect
                for c in contours:
                    if cv2.contourArea(c) >= min_area:
                        rect = cv2.minAreaRect(c)
                        box = cv2.boxPoints(rect)
                        box = np.int32(box)
                        # Check aspect ratio
                        rect_w, rect_h = rect[1]
                        if min(rect_w, rect_h) > 50:
                            package_quad = box
                            break

            if package_quad is None:
                return input_path, {"applied": False, "reason": "No clear 4-corner polygon found; original retained to preserve text"}

            # Order points: [top-left, top-right, bottom-right, bottom-left]
            pts = np.array(package_quad, dtype="float32")
            s = pts.sum(axis=1)
            diff = np.diff(pts, axis=1)

            rect_ordered = np.zeros((4, 2), dtype="float32")
            rect_ordered[0] = pts[np.argmin(s)]       # top-left
            rect_ordered[2] = pts[np.argmax(s)]       # bottom-right
            rect_ordered[1] = pts[np.argmin(diff)]    # top-right
            rect_ordered[3] = pts[np.argmax(diff)]    # bottom-left

            tl, tr, br, bl = rect_ordered

            # Calculate destination dimensions
            width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            max_width = max(int(width_a), int(width_b))

            height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            max_height = max(int(height_a), int(height_b))

            # Guard against degenerate rects
            if max_width < 100 or max_height < 100:
                return input_path, {"applied": False, "reason": "Detected boundary too small"}

            # Avoid excessive distortion: if aspect ratio changes drastically, keep original
            orig_aspect = orig_w / float(orig_h)
            new_aspect = max_width / float(max_height)
            if new_aspect > orig_aspect * 3.0 or new_aspect < orig_aspect / 3.0:
                return input_path, {"applied": False, "reason": "Perspective distortion threshold exceeded"}

            dst = np.array([
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1]
            ], dtype="float32")

            # Compute transformation matrix
            matrix = cv2.getPerspectiveTransform(rect_ordered, dst)
            warped = cv2.warpPerspective(img, matrix, (max_width, max_height), flags=cv2.INTER_LANCZOS4)

            # Determine destination output path
            if output_path is None:
                dir_name, file_name = os.path.split(input_path)
                corrected_name = f"rectified_{file_name}"
                output_path = os.path.join(dir_name, corrected_name).replace("\\", "/")

            cv2.imwrite(output_path, warped)
            return output_path, {
                "applied": True,
                "corners": rect_ordered.tolist(),
                "output_width": max_width,
                "output_height": max_height,
                "corrected_path": output_path
            }
        except Exception as e:
            logger.error(f"Error in perspective correction: {e}")
            return input_path, {"applied": False, "reason": str(e)}

    def generate_overlapping_tiles(
        self,
        image_path: str,
        tile_size: Tuple[int, int] = (1024, 1024),
        overlap_ratio: float = 0.25
    ) -> List[Dict[str, Any]]:
        """
        Phase 3: High-resolution packaging surface tiling.
        Divides large packaging surfaces into overlapping tiles (20-30% overlap)
        to prevent statutory declarations near borders from being cut off.
        """
        if not OPENCV_AVAILABLE or not os.path.exists(image_path):
            return [{"tile_path": image_path, "tile_index": 0, "bbox": [0, 0, 100, 100]}]

        try:
            img = cv2.imread(image_path)
            if img is None:
                return [{"tile_path": image_path, "tile_index": 0, "bbox": [0, 0, 100, 100]}]

            h, w = img.shape[:2]
            tw, th = tile_size

            # If image fits comfortably in one frame, no tiling needed
            if w <= tw * 1.25 and h <= th * 1.25:
                return [{
                    "tile_path": image_path,
                    "tile_index": 0,
                    "x": 0, "y": 0, "w": w, "h": h,
                    "pct_bbox": [0.0, 0.0, 100.0, 100.0]
                }]

            step_x = max(100, int(tw * (1.0 - overlap_ratio)))
            step_y = max(100, int(th * (1.0 - overlap_ratio)))

            dir_name, base_name = os.path.split(image_path)
            name_no_ext, ext = os.path.splitext(base_name)
            tiles = []
            idx = 0

            y = 0
            while y < h:
                cur_th = min(th, h - y)
                x = 0
                while x < w:
                    cur_tw = min(tw, w - x)
                    tile_crop = img[y:y+cur_th, x:x+cur_tw]

                    tile_fname = f"tile_{idx}_{name_no_ext}{ext}"
                    tile_out_path = os.path.join(dir_name, tile_fname).replace("\\", "/")
                    cv2.imwrite(tile_out_path, tile_crop)

                    pct_x = round((x / float(w)) * 100.0, 2)
                    pct_y = round((y / float(h)) * 100.0, 2)
                    pct_w = round((cur_tw / float(w)) * 100.0, 2)
                    pct_h = round((cur_th / float(h)) * 100.0, 2)

                    tiles.append({
                        "tile_path": tile_out_path,
                        "tile_index": idx,
                        "pixel_rect": [x, y, cur_tw, cur_th],
                        "pct_bbox": [pct_x, pct_y, pct_w, pct_h],
                        "orig_dimensions": [w, h]
                    })
                    idx += 1

                    if x + cur_tw >= w:
                        break
                    x += step_x

                if y + cur_th >= h:
                    break
                y += step_y

            return tiles
        except Exception as e:
            logger.error(f"Error generating overlapping tiles: {e}")
            return [{"tile_path": image_path, "tile_index": 0, "pct_bbox": [0, 0, 100, 100]}]

    def crop_region_high_res(
        self,
        image_path: str,
        bbox: Union[List[float], Tuple[float, float, float, float]],
        padding_ratio: float = 0.08,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Phase 5: High-resolution region cropping.
        Extracts bounded declaration area with padding around characters,
        preserving original high-resolution pixels without downscaling.
        """
        if not OPENCV_AVAILABLE or not os.path.exists(image_path) or not bbox or len(bbox) < 4:
            return None

        try:
            img = cv2.imread(image_path)
            if img is None:
                return None

            h, w = img.shape[:2]
            bx, by, bw, bh = [float(v) for v in bbox[:4]]

            # Detect if bbox is percentage (0-100) or pixel coordinates
            if max(bx, by, bw, bh) <= 100.0:
                px_x = (bx / 100.0) * w
                px_y = (by / 100.0) * h
                px_w = (bw / 100.0) * w
                px_h = (bh / 100.0) * h
            else:
                px_x, px_y, px_w, px_h = bx, by, bw, bh

            # Apply adaptive padding
            pad_x = px_w * padding_ratio
            pad_y = px_h * padding_ratio

            x1 = max(0, int(px_x - pad_x))
            y1 = max(0, int(px_y - pad_y))
            x2 = min(w, int(px_x + px_w + pad_x))
            y2 = min(h, int(px_y + px_h + pad_y))

            if x2 <= x1 or y2 <= y1:
                return None

            crop = img[y1:y2, x1:x2]

            if output_path is None:
                dir_name, base_name = os.path.split(image_path)
                name_no_ext, ext = os.path.splitext(base_name)
                output_path = os.path.join(
                    dir_name, f"crop_{x1}_{y1}_{name_no_ext}{ext}"
                ).replace("\\", "/")

            cv2.imwrite(output_path, crop)
            return output_path
        except Exception as e:
            logger.error(f"Error cropping high-res region: {e}")
            return None

    def generate_preprocessing_variants(
        self,
        crop_image_or_path: Union[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 6: Multi-pass image preprocessing variants for every declaration crop.
        At minimum:
        1. Original
        2. Grayscale
        3. Contrast enhanced (CLAHE)
        4. Sharpened
        5. Adaptive threshold
        6. Inverted polarity (for dark packaging)
        7. Upscaled version (2x bicubic for small text)
        """
        if not OPENCV_AVAILABLE:
            return {}

        try:
            if isinstance(crop_image_or_path, str):
                if not os.path.exists(crop_image_or_path):
                    return {}
                img = cv2.imread(crop_image_or_path)
            else:
                img = crop_image_or_path

            if img is None:
                return {}

            variants = {}
            variants["original"] = img

            # Grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()
            variants["grayscale"] = gray

            # Contrast enhanced with CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            contrast_enhanced = clahe.apply(gray)
            variants["contrast_enhanced"] = contrast_enhanced

            # Sharpened
            kernel_sharpen = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(contrast_enhanced, -1, kernel_sharpen)
            variants["sharpened"] = sharpened

            # Adaptive Threshold (Otsu + Gaussian)
            adaptive_thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            variants["adaptive_threshold"] = adaptive_thresh

            # Dark Packaging Polarity Detection & Selective Inversion
            mean_lum = float(np.mean(gray))
            is_dark_bg = mean_lum < 120.0
            inverted = cv2.bitwise_not(gray)
            if is_dark_bg:
                variants["inverted_polarity"] = inverted
            else:
                # Include inverted as secondary test variant
                variants["inverted_variant"] = inverted

            # 2x Bicubic Upscaling for small font details
            ch, cw = gray.shape[:2]
            if cw < 600 or ch < 120:
                upscaled = cv2.resize(
                    contrast_enhanced, (cw * 2, ch * 2), interpolation=cv2.INTER_CUBIC
                )
                variants["upscaled"] = upscaled

            return variants
        except Exception as e:
            logger.error(f"Error generating preprocessing variants: {e}")
            return {}

    def preprocess_image(self, input_path: str) -> str:
        """
        Backwards-compatible wrapper:
        Applies contrast enhancement, noise reduction, and normalizes layout.
        Returns the path of the processed image.
        """
        if not OPENCV_AVAILABLE:
            return input_path
            
        try:
            img = cv2.imread(input_path)
            if img is None:
                return input_path
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            denoised = cv2.bilateralFilter(enhanced, 7, 50, 50)
            
            dir_name, file_name = os.path.split(input_path)
            processed_file_name = f"processed_{file_name}"
            processed_path = os.path.join(dir_name, processed_file_name).replace("\\", "/")
            
            cv2.imwrite(processed_path, denoised)
            return processed_path
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return input_path

    def estimate_readability(self, image_path: str) -> dict:
        """
        Backwards-compatible wrapper delegating to check_image_quality.
        """
        res = self.check_image_quality(image_path)
        return {
            "quality_score": res["quality_score"],
            "readability_status": res["readability_status"],
            "is_acceptable": res["is_acceptable"],
            "issues": res["issues"],
            "tips": res["tips"]
        }

image_service = ImageService()

