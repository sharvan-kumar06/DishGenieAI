"""
Custom OpenCV Multi-Item Segmentation and Bounding-Box Detection Engine.
Isolates multiple individual produce items from a single image using deterministic
morphology, edge detection, contour filtering, and IoU-based bounding box merging.
Provides fallback to full-image inference for single-item images.
"""

import base64
import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def calculate_iou(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> float:
    """
    Computes Intersection-over-Union (IoU) between two bounding boxes (x, y, w, h).
    """
    xa1, ya1, wa, ha = box_a
    xa2, ya2 = xa1 + wa, ya1 + ha

    xb1, yb1, wb, hb = box_b
    xb2, yb2 = xb1 + wb, yb1 + hb

    # Intersection coordinates
    xi1 = max(xa1, xb1)
    yi1 = max(ya1, yb1)
    xi2 = min(xa2, xb2)
    yi2 = min(ya2, yb2)

    inter_w = max(0, xi2 - xi1)
    inter_h = max(0, yi2 - yi1)
    inter_area = inter_w * inter_h

    area_a = wa * ha
    area_b = wb * hb

    union_area = float(area_a + area_b - inter_area)
    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def is_contained(inner: Tuple[int, int, int, int], outer: Tuple[int, int, int, int], threshold: float = 0.70) -> bool:
    """
    Checks if 'inner' box is largely contained inside 'outer' box.
    """
    xi, yi, wi, hi = inner
    xo, yo, wo, ho = outer

    inter_x1 = max(xi, xo)
    inter_y1 = max(yi, yo)
    inter_x2 = min(xi + wi, xo + wo)
    inter_y2 = min(yi + hi, yo + ho)

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    inner_area = wi * hi
    if inner_area <= 0:
        return False

    return (inter_area / inner_area) >= threshold


def merge_boxes(boxes: List[Tuple[int, int, int, int]], iou_threshold: float = 0.35) -> List[Tuple[int, int, int, int]]:
    """
    Non-Maximum Suppression & overlapping box merging for candidate contours.
    Merges overlapping boxes into their enclosing bounding box.
    """
    if not boxes:
        return []

    merged = list(boxes)
    changed = True

    while changed:
        changed = False
        new_merged = []
        skip_indices = set()

        for i in range(len(merged)):
            if i in skip_indices:
                continue

            current_box = merged[i]
            for j in range(i + 1, len(merged)):
                if j in skip_indices:
                    continue

                compare_box = merged[j]
                iou = calculate_iou(current_box, compare_box)
                contained_ij = is_contained(current_box, compare_box)
                contained_ji = is_contained(compare_box, current_box)

                if iou >= iou_threshold or contained_ij or contained_ji:
                    # Merge boxes into enclosing boundary
                    x1 = min(current_box[0], compare_box[0])
                    y1 = min(current_box[1], compare_box[1])
                    x2 = max(current_box[0] + current_box[2], compare_box[0] + compare_box[2])
                    y2 = max(current_box[1] + current_box[3], compare_box[1] + compare_box[3])
                    current_box = (x1, y1, x2 - x1, y2 - y1)
                    skip_indices.add(j)
                    changed = True

            new_merged.append(current_box)

        merged = new_merged

    return merged


class ItemSegmenter:
    """
    Custom OpenCV pipeline to segment multiple food items from a single image.
    Uses:
      1. Gaussian blur
      2. Adaptive thresholding & Otsu edge detection
      3. Morphological closing & dilation
      4. Contour discovery & area filtering
      5. Non-Maximum Suppression / IoU merging
      6. Full-image fallback for single-item images
    """

    def __init__(self, min_area_ratio: float = 0.005, max_area_ratio: float = 0.92):
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio

    def segment(self, image_rgb: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Segments food items from an RGB image.
        Returns a list of bounding boxes (x, y, w, h).
        If only 1 or no clear contour is found, returns [(0, 0, W, H)] as full-image fallback.
        """
        if image_rgb is None or image_rgb.size == 0:
            return []

        h, w = image_rgb.shape[:2]
        total_area = float(h * w)

        min_area = max(1000, int(total_area * self.min_area_ratio))
        max_area = int(total_area * self.max_area_ratio)

        # 1. Convert to Grayscale
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

        # 2. Gaussian Blur to reduce background noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. Dual-path foreground segmentation:
        # Path A: Otsu automatic thresholding
        _, thresh_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Path B: Canny edge detection
        edges = cv2.Canny(blurred, 30, 110)

        # Path C: Adaptive Gaussian thresholding for uneven lighting
        thresh_adapt = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 4
        )

        # Combine edge and intensity maps
        foreground_map = cv2.bitwise_or(thresh_otsu, edges)
        foreground_map = cv2.bitwise_or(foreground_map, thresh_adapt)

        # 4. Morphological closing to fill object interiors
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        closed = cv2.morphologyEx(foreground_map, cv2.MORPH_CLOSE, kernel_close, iterations=2)

        # Small dilation to bridge close segments of the same item
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated = cv2.dilate(closed, kernel_dilate, iterations=1)

        # 5. Find external contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidate_boxes: List[Tuple[int, int, int, int]] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            bx, by, bw, bh = cv2.boundingRect(cnt)
            box_area = bw * bh

            if box_area < min_area:
                continue

            # Discard extreme aspect ratios (lines, borders)
            aspect = float(bw) / float(bh) if bh > 0 else 1.0
            if aspect < 0.12 or aspect > 8.0:
                continue

            # Ignore borders that encompass almost the entire image if smaller items exist
            if box_area > max_area and len(contours) > 1:
                continue

            candidate_boxes.append((bx, by, bw, bh))

        # 6. Merge overlapping boxes with IoU suppression
        merged_boxes = merge_boxes(candidate_boxes, iou_threshold=0.30)

        # 7. Fallback Logic:
        # If no contours or only 1 contour found, fall back to passing the full image
        if len(merged_boxes) <= 1:
            logger.info(f"[ItemSegmenter] Single item or ambiguous contours ({len(merged_boxes)}); falling back to full image.")
            return [(0, 0, w, h)]

        logger.info(f"[ItemSegmenter] Discovered {len(merged_boxes)} isolated item bounding boxes.")
        return merged_boxes

    @staticmethod
    def get_padded_crop(
        image_rgb: np.ndarray,
        box: Tuple[int, int, int, int],
        pad_ratio: float = 0.08,
    ) -> np.ndarray:
        """
        Extracts a crop from image_rgb for the given bounding box (x, y, w, h)
        with contextual padding (clamped to image dimensions).
        """
        h, w = image_rgb.shape[:2]
        bx, by, bw, bh = box

        pad_x = int(bw * pad_ratio)
        pad_y = int(bh * pad_ratio)

        x1 = max(0, bx - pad_x)
        y1 = max(0, by - pad_y)
        x2 = min(w, bx + bw + pad_x)
        y2 = min(h, by + bh + pad_y)

        return image_rgb[y1:y2, x1:x2].copy()

    @staticmethod
    def annotate_image(
        image_rgb: np.ndarray,
        detections: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Draws bounding boxes, ingredient names, counts, and expiry days on a copy of image_rgb.
        Color coding:
          - 'Use First': Red/Coral (RGB: 225, 29, 72)
          - 'Medium': Amber/Yellow (RGB: 217, 119, 6)
          - 'Fresh': Emerald/Green (RGB: 5, 150, 105)
        """
        annotated = image_rgb.copy()
        h, w = annotated.shape[:2]

        color_map = {
            "Use First": (225, 29, 72),   # Rose/Red
            "Medium": (217, 119, 6),      # Amber
            "Fresh": (5, 150, 105),       # Emerald
        }

        for idx, det in enumerate(detections, 1):
            box = det.get("box", {})
            bx = int(box.get("x", 0))
            by = int(box.get("y", 0))
            bw = int(box.get("w", w))
            bh = int(box.get("h", h))

            status = det.get("status", "Fresh")
            color = color_map.get(status, (5, 150, 105))

            name = det.get("ingredient", "Item").replace("_", " ").title()
            expiry = det.get("expiry_days", 7)
            conf_pct = int(round(det.get("confidence", 0.9) * 100))

            if status == "Use First":
                tag = f"#{idx} {name} ({expiry}d) [USE FIRST]"
            else:
                tag = f"#{idx} {name} ({expiry}d)"

            # Draw outer rectangle with rounded corner aesthetic or clean 2-3px border
            thickness = max(2, int(min(h, w) * 0.004))
            cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), color, thickness)

            # Draw label banner background
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.45, min(0.85, w * 0.0008))
            font_thickness = max(1, int(thickness * 0.7))
            (text_w, text_h), baseline = cv2.getTextSize(tag, font, font_scale, font_thickness)

            tag_y1 = max(0, by - text_h - 10)
            tag_y2 = by
            tag_x1 = bx
            tag_x2 = min(w, bx + text_w + 12)

            # If tag would go off top, draw inside box
            if by - text_h - 10 < 0:
                tag_y1 = by
                tag_y2 = by + text_h + 10

            cv2.rectangle(annotated, (tag_x1, tag_y1), (tag_x2, tag_y2), color, -1)
            cv2.putText(
                annotated,
                tag,
                (tag_x1 + 6, tag_y2 - 6),
                font,
                font_scale,
                (255, 255, 255),
                font_thickness,
                cv2.LINE_AA,
            )

        return annotated

    @staticmethod
    def encode_base64_jpeg(image_rgb: np.ndarray, quality: int = 88) -> str:
        """
        Encodes an RGB NumPy image to a Base64 data URL: 'data:image/jpeg;base64,...'
        """
        # Convert RGB to BGR for OpenCV encoding
        bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        success, buffer = cv2.imencode(".jpg", bgr, encode_params)
        if not success:
            return ""
        b64_str = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"


# Global singleton instance
_segmenter_instance: Optional[ItemSegmenter] = None


def get_item_segmenter() -> ItemSegmenter:
    global _segmenter_instance
    if _segmenter_instance is None:
        _segmenter_instance = ItemSegmenter()
    return _segmenter_instance
