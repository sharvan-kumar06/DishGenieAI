import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

try:
    from app.services.freshness_estimator import FreshnessAndExpiryEstimator, get_freshness_estimator
    from app.services.item_segmenter import ItemSegmenter, get_item_segmenter
except ImportError:
    from backend.app.services.freshness_estimator import FreshnessAndExpiryEstimator, get_freshness_estimator
    from backend.app.services.item_segmenter import ItemSegmenter, get_item_segmenter

logger = logging.getLogger(__name__)

# Base directory resolved relative to this file: backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_MODEL_PATH = BACKEND_DIR / "models" / "dishgenie_cnn.keras"
DEFAULT_CLASSES_PATH = BACKEND_DIR / "models" / "dishgenie_classes.json"


class VisionService:
    """
    Reusable Computer Vision Service for DishGenie.
    Loads the trained CNN and class mappings once at startup and performs
    validated preprocessing, multi-item OpenCV segmentation, CNN classification,
    freshness grading, item counting, and visual annotation.
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

        self.segmenter: ItemSegmenter = get_item_segmenter()
        self.freshness_estimator: FreshnessAndExpiryEstimator = get_freshness_estimator()

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

    def preprocess_image(self, image_input: Union[bytes, io.BytesIO, Image.Image, np.ndarray]) -> np.ndarray:
        """
        Preprocesses an image to match the CNN input shape requirements:
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
        elif isinstance(image_input, np.ndarray):
            pil_img = Image.fromarray(image_input)
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        # Convert to RGB (handles RGBA, grayscale, CMYK, P with transparency, etc.)
        if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
            rgb_img = pil_img.convert("RGBA").convert("RGB")
        else:
            rgb_img = pil_img.convert("RGB")

        # Resize to 224 x 224
        resized_img = rgb_img.resize((224, 224), Image.Resampling.BILINEAR)

        # Convert to NumPy array
        img_array = np.array(resized_img, dtype=np.float32)

        # Add batch dimension -> (1, 224, 224, 3)
        batched_array = np.expand_dims(img_array, axis=0)

        return batched_array

    def _infer_array(
        self,
        image_array: np.ndarray,
        top_k: int = 3,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Internal helper: executes CNN forward pass on a preprocessed (1, 224, 224, 3) batch.
        """
        try:
            raw_predictions = self.model.predict(image_array, verbose=0)
        except Exception as e:
            logger.error(f"[VisionService] Inference execution failed: {e}", exc_info=True)
            raise RuntimeError(f"Model inference failed during computation: {e}") from e

        probabilities = raw_predictions[0]

        # Apply softmax if output is logits
        if np.max(probabilities) > 1.0 or np.min(probabilities) < 0.0 or not np.isclose(np.sum(probabilities), 1.0, atol=0.05):
            exp_preds = np.exp(probabilities - np.max(probabilities))
            probabilities = exp_preds / np.sum(exp_preds)

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
        return primary_prediction, top_predictions

    def predict(
        self,
        image_input: Union[bytes, io.BytesIO, Image.Image],
        top_k: int = 3,
        min_confidence: float = 0.50,
    ) -> Dict[str, Any]:
        """
        Full Multi-Object Detection, Counting, and Expiry Estimation Pipeline:
        1. Custom OpenCV contour segmentation & bounding box extraction
        2. Fallback to full-image inference for single-item images
        3. Sequential CNN inference on cropped bounding boxes
        4. Confidence thresholding (probability >= 0.50) to ignore background noise
        5. Visual freshness grading & shelf life calculation for each detected crop
        6. Item counting & inventory aggregation
        7. Visual annotation with bounding boxes, names, and expiry days
        """
        if not self.is_available:
            raise RuntimeError("VisionService is not initialized or model is unavailable.")

        # 1. Load PIL Image and extract RGB NumPy representation
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
        elif isinstance(image_input, np.ndarray):
            pil_img = Image.fromarray(image_input)
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        rgb_img = pil_img.convert("RGB")
        image_rgb = np.array(rgb_img)
        img_h, img_w = image_rgb.shape[:2]

        # 2. Segment items using OpenCV contour discovery
        candidate_boxes = self.segmenter.segment(image_rgb)

        detections: List[Dict[str, Any]] = []
        is_multi_item = len(candidate_boxes) > 1

        # 3. If multiple boxes detected, classify each crop
        if is_multi_item:
            logger.info(f"[VisionService] Processing {len(candidate_boxes)} candidate crops sequentially...")
            for box in candidate_boxes:
                bx, by, bw, bh = box
                crop = self.segmenter.get_padded_crop(image_rgb, box, pad_ratio=0.08)
                if crop.shape[0] < 20 or crop.shape[1] < 20:
                    continue

                crop_batched = self.preprocess_image(crop)
                primary, _ = self._infer_array(crop_batched, top_k=1)

                # Filter low-confidence background crops
                if primary["confidence"] >= min_confidence:
                    freshness = self.freshness_estimator.analyze_crop(crop, primary["name"])
                    detections.append({
                        "ingredient": primary["name"],
                        "confidence": primary["confidence"],
                        "box": {"x": int(bx), "y": int(by), "w": int(bw), "h": int(bh)},
                        "freshness_score": freshness["freshness_score"],
                        "expiry_days": freshness["estimated_expiry_days"],
                        "status": freshness["status"],
                    })
                else:
                    logger.debug(
                        f"[VisionService] Crop at ({bx}, {by}, {bw}, {bh}) dropped: confidence {primary['confidence']} < {min_confidence}"
                    )

        # 4. Fallback to Full-Image Inference if single item or if all crops were low confidence
        if not detections:
            logger.info("[VisionService] Executing full-image inference fallback...")
            full_batched = self.preprocess_image(pil_img)
            primary_full, top_predictions = self._infer_array(full_batched, top_k=top_k)
            freshness = self.freshness_estimator.analyze_crop(image_rgb, primary_full["name"])

            detections.append({
                "ingredient": primary_full["name"],
                "confidence": primary_full["confidence"],
                "box": {"x": 0, "y": 0, "w": int(img_w), "h": int(img_h)},
                "freshness_score": freshness["freshness_score"],
                "expiry_days": freshness["estimated_expiry_days"],
                "status": freshness["status"],
            })
        else:
            # Build top_predictions from detections for backward compatibility
            sorted_detections = sorted(detections, key=lambda x: x["confidence"], reverse=True)
            top_predictions = [
                {"name": d["ingredient"], "confidence": d["confidence"]}
                for d in sorted_detections[:top_k]
            ]

        # 5. Aggregate item counts and inventory
        ingredient_map: Dict[str, Dict[str, Any]] = {}
        for det in detections:
            ing = det["ingredient"]
            if ing not in ingredient_map:
                ingredient_map[ing] = {
                    "ingredient": ing,
                    "count": 0,
                    "min_expiry_days": det["expiry_days"],
                    "status": det["status"],
                }
            ingredient_map[ing]["count"] += 1
            if det["expiry_days"] < ingredient_map[ing]["min_expiry_days"]:
                ingredient_map[ing]["min_expiry_days"] = det["expiry_days"]

        # Recalculate status for aggregated inventory items
        for ing, info in ingredient_map.items():
            if info["min_expiry_days"] <= 3:
                info["status"] = "Use First"
            elif info["min_expiry_days"] <= 7:
                info["status"] = "Medium"
            else:
                info["status"] = "Fresh"

        inventory = list(ingredient_map.values())
        total_items_detected = sum(item["count"] for item in inventory)

        # 6. Generate annotated visualization image
        annotated_rgb = self.segmenter.annotate_image(image_rgb, detections)
        annotated_b64 = self.segmenter.encode_base64_jpeg(annotated_rgb)

        primary_prediction = top_predictions[0] if top_predictions else {
            "name": detections[0]["ingredient"],
            "confidence": detections[0]["confidence"],
        }

        logger.info(
            f"[VisionService] Completed multi-item detection: {len(detections)} instances, "
            f"{len(inventory)} unique produce classes (Total count: {total_items_detected})."
        )

        return {
            "prediction": primary_prediction,
            "top_predictions": top_predictions,
            "inventory": inventory,
            "detections": detections,
            "annotated_image": annotated_b64,
            "total_items_detected": total_items_detected,
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
