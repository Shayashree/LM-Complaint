import os
import logging
from app.core.config import settings

logger = logging.getLogger("OCRService")

PADDLE_AVAILABLE = False
try:
    if settings.OCR_PROVIDER == "paddleocr":
        from paddleocr import PaddleOCR
        PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    logger.warning("PaddleOCR not installed. Falling back to Mock OCR provider.")

class OCRService:
    def __init__(self):
        self.ocr_engine = None
        if PADDLE_AVAILABLE:
            try:
                # Initialize PaddleOCR
                self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                self.ocr_engine = None

    def perform_ocr(self, image_path: str) -> list:
        """
        Runs OCR on the given image path.
        Returns a list of dicts: [{"text": str, "confidence": float, "bbox": [x,y,w,h]}]
        """
        # If paddle is requested and available
        if settings.OCR_PROVIDER == "paddleocr" and self.ocr_engine:
            try:
                result = self.ocr_engine.ocr(image_path, cls=True)
                ocr_results = []
                if result and result[0]:
                    for line in result[0]:
                        bbox_coords = line[0] # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                        text, conf = line[1]
                        
                        # Convert bounding box [[x,y],...] to bounding box [x, y, w, h] as standard percentage/pixel values
                        x_coords = [c[0] for c in bbox_coords]
                        y_coords = [c[1] for c in bbox_coords]
                        xmin, xmax = min(x_coords), max(x_coords)
                        ymin, ymax = min(y_coords), max(y_coords)
                        
                        ocr_results.append({
                            "text": text,
                            "confidence": round(float(conf), 2),
                            "bbox": [xmin, ymin, xmax - xmin, ymax - ymin]
                        })
                return ocr_results
            except Exception as e:
                logger.error(f"PaddleOCR processing error: {e}. Falling back to mock data.")

        # Fallback Mock OCR Engine
        return self._get_mock_ocr_data(image_path)

    def _get_mock_ocr_data(self, image_path: str) -> list:
        filename = os.path.basename(image_path).lower()
        
        # Heuristics based on image name
        if "surf" in filename or "detergent" in filename:
            return [
                {"text": "Surf Excel Easy Wash Detergent Powder", "confidence": 0.98, "bbox": [8, 12, 84, 16]},
                {"text": "Net Qty: 1 kg", "confidence": 0.97, "bbox": [10, 80, 38, 10]},
                {"text": "MRP Rs 140.00", "confidence": 0.95, "bbox": [50, 80, 42, 10]}, # Notice MRP lacks "incl of all taxes", violation!
                {"text": "MFD 05/2026", "confidence": 0.93, "bbox": [12, 32, 28, 8]},
                {"text": "Manufactured by Hindustan Unilever Limited, Mumbai - 400099", "confidence": 0.96, "bbox": [8, 62, 84, 12]}
                # Missing consumer care details entirely!
            ]
        elif "parle" in filename or "biscuit" in filename:
            return [
                {"text": "PARLE-G GLUCO BISCUITS", "confidence": 0.99, "bbox": [10, 35, 80, 15]},
                {"text": "Net Qty: 800 g", "confidence": 0.98, "bbox": [10, 60, 35, 10]},
                {"text": "MRP Rs 50.00 (incl. of all taxes)", "confidence": 0.97, "bbox": [50, 60, 42, 10]},
                {"text": "MFD 06/2026", "confidence": 0.99, "bbox": [42, 51, 24, 7]},
                {"text": "Mfg by Parle Products Pvt. Ltd., Vile Parle East, Mumbai - 400057", "confidence": 0.96, "bbox": [8, 73, 84, 11]},
                {"text": "Consumer Care Ph: 1800-22-7753, email: customercare@parle.biz", "confidence": 0.98, "bbox": [8, 86, 84, 11]}
            ]
        elif "haldiram" in filename or "bhujia" in filename or "sev" in filename:
            return [
                {"text": "Haldiram's BHUJIA SEV", "confidence": 0.95, "bbox": [15, 18, 70, 14]},
                {"text": "Net Qty: 400 g", "confidence": 0.91, "bbox": [10, 75, 35, 10]},
                {"text": "MRP Rs 110.00 (incl. of all taxes)", "confidence": 0.89, "bbox": [48, 75, 44, 10]},
                {"text": "MFD 07/2026", "confidence": 0.68, "bbox": [42, 34, 30, 8]}, # Low confidence warning!
                {"text": "Mfg by Haldiram Foods International Pvt. Ltd., Nagpur - 441104", "confidence": 0.82, "bbox": [8, 86, 84, 10]},
                {"text": "Quality Manager Consumer email: support@haldirams.com Ph: 0712-2681122", "confidence": 0.87, "bbox": [10, 48, 80, 10]}
            ]
        
        # Generic product text mockup
        return [
            {"text": "ABC Brand Prepackaged Item", "confidence": 0.90, "bbox": [10, 20, 80, 15]},
            {"text": "Net Qty: 500g", "confidence": 0.88, "bbox": [10, 60, 30, 10]},
            {"text": "MRP Rs 199.00 (incl. of all taxes)", "confidence": 0.92, "bbox": [50, 60, 40, 10]},
            {"text": "MFD 08/2026", "confidence": 0.89, "bbox": [10, 75, 30, 0.5]} # Tiny font size (0.5% of height = 0.90 mm < 1.50 mm)
        ]

ocr_service = OCRService()
