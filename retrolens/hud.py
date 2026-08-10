import time
from typing import List

import cv2
import numpy as np


class Hud:
    FONT = cv2.FONT_HERSHEY_SIMPLEX

    @staticmethod
    def draw(
        frame: np.ndarray,
        *,
        mode_str: str,
        filter_names: List[str],
        active_idx: int,
        fps: float,
        intensity: float,
        is_recording: bool,
        rec_elapsed: float,
        show_help: bool,
    ) -> np.ndarray:
        h, w = frame.shape[:2]

        cv2.rectangle(frame, (0, 0), (w, 34), (20, 20, 20), -1)
        cv2.putText(frame, f"MODE: {mode_str}", (10, 23), Hud.FONT, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"FPS: {fps:4.1f}", (w - 110, 23), Hud.FONT, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        n = len(filter_names)
        prev_name = filter_names[(active_idx - 1) % n]
        cur_name = filter_names[active_idx]
        next_name = filter_names[(active_idx + 1) % n]
        cv2.rectangle(frame, (0, h - 34), (w, h), (20, 20, 20), -1)
        cv2.putText(frame, prev_name, (16, h - 12), Hud.FONT, 0.42, (120, 120, 120), 1, cv2.LINE_AA)
        cur_x = max(0, w // 2 - 90)
        cv2.putText(frame, f"> {cur_name.upper()} <", (cur_x, h - 12), Hud.FONT, 0.55, (0, 255, 0), 2, cv2.LINE_AA)
        next_x = max(0, w - 150)
        cv2.putText(frame, next_name, (next_x, h - 12), Hud.FONT, 0.42, (120, 120, 120), 1, cv2.LINE_AA)

        bar_x, bar_y, bar_w, bar_h = 10, 42, 130, 8
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (90, 90, 90), 1)
        fill = int(bar_w * float(np.clip(intensity, 0.0, 1.0)))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill, bar_y + bar_h), (0, 200, 255), -1)
        cv2.putText(frame, "INTENSITY", (bar_x + bar_w + 8, bar_y + 8), Hud.FONT, 0.35, (180, 180, 180), 1, cv2.LINE_AA)

        if is_recording:
            if int(time.time() * 2) % 2 == 0:
                cv2.circle(frame, (w - 24, 45), 6, (0, 0, 255), -1)
            cv2.putText(frame, f"REC {rec_elapsed:5.1f}s", (w - 130, 50), Hud.FONT, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

        if show_help:
            Hud._draw_help(frame)
        return frame

    @staticmethod
    def _draw_help(frame: np.ndarray) -> None:
        h, w = frame.shape[:2]
        panel_w, panel_h = 400, 300
        x0, y0 = max(0, w // 2 - panel_w // 2), max(0, h // 2 - panel_h // 2)
        x1, y1 = min(w, x0 + panel_w), min(h, y0 + panel_h)

        panel = frame.copy()
        cv2.rectangle(panel, (x0, y0), (x1, y1), (15, 15, 15), -1)
        cv2.addWeighted(panel, 0.85, frame, 0.15, 0, dst=frame)
        cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 255, 255), 1)

        lines = [
            ("RETROLENS CONTROLS", (0, 255, 255), 0.58),
            ("Pinch thumb+index: next filter", (230, 230, 230), 0.45),
            ("N / P: next / previous filter", (230, 230, 230), 0.45),
            ("1-9: jump straight to a filter", (230, 230, 230), 0.45),
            ("Both fists closed: toggle 3D mode", (230, 230, 230), 0.45),
            ("C: toggle 3D mode manually", (230, 230, 230), 0.45),
            ("Spread hands apart: raise intensity", (230, 230, 230), 0.45),
            ("S: screenshot    R: start/stop recording", (230, 230, 230), 0.45),
            ("H: toggle this help    Q: quit", (230, 230, 230), 0.45),
        ]
        y = y0 + 34
        for text, color, scale in lines:
            cv2.putText(frame, text, (x0 + 18, y), Hud.FONT, scale, color, 1, cv2.LINE_AA)
            y += 30
