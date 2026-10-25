"""
Test suite for DishGenieAI custom OpenCV Multi-Item Segmentation, Counting,
Visual Freshness Grading, Expiry Estimation, and Qwen2.5 Prompt Injection.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.app.schemas.recipe import InventoryItem, RecipePreferences, RecipeRequest
from backend.app.services.freshness_estimator import (
    BASE_SHELF_LIFE_DAYS,
    FreshnessAndExpiryEstimator,
    get_base_shelf_life,
)
from backend.app.services.item_segmenter import (
    ItemSegmenter,
    merge_boxes,
    calculate_iou,
)
from backend.app.services.recipe_service import RecipeService
from backend.app.services.vision_service import DEFAULT_CLASSES_PATH, VisionService


class TestItemSegmenter(unittest.TestCase):
    def setUp(self):
        self.segmenter = ItemSegmenter(
            min_area_ratio=0.01,
            max_area_ratio=0.95,
        )

    def test_single_item_fallback(self):
        # A uniform blank image with no distinct edges/contours
        blank_img = np.full((300, 300, 3), 240, dtype=np.uint8)
        boxes = self.segmenter.segment(blank_img)
        # Should fall back to the entire image
        self.assertEqual(len(boxes), 1)
        self.assertEqual(boxes[0], (0, 0, 300, 300))

    def test_multi_item_segmentation(self):
        # Create a synthetic image with 3 distinct items on a clean background
        img = np.full((400, 500, 3), 245, dtype=np.uint8)
        # Item 1: dark green circle
        cv2.circle(img, (100, 150), 45, (30, 140, 40), -1)
        # Item 2: red rectangle
        cv2.rectangle(img, (240, 100), (330, 200), (20, 30, 200), -1)
        # Item 3: orange circle
        cv2.circle(img, (400, 280), 50, (10, 120, 220), -1)

        boxes = self.segmenter.segment(img)
        self.assertGreaterEqual(len(boxes), 3)

    def test_iou_box_merging(self):
        # Two highly overlapping boxes
        b1 = (50, 50, 100, 100)
        b2 = (55, 55, 95, 95)
        merged = merge_boxes([b1, b2], iou_threshold=0.35)
        self.assertEqual(len(merged), 1)

    def test_annotation_generation(self):
        img = np.full((200, 200, 3), 200, dtype=np.uint8)
        detections = [
            {
                "box": {"x": 10, "y": 10, "w": 80, "h": 80},
                "ingredient": "tomato",
                "confidence": 0.92,
                "expiry_days": 4,
                "status": "Medium",
            }
        ]
        annotated = self.segmenter.annotate_image(img, detections)
        self.assertEqual(annotated.shape, img.shape)
        b64 = self.segmenter.encode_base64_jpeg(annotated)
        self.assertTrue(b64.startswith("data:image/jpeg;base64,"))
        self.assertGreater(len(b64), 100)


class TestFreshnessAndExpiryEstimator(unittest.TestCase):
    def setUp(self):
        self.estimator = FreshnessAndExpiryEstimator()

    def test_all_247_classes_mapped(self):
        # Verify all classes in dishgenie_classes.json have valid base shelf life
        if DEFAULT_CLASSES_PATH.exists():
            with open(DEFAULT_CLASSES_PATH, "r", encoding="utf-8") as f:
                classes = json.load(f)
            for cls in classes:
                days = get_base_shelf_life(cls)
                self.assertIsInstance(days, int)
                self.assertGreaterEqual(days, 1)

    def test_fresh_vs_stale_scoring(self):
        # Create a fresh vibrant green patch
        fresh_crop = np.zeros((100, 100, 3), dtype=np.uint8)
        fresh_crop[:, :] = (40, 200, 30)  # RGB vibrant green

        res_fresh = self.estimator.analyze_crop(fresh_crop, "spinach")
        self.assertGreaterEqual(res_fresh["freshness_score"], 0.70)
        self.assertIn(res_fresh["status"], ["Fresh", "Medium"])

        # Create a decayed / brown spotted patch
        decayed_crop = np.zeros((100, 100, 3), dtype=np.uint8)
        decayed_crop[:, :] = (60, 40, 20)  # Dark brownish
        decayed_crop[::2, ::2] = (15, 15, 15)

        res_decayed = self.estimator.analyze_crop(decayed_crop, "spinach")
        self.assertLess(res_decayed["freshness_score"], res_fresh["freshness_score"])
        self.assertLessEqual(res_decayed["estimated_expiry_days"], res_fresh["estimated_expiry_days"])

    def test_use_first_flag_threshold(self):
        res = self.estimator.analyze_crop(
            np.full((80, 80, 3), 30, dtype=np.uint8),
            "cilantro",
        )
        self.assertLessEqual(res["estimated_expiry_days"], 3)
        self.assertEqual(res["status"], "Use First")


class TestVisionServiceMultiObjectInference(unittest.TestCase):
    def test_multi_crop_inventory_aggregation(self):
        service = VisionService()
        service.class_names = ["tomato", "potato", "onion", "carrot"]

        # Mock model instance
        mock_model = MagicMock()
        service.model = mock_model

        tomato_name = "tomato"
        potato_name = "potato"
        tomato_idx = 0
        potato_idx = 1

        # Valid probability distributions that sum to 1.0
        prob_tomato = np.array([[0.94, 0.02, 0.02, 0.02]], dtype=np.float32)
        prob_potato = np.array([[0.02, 0.94, 0.02, 0.02]], dtype=np.float32)

        # Let model return tomato twice, then potato
        call_count = {"count": 0}

        def mock_predict_fn(batch, verbose=0):
            call_count["count"] += 1
            if call_count["count"] <= 2:
                return prob_tomato
            return prob_potato

        mock_model.predict.side_effect = mock_predict_fn

        # Synthetic multi-item image with 3 distinct shapes that pass contour detection
        img = np.full((400, 500, 3), 245, dtype=np.uint8)
        cv2.circle(img, (100, 150), 45, (30, 140, 40), -1)
        cv2.rectangle(img, (240, 100), (330, 200), (20, 30, 200), -1)
        cv2.circle(img, (400, 280), 50, (10, 120, 220), -1)

        result = service.predict(img)

        # Check that result contains inventory and detections
        self.assertIn("inventory", result)
        self.assertIn("detections", result)
        self.assertIn("annotated_image", result)

        inventory_map = {item["ingredient"]: item for item in result["inventory"]}
        self.assertIn(tomato_name, inventory_map)
        self.assertIn(potato_name, inventory_map)
        self.assertEqual(inventory_map[tomato_name]["count"], 2)
        self.assertEqual(inventory_map[potato_name]["count"], 1)
        self.assertEqual(result["total_items_detected"], 3)


class TestRecipePromptInjection(unittest.TestCase):
    def test_prompt_includes_inventory_and_use_first(self):
        service = RecipeService(load_weights=False)

        req = RecipeRequest(
            ingredients=["tomato", "potato", "spinach"],
            inventory=[
                InventoryItem(
                    ingredient="spinach",
                    count=2,
                    min_expiry_days=2,
                    status="Use First",
                ),
                InventoryItem(
                    ingredient="tomato",
                    count=3,
                    min_expiry_days=6,
                    status="Fresh",
                ),
            ],
            preferences=RecipePreferences(
                diet="Vegetarian",
                cuisine="Indian",
                cooking_time=30,
                difficulty="Easy",
                servings=2,
            ),
        )

        messages = service.build_prompt_and_messages(
            ingredients=req.ingredients,
            preferences=req.preferences,
            candidates=[],
            inventory=req.inventory,
        )

        system_content = messages[0]["content"]
        user_content = messages[1]["content"]

        # Verify prompt injection
        self.assertIn("Available Inventory", user_content)
        self.assertIn("Spinach", user_content)
        self.assertIn("USE FIRST", user_content)
        self.assertIn("2 item(s)", user_content)
        self.assertIn("Tomato", user_content)
        self.assertIn("FOOD WASTE PREVENTION", system_content)
        self.assertIn("SHOPPING LIST SHORTFALL", system_content)


if __name__ == "__main__":
    unittest.main()
