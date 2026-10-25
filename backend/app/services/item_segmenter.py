"""
Custom OpenCV Multi-Item Segmentation and Bounding-Box Detection Engine.
Deterministic Watershed Segmentation + Multi-Scale Bounding-Box Splitting.
Separates touching or adjacent produce items using:
  1. LAB + HSV border background color estimation & background distance subtraction.
  2. Morphological opening (MORPH_OPEN) to prevent merging adjacent items.
  3. Distance Transform (DIST_L2) peak detection (> 0.45 * max) for seed marker isolation.
  4. cv2.watershed boundary partitioning along contact lines.
  5. Geometric & Color-space multi-item splitting fallback for oversized/elongated boxes.
  6. Robust single-item full-image fallback.
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


def is_contained(inner: Tuple[int, int, int, int], outer: Tuple[int, int, int, int], threshold: float = 0.75) -> bool:
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


def merge_boxes(boxes: List[Tuple[int, int, int, int]], iou_threshold: float = 0.30) -> List[Tuple[int, int, int, int]]:
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


def split_elongated_or_large_box(
    box: Tuple[int, int, int, int],
    img_shape: Optional[Tuple[int, ...]] = None,
    image_rgb: Optional[np.ndarray] = None,
    max_area_ratio: float = 0.18,
    max_aspect_ratio: float = 1.6,
) -> List[Tuple[int, int, int, int]]:
    """
    Multi-Scale Blob Splitting Fallback:
    If a bounding box covers > 18% of image area OR has aspect ratio > 1.6,
    splits it along its longest axis into two overlapping sub-boxes (16% overlap).
    """
    if img_shape is not None:
        img_h, img_w = img_shape[:2]
    elif image_rgb is not None:
        img_h, img_w = image_rgb.shape[:2]
    else:
        img_h, img_w = 800, 800

    total_area = float(img_h * img_w)
    bx, by, bw, bh = box
    box_area = float(bw * bh)

    aspect = float(max(bw, bh)) / float(max(1, min(bw, bh)))
    is_oversized = (box_area / total_area) > max_area_ratio
    is_elongated = aspect > max_aspect_ratio

    if not (is_oversized or is_elongated):
        return [box]

    # Split along longest axis with 16% overlap
    if bw >= bh:
        # Horizontal split (side-by-side items)
        sub_w = int(bw * 0.58)
        box1 = (bx, by, sub_w, bh)
        box2 = (min(img_w - 1, bx + bw - sub_w), by, sub_w, bh)
    else:
        # Vertical split (stacked items)
        sub_h = int(bh * 0.58)
        box1 = (bx, by, bw, sub_h)
        box2 = (bx, min(img_h - 1, by + bh - sub_h), bw, sub_h)

    return [box1, box2]


# Global cached YOLO detector instance
_YOLO_DETECTOR = None
_YOLO_LOAD_FAILED = False


def get_yolo_rpn_detector():
    """
    Returns cached lightweight YOLO detector as class-agnostic Region Proposal Network (RPN).
    First attempts YOLO('yolov8s-worldv2.pt') with produce vocabulary;
    falls back to YOLO('yolov8n.pt'), and falls back to OpenCV Watershed if offline.
    """
    global _YOLO_DETECTOR, _YOLO_LOAD_FAILED
    if _YOLO_DETECTOR is not None:
        return _YOLO_DETECTOR
    if _YOLO_LOAD_FAILED:
        return None
    try:
        from ultralytics import YOLO
        try:
            detector = YOLO("yolov8s-worldv2.pt")
            detector.set_classes(["fruit", "vegetable", "food", "produce"])
            logger.info("[ItemSegmenter] Loaded YOLOv8s-WorldV2 with produce vocabulary.")
        except Exception as e:
            logger.warning(f"[ItemSegmenter] YOLO-World initialization failed, falling back to yolov8n.pt: {e}")
            detector = YOLO("yolov8n.pt")
            logger.info("[ItemSegmenter] Loaded YOLOv8n lightweight detector.")
        _YOLO_DETECTOR = detector
        return _YOLO_DETECTOR
    except Exception as err:
        logger.warning(f"[ItemSegmenter] Ultralytics YOLO not available, using OpenCV Watershed: {err}")
        _YOLO_LOAD_FAILED = True
        return None


class ItemSegmenter:
    """
    Two-Stage Hybrid Instance Localization & Computer Vision Engine:
      - Stage 1: Pretrained Deep Learning Region Proposal Network (YOLO conf=0.15, iou=0.45)
                 used strictly as class-agnostic bounding-box localizer.
      - Fallback: OpenCV Watershed + CLAHE valley separation for dense touching piles.
    """

    def __init__(
        self,
        min_area_ratio: float = 0.06,
        max_area_ratio: float = 0.95,
        min_dim_ratio: float = 0.15,
        peak_ratio: float = 0.45,
    ):
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio
        self.min_dim_ratio = min_dim_ratio
        self.peak_ratio = peak_ratio

    def propose_regions_yolo(
        self,
        image_rgb: np.ndarray,
        conf: float = 0.15,
        iou: float = 0.45,
    ) -> List[Tuple[int, int, int, int]]:
        """
        Stage 1: Pretrained Instance Localization (Region Proposal Network).
        Uses a lightweight pretrained detector as a Class-Agnostic Region Proposal Network (RPN).
        Detects individual fruit/vegetable instances in dense or overlapping piles (conf=0.15, iou=0.45).
        Completely ignores YOLO's predicted class labels.
        """
        detector = get_yolo_rpn_detector()
        if detector is None or image_rgb is None or image_rgb.size == 0:
            return []

        h, w = image_rgb.shape[:2]
        total_pixels = float(h * w)
        min_area = max(250, int(total_pixels * 0.015))

        try:
            results = detector.predict(image_rgb, conf=conf, iou=iou, verbose=False)
            if not results or len(results) == 0 or results[0].boxes is None:
                return []

            boxes_xyxy = results[0].boxes.xyxy.cpu().numpy()
            if len(boxes_xyxy) == 0:
                return []

            proposed_boxes: List[Tuple[int, int, int, int]] = []
            for box in boxes_xyxy:
                x1, y1, x2, y2 = box
                bx = max(0, int(round(x1)))
                by = max(0, int(round(y1)))
                bw = min(w - bx, int(round(x2 - x1)))
                bh = min(h - by, int(round(y2 - y1)))

                area = bw * bh
                if area < min_area:
                    continue
                # If multiple boxes were detected, filter out full-image proposals that encompass the scene
                if len(boxes_xyxy) > 1 and (area / total_pixels) > 0.90:
                    continue

                proposed_boxes.append((bx, by, bw, bh))

            # Limit maximum counted units to 12
            if len(proposed_boxes) > 12:
                proposed_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
                proposed_boxes = proposed_boxes[:12]

            return proposed_boxes
        except Exception as e:
            logger.warning(f"[ItemSegmenter] YOLO RPN inference error: {e}")
            return []

    @staticmethod
    def estimate_background_colors(image_rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Estimates representative background colors in LAB and HSV spaces
        by sampling 4 corner patches from the image borders.
        """
        h, w = image_rgb.shape[:2]
        ch = max(4, int(h * 0.08))
        cw = max(4, int(w * 0.08))

        # Sample 4 corners
        c1 = image_rgb[0:ch, 0:cw]
        c2 = image_rgb[0:ch, w - cw:w]
        c3 = image_rgb[h - ch:h, 0:cw]
        c4 = image_rgb[h - ch:h, w - cw:w]
        corners_rgb = np.vstack([c1.reshape(-1, 3), c2.reshape(-1, 3), c3.reshape(-1, 3), c4.reshape(-1, 3)])

        # Convert corners to LAB and HSV
        corners_bgr = cv2.cvtColor(corners_rgb.reshape(-1, 1, 3), cv2.COLOR_RGB2BGR)
        corners_lab = cv2.cvtColor(corners_bgr, cv2.COLOR_BGR2LAB).reshape(-1, 3)
        corners_hsv = cv2.cvtColor(corners_bgr, cv2.COLOR_BGR2HSV).reshape(-1, 3)

        med_lab = np.median(corners_lab, axis=0)
        med_hsv = np.median(corners_hsv, axis=0)

        return med_lab, med_hsv

    def create_foreground_mask(self, image_rgb: np.ndarray) -> np.ndarray:
        """
        Builds a clean binary foreground mask using background distance subtraction,
        Otsu adaptive thresholding, and morphological opening (NO large closing).
        """
        h, w = image_rgb.shape[:2]
        med_lab, med_hsv = self.estimate_background_colors(image_rgb)

        # 1. Color space transformations
        bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        # 2. Euclidean color distance from background in LAB space
        diff_lab = lab - med_lab.reshape(1, 1, 3)
        dist_lab = np.sqrt(np.sum(diff_lab ** 2, axis=2))
        dist_norm = cv2.normalize(dist_lab, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # 3. Dual thresholding: Otsu on color distance + Adaptive on intensity
        _, mask_otsu = cv2.threshold(dist_norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        blurred_gray = cv2.GaussianBlur(gray, (5, 5), 0)
        mask_adapt = cv2.adaptiveThreshold(
            blurred_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 4
        )

        # Edge cues to preserve boundaries
        edges = cv2.Canny(blurred_gray, 30, 110)

        # Combine cues: primarily color distance with edge/contrast support
        fg_raw = cv2.bitwise_or(mask_otsu, edges)
        fg_raw = cv2.bitwise_or(fg_raw, mask_adapt)

        # 4. Strict MORPH_OPEN to clear bridges and separate touching items
        # Avoid large closing: large closing merges separate fruits/vegetables!
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_open = cv2.morphologyEx(fg_raw, cv2.MORPH_OPEN, kernel_open, iterations=2)

        # Mild dilation (3x3) to restore true interior edges without bridging
        kernel_mild = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_clean = cv2.dilate(fg_open, kernel_mild, iterations=1)

        return fg_clean

    def filter_candidate_boxes(
        self,
        boxes: List[Tuple[int, int, int, int]],
        img_shape: Tuple[int, int],
    ) -> List[Tuple[int, int, int, int]]:
        """
        Applies strict filtering to eliminate tiny internal texture crops, shadow creases,
        and internal boxes contained within larger produce regions:
          1. Discard boxes with area < 6% of image area, or width < 15%, or height < 15%.
          2. Discard boxes that are > 70% contained inside another larger detected box.
          3. Apply Non-Maximum Suppression (IoU threshold = 0.30) to merge overlapping boxes.
        """
        img_h, img_w = img_shape[:2]
        total_area = float(img_h * img_w)
        min_area = total_area * self.min_area_ratio
        min_w = img_w * self.min_dim_ratio
        min_h = img_h * self.min_dim_ratio

        # 1. Size & dimension thresholding
        valid_size_boxes = []
        for box in boxes:
            bx, by, bw, bh = box
            area = bw * bh
            if area < min_area:
                continue
            if bw < min_w or bh < min_h:
                continue
            valid_size_boxes.append(box)

        if not valid_size_boxes:
            return []

        # 2. Internal containment filtering (> 70% contained inside a larger box)
        uncontained_boxes = []
        for i, box_i in enumerate(valid_size_boxes):
            area_i = box_i[2] * box_i[3]
            is_internal = False
            for j, box_j in enumerate(valid_size_boxes):
                if i == j:
                    continue
                area_j = box_j[2] * box_j[3]
                if area_j > area_i and is_contained(box_i, box_j, threshold=0.70):
                    is_internal = True
                    break
            if not is_internal:
                uncontained_boxes.append(box_i)

        # 3. Non-Maximum Suppression with IoU = 0.30
        merged = merge_boxes(uncontained_boxes, iou_threshold=0.30)
        return merged

    def segment_watershed(
        self,
        image_rgb: np.ndarray,
        fg_mask: np.ndarray,
    ) -> Tuple[List[Tuple[int, int, int, int]], int]:
        """
        Applies Distance Transform and Watershed segmentation to split touching objects.
        Applies strong 21x21 Gaussian smoothing and center NMS (min distance 18% of min dim)
        to prevent textured bumps on bitter gourd/papaya/capsicum from overcounting.
        Caps dense homogeneous piles to a maximum of 12 counted units.
        Returns extracted bounding boxes [(x, y, w, h), ...] and total raw peak marker count.
        """
        h, w = image_rgb.shape[:2]
        total_area = float(h * w)
        min_area = max(400, int(total_area * self.min_area_ratio))
        max_area = int(total_area * self.max_area_ratio)

        # 1. Distance transform on foreground mask
        dist_transform = cv2.distanceTransform(fg_mask, cv2.DIST_L2, 5)
        dist_raw_max = float(dist_transform.max())

        if dist_raw_max <= 1.0:
            return [], 1

        # 2. Strong Gaussian smoothing (kernel = 21x21) to eliminate textured bumps and ridges
        dist_smooth = cv2.GaussianBlur(dist_transform, (21, 21), 0)
        dist_max = float(dist_smooth.max())
        if dist_max <= 0.5:
            dist_smooth = dist_transform
            dist_max = dist_raw_max

        # 3. Minimum Euclidean distance between detected object centers: 18% of min(image_width, image_height)
        min_peak_dist = max(18.0, 0.18 * min(h, w))

        # Local maxima detection on smoothed distance transform
        k_size = max(15, int(min_peak_dist * 0.70))
        if k_size % 2 == 0:
            k_size += 1
        kernel_local = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        dilated_dist = cv2.dilate(dist_smooth, kernel_local)
        local_peaks_mask = (dist_smooth == dilated_dist) & (dist_smooth > self.peak_ratio * dist_max)

        peak_y, peak_x = np.where(local_peaks_mask)
        peak_points = []
        for py, px in zip(peak_y, peak_x):
            peak_points.append((int(px), int(py), float(dist_smooth[py, px])))

        # Sort peak candidates by smoothed distance transform intensity descending
        peak_points.sort(key=lambda p: p[2], reverse=True)

        # Greedy Non-Maximum Suppression on center points with min_peak_dist (cap at 12 units)
        accepted_peaks: List[Tuple[int, int]] = []
        for px, py, _ in peak_points:
            too_close = False
            for ax, ay in accepted_peaks:
                if np.hypot(px - ax, py - ay) < min_peak_dist:
                    too_close = True
                    break
            if not too_close:
                accepted_peaks.append((px, py))
                if len(accepted_peaks) >= 12:
                    break

        # Fallback to single center peak if NMS produced 0
        if not accepted_peaks:
            max_pos = np.unravel_index(np.argmax(dist_smooth), dist_smooth.shape)
            accepted_peaks = [(int(max_pos[1]), int(max_pos[0]))]

        num_peaks = len(accepted_peaks)

        # 4. Create watershed markers from accepted peak seeds
        peak_seeds = np.zeros((h, w), dtype=np.uint8)
        markers = np.zeros((h, w), dtype=np.int32)
        seed_r = max(4, int(min_peak_dist * 0.15))
        for i, (px, py) in enumerate(accepted_peaks, start=1):
            cv2.circle(peak_seeds, (px, py), seed_r, 255, -1)
            cv2.circle(markers, (px, py), seed_r, i, -1)

        # Background and unknown boundary regions
        kernel_bg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        sure_bg = cv2.dilate(fg_mask, kernel_bg, iterations=2)
        unknown = cv2.subtract(sure_bg, peak_seeds)

        markers = markers + 1
        markers[unknown == 255] = 0

        # 5. Execute Watershed
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        cv2.watershed(image_bgr, markers)

        # 6. Extract isolated bounding boxes from watershed components
        detected_boxes: List[Tuple[int, int, int, int]] = []
        for label_id in range(2, num_peaks + 2):
            comp_mask = (markers == label_id).astype(np.uint8)
            cnts, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if area < min_area:
                    continue
                bx, by, bw, bh = cv2.boundingRect(cnt)
                box_area = bw * bh
                if box_area < min_area or box_area > max_area:
                    continue

                aspect = float(bw) / float(bh) if bh > 0 else 1.0
                if aspect < 0.12 or aspect > 8.0:
                    continue

                detected_boxes.append((bx, by, bw, bh))

        return detected_boxes, num_peaks

    @staticmethod
    def split_elongated_or_large_box(
        image_rgb: np.ndarray,
        box: Tuple[int, int, int, int],
        max_area_ratio: float = 0.18,
        max_aspect_ratio: float = 1.6,
    ) -> List[Tuple[int, int, int, int]]:
        """Static helper forwarding to split_elongated_or_large_box."""
        return split_elongated_or_large_box(
            box=box,
            image_rgb=image_rgb,
            max_area_ratio=max_area_ratio,
            max_aspect_ratio=max_aspect_ratio,
        )

    def segment_dense_pile(
        self,
        image_rgb: np.ndarray,
        fg_mask: np.ndarray,
    ) -> List[Tuple[int, int, int, int]]:
        """
        Dense Homogeneous Pile Mode:
          - Applies CLAHE (clipLimit=2.5, tileGridSize=(8,8)) to L channel in LAB color space.
          - Inverts dark shadow valleys/edges between touching items (Canny edges + dark valley
            thresholding where L < 35th percentile) to separate touching fruits/vegetables.
          - Computes cv2.distanceTransform on the valley-separated mask, smoothed with GaussianBlur(15, 15).
          - Finds local maxima peaks with min_distance = int(0.18 * min(h, w)) and threshold_rel = 0.35.
          - Clamps total pile count between 2 and 12.
          - Generates individual bounding boxes around each valid peak (no containment deletion).
        """
        h, w = image_rgb.shape[:2]
        min_dim = min(h, w)
        min_peak_dist = max(18.0, 0.18 * min_dim)

        # 1. LAB + CLAHE on L channel
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        l_chan = lab[:, :, 0]
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l_clahe = clahe.apply(l_chan)

        # 2. Invert dark shadow valleys/edges between touching items
        fg_indices = np.where(fg_mask > 0)
        if len(fg_indices[0]) > 0:
            fg_l_vals = l_clahe[fg_indices]
            p35 = float(np.percentile(fg_l_vals, 35))
            dark_valleys = (l_clahe < p35) & (fg_mask > 0)
        else:
            dark_valleys = np.zeros((h, w), dtype=bool)

        edges = cv2.Canny(l_clahe, 40, 120)
        edges_in_fg = (edges > 0) & (fg_mask > 0)

        crevices = dark_valleys | edges_in_fg
        kernel_crevice = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated_crevices = cv2.dilate(crevices.astype(np.uint8), kernel_crevice, iterations=1)

        valley_separated_mask = fg_mask.copy()
        valley_separated_mask[dilated_crevices > 0] = 0

        # Morphological opening to clean small stray bits
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        valley_separated_mask = cv2.morphologyEx(valley_separated_mask, cv2.MORPH_OPEN, kernel_clean)

        # 3. Distance transform on valley-separated mask + Gaussian blur (15x15)
        dist_transform = cv2.distanceTransform(valley_separated_mask, cv2.DIST_L2, 5)
        dist_smooth = cv2.GaussianBlur(dist_transform, (15, 15), 0)
        dist_max = float(dist_smooth.max())

        # Fallback to fg_mask if valley separation removed too much foreground
        if dist_max <= 2.0:
            dist_transform = cv2.distanceTransform(fg_mask, cv2.DIST_L2, 5)
            dist_smooth = cv2.GaussianBlur(dist_transform, (15, 15), 0)
            dist_max = float(dist_smooth.max())

        # 4. Local maxima peaks with min_distance = int(0.18 * min(h, w)) and threshold_rel = 0.35
        k_size = max(15, int(min_peak_dist * 0.70))
        if k_size % 2 == 0:
            k_size += 1
        kernel_local = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        dilated_dist = cv2.dilate(dist_smooth, kernel_local)

        threshold_val = 0.35 * dist_max
        local_peaks_mask = (dist_smooth == dilated_dist) & (dist_smooth > threshold_val) & (fg_mask > 0)

        py, px = np.where(local_peaks_mask)
        peak_candidates = []
        for y, x in zip(py, px):
            peak_candidates.append((int(x), int(y), float(dist_smooth[y, x])))

        peak_candidates.sort(key=lambda c: c[2], reverse=True)

        accepted_peaks: List[Tuple[int, int]] = []
        for x, y, _ in peak_candidates:
            if not any(np.hypot(x - ax, y - ay) < min_peak_dist for ax, ay in accepted_peaks):
                accepted_peaks.append((x, y))
                if len(accepted_peaks) >= 12:
                    break

        # 5. Clamp total pile count between 2 and 12
        if len(accepted_peaks) < 2:
            # Lower threshold to find subtle secondary peaks
            thresh_val_low = 0.18 * dist_max
            min_dist_low = max(14.0, 0.14 * min_dim)
            local_peaks_low = (dist_smooth == dilated_dist) & (dist_smooth > thresh_val_low) & (fg_mask > 0)
            py2, px2 = np.where(local_peaks_low)
            candidates2 = [(int(x), int(y), float(dist_smooth[y, x])) for y, x in zip(py2, px2)]
            candidates2.sort(key=lambda c: c[2], reverse=True)
            for x, y, _ in candidates2:
                if not any(np.hypot(x - ax, y - ay) < min_dist_low for ax, ay in accepted_peaks):
                    accepted_peaks.append((x, y))
                    if len(accepted_peaks) >= 12:
                        break

        if len(accepted_peaks) < 2:
            # If still only 1 peak in a large pile covering > 45%, split along the pile's major dimension
            cnts, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if cnts:
                largest_c = max(cnts, key=cv2.contourArea)
                bx, by, bw, bh = cv2.boundingRect(largest_c)
                if bw >= bh:
                    p1 = (max(0, bx + int(bw * 0.35)), by + bh // 2)
                    p2 = (min(w - 1, bx + int(bw * 0.65)), by + bh // 2)
                else:
                    p1 = (bx + bw // 2, max(0, by + int(bh * 0.35)))
                    p2 = (bx + bw // 2, min(h - 1, by + int(bh * 0.65)))
                accepted_peaks = [p1, p2]
            else:
                accepted_peaks = [(w // 3, h // 2), (2 * w // 3, h // 2)]

        accepted_peaks = accepted_peaks[:12]

        # 6. Generate a bounding box around each valid peak (using watershed partitioning)
        peak_seeds = np.zeros((h, w), dtype=np.uint8)
        markers = np.zeros((h, w), dtype=np.int32)
        seed_r = max(4, int(min_peak_dist * 0.15))
        for i, (px_val, py_val) in enumerate(accepted_peaks, start=1):
            cv2.circle(peak_seeds, (px_val, py_val), seed_r, 255, -1)
            cv2.circle(markers, (px_val, py_val), seed_r, i, -1)

        kernel_bg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        sure_bg = cv2.dilate(fg_mask, kernel_bg, iterations=2)
        unknown = cv2.subtract(sure_bg, peak_seeds)

        markers = markers + 1
        markers[unknown == 255] = 0

        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        cv2.watershed(image_bgr, markers)

        pile_boxes: List[Tuple[int, int, int, int]] = []
        box_half = max(25, int(min_peak_dist * 0.70))

        for i, (px_val, py_val) in enumerate(accepted_peaks, start=2):
            comp = (markers == i).astype(np.uint8)
            cnts_comp, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            got_box = False
            if cnts_comp:
                largest_comp = max(cnts_comp, key=cv2.contourArea)
                if cv2.contourArea(largest_comp) >= 300:
                    bx, by, bw, bh = cv2.boundingRect(largest_comp)
                    aspect = float(bw) / float(bh) if bh > 0 else 1.0
                    if 0.15 <= aspect <= 6.5:
                        pile_boxes.append((bx, by, bw, bh))
                        got_box = True
            if not got_box:
                bx = max(0, px_val - box_half)
                by = max(0, py_val - box_half)
                bw = min(w - bx, 2 * box_half)
                bh = min(h - by, 2 * box_half)
                pile_boxes.append((bx, by, bw, bh))

        return pile_boxes

    def segment_with_pile_info(
        self,
        image_rgb: np.ndarray,
    ) -> Tuple[List[Tuple[int, int, int, int]], Dict[str, Any]]:
        """
        Two-Stage Hybrid Localization Strategy:
          - Stage 1: Pretrained Deep Learning Region Proposal Network (YOLO conf=0.15, iou=0.45)
            for high-accuracy individual instance proposals in both separated items and dense piles.
          - Fallback: Deterministic OpenCV Watershed & CLAHE valley separation (if offline or synthetic).
        """
        if image_rgb is None or image_rgb.size == 0:
            return [], {"is_pile": False, "peak_count": 0, "fg_ratio": 0.0}

        h, w = image_rgb.shape[:2]
        total_pixels = float(h * w)

        # 0. Stage 1: Pretrained Deep Learning Region Proposal Network (RPN)
        yolo_boxes = self.propose_regions_yolo(image_rgb, conf=0.15, iou=0.45)
        if yolo_boxes:
            logger.info(
                f"[ItemSegmenter] Stage 1 YOLO RPN proposed {len(yolo_boxes)} instance bounding boxes."
            )
            max_pairwise_iou = 0.0
            if len(yolo_boxes) > 1:
                for i in range(len(yolo_boxes)):
                    for j in range(i + 1, len(yolo_boxes)):
                        max_pairwise_iou = max(max_pairwise_iou, calculate_iou(yolo_boxes[i], yolo_boxes[j]))

            is_pile = (len(yolo_boxes) > 1 and max_pairwise_iou >= 0.15)
            pile_info = {
                "is_pile": is_pile,
                "peak_count": len(yolo_boxes),
                "fg_ratio": 0.50 if is_pile else 0.25,
                "method": "yolo_rpn",
            }
            return yolo_boxes, pile_info

        # 1. Clean foreground mask
        fg_mask = self.create_foreground_mask(image_rgb)
        fg_area = float(np.count_nonzero(fg_mask))
        fg_ratio = fg_area / total_pixels

        # 2. Analyze external contours
        cnts, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_contour_area = max(400, int(total_pixels * 0.02))
        valid_cnts = [c for c in cnts if cv2.contourArea(c) >= min_contour_area]

        largest_cnt_area = cv2.contourArea(max(valid_cnts, key=cv2.contourArea)) if valid_cnts else 0.0
        largest_cnt_ratio = largest_cnt_area / total_pixels

        # MODE B: Dense Homogeneous Pile Mode (1 large foreground contour covers > 45% of image area)
        is_dense_pile = (largest_cnt_ratio > 0.45) or (fg_ratio > 0.45 and len(valid_cnts) <= 1)
        if is_dense_pile:
            logger.info(
                f"[ItemSegmenter] Dense Homogeneous Pile Mode triggered "
                f"(largest_contour={largest_cnt_ratio:.2%}, fg_ratio={fg_ratio:.2%})."
            )
            pile_boxes = self.segment_dense_pile(image_rgb, fg_mask)
            pile_info = {
                "is_pile": True,
                "peak_count": len(pile_boxes),
                "fg_ratio": round(fg_ratio, 3),
            }
            return pile_boxes, pile_info

        # MODE A: Separated Objects Mode (2+ distinct separated contours with background between them)
        if len(valid_cnts) >= 2:
            logger.info(
                f"[ItemSegmenter] Separated Objects Mode triggered ({len(valid_cnts)} distinct contours)."
            )
            raw_boxes = [cv2.boundingRect(c) for c in valid_cnts]
            filtered_boxes = self.filter_candidate_boxes(raw_boxes, (h, w))
            pile_info = {
                "is_pile": False,
                "peak_count": len(filtered_boxes),
                "fg_ratio": round(fg_ratio, 3),
            }
            return filtered_boxes, pile_info

        # Fallback for single smaller item or touching items (< 45% area)
        raw_boxes, raw_peaks = self.segment_watershed(image_rgb, fg_mask)
        if not raw_boxes and valid_cnts:
            raw_boxes = [cv2.boundingRect(c) for c in valid_cnts]

        filtered_boxes = self.filter_candidate_boxes(raw_boxes, (h, w))
        if len(filtered_boxes) <= 1:
            final_boxes = [(0, 0, w, h)]
        else:
            final_boxes = filtered_boxes

        pile_info = {
            "is_pile": False,
            "peak_count": max(len(final_boxes), raw_peaks),
            "fg_ratio": round(fg_ratio, 3),
        }
        return final_boxes, pile_info

    def segment(self, image_rgb: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Segments food items from an RGB image.
        Uses Two-Mode Counting Strategy to isolate items without undercounting piles.
        Returns a list of bounding boxes (x, y, w, h).
        """
        boxes, _ = self.segment_with_pile_info(image_rgb)
        return boxes

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
    def get_square_context_crop(
        image_rgb: np.ndarray,
        box: Tuple[int, int, int, int],
        margin_ratio: float = 0.25,
    ) -> np.ndarray:
        """
        Expands the bounding box by 25% margin on all sides and converts it into
        a square crop (clamped to image bounds), ensuring the CNN sees the full
        vegetable outline and context rather than a zoomed-in skin texture patch.
        """
        h, w = image_rgb.shape[:2]
        bx, by, bw, bh = box

        max_dim = max(bw, bh)
        side = int(max_dim * (1.0 + 2 * margin_ratio))
        side = min(side, min(h, w))

        cx = bx + bw // 2
        cy = by + bh // 2

        x1 = cx - side // 2
        y1 = cy - side // 2
        x2 = x1 + side
        y2 = y1 + side

        if x1 < 0:
            x2 = min(w, x2 - x1)
            x1 = 0
        if y1 < 0:
            y2 = min(h, y2 - y1)
            y1 = 0
        if x2 > w:
            x1 = max(0, x1 - (x2 - w))
            x2 = w
        if y2 > h:
            y1 = max(0, y1 - (y2 - h))
            y2 = h

        crop = image_rgb[y1:y2, x1:x2].copy()
        if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
            return image_rgb.copy()
        return crop

    @staticmethod
    def annotate_image(
        image_rgb: np.ndarray,
        detections: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Draws bounding boxes, ingredient names, counts, and expiry days on a copy of image_rgb.
        Color coding strictly based on estimated_expiry_days:
          - 'Use First' (<= 3d): Rose/Red (RGB: 225, 29, 72)
          - 'Medium' (4-7d): Amber/Yellow (RGB: 217, 119, 6)
          - 'Fresh' (> 7d): Emerald/Green (RGB: 5, 150, 105)
        [USE FIRST] is ONLY appended to the label if estimated_expiry_days <= 3.
        """
        annotated = image_rgb.copy()
        h, w = annotated.shape[:2]

        color_fresh = (5, 150, 105)     # Emerald/Green
        color_medium = (217, 119, 6)     # Amber/Yellow
        color_use_first = (225, 29, 72)  # Rose/Red

        for idx, det in enumerate(detections, 1):
            box = det.get("box", {})
            bx = int(box.get("x", 0))
            by = int(box.get("y", 0))
            bw = int(box.get("w", w))
            bh = int(box.get("h", h))

            name = det.get("ingredient", "Item").replace("_", " ").title()
            expiry = int(det.get("expiry_days", 7))

            # Strict expiration-based color & tag
            if expiry <= 3:
                color = color_use_first
                tag = f"#{idx} {name} ({expiry}d) [USE FIRST]"
            elif expiry <= 7:
                color = color_medium
                tag = f"#{idx} {name} ({expiry}d)"
            else:
                color = color_fresh
                tag = f"#{idx} {name} ({expiry}d)"

            thickness = max(2, int(min(h, w) * 0.004))
            cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), color, thickness)

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.45, min(0.85, w * 0.0008))
            font_thickness = max(1, int(thickness * 0.7))
            (text_w, text_h), _ = cv2.getTextSize(tag, font, font_scale, font_thickness)

            tag_y1 = max(0, by - text_h - 10)
            tag_y2 = by
            tag_x1 = bx
            tag_x2 = min(w, bx + text_w + 12)

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
