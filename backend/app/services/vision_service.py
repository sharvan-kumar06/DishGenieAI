import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

# Base directory resolved relative to this file: backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_MODEL_PATH = BACKEND_DIR / "models" / "dishgenie_cnn.keras"
DEFAULT_CLASSES_PATH = BACKEND_DIR / "models" / "dishgenie_classes.json"


class VisionService:
    """
    Reusable Computer Vision Service for DishGenie.
    Loads the trained CNN and class mappings once at startup and performs
    validated preprocessing and inference on ingredient images.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        classes_path: Optional[Union[str, Path]] = None,
    ):
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self.classes_path = Path(classes_path) if classes_path else DEFAULT_CLASSES_PATH
        
        self.model: Optional[tf.keras.Model] = None
        self.class_names: List[str] = []
        
        # Load resources immediately to ensure fail-fast behavior at startup
        self._load_resources()

    def _load_resources(self) -> None:
        """
        Validates and loads the class names JSON and CNN model once.
        Fails fast with clear descriptive exceptions if missing or corrupted.
        """
        # 1. Validate class file existence
        if not self.classes_path.exists():
            raise FileNotFoundError(
                f"[VisionService] Class names JSON not found at: {self.classes_path.resolve()}"
            )

        # 2. Parse class names JSON (supports both {"class": idx} dict and ["class", ...] list)
        try:
            with open(self.classes_path, "r", encoding="utf-8") as f:
                raw_classes = json.load(f)

            if isinstance(raw_classes, dict):
                # Format: {"agaricus_bisporus": 0, "apple": 6, ...}
                first_key, first_val = next(iter(raw_classes.items()))
                if isinstance(first_val, int):
                    sorted_items = sorted(raw_classes.items(), key=lambda x: int(x[1]))
                    self.class_names = [str(k) for k, _ in sorted_items]
                else:
                    sorted_items = sorted(raw_classes.items(), key=lambda x: int(x[0]))
                    self.class_names = [str(v) for _, v in sorted_items]
            elif isinstance(raw_classes, list):
                self.class_names = [str(c) for c in raw_classes]
            else:
                raise ValueError("Classes JSON must contain a list of strings or a dict mapping classes to indices.")

            if len(self.class_names) == 0:
                raise ValueError("Parsed class names list cannot be empty.")

            logger.info(f"[VisionService] Loaded {len(self.class_names)} classes.")
        except Exception as e:
            raise ValueError(
                f"[VisionService] Failed to load/parse class names from {self.classes_path}: {e}"
            ) from e

        # 3. Validate model file existence
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"[VisionService] CNN model file not found at: {self.model_path.resolve()}"
            )

        # 4. Load Keras model
        try:
            logger.info(f"[VisionService] Loading CNN model from: {self.model_path.resolve()}...")
            self.model = tf.keras.models.load_model(str(self.model_path))
            logger.info("[VisionService] CNN model loaded successfully into memory.")
        except Exception as e:
            raise RuntimeError(
                f"[VisionService] Failed to load CNN model from {self.model_path}: {e}"
            ) from e

    @property
    def is_available(self) -> bool:
        """Returns True if the model and classes are loaded and ready."""
        return self.model is not None and len(self.class_names) > 0

    def preprocess_image(self, image_input: Union[bytes, io.BytesIO, Image.Image]) -> np.ndarray:
        """
        Preprocesses an image to match the exact requirements validated in predict.py:
        1. Convert image to RGB
        2. Resize to 224 x 224
        3. Convert to NumPy array
        4. Add batch dimension: shape (1, 224, 224, 3)
        
        NOTE: Does NOT divide by 255 because the CNN model architecture contains
        its own internal Rescaling(1/255) layer.
        """
        if isinstance(image_input, bytes):
            if len(image_input) == 0:
                raise ValueError("Uploaded image file is empty.")
            try:
                pil_img = Image.open(io.BytesIO(image_input))
            except UnidentifiedImageError as e:
                raise ValueError("Uploaded file is not a valid or supported image.") from e
        elif isinstance(image_input, io.BytesIO):
            try:
                image_input.seek(0)
                pil_img = Image.open(image_input)
            except UnidentifiedImageError as e:
                raise ValueError("Provided stream is not a valid or supported image.") from e
        elif isinstance(image_input, Image.Image):
            pil_img = image_input
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        # Step 5: Convert to RGB (handles RGBA, grayscale, CMYK, P with transparency, etc.)
        if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
            rgb_img = pil_img.convert("RGBA").convert("RGB")
        else:
            rgb_img = pil_img.convert("RGB")

        # Step 6: Resize to 224 x 224
        resized_img = rgb_img.resize((224, 224), Image.Resampling.BILINEAR)

        # Step 7: Convert to NumPy array
        img_array = np.array(resized_img, dtype=np.float32)

        # Step 8: Add batch dimension -> (1, 224, 224, 3)
        batched_array = np.expand_dims(img_array, axis=0)

        return batched_array

    def predict(
        self,
        image_input: Union[bytes, io.BytesIO, Image.Image],
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Executes CNN inference and returns structured primary & top_k predictions.
        
        Confidence values are returned as decimals between 0.0 and 1.0 (rounded to 4 decimal places).
        """
        if not self.is_available:
            raise RuntimeError("VisionService is not initialized or model is unavailable.")

        # Preprocess input image using validated pipeline
        image_array = self.preprocess_image(image_input)

        # Step 9: Pass image to CNN
        try:
            raw_predictions = self.model.predict(image_array, verbose=0)
        except Exception as e:
            logger.error(f"[VisionService] Inference execution failed: {e}", exc_info=True)
            raise RuntimeError(f"Model inference failed during computation: {e}") from e

        probabilities = raw_predictions[0]

        # In case the output is logits rather than softmax probabilities, apply softmax
        if np.max(probabilities) > 1.0 or np.min(probabilities) < 0.0 or not np.isclose(np.sum(probabilities), 1.0, atol=0.05):
            # Check if output is logits
            exp_preds = np.exp(probabilities - np.max(probabilities))
            probabilities = exp_preds / np.sum(exp_preds)

        # Determine indices sorted by confidence in descending order
        top_indices = np.argsort(probabilities)[::-1][:top_k]

        top_predictions: List[Dict[str, Any]] = []
        for idx in top_indices:
            idx_int = int(idx)
            class_name = (
                self.class_names[idx_int]
                if idx_int < len(self.class_names)
                else f"Class_{idx_int}"
            )
            conf = float(np.clip(probabilities[idx_int], 0.0, 1.0))
            top_predictions.append({
                "name": class_name,
                "confidence": round(conf, 4),
            })

        primary_prediction = top_predictions[0] if top_predictions else {
            "name": "Unknown",
            "confidence": 0.0,
        }

        # Step 10: Return structured predictions
        return {
            "prediction": primary_prediction,
            "top_predictions": top_predictions,
        }


# Singleton instance container
_vision_service_instance: Optional[VisionService] = None


def get_vision_service() -> VisionService:
    """
    Returns the single global VisionService instance.
    Initializes it if not yet loaded.
    """
    global _vision_service_instance
    if _vision_service_instance is None:
        _vision_service_instance = VisionService()
    return _vision_service_instance


# Convenience proxy / default instance
vision_service = get_vision_service()

