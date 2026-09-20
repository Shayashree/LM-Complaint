from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import numpy as np

class VisionGroundingProvider(ABC):
    """
    Abstract visual grounding / localization provider interface.
    Answers: WHERE is the statutory declaration printed on the package?
    """
    @abstractmethod
    def locate_declarations(
        self,
        image_path: str,
        declarations_to_find: Dict[str, str],
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        pass

class OCRProvider(ABC):
    """
    Abstract Optical Character Recognition provider interface.
    Performs multi-pass character extraction with consensus voting.
    """
    @abstractmethod
    def perform_ocr(
        self,
        image_path_or_crop: Union[str, np.ndarray],
        field_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        pass

class VisionReasoningProvider(ABC):
    """
    Abstract Vision Reasoning / AI Cross-Verification provider interface.
    Acts as a cross-verification layer for difficult visual cases without replacing OCR.
    """
    @abstractmethod
    def cross_verify(
        self,
        crop_image_or_path: Union[str, np.ndarray],
        field_name: str,
        raw_ocr_value: str,
        **kwargs
    ) -> Dict[str, Any]:
        pass
