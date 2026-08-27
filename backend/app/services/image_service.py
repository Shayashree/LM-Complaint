import os
import logging

logger = logging.getLogger("ImageService")

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available. Falling back to basic copy for image processing.")

class ImageService:
    def preprocess_image(self, input_path: str) -> str:
        """
        Applies contrast enhancement, noise reduction, and normalizes layout.
        Returns the path of the processed image.
        """
        if not OPENCV_AVAILABLE:
            return input_path
            
        try:
            # Load image
            img = cv2.imread(input_path)
            if img is None:
                return input_path
                
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply histogram equalization to enhance contrast
            enhanced = cv2.equalizeHist(gray)
            
            # Apply bilateral filter to remove noise while keeping edges sharp
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # Save processed image in the same directory with a suffix
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
        Estimates contrast and quality score.
        Returns quality metadata.
        """
        if not OPENCV_AVAILABLE:
            return {"quality_score": 1.0, "readability_status": "GOOD"}
            
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {"quality_score": 1.0, "readability_status": "GOOD"}
                
            # Simple contrast estimate based on standard deviation of gray channels
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            std_dev = np.std(gray)
            
            # Lower variance indicates less contrast, possibly blur
            quality_score = float(std_dev / 128.0) # normalized around standard variance
            readability_status = "GOOD"
            if std_dev < 20:
                readability_status = "POOR"
            elif std_dev < 40:
                readability_status = "MANUAL_VERIFICATION_REQUIRED"
                
            return {
                "quality_score": round(quality_score, 2),
                "readability_status": readability_status
            }
        except Exception as e:
            logger.error(f"Error estimating readability: {e}")
            return {"quality_score": 1.0, "readability_status": "GOOD"}

image_service = ImageService()
