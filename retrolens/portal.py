from typing import Callable, List, Tuple

import cv2
import numpy as np

Point = Tuple[int, int]
FilterFn = Callable[[np.ndarray, float], np.ndarray]


class PortalRenderer:
    @staticmethod
    def render(
        frame: np.ndarray,
        pts: List[Point],
        filter_fn: FilterFn,
        intensity: float = 1.0,
        feather: int = 3,
        border_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> np.ndarray:
        poly = np.array(pts, dtype=np.int32)
        x, y, w, h = cv2.boundingRect(poly)
        x, y = max(0, x), max(0, y)
        w = min(w, frame.shape[1] - x)
        h = min(h, frame.shape[0] - y)

        if w <= 10 or h <= 10:
            return frame

        roi = frame[y : y + h, x : x + w]
        processed = filter_fn(roi, intensity)
        if processed.shape != roi.shape:
            processed = cv2.resize(processed, (w, h))

        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, [poly - [x, y]], 255)
        if feather > 0:
            mask = cv2.GaussianBlur(mask, (feather * 2 + 1, feather * 2 + 1), 0)
        mask_f = (mask.astype(np.float32) / 255.0)[..., None]

        blended = roi.astype(np.float32) * (1 - mask_f) + processed.astype(np.float32) * mask_f
        frame[y : y + h, x : x + w] = blended.astype(np.uint8)

        cv2.polylines(frame, [poly], isClosed=True, color=border_color, thickness=2, lineType=cv2.LINE_AA)
        return frame
