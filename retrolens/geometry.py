from typing import List, Sequence, Tuple

import numpy as np

Point = Tuple[int, int]


class GeometryUtils:
    @staticmethod
    def euclidean_dist(p1: Sequence[float], p2: Sequence[float]) -> float:
        return float(np.hypot(p1[0] - p2[0], p1[1] - p2[1]))

    @staticmethod
    def is_fist_closed(landmarks, w: int, h: int, threshold: float) -> bool:
        wrist = np.array([landmarks[0].x * w, landmarks[0].y * h])
        tips = (8, 12, 16, 20)
        distances = [
            np.linalg.norm(np.array([landmarks[t].x * w, landmarks[t].y * h]) - wrist)
            for t in tips
        ]
        return float(np.mean(distances)) < threshold

    @staticmethod
    def is_hand_rotated(thumb: Point, index: Point) -> bool:
        dx, dy = index[0] - thumb[0], index[1] - thumb[1]
        return (dy > 25) or (abs(dx) > abs(dy) * 1.1)

    @staticmethod
    def sort_quad_clean(pts: List[Point]) -> np.ndarray:
        """Order 4 points into a non-self-intersecting quad (TL, TR, BR, BL)."""
        arr = np.array(pts, dtype=np.float32)
        x_sorted = arr[np.argsort(arr[:, 0]), :]
        leftmost = x_sorted[:2, :][np.argsort(x_sorted[:2, 1]), :]
        rightmost = x_sorted[2:, :][np.argsort(x_sorted[2:, 1]), :]
        return np.array([leftmost[0], rightmost[0], rightmost[1], leftmost[1]], dtype=np.int32)

    @staticmethod
    def sort_quad_bowtie(pts: List[Point]) -> np.ndarray:
        """Deliberately cross two corners, producing the 'bowtie' portal shape."""
        arr = np.array(pts, dtype=np.float32)
        x_sorted = arr[np.argsort(arr[:, 0]), :]
        leftmost = x_sorted[:2, :][np.argsort(x_sorted[:2, 1]), :]
        rightmost = x_sorted[2:, :][np.argsort(x_sorted[2:, 1]), :]
        return np.array([leftmost[0], rightmost[1], rightmost[0], leftmost[1]], dtype=np.int32)

    @staticmethod
    def centroid(pts: Sequence[Point]) -> Tuple[float, float]:
        arr = np.array(pts, dtype=np.float32)
        c = arr.mean(axis=0)
        return float(c[0]), float(c[1])
