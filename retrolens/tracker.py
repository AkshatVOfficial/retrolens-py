from typing import List

import mediapipe as mp
import numpy as np

from .config import PipelineConfig


class HandTracker:
    def __init__(self, cfg: PipelineConfig):
        self.cfg = cfg
        self._mp_hands = mp.solutions.hands
        self._mp_draw = mp.solutions.drawing_utils
        self._draw_spec = self._mp_draw.DrawingSpec(color=(0, 255, 255), thickness=1, circle_radius=2)
        self.detector = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=cfg.max_num_hands,
            model_complexity=cfg.model_complexity,
            min_detection_confidence=cfg.min_detection_confidence,
            min_tracking_confidence=cfg.min_tracking_confidence,
        )
        self._smoothed_tips: List[np.ndarray] = []

    def process(self, rgb_frame: np.ndarray):
        return self.detector.process(rgb_frame)

    def smooth_tips(self, hand_idx: int, raw_tips: np.ndarray) -> np.ndarray:
        """Blend this frame's fingertip coordinates with the running average
        for that hand slot. ``hand_idx`` is MediaPipe's per-frame detection
        order, which is a reasonable proxy for hand identity within a single
        gesture but isn't guaranteed stable if a hand briefly leaves frame."""
        alpha = self.cfg.smoothing_alpha
        while len(self._smoothed_tips) <= hand_idx:
            self._smoothed_tips.append(raw_tips.copy())
        prev = self._smoothed_tips[hand_idx]
        smoothed = alpha * raw_tips + (1 - alpha) * prev
        self._smoothed_tips[hand_idx] = smoothed
        return smoothed

    def reset_smoothing(self, active_hand_count: int) -> None:
        """Drop smoothing state for hand slots that are no longer visible so
        a returning hand doesn't snap back to a stale average."""
        self._smoothed_tips = self._smoothed_tips[:active_hand_count]

    def draw(self, frame, hand_landmarks) -> None:
        self._mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            self._mp_hands.HAND_CONNECTIONS,
            self._draw_spec,
            self._draw_spec,
        )

    def close(self) -> None:
        self.detector.close()
